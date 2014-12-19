# from ga_ows.views import wms, wfs
import shutil
import json
from zipfile import ZipFile

import pandas
from django.contrib.gis.geos import Polygon
from ga_resources.models import SpatialMetadata
import os
from osgeo import osr, ogr
from . import Driver
from pandas import DataFrame
from shapely import wkb
from django.template.defaultfilters import slugify
import re


def ogrfield(elt):
    return re.sub('-', '_', slugify(elt).encode('ascii'))[0:10]


def identity(x):
    return '"' + x + '"' if isinstance(x, basestring) else str(x)


dtypes = {
    'int64': ogr.OFTInteger,
    'float64': ogr.OFTReal,
    'object': ogr.OFTString,
    'datetime64[ns]': ogr.OFTDateTime
}
geomTypes = {
    'GeometryCollection': ogr.wkbGeometryCollection,
    'LinearRing': ogr.wkbLinearRing,
    'LineString': ogr.wkbLineString,
    'MultiLineString': ogr.wkbMultiLineString,
    'MultiPoint': ogr.wkbMultiPoint,
    'MultiPolygon': ogr.wkbMultiPolygon,
    'Point': ogr.wkbPoint,
    'Polygon': ogr.wkbPolygon
}


def transform(geom, crx):
    if crx:
        geom.Transform(crx)
    return geom


