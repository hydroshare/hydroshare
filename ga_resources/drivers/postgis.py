# from ga_ows.views import wms, wfs
from uuid import uuid4
import json

from django.conf import settings as s
from django.contrib.gis.geos import Polygon, GEOSGeometry
import os
from osgeo import osr
from . import Driver
from pandas import DataFrame
from shapely import wkb
from psycopg2 import connect
from django.db import connection as django_db_connection
from django.db import connections as django_db_connections
import pandas


def identity(x):
    return '"' + x + '"' if isinstance(x, basestring) else str(x)

def transform(geom, crx):
    if crx:
        geom.Transform(crx)
    return geom


class PostGISDriver(Driver):
    """
    Config Parameters:
        * dbname : string (required if not use_django_dbms)
        * user : string (optional)
        * password : string (optional)
        * host : string (optional)
        * port : integer (optional)
        * use_django_dbms : boolean (default false)
        * django_dbms_alias : string (default: use django's default connection)
        * table : the default table to use
        * tables : dict of layer names -> tables, must all be in the same coordinate system for now.  Can also be select queries. paired with the geometry field name.
        * estimate_extent : see mapnik documentation
        * cursor_size : int. default of 2000 for "big" tables else ignored
        * srid : the native srid of the tables
    """

    def ready_data_resource(self, **kwargs):
        slug, srs = super(PostGISDriver, self).ready_data_resource(**kwargs)
        cfg = self.resource.driver_config
        conn = {
            'type': 'postgis'
        }

        def addcfg(k):
            if k in cfg:
                conn[k] = cfg[k]

        if cfg.get('use_django_dbms', False):
            alias = cfg.get('django_dbms_alias', 'default')
            db = s.DATABASES[alias]
            conn['dbname'] = db['NAME']
            if "HOST" in db and len(db["HOST"]) > 0:
                conn['host'] = db['HOST']
            if "USER" in db and len(db["USER"]) > 0:
                conn['user'] = db['USER']
            if "PASSWORD" in db and len(db["PASSWORD"]) > 0:
                conn['password'] = db['PASSWORD']
            if "PORT" in db and len(db["PORT"]) > 0:
                conn['port'] = db['PORT']
        else:
            addcfg('dbname')
            addcfg('host')
            addcfg('user')
            addcfg('password')
            addcfg('port')

        addcfg('estimate_extent')
        
        if 'sublayer' in kwargs:
            conn['id'] = conn['name'] = kwargs['sublayer']
        table, geometry_field = self._table(**kwargs)

        conn['table'] = table
        conn['geometry_field'] = geometry_field

        if self.resource.big:
            conn['cursor_size'] = cfg.get('cursor_size', 2000)

        return slug, srs, conn

    def _connection(self):
        # create a database connection, or use the
        cfg = self.resource.driver_config
        if cfg.get('use_django_dbms', False):
            if cfg.get('django_dbms_alias', None):
                connection = django_db_connections[cfg['django_dbms_alias']]
            else:
                connection = django_db_connection
        else:
            connection = connect(
                database=cfg['dbname'],
                user=cfg.get('user', None),
                password=cfg.get('password', None),
                host=cfg.get('host', None),
                port=cfg.get('port', None)
            )
        return connection

    def compute_fields(self, **kwargs):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        super(PostGISDriver, self).compute_fields(**kwargs)
        cfg = self.resource.driver_config
        connection = self._connection()
        xmin=ymin=float('inf')
        ymax=xmax=float('-inf')

        dataframe = self.get_filename('dfx')
        if os.path.exists(dataframe):
            os.unlink(dataframe)

        for entry in [cfg['table']] + cfg.get('tables', {}).values():
            if isinstance(entry, list):
                table, geom_field = entry
            elif entry.startswith('#'):
                table, geom_field = self._table(sublayer=entry[1:])
            else:
                table = entry
                geom_field = 'geometry'
            c = connection.cursor()
            c.execute("select AsText(st_extent({geom_field})) from {table}".format(geom_field=geom_field, table=table))

            xmin0, ymin0, xmax0, ymax0 = GEOSGeometry(c.fetchone()[0]).extent
            xmin = xmin0 if xmin0 < xmin else xmin
            ymin = ymin0 if ymin0 < ymin else ymin
            xmax = xmax0 if xmax0 > xmax else xmax
            ymax = ymax0 if ymax0 > ymax else ymax

        crs = osr.SpatialReference()
        crs.ImportFromEPSG(cfg['srid'])
        self.resource.spatial_metadata.native_srs = crs.ExportToProj4()

        e4326 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        crx = osr.CoordinateTransformation(crs, e4326)
        x04326, y04326, _ = crx.TransformPoint(xmin, ymin)
        x14326, y14326, _ = crx.TransformPoint(xmax, ymax)

        print xmin, xmax, ymin, ymax
        print x04326, y04326, x14326, y14326
        self.resource.spatial_metadata.bounding_box = Polygon.from_bbox((x04326, y04326, x14326, y14326))
        self.resource.spatial_metadata.native_bounding_box = Polygon.from_bbox((xmin, ymin, xmax, ymax))
        self.resource.spatial_metadata.three_d = False

        self.resource.spatial_metadata.save()
        self.resource.save()

    def _table(self, **kwargs):
        cfg = self.resource.driver_config
        if 'sublayer' in kwargs:
            entry = cfg['tables'][kwargs['sublayer']]
            if isinstance(entry, list):
               table, geometry_field = entry
            else:
               table = entry
               geometry_field = 'geometry'
        else:
            entry = cfg['table']
            if isinstance(entry, list):
               table, geometry_field = entry
            elif entry.startswith("#"):
               return self._table(sublayer=entry[1:])
            else:
               table = entry
               geometry_field = 'geometry'

        return table, geometry_field

    def get_data_for_point(self, wherex, wherey, srs, **kwargs):
        result, x1, y1, fuzziness = super(PostGISDriver, self).get_data_for_point(wherex, wherey, srs, **kwargs)
        cfg = self.resource.driver_config
        table, geometry_field = self._table(**kwargs)

        if fuzziness == 0:
            geometry = "GeomFromText('POINT({x} {y})', {srid})".format(
                x = x1,
                y = y1,
                srid = cfg['srid']
            )
        else:
            geometry = "ST_Buffer(GeomFromText('POINT({x} {y})', {srid}), {fuzziness})".format(
                x = x1,
                y = y1,
                srid = cfg['srid'],
                fuzziness = fuzziness
            )

        cursor = self._cursor(**kwargs)

        cursor.execute("SELECT * FROM {table} WHERE ST_Intersects({geometry}, {geometry_field})".format(
            geometry = geometry,
            table = table,
            geometry_field = geometry_field
        ))
        rows = [list(r) for r in cursor.fetchall()]
        keys = [c.name for c in cursor.description]

        return [dict(zip(keys, r)) for r in rows]

    def attrquery(self, key, value):
        if '__' not in key:
            return key+'='+value

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

    def _cursor(self, **kwargs):
        connection = self._connection()
        if 'big' in kwargs or (
                self.resource.big and 'count' not in kwargs): # if we don't have control over the result size of a big resource, use a server side cursor
            cursor = connection.cursor('cx' + uuid4().hex)
        else:
            cursor = connection.cursor()

        return cursor


    def as_dataframe(self, **kwargs):
        """
        Creates a dataframe object for a shapefile's main layer using layer_as_dataframe. This object is cached on disk for
        layer use, but the cached copy will only be picked up if the shapefile's mtime is older than the dataframe's mtime.

        :param shp: The shapefile
        :return:
        """

        dfx_path = self.get_filename('dfx')

        if len(kwargs) != 0:
            cfg = self.resource.driver_config
            lyr = {}
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

                lyr['bbox'] = (minx, miny, maxx, maxy)
            elif 'boundary' in kwargs:
                lyr['boundary'] = kwargs['boundary']


            if 'query' in kwargs:
                lyr['query'] = []

                if isinstance(kwargs['query'], basestring):
                    query = json.loads(kwargs['query'])
                else:
                    query = kwargs['query']

                lyr['query'] = ' AND '.join(self.attrquery(key, value) for key, value in query.items())

            start = kwargs['start'] if 'start' in kwargs else 0
            count = start + kwargs['count'] if 'count' in kwargs else -1


            # contsruct query

            cursor = self._cursor(**kwargs)


            q = "SELECT AsBinary({geometry_column}), * FROM {table} AS w WHERE "
            addand = False
            if 'bbox' in lyr:
                q += "{geometry_column} && ST_SetSRID(ST_MakeBox2D(ST_Point({xmin}, {ymin}), ST_Point({xmax}, {ymax})), {srid}) "
                addand = True

            if 'boundary' in lyr:
                q += "ST_Intersects(GeomFromText('{boundary}', {geometry_column}))"
                addand = True

            if 'query' in lyr:
                if addand:
                    q += ' AND '
                q += lyr['query']

            if count > 0:
                q += ' LIMIT {count}'.format(count=count)

            table, geometry_column = self._table(**kwargs)
            if table.strip().lower().startswith('select'):
                table = '(' + table + ")"

            cursor.execute(q.format(
                boundary = cfg.get('boundary', None),
                geometry_column = geometry_column,
                table = table,
                srid=cfg.get('srid',4326),
                **dict(zip(('xmin','ymin','xmax','ymax'), lyr.get('bbox',(0,0,0,0))))
            ))
            for i in range(start):
                cursor.fetchone()

            names = [c.name for c in cursor.description]
            throwaway_ix = names[1:].index(geometry_column) + 1
            records = []
            for record in cursor:
                records.append({name: value for i, (name, value) in enumerate(zip(names, record)) if i != throwaway_ix})
                records[-1]['geometry'] = wkb.loads(str(records[-1]['asbinary']))
                del records[-1]['asbinary']

            df = DataFrame.from_records(data=records)

            if 'sort_by' in kwargs:
                df = df.sort_index(by=kwargs['sort_by'])

            return df

        elif hasattr(self, '_df'):
            return self._df

        elif os.path.exists(dfx_path):
            self._df = pandas.read_pickle(dfx_path)
            return self._df
        else:
            table, geometry_column = self._table(**kwargs)
            query = "SELECT AsBinary({geometry_column}), * FROM {table}".format(table=table, geometry_column=geometry_column)
            print query
            cursor = self._cursor(**kwargs)
            cursor.execute(query)
            names = [c.name for c in cursor.description]
            throwaway_ix = names[1:].index(geometry_column) + 1
            records = []
            for record in cursor.fetchall():
                records.append({name: value for i, (name, value) in enumerate(zip(names, record)) if i != throwaway_ix})
                records[-1]['geometry'] = wkb.loads(str(records[-1]['asbinary']))
                del records[-1]['asbinary']

            df = DataFrame.from_records(data=records)
            df.to_pickle(dfx_path)
            self._df = df
            return self._df




driver = PostGISDriver
