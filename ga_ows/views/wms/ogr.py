from ga_ows.views.wms.base import WMSAdapterBase, WMSCache

from django.contrib.gis.geos import Point
from osgeo import osr
from ga_ows.rendering.cairo_geodjango_renderer import RenderingContext
from ga_ows.utils import create_spatialref

class OGRDatasetCollectionAdapter(WMSAdapterBase):
    def __init__(self, collection_name, storage_backend):
        pass

class OGRDatasetWMSAdapter(WMSAdapterBase):
    """ A default implementation of the WMS adapter for an OGR dataset."""

    def __init__(self, dataset, styles, time_property=None, elevation_property=None, version_property=None, requires_time=False, requires_version=False, requires_elevation=False, cache_route='default', simplify=False):
        """
        :param dataset: An OGR dataset to expose.
        :param styles: A map of style names to :class:`ga_ows.rendering.styler.Stylesheet`
        :param time_property: The property name of "time" when that is handled specifically
        :param elevation_property:  The property name that contains elevation when that is handled specifically
        :param version_property: THe property name that contains the record version if that is handled specifically.
        :param cache_route: The MongoDB route name (in :const:`settings.MONGODB_ROUTES).  Defaults to 'default'
        :param simplify: Simplify geometry based on the pixel size if true.  Only useful for polylines / polygons.  May break complicated geometries, so the default is False.  Set to true if renders are unacceptably slow.
        :return:
        """
        super(OGRDatasetWMSAdapter, self).__init__(
            styles,
            requires_time=requires_time,
            requires_elevation=requires_elevation,
            requires_version=requires_version
        )

        self.time_property = time_property
        self.elevation_property = elevation_property
        self.version_property = version_property
        self.dataset = dataset
        self.cache = WMSCache(cache_route, self.dataset.GetName() + "__wms_cache")
        self.simplify = simplify

    def cache_result(self, item, **kwargs):
        locator = kwargs
        if 'fresh' in locator:
            del locator['fresh']
        locator['model'] = self.dataset.GetName()

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
            'model' : self.dataset.GetName()
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
        t_srs = self.dataset.GetSpatialRef()
        crx = osr.CoordinateTransformation(s_srs, t_srs)
        wherex, wherey, _0 = crx.TransformPoint(wherex, wherey, 0)

        if not filter:
            for layer in layers:
                l = self.dataset.GetLayerByName(layer)
                l.ResetReading()
                l.SetSpatialFilterRect(wherex, wherey, wherex+0.0001, wherey+0.0001)
                return [f for f in l]
        else:
            for layer in layers:
                l = self.dataset.GetLayerByName(layer)
                l.ResetReading()
                l.SetSpatialFilterRect(wherex, wherey, wherex+0.0001, wherey+0.0001)
                return [f for f in l] # TODO apply filter.

    def get_2d_dataset(self, **kwargs):
        # TODO apply filtering.  Should start supporting CQL soon.
        layers, srs, bbox, width, height, styles, bgcolor, transparent, time, elevation, v, filter = [kwargs[k] if k in kwargs else None for k in ['layers', 'srs', 'bbox', 'width', 'height', 'styles', 'bgcolor', 'transparent', 'time', 'elevation', 'v', 'filter']]
        ds = self.dataset.Clone()
        minx,miny,maxx,maxy = bbox
        if filter is None:
            filter = {}

        if self.requires_time and not time:
            raise Exception("this service requires a time parameter")
        if self.requires_elevation and not elevation:
            raise Exception('this service requires an elevation')

        ss = None
        if type(self.styles) is dict:
            if not styles and 'default' in self.styles:
                ss = self.styles['default']
            elif styles:
                ss = self.styles[styles]
        else:
            ss = self.styles

        ctx = RenderingContext(ss, minx, miny, maxx, maxy, width, height)

        t_srs = osr.SpatialReference()
        t_srs.ImportFromEPSG(int(srs))
        l0 = self.dataset.GetLayer(0)
        s_srs = l0.GetSpatialRef()

        s_mins = Point(minx, miny, srid=t_srs.wkt)
        s_maxs = Point(maxx, maxy, srid=t_srs.wkt)
        s_mins.transform(s_srs.wkt)
        s_maxs.transform(s_srs.wkt)

        ls = {}
        crx = osr.CoordinateTransformation(s_srs, t_srs)

        def xform(f):
            f.SetGeometry(f.geometry().Transform(crx))

        for query_layer in layers:
            ls[query_layer] = ds.GetLayerByName(query_layer)
            ls[query_layer].ResetReading()
            ls[query_layer].SetSpatialFilterRect(s_mins.x, s_mins.y, s_maxs.x, s_maxs.y)

        for query_layer in layers:
            mysrs = self.nativesrs(query_layer)
            if mysrs == srs:
                ctx.render(ls[query_layer], lambda k: k[query_layer])
            else:
                ctx.render(ls[query_layer], lambda k: xform(k[query_layer]))

        return ctx.surface

    def layerlist(self):
        return [self.dataset.GetLayer(k).GetName() for k in range(self.dataset.GetLayerCount())]

    def nativesrs(self, layer):
        return self.dataset.GetLayerByName(layer).GetSpatialRef()

    def nativebbox(self):
        import sys
        minx, miny, maxx, maxy = sys.maxint, sys.maxint, -sys.maxint, -sys.maxint
        for k in range(self.dataset.GetLayerCount()):
            l = self.dataset.GetLayer(k)
            xminx, xmaxx, xminy, xmaxy = l.GetExtent()
            minx = min(xminx, minx)
            miny = min(xminy, miny)
            maxy = max(xmaxy, maxy)
            maxx = max(xmaxx, maxx)

        return (minx, miny, maxx, maxy)

    def get_valid_times(self, **kwargs):
        raise NotImplementedError()

    def get_valid_versions(self, **kwargs):
        raise NotImplementedError()

    def get_valid_elevations(self, **kwargs):
        raise NotImplementedError()

    def get_service_boundaries(self):
        return self.nativebbox()

    def get_layer_descriptions(self):
        ret = []
        for k in range(self.dataset.GetLayerCount()):
            l = self.dataset.GetLayer(k)
            for field in l.schema:
                layer = {}
                layer['name'] = l.GetName()
                layer['title'] = l.GetName()
                layer['srs'] = l.GetSpatialRef().ExportToXML()
                layer['queryable'] = True
                layer['minx'], layer['maxx'], layer['miny'], layer['maxy'] = l.GetExtent()
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
                    ll_minx, ll_miny, _0 = crx.TransformPoint(layer['minx'], layer['miny'], 0)
                    ll_maxx, ll_maxy, _0 = crx.TransformPoint(layer['maxx'], layer['maxy'], 0)

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