class OGRDriver(Driver):
    def ready_data_resource(self, **kwargs):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        slug, srs = super(OGRDriver, self).ready_data_resource(**kwargs)
        cfg = self.resource.driver_config

        mapnik_config = {
            'type' : 'ogr',
            'base' : self.cache_path,
        }

        if 'sublayer' in kwargs:
            mapnik_config['layer'] = kwargs['sublayer']
        elif 'layer' in cfg:
            mapnik_config['layer'] = cfg['layer']
        elif 'layer_by_index' in cfg:
            mapnik_config['layer_by_index'] = cfg['layer_by_index']
        else:
            mapnik_config['layer_by_index'] = 0

        if 'multiple_geometries' in cfg:
            mapnik_config['multiple_geometries'] = cfg['multiple_geometries']

        if 'encoding' in cfg:
            mapnik_config['encoding'] = cfg['encoding']

        if 'string' in cfg:
            mapnik_config['string'] = cfg['string']
        else:
            mapnik_config['file'] = self.get_master_filename()

        return slug, srs, mapnik_config

    def get_master_filename(self):
        cfg = self.resource.driver_config

        if 'file' in cfg:
            return self.cache_path + '/' + cfg['file']
        elif 'xtn' in cfg:
            return self.get_filename(cfg['xtn'])
        else:
            return self.get_filename('')[:-1]  # omit the trailing period and assume we're using the directory (such as for MapInfo)


    def compute_fields(self, **kwargs):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        super(OGRDriver, self).compute_fields(**kwargs)

        # if we have a zip archive, we should expand it now
        archive_filename = self.get_filename('zip')
        if os.path.exists(archive_filename):
            archive = ZipFile(self.cached_basename + self.src_ext)
            os.mkdir(self.cached_basename) # we will put everything cached underneath the cached base directory
            archive.extractall(self.cached_basename)

        ds = ogr.Open(self.get_master_filename())
        lyr = ds.GetLayerByIndex(0) if 'sublayer' not in kwargs else ds.GetLayerByName(kwargs['sublayer'])
        xmin, xmax, ymin, ymax = lyr.GetExtent()
        crs = lyr.GetSpatialRef()

        self.resource.spatial_metadata.native_srs = crs.ExportToProj4()
        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        crx = osr.CoordinateTransformation(crs, e4326)
        x04326, y04326, _ = crx.TransformPoint(xmin, ymin)
        x14326, y14326, _ = crx.TransformPoint(xmax, ymax)
        self.resource.spatial_metadata.bounding_box = Polygon.from_bbox((x04326, y04326, x14326, y14326))
        self.resource.spatial_metadata.native_bounding_box = Polygon.from_bbox((xmin, ymin, xmax, ymax))
        self.resource.spatial_metadata.three_d = False

        self.resource.spatial_metadata.save()
        self.resource.save()


    def get_data_fields(self, **kwargs):
        _, _, result = self.ready_data_resource(**kwargs)
        ds = ogr.Open(self.get_master_filename())
        lyr = ds.GetLayerByIndex(0) if 'layer' not in kwargs else ds.GetLayerByName(kwargs['sublayer'])
        return [(field.name, field.GetTypeName(), field.width) for field in lyr.schema]

    def get_data_for_point(self, wherex, wherey, srs, **kwargs):
        result, x1, y1, epsilon = super(OGRDriver, self).get_data_for_point(wherex, wherey, srs, **kwargs)
        ds = ogr.Open(result['file'])
        lyr = ds.GetLayerByIndex(0) if 'sublayer' not in kwargs else ds.GetLayerByName(kwargs['sublayer'])

        if epsilon == 0:
            lyr.SetSpatialFilter(ogr.CreateGeometryFromWkt("POINT({x1} {y1})".format(**locals())))
        else:
            from django.contrib.gis import geos

            wkt = geos.Point(x1, y1).buffer(epsilon).wkt
            print wkt
            lyr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))
        return [f.items() for f in lyr]

    def attrquery(self, key, value):
        key, op = key.split('__')
        op = {
            'gt': ">",
            'gte': ">=",
            'lt': "<",
            'lte': '<=',
            'startswith': 'LIKE',
            'endswith': 'LIKE',
            'istartswith': 'ILIKE',
            'iendswith': 'ILIKE',
            'icontains': "ILIKE",
            'contains': "LIKE",
            'in': 'IN',
            'ne': "<>"
        }[op]

        value = {
            'gt': identity,
            'gte': identity,
            'lt': identity,
            'lte': identity,
            'startswith': lambda x: '%' + x,
            'endswith': lambda x: x + '%',
            'istartswith': lambda x: '%' + x,
            'iendswith': lambda x: x + '%',
            'icontains': lambda x: '%' + x + '%',
            'contains': lambda x: '%' + x + '%',
            'in': lambda x: x if isinstance(x, basestring) else '(' + ','.join(identity(a) for a in x) + ')',
            'ne': identity
        }[op](value)

        return ' '.join([key, op, value])

    def as_dataframe(self, **kwargs):
        """
        Creates a dataframe object for a shapefile's main layer using layer_as_dataframe. This object is cached on disk for
        layer use, but the cached copy will only be picked up if the shapefile's mtime is older than the dataframe's mtime.

        :param shp: The shapefile
        :return:
        """

        dfx_path = self.get_filename('dfx')

        if len(kwargs) != 0:
            ds = ogr.Open(self.get_master_filename())
            lyr = ds.GetLayerByIndex(0)
            crx = xrc = None

            if 'bbox' in kwargs:
                minx, miny, maxx, maxy = kwargs['bbox']

                if 'srs' in kwargs:
                    if isinstance(kwargs['srs'], basestring):
                        s_srs = osr.SpatialReference()
                        if kwargs['srs'].lower().startswith('epsg:'):
                            s_srs.ImportFromEPSG(int(kwargs['srs'].split(':')[1]))
                        else:
                            s_srs.ImportFromProj4(kwargs['srs'])
                    else:
                        s_srs = kwargs['srs']

                    t_srs = self.resource.srs

                    if s_srs.ExportToProj4() != t_srs.ExportToProj4():
                        crx = osr.CoordinateTransformation(s_srs, t_srs)
                        minx, miny, _ = crx.TransformPoint(minx, miny)
                        maxx, maxy, _ = crx.TransformPoint(maxx, maxy)
                        xrc = osr.CoordinateTransformation(t_srs, s_srs)

                lyr.SetSpatialFilterRect(minx, miny, maxx, maxy)
            elif 'boundary' in kwargs:
                boundary = ogr.Geometry(geomTypes[kwargs['boundary_type']], kwargs["boundary"])
                lyr.SetSpatialFilter(boundary)

            if 'query' in kwargs:
                if isinstance(kwargs['query'], basestring):
                    query = json.loads(kwargs['query'])
                else:
                    query = kwargs['query']

                for key, value in query.items():
                    attrq = self.attrquery(key, value) if '__' in key else key, '='
                    lyr.SetAttributeFilter(attrq)

            start = kwargs['start'] if 'start' in kwargs else 0
            count = kwargs['count'] if 'count' in kwargs else len(lyr) - start

            records = []
            for i in range(start):
                lyr.next()

            for i in range(count):
                f = lyr.next()
                if f.geometry():
                    records.append(
                        dict(fid=i, geometry=wkb.loads(transform(f.geometry(), xrc).ExportToWkb()), **f.items()))

            df = DataFrame.from_records(
                data=records,
                index='fid'
            )

            if 'sort_by' in kwargs:
                df = df.sort_index(by=kwargs['sort_by'])

            return df

        elif hasattr(self, '_df'):
            return self._df

        elif os.path.exists(dfx_path) and os.stat(dfx_path).st_mtime >= os.stat(self.get_master_filename()).st_mtime:
            if self.resource.big:
                self._df = pandas.read_hdf(dfx_path, 'df')
            else:
                self._df = pandas.read_pickle(dfx_path)
            return self._df
        else:
            ds = ogr.Open(self.get_master_filename())
            lyr = ds.GetLayerByIndex(0)
            df = DataFrame.from_records(
                data=[dict(fid=f.GetFID(), geometry=wkb.loads(f.geometry().ExportToWkb()), **f.items()) for f in lyr if
                      f.geometry()],
                index='fid'
            )
            if self.resource.big:
                df.to_hdf(dfx_path, 'df')
            else:
                df.to_pickle(dfx_path)
            self._df = df
            return self._df

    @classmethod
    def from_dataframe(cls, df, shp, driver, srs, in_subdir=False):
        """Write an dataframe object out as a shapefile"""

        drv = ogr.GetDriverByName(driver)

        if driver != 'Memory':
            if in_subdir:
                if os.path.exists(shp):
                    shutil.rmtree(shp)
                os.mkdir(shp)
            else:
                if os.path.exists(shp):
                    os.unlink(shp)

        ds = drv.CreateDataSource(shp)
        keys = df.keys()
        fieldDefns = [ogr.FieldDefn(ogrfield(name), dtypes[df[name].dtype.name]) for name in keys if name != 'geometry']

        geomType = geomTypes[(f for f in df['geometry']).next().type]
        l = ds.CreateLayer(
            name=os.path.split(shp)[-1],
            srs=srs,
            geom_type=geomType
        )
        for f in fieldDefns:
            l.CreateField(f)

        for i, record in df.iterrows():
            feature = ogr.Feature(l.GetLayerDefn())

            for field, value in ((k, v) for k, v in record.to_dict().items() if k != 'geometry'):
                if isinstance(value, basestring):
                    value = value.encode('ascii')
                feature.SetField(ogrfield(field), value)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(record['geometry'].wkb))
            l.CreateFeature(feature)

        if driver != 'Memory': # then write to file and flush the dataset
            del ds
        else: # we're done.  return the dataset that was created in memory.
            return ds


driver = OGRDriver
