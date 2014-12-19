from ga_ows.views.wms.base import WMSAdapterBase, WMSCache

from collections import defaultdict
from django.contrib.gis.db.models.proxy import GeometryProxy
from django.contrib.gis.db.models import GeometryField
import shapely.geometry as g
from django.contrib.gis.geos import GEOSGeometry, Point
from osgeo import osr
from django.contrib.gis import gdal as djgdal
from ga_ows.rendering.cairo_geodjango_renderer import RenderingContext
from ga_ows.utils import create_spatialref


class GeoDjangoWMSAdapter(WMSAdapterBase):
    """ A default implementation of the WMS adapter for an object in the GeoDjango ORM."""

    def __init__(self, cls, styles, time_property=None, elevation_property=None, version_property=None, requires_time=False, requires_version=False, requires_elevation=False, cache_route='default', simplify=False):
        """
        :param cls: The model class to expose
        :param styles: A map of style names to :class:`ga_ows.rendering.styler.Stylesheet`
        :param time_property: The property name of "time" when that is handled specifically
        :param elevation_property:  The property name that contains elevation when that is handled specifically
        :param version_property: THe property name that contains the record version if that is handled specifically.
        :param cache_route: The MongoDB route name (in :const:`settings.MONGODB_ROUTES).  Defaults to 'default'
        :param simplify: Simplify geometry based on the pixel size if true.  Only useful for polylines / polygons.  May break complicated geometries, so the default is False.  Set to true if renders are unacceptably slow.
        :return:
        """
        super(GeoDjangoWMSAdapter, self).__init__(
            styles,
            requires_time=requires_time,
            requires_elevation=requires_elevation,
            requires_version=requires_version
        )

        self.time_property = time_property
        self.elevation_property = elevation_property
        self.version_property = version_property
        self.cls = cls
        self.cache = WMSCache.for_geodjango_model(self.cls, route=cache_route)
        self.simplify = simplify

    def cache_result(self, item, **kwargs):
        locator = kwargs
        if 'fresh' in locator:
            del locator['fresh']
        locator['model'] = self.cls._meta.object_name

        self.cache.save(item, **kwargs)

    def get_cache_record(self, layers, srs, bbox, width, height, styles, format, bgcolor, transparent, time, elevation, v, filter, **kwargs):
        locator = {
            'layers' : layers,
            'srs' : srs,
            'bbox' : bbox,
            'width' : width,
            'height' : height,
            'styles' : styles,
            'format' : format,
            'bgcolor' : bgcolor,
            'transparent' : transparent,
            'time' : time,
            'elevation' : elevation,
            'v' : v,
            'filter' : filter,
            'model' : self.cls._meta.object_name
        }

        return self.cache.locate(**locator)

    def get_feature_info(self, wherex, wherey, layers, callback, format, feature_count, srs, filter):
        if type(srs) is int:
            kind='srid'
        elif srs.upper().startswith('EPSG'):
            kind=None
        elif srs.startswith('-') or srs.startswith('+'):
            kind='proj'
        else:
            kind='wkt'

        s_srs = create_spatialref(srs, srs_format=kind)
        t_srs = self.cls.srs
        crx = osr.CoordinateTransformation(s_srs, t_srs)
        wherex, wherey, _0 = crx.TransformPoint(wherex, wherey, 0)

        if not filter:
            return [self.cls.objects.filter({ layer + "__contains" : g.Point(wherex, wherey) }).limit(feature_count).values() for layer in layers]
        else:
            return [self.cls.objects.filter({ layer + "__contains" : g.Point(wherex, wherey) }).filter(**filter).limit(feature_count).values() for layer in layers]

    def get_2d_dataset(self, **kwargs):
        layers, srs, bbox, width, height, styles, bgcolor, transparent, time, elevation, v, filter = [kwargs[k] if k in kwargs else None for k in ['layers', 'srs', 'bbox', 'width', 'height', 'styles', 'bgcolor', 'transparent', 'time', 'elevation', 'v', 'filter']]
        minx,miny,maxx,maxy = bbox

        if filter is None:
            filter = {}

        if self.requires_time and not time:
            raise Exception("this service requires a time parameter")
        if self.requires_elevation and not elevation:
            raise Exception('this service requires an elevation')

        ss = None
        required_fields = tuple()
        if type(self.styles) is dict:
            if not styles and 'default' in self.styles:
                ss = self.styles['default']
            elif styles:
                ss = self.styles[styles]
        else:
            ss = self.styles
            required_fields = ss.required_fields

        ctx = RenderingContext(ss, minx, miny, maxx, maxy, width, height)

        t_srs = djgdal.SpatialReference(srs)
        s_srs = djgdal.SpatialReference(self.nativesrs(layers[0]))

        s_mins = Point(minx, miny, srid=t_srs.wkt)
        s_maxs = Point(maxx, maxy, srid=t_srs.wkt)
        s_mins.transform(s_srs.wkt)
        s_maxs.transform(s_srs.wkt)

        geom = GEOSGeometry('POLYGON(({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))'.format(
            minx=s_mins.x,
            miny=s_mins.y,
            maxx=s_maxs.x,
            maxy=s_maxs.y
        ))

        for query_layer in layers:
            filter[query_layer + "__bboverlaps"] = geom


        def xform(g):
            if self.simplify:
                k = g.simplify((maxx-minx) / width)
                if k:
                    g = k
            g.transform(t_srs.wkt)
            return g

        for query_layer in layers:
            qs = self.cls.objects.filter(**filter)
            if required_fields:
                qs = qs.only(*required_fields).values(*required_fields)
            else:
                qs = qs.values()

            mysrs = self.nativesrs(query_layer)
            if mysrs == srs:
                ctx.render(qs, lambda k: k[query_layer])
            else:
                ctx.render(qs, lambda k: xform(k[query_layer]))

        return ctx.surface

    def layerlist(self):
        for k,v in self.cls.__dict__.items():
            if type(v) is GeometryProxy:
                yield k

    def nativesrs(self, layer):
        return self.cls.__dict__[layer]._field.srid

    def nativebbox(self):
        return self.cls.objects.extent()

    def get_valid_times(self, **kwargs):
        if self.time_property:
            qs = self.cls.objects.all()
            if 'filter' in kwargs:
                qs = qs.filter(**kwargs['filter'])
            return [t[0] for t in qs.values_list(self.time_property)]

    def get_valid_versions(self, **kwargs):
        qs = self.cls.objects.all()
        if 'filter' in kwargs:
            qs = qs.filter(**kwargs['filter'])

        if self.version_property and self.time_property:
            ret = defaultdict(lambda: [])
            for t in qs.values_list(self.time_property, self.version_property):
                ret[t[0]].append(t[1])
            return ret
        elif self.version_property:
            return [t[0] for t in qs.values_list(self.version_property)]

    def get_valid_elevations(self, **kwargs):
        qs = self.cls.objects.all()
        if 'filter' in kwargs:
            qs = qs.filter(**kwargs['filter'])

        if self.elevation_property:
            return [t[0] for t in qs.values_list(self.elevation_property)]

    def get_service_boundaries(self):
        return self.nativebbox()

    def get_layer_descriptions(self):
        ret = []
        for field in filter(lambda f: isinstance(f, GeometryField), self.cls._meta.fields):
            layer = dict()
            layer['name'] = field.name
            layer['title'] = field.verbose_name
            layer['srs'] = field.srid
            layer['queryable'] = True
            minx, miny, maxx, maxy = self.cls.objects.all().extent()
            layer['minx'] = minx
            layer['miny'] = miny
            layer['maxx'] = maxx
            layer['maxy'] = maxy
            if field.srid == 4326:
                layer['ll_minx'] = layer['minx']
                layer['ll_miny'] = layer['miny']
                layer['ll_maxx'] = layer['maxx']
                layer['ll_maxy'] = layer['maxy']
            else:
                s_srs = osr.SpatialReference()
                s_srs.ImportFromEPSG(field.srid)
                t_srs = osr.SpatialReference()
                t_srs.ImportFromEPSG(4326)
                crx = osr.CoordinateTransformation(s_srs, t_srs)
                ll_minx, ll_miny, _0 = crx.TransformPoint(minx, miny, 0)
                ll_maxx, ll_maxy, _0 = crx.TransformPoint(maxx, maxy, 0)

                layer['ll_minx'] = ll_minx
                layer['ll_miny'] = ll_miny
                layer['ll_maxx'] = ll_maxx
                layer['ll_maxy'] = ll_maxy
            layer['styles'] = []
            if isinstance(self.styles, dict):
                for style in self.styles.keys():
                    layer['styles'].append({
                        "name" : style,
                        "title" : style,
                        "legend_width" : 0,
                        "legend_height" : 0,
                        "legend_url" : ""
                    })
                    if hasattr(self.styles[style], 'legend_url'):
                        layer['styles'][-1]['legend_url'] = self.styles[style].legend_url
            ret.append(layer)
        return ret
