import json
import cPickle
import shutil
from collections import OrderedDict
from hashlib import md5
from datetime import datetime
from urllib2 import urlopen
import time
import math
from sqlite3 import dbapi2 as db

from django.utils.timezone import utc
from ga_resources import models as m, dispatch
from ga_resources.models import DataResource
import os
from django.conf import settings as s
import sh
import requests
import re
from django.conf import settings
from ga_resources import predicates


try:
   import mapnik
except ImportError:
   import mapnik2 as mapnik

from osgeo import osr

VECTOR = False
RASTER = True

class Driver(object):
    """Abstract class that defines a number of reusable methods to load geographic data and create services from it"""
    def __init__(self, data_resource):
        self.resource = data_resource
        self.cache_path = self.resource.cache_path
        self.cached_basename = os.path.join(self.cache_path, os.path.split(self.resource.slug)[-1])
        
    def clear_cache(self):
        shutil.rmtree(self.cache_path, ignore_errors=True)

    def initialize_cache(self):
        os.mkdir(self.cache_path)

    def ensure_local_file(self, freshen=False):
        """Ensures that if a resource comes from a URL that it has been retrieved in its entirety.

            :param freshen: True if this file should be downloaded and the cache obliterated.  False otherwise.

            :return: True if the file has changed since the last time this was called.  False if the file has not changed
                    and None if there is no local file to be had (true for PostGIS driver and some custom drivers)
        """

        if not self.supports_local_caching():
            return None

        if self.resource.resource_file:
            _, ext = os.path.splitext(self.resource.resource_file.name)
        elif self.resource.resource_url:
            _, ext = os.path.splitext(self.resource.resource_url)
        else:
            return None

        cached_filename = self.cached_basename + ext
        self.src_ext = ext

        ready = os.path.exists(cached_filename) and not freshen
        
        if freshen:
            self.clear_cache()
            self.initialize_cache()

        if not ready:
            if self.resource.resource_file:
                if os.path.exists(cached_filename):
                    os.unlink(cached_filename)
                try:
                    os.symlink(os.path.join(s.MEDIA_ROOT, self.resource.resource_file.name), cached_filename)
                except:
                    pass
            elif self.resource.resource_url:
                if self.resource.resource_url.startswith('ftp'):
                    result = urlopen(self.resource.resource_url).read()
                    if result:
                        with open(cached_filename, 'wb') as resource_file:
                            resource_file.write(result)
                else:
                    result = requests.get(self.resource.resource_url)
                    if result.ok:
                        with open(cached_filename, 'wb') as resource_file:
                            resource_file.write(result.content)
            return True
        else:
            return False

    def data_size(self):
        sz = 0
        if self.resource.resource_file and os.path.exists(self.resource.resource_file.path):
            sz += os.stat(self.resource.resource_file.path).st_size
        for line in sh.du('-cs', self.cache_path):
            if line.startswith('.'):
                sz += int(line.split(' ')[-1])
        return sz


    @classmethod
    def supports_mutiple_layers(cls):
        """If a single resource can contain multiple layers, this returns True."""

        return True

    @classmethod
    def supports_download(cls):
        """If a user could download the resource in its entirety, this returns True."""

        return True

    @classmethod
    def supports_related(cls):
        """True if this driver supports "join-on-key" functionality with the RelatedResource model"""
        return True

    @classmethod
    def supports_upload(cls):
        """True if the user can upload a file as part of this reosurce"""
        return True

    @classmethod
    def supports_configuration(cls):
        """True if the resource must be configured with a resource_config attribute"""
        return True

    @classmethod
    def supports_point_query(cls):
        """True if a single geographic point can be queried."""
        return True

    @classmethod
    def supports_spatial_query(cls):
        """True if a spatial query or bounding box can be queried"""
        return True

    @classmethod
    def supports_rest(cls):
        """True if the REST API is supported for data sources"""
        return True

    @classmethod
    def supports_local_caching(cls):
        """True if the whole resource is downloaded and cached locally.  False for stream-based drivers"""
        return True

    @classmethod
    def datatype(cls):
        """returns VECTOR or RASTER"""
        return VECTOR

    def filestream(self):
        """returns an open file stream from the locally cached file.  Must support local caching."""

        self.ensure_local_file()
        return open(self.cached_basename + self.src_ext)

    def mimetype(self):
        """The mime type to use when returning the original resource file via HTTP"""
        return "application/octet-stream"

    def ready_data_resource(self, **kwargs):
        """Abstract. Ensures that the file is local and ensures that spatial metadata has been computed for the resource.
        Full implementations of this method should also return a mapnik config dictionary as the last item of the tuple.

        :return: a tuple that includes the resource slug and the spatial reference system as a osr.SpatialReference object
        """

        changed = self.ensure_local_file(freshen='fresh' in kwargs and kwargs['fresh'])
        if changed:
            self.compute_fields()

        return self.resource.slug, self.resource.srs

    def compute_fields(self):
        """
        Compute the spatial metadata fields in the DataResource. Abstract.
        """
        if self.ensure_local_file() is not None:
            filehash = md5()
            with open(self.cached_basename + self.src_ext) as f:
                b = f.read(10 * 1024768)
                while b:
                    filehash.update(b)
                    b = f.read(10 * 1024768)

            md5sum = filehash.hexdigest()
            if md5sum != self.resource.md5sum:
                self.resource.md5sum = md5sum
                self.resource.last_change = datetime.utcnow().replace(tzinfo=utc)


    def get_metadata(self, **kwargs):
        """Abstract. If there is metadata conforming to some standard, then return it here"""
        return {}

    def get_data_fields(self, **kwargs):
        """If this is a shapefile, return the names of the fields in the DBF and their datattypes.  If this is a data
        raster (as opposed to an RGB or grayscale raster, return the names of the bands or subdatasets and their
        datatypes."""
        return []

    def get_filename(self, xtn):
        """
        Get a filename for a cached entity related to the underlying resource.

        :param xtn: The file extension to used.
        :return: The cached filename.  No guarantees it exists. The filename consists of the original filename stripped
        of its extension and the new extension appended.
        """
        filename = os.path.split(self.resource.slug)[-1]
        return os.path.join(self.cache_path, filename + '.' + xtn)

    def get_data_for_point(self, wherex, wherey, srs, fuzziness=30, **kwargs):
        """
        Get data for a single x,y point.  This should be supported for raw rasters as well as vector data, but obviously
        RGB data is kind of pointless.

        :param wherex: the x coordinate
        :param wherey: the y coordinate
        :param srs: a spatial reference system, either as a string EPSG:#### or PROJ.4 string, or as an osr.SpatialReference
        :param fuzziness: the distance in map units from the xy coodrinate that features data should be pulled from
        :param kwargs: if fuzziness is 0, then keyword args bbox, width, and height should be passed in to let the
            engine figure out how big a "point" is.
        :return: a four-tuple of:
        """
        _, nativesrs, result = self.ready_data_resource(**kwargs)

        s_srs = osr.SpatialReference()
        t_srs = nativesrs

        if isinstance(srs, osr.SpatialReference):
            s_srs = srs
        elif srs.lower().startswith('epsg'):
            s_srs.ImportFromEPSG(int(srs.split(':')[-1]))
        else:
            s_srs.ImportFromProj4(srs.encode('ascii'))

        crx = osr.CoordinateTransformation(s_srs, t_srs)
        x1, y1, _ = crx.TransformPoint(wherex, wherey)
        
        # transform wherex and wherey to 3857 and then add $fuzziness meters to them
        # transform the fuzzy coords to $nativesrs
        # substract fuzzy coords from x1 and y1 to get the fuzziness needed in the native coordinate space
        epsilon = 0
        if fuzziness > 0:
           meters = osr.SpatialReference()
           meters.ImportFromEPSG(3857) # use web mercator for meters
           nat2met = osr.CoordinateTransformation(s_srs, meters) # switch from the input srs to the metric one
           met2nat = osr.CoordinateTransformation(meters, t_srs) # switch from the metric srs to the native one
           mx, my, _ = nat2met.TransformPoint(wherex, wherey) # calculate the input coordinates in meters
           fx = mx+fuzziness # add metric fuzziness to the x coordinate only to get a radius
           fy = my 
           fx, fy, _ = met2nat.TransformPoint(fx, fy)
           epsilon = fx - x1 # the geometry should be buffered by this much
        elif 'bbox' in kwargs and 'width' in kwargs and 'height' in kwargs:
           # use the bounding box to calculate a radius of 8 pixels around the input point
           minx, miny, maxx, maxy = kwargs['bbox']
           width = int(kwargs['width']) # the tile width in pixels
           height = int(kwargs['height']) # the tile height in pixels
           dy = (maxy-miny)/height # the height delta in native coordinate units between pixels
           dx = (maxx-minx)/width # the width delta in native coordinate units between pixels
           x2, y2, _ = crx.TransformPoint(wherex+dx*8, wherey) # return a point 8 pixels to the right of the source point in native coordinate units
           epsilon = x2 - x1 # the geometry should be buffered by this much
        else:
           pass

        return result, x1, y1, epsilon

    def as_dataframe(self, **kwargs):
        """Return the entire dataset as a pandas dataframe"""

        raise NotImplementedError("This driver does not support dataframes")

    def summary(self, **kwargs):
        """Requires dataframe support.  Return a summary of the dataframe using pandas's standard methods and our own
        predicates"""

        sum_path = self.get_filename('sum')
        if self.resource.big and os.path.exists(sum_path):
            with open(sum_path) as sm:
                return cPickle.load(sm)

        df = self.as_dataframe(**kwargs)
        keys = [k for k in df.keys() if k != 'geometry']
        type_table = {
            'float64': 'number',
            'int64': 'number',
            'object': 'text'
        }

        ctx = [{'name': k} for k in keys]
        for i, k in enumerate(keys):
            s = df[k]
            ctx[i]['kind'] = type_table[s.dtype.name]
            ctx[i]['tags'] = [tag for tag in [
                'unique' if predicates.unique(s) else None,
                'not null' if predicates.not_null(s) else None,
                'null' if predicates.some_null(s) else None,
                'empty' if predicates.all_null(s) else None,
                'categorical' if predicates.categorical(s) else None,
                'open ended' if predicates.continuous(s) else None,
                'mostly null' if predicates.mostly_null(s) else None,
                'uniform' if predicates.uniform(s) else None
            ] if tag]
            if 'categorical' in ctx[i]['tags']:
                ctx[i]['uniques'] = [x for x in s.unique()]
            for k, v in s.describe().to_dict().items():
                ctx[i][k] = v

        if self.resource.big:
            with open(sum_path, 'w') as sm:
                cPickle.dump(ctx, sm)

        return ctx




def compile_layer(rl, layer_id, srs, css_classes, **parameters):
    """Take a RenderedLayer and turn it into a Mapnik input file clause"""

    return {
        "id" : parameters['id'] if 'id' in parameters else re.sub('/', '_', layer_id),
        "name" : parameters['name'] if 'name' in parameters else re.sub('/', '_', layer_id),
        "class" : ' '.join(rl.default_class if 'default' else cls for cls in css_classes).strip(),
        "srs" : srs if isinstance(srs, basestring) else srs.ExportToProj4(),
        "Datasource" : parameters
    }

def compile_mml(srs, styles, *layers):
    """Take multiple layers and stylesheets and turn it into a Mapnik input file"""
    stylesheets = [m.Style.objects.get(slug=s.split('.')[0]) for s in styles]
    css_classes = set([s.split('.')[1] if '.' in s else 'default' for s in styles])

    mml = {
        'srs' : srs,
        'Stylesheet' : [{ "id" : re.sub('/', '_', stylesheet.slug), "data" : stylesheet.stylesheet} for stylesheet in stylesheets],
        'Layer' : [compile_layer(rl, layer_id, lsrs, css_classes, **parms) for rl, (layer_id, lsrs, parms) in layers]
    }
    return mml


def compile_mapfile(name, srs, stylesheets, *layers):
    """Compile from Carto to Mapnik"""

    with open(name + ".mml", 'w') as mapfile:
        mapfile.write(json.dumps(compile_mml(srs, stylesheets, *layers), indent=4))
    carto = sh.Command(settings.CARTO_HOME + "/bin/carto")
    carto(name + '.mml', _out=name + '.xml')


LAYER_CACHE_PATH = os.path.join(s.MEDIA_ROOT, '.cache', '_cached_layers')
if not os.path.exists(LAYER_CACHE_PATH):
    sh.mkdir('-p', LAYER_CACHE_PATH)

def cache_entry_name(layers, srs, styles, bgcolor=None, transparent=True, query=None):
    d = OrderedDict(layers=layers, srs=srs, styles=styles, bgcolor=bgcolor, transparent=transparent)
    if query: # insert the query keys, but ensure a consistent order
        keys = sorted(query.keys())
        for k in keys:
            d[k] = query[k]

    shortname = md5()
    for key, value in d.items():
        shortname.update(key)
        shortname.update(unicode(value))
    cache_entry_basename = shortname.hexdigest()
    return os.path.join(LAYER_CACHE_PATH, cache_entry_basename)

def prepare_wms(layers, srs, styles, bgcolor=None, transparent=True, **kwargs):
    """Take a WMS query and turn it into the appropriate MML file, if need be.  Or look up the cached MML file"""

    if not os.path.exists(LAYER_CACHE_PATH):
        os.makedirs(LAYER_CACHE_PATH)  # just in case it's not there yet.

    cached_filename = cache_entry_name(
        layers, srs, styles,
        bgcolor=bgcolor,
        transparent=transparent,
        query=kwargs['query'] if 'query' in kwargs else None
    )

    layer_specs = []
    for layer in layers:
        if "#" in layer:
            layer, kwargs['sublayer'] = layer.split("#") 
        rendered_layer = m.RenderedLayer.objects.get(slug=layer)
        driver = rendered_layer.data_resource.driver_instance
        layer_spec = driver.ready_data_resource(**kwargs)
        layer_specs.append((rendered_layer, layer_spec))

    if not os.path.exists(cached_filename + ".xml"):  # not an else as previous clause may remove file.
        try:
            with open(cached_filename + ".lock", 'w') as w:
                 compile_mapfile(cached_filename, srs, styles, *layer_specs)
            os.unlink(cached_filename + ".lock")
        except sh.ErrorReturnCode_1, e:
            raise RuntimeError(str(e.stderr))
        except:
            pass

    return cached_filename


def trim_cache(layers=list(), styles=list()):
    """destroy relevant tile caches and cached mapnik files that are affected by a style or layer change"""
    names = []
    data = db.connect(os.path.join(LAYER_CACHE_PATH, 'directory.sqlite'))
    c = data.cursor()
    c.executemany('select basename from layers where slug=?', layers)
    names.extend( c.fetchall() )
    c.close()
    c = data.cursor()
    c.executemany('select basename from styles where slug=?', styles)
    names.extend( c.fetchall() )

    for name in names:
        if os.path.exists(name + '.mbtiles'):
            os.unlink(name + '.mbtiles')
        if os.path.exists(name + '.json'):
            os.unlink(name + '.json')
        if os.path.exists(name + '.wmsresults'):
            os.unlink(name + '.wmsresults')
        if os.path.exists(name + '.mml'):
            os.unlink(name + '.mml')
        if os.path.exists(name + '.xml'):
            os.unlink(name + '.xml')
        if os.path.exists(name + '.carto'):
            os.unlink(name + '.carto')


def render(fmt, width, height, bbox, srs, styles, layers, **kwargs):
    """Render a WMS request or a tile.  TODO - create an SQLite cache for this as well, based on hashed filename."""

    if srs.lower().startswith('epsg'):
        if srs.endswith("900913") or srs.endswith("3857"):
            srs = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null"
        else:
            srs = "+init=" + srs.lower()

    name = prepare_wms(layers, srs, styles, **kwargs)
    filename = "{name}.{bbox}.{width}x{height}.{fmt}".format(
        name=name,
        bbox='_'.join(str(b) for b in bbox),
        width=width,
        height=height,
        fmt=fmt
    )

    while os.path.exists(name + ".lock"):
        time.sleep(0.05)
    m = mapnik.Map(width, height)
    mapnik.load_map(m, name + '.xml')
    m.zoom_to_box(mapnik.Box2d(*bbox))
    mapnik.render_to_file(m, filename, fmt)

    with open(filename) as tiledata:
        tile = buffer(tiledata.read())
    os.unlink(filename)

    return filename, tile



### following procedures and functions are in support of the tiled mapping services, TMS

def deg2num(lat_deg, lon_deg, zoom):
    """
    degree to tile number

    :param lat_deg: degrees lon
    :param lon_deg: degrees lat
    :param zoom: web mercator zoom level
    :return: x, y tile coordinates as a tuple
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


def num2deg(xtile, ytile, zoom):
    """
    Tile number to degree of southwest point.

    :param xtile: column
    :param ytile: row
    :param zoom: mercator zoom level
    :return: the degree of the southwest corner as a lat/lon pair.
    """
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lon_deg, lat_deg)


class CacheManager(object):
    """For every cache that is added to the filesystem, take note of it so if the underlying data changes it can be
    destroyed"""
    def __init__(self):
        self.cachename = os.path.join(LAYER_CACHE_PATH, 'directory.sqlite')
        self.tile_caches = {}
        self.wms_caches = {}

        if os.path.exists(self.cachename):
            conn = db.connect(self.cachename)
        else:
            conn = db.connect(self.cachename)
            cursor = conn.cursor()
            cursor.executescript("""
                BEGIN TRANSACTION;
                CREATE TABLE caches (name text PRIMARY KEY, kind text);
                CREATE TABLE layers (slug text primary key, cache_name text);
                CREATE TABLE styles (slug text primary key, cache_name text);
                END TRANSACTION;
                ANALYZE;
                VACUUM;
            """)
            conn.commit()

        self.conn = conn

    @classmethod
    def get(cls):
        import threading

        if not hasattr(cls, '_mgr'):
            cls._mgr = threading.local()
        if not hasattr(cls._mgr, 'mgr'):
            cls._mgr.mgr = CacheManager()

        return cls._mgr.mgr

    def get_tile_cache(self, layers, styles, **kwargs):

        name = cache_entry_name(
            layers,
            "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null",
            styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', True),
            query=kwargs.get('query', None)
        )
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO caches (name, kind) VALUES (:name, :kind)", { "name" : name, "kind" : "tile" })
        for layer in layers:
            c.execute("INSERT OR REPLACE INTO layers (slug, cache_name) VALUES (:layer, :name)", {
                "layer" : layer if isinstance(layer, basestring) else layer.slug,
                "name" : name
            })
        for style in styles:
            c.execute("INSERT OR REPLACE INTO styles (slug, cache_name) VALUES (:style, :name)", {
                "style" : style if isinstance(style, basestring) else style.slug,
                "name" : name
            })
        self.conn.commit()

        if name not in self.tile_caches:
            self.tile_caches[name] = MBTileCache(layers, styles,
                                                 bgcolor=kwargs.get('bgcolor', None),
                                                 transparent=kwargs.get('transparent', True),
                                                 query=kwargs.get('query', None)
            )
        return self.tile_caches[name]


    def get_wms_cache(self, layers, srs, styles, **kwargs):
        name = cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', True),
            query=kwargs.get('query', None)
        )
        if name not in self.wms_caches:
            self.wms_caches[name] = MBTileCache(layers, styles,
                                                bgcolor=kwargs.get('bgcolor', None),
                                                transparent=kwargs.get('transparent', True),
                                                query=kwargs.get('query', None))
        return self.wms_caches[name]


    def shave_caches(self, resource, bbox):
        """Iterate over all caches using a particular resource and remove any resources overlapping the bounding box"""


        if isinstance(resource, basestring):
            resource = DataResource.objects.get(slug=resource)
        for layer in resource.renderedlayer_set.all():
            c = self.conn.cursor()
            c.execute('select cache_name from layers where slug=?', [layer.slug])
            for (k,) in c.fetchall():
                MBTileCache.shave_cache(k+'.mbtiles', bbox.extent)

    def remove_caches_for_layer(self, layer):
        """Iterate over all the caches using a particular layer and burn them"""
        c = self.conn.cursor()
        c.execute('select cache_name from layers where slug=?', [layer.slug])
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                os.unlink(k + '.mbtiles')
            if os.path.exists(k + '.json'):
                os.unlink(k + '.json')
            if os.path.exists(k + '.wmsresults'):
                os.unlink(k + '.wmsresults')
            if os.path.exists(k + '.mml'):
                os.unlink(k + '.mml')
            if os.path.exists(k + '.xml'):
                os.unlink(k + '.xml')
            if os.path.exists(k + '.carto'):
                os.unlink(k + '.carto')

            c.execute('delete from caches where name=?', [k])
            c.execute('delete from layers where cache_name=?', [k])
            c.execute('delete from styles where cache_name=?', [k])

    def remove_caches_for_style(self, style):
        """Iterate over all caches using a particular stylesheet and burn them"""
        c = self.conn.cursor()
        c.execute('select cache_name from styles where slug=?', [style.slug])
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                os.unlink(k + '.mbtiles')
            if os.path.exists(k + '.json'):
                os.unlink(k + '.json')
            if os.path.exists(k + '.wmsresults'):
                os.unlink(k + '.wmsresults')
            if os.path.exists(k + '.mml'):
                os.unlink(k + '.mml')
            if os.path.exists(k + '.xml'):
                os.unlink(k + '.xml')
            if os.path.exists(k + '.carto'):
                os.unlink(k + '.carto')
            c.execute('delete from caches where name=?', [k])
            c.execute('delete from layers where cache_name=?', [k])
            c.execute('delete from styles where cache_name=?', [k])

    def layer_cache_size(self, layer):
        sz = 0
        c = self.conn.cursor()
        c.execute('select cache_name from layers where slug=?', [layer.slug if not isinstance(layer, basestring) else layer])
        for (k,) in c.fetchall():
            if os.path.exists(k + '.mbtiles'):
                sz += os.stat(k + '.mbtiles').st_size
        return sz

    def resource_cache_size(self, resource):
        return sum(self.layer_cache_size(layer) for layer in
                   m.RenderedLayer.objects.filter(
                       data_resource__slug =resource if isinstance(resource, basestring) else resource.slug
                   )
        )


    def remove_caches_for_resource(self, resource):
        """Iterate over all caches using a particular resource and burn them"""
        for layer in m.RenderedLayer.objects.filter(data_resource__slug = resource):
            self.remove_caches_for_layer(layer.slug)

class MBTileCache(object):
    def __init__(self, layers, styles, **kwargs):
        self.srs = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null"
        self.name = cache_entry_name(
            layers, self.srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', True),
            query=kwargs.get('query', None)
        )
        self.cachename = self.name + '.mbtiles'

        self.layers = layers if not isinstance(layers, basestring) else [layers]
        self.styles = styles if not isinstance(styles, basestring) else [styles]
        self.kwargs = kwargs
        e4326 = osr.SpatialReference()
        e3857 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        e3857.ImportFromEPSG(900913)
        self.crx = osr.CoordinateTransformation(e4326, e3857)

        paths = os.path.split(self.cachename)[:-1]
        p = ''
        for name in paths:
            p += '/' + name
            if not os.path.exists(p):
                os.mkdir(p)

        if os.path.exists(self.cachename):
            conn = db.connect(self.cachename)
        else:
            conn = db.connect(self.cachename)
            cursor = conn.cursor()
            cursor.executescript("""
                    BEGIN TRANSACTION;
                    CREATE TABLE android_metadata (locale text);
                    CREATE TABLE grid_key (grid_id TEXT,key_name TEXT);
                    CREATE TABLE grid_utfgrid (grid_id TEXT,grid_utfgrid BLOB);
                    CREATE TABLE keymap (key_name TEXT,key_json TEXT);
                    CREATE TABLE images (tile_data blob,tile_id text);
                    CREATE TABLE map (zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_id TEXT,grid_id TEXT);
                    CREATE TABLE metadata (name text,value text);
                    CREATE VIEW tiles AS SELECT map.zoom_level AS zoom_level,map.tile_column AS tile_column,map.tile_row AS tile_row,images.tile_data AS tile_data FROM map JOIN images ON images.tile_id = map.tile_id ORDER BY zoom_level,tile_column,tile_row;
                    CREATE VIEW grids AS SELECT map.zoom_level AS zoom_level,map.tile_column AS tile_column,map.tile_row AS tile_row,grid_utfgrid.grid_utfgrid AS grid FROM map JOIN grid_utfgrid ON grid_utfgrid.grid_id = map.grid_id;
                    CREATE VIEW grid_data AS SELECT map.zoom_level AS zoom_level,map.tile_column AS tile_column,map.tile_row AS tile_row,keymap.key_name AS key_name,keymap.key_json AS key_json FROM map JOIN grid_key ON map.grid_id = grid_key.grid_id JOIN keymap ON grid_key.key_name = keymap.key_name;
                    CREATE UNIQUE INDEX grid_key_lookup ON grid_key (grid_id,key_name);
                    CREATE UNIQUE INDEX grid_utfgrid_lookup ON grid_utfgrid (grid_id);
                    CREATE UNIQUE INDEX keymap_lookup ON keymap (key_name);
                    CREATE UNIQUE INDEX images_id ON images (tile_id);
                    CREATE UNIQUE INDEX map_index ON map (zoom_level, tile_column, tile_row);
                    CREATE UNIQUE INDEX name ON metadata (name);
                    END TRANSACTION;
                    ANALYZE;
                    VACUUM;
               """)
            cursor.close()

        self.cache = conn

    def fetch_tile(self, z, x, y):
        tile_id = u':'.join(str(k) for k in (z,x,y))
        sw = self.crx.TransformPoint(*num2deg(x, y+1, z))
        ne = self.crx.TransformPoint(*num2deg(x+1, y, z))
        width = 256
        height = 256
        insert_map = """INSERT OR REPLACE INTO map (tile_id,zoom_level,tile_column,tile_row,grid_id) VALUES(?,?,?,?,'');"""
        insert_data = """INSERT OR REPLACE INTO images (tile_id,tile_data) VALUES(?,?);"""

        c = self.cache.cursor()
        c.execute("SELECT tile_data FROM images WHERE tile_id=?", [tile_id])
        try:
            blob = buffer(c.fetchone()[0])
        except:
            dispatch.tile_rendered.send(sender=CacheManager, layers=self.layers, styles=self.styles)
            _, blob = render('png', width, height, (sw[0], sw[1], ne[0], ne[1]), self.srs, self.styles, self.layers, **self.kwargs)
            if len(blob) > 350:
                d = self.cache.cursor()
                d.execute(insert_map, [tile_id, z, x, y])
                d.execute(insert_data, [tile_id, blob])
                self.cache.commit()
                d.close()
        c.close()

        return blob

    def seed_tiles(self, min_zoom, max_zoom, minx, miny, maxx, maxy):
        for z in range(min_zoom, max_zoom+1):
            mnx, mny = deg2num(miny, minx, z)
            mxx, mxy = deg2num(maxy, maxx, z)
            for x in range(mnx, mxx+1):
                for y in range(mny, mxy+1):
                    self.fetch_tile(z, x, y)

    @classmethod
    def shave_cache(cls, filename, bbox):
        """Empties a bounding box out of the cache at all zoom levels to be regenerated on demand.  For supporting
        minor edits on data"""
        x1, y1, x2, y2 = bbox
        conn = db.connect(filename)
        c = conn.cursor()
        c.execute('select min(zoom_level) from map')
        c.execute('select max(zoom_level) from map')
        min_zoom = c.fetchone()
        max_zoom = c.fetchone()

        if min_zoom:
            min_zoom = min_zoom[0]
        else:
            min_zoom = 0
        if max_zoom:
            max_zoom = max_zoom[0]
        else:
            max_zoom = 32

        c.close()

        c = conn.cursor()

        del_map_entry = """
        DELETE FROM map WHERE
            tile_column >= ? AND
            tile_row >= ? AND
            tile_column <= ? AND
            tile_row <= ? AND
            zoom_level = ?
        """

        del_tile_data = """
        DELETE FROM images
        WHERE tile_id IN (
            SELECT tile_id
            FROM map WHERE
                tile_column >= ? AND
                tile_row >= ? AND
                tile_column <= ? AND
                tile_row <= ? AND
                zoom_level = ?
        )
        """
        e4326 = osr.SpatialReference()
        e3857 = osr.SpatialReference()
        e4326.ImportFromEPSG(4326)
        e3857.ImportFromEPSG(900913)
        crx = osr.CoordinateTransformation(e3857, e4326)
        x1, y1, _ = crx.TransformPoint(x1, y1)
        x2, y2, _ = crx.TransformPoint(x2, y2)

        for zoom in range(min_zoom, max_zoom+1):
            a1, b1 = deg2num(y1, x1, zoom)
            a2, b2 = deg2num(y2, x2, zoom)
            print 'deleting tiles from {a1},{b1} - {a2},{b2} for {zoom}'.format(**locals())
            c.execute(del_tile_data, [a1, b1, a2, b2, zoom])
            c.execute(del_map_entry, [a1, b1, a2, b2, zoom])

        c.execute('ANALYZE')
        c.execute('VACUUM')

        conn.commit()
        conn.close()


class WMSResultsCache(object):
    def __init__(self, layers, srs, styles, **kwargs):
        self.name = cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', None),
            query=kwargs.get('query', None)
        )
        self.cachename = self.name + '.wmscache'

        self.srs = srs
        self.layers = layers
        self.styles = styles
        self.kwargs = kwargs

        if os.path.exists(self.cachename):
            conn = db.connect(self.cachename)
            conn.enable_load_extension(True)
            conn.execute("select load_extension('libspatialite.so')")
        else:
            conn = db.connect(self.cachename)
            conn.enable_load_extension(True)
            conn.execute("select load_extension('libspatialite.so')")
            cursor = conn.cursor()
            cursor.executescript("""
                 BEGIN TRANSACTION;
                 SELECT InitSpatialMetadata();
                 CREATE TABLE tiles (hash_key TEXT, last_use DATETIME, tile_data BLOB);
                 SELECT AddGeometryColumn('tiles','bounds', 4326,  'POINT', 'XY');
                 SELECT CreateSpatialIndex('tiles','bounds');
                 CREATE UNIQUE INDEX hash_key_lookup ON tiles (hash_key);
                 CREATE INDEX lru ON tiles (last_use);
                 END TRANSACTION;
                 ANALYZE;
                 VACUUM;
            """)
            cursor.close()
            CacheManager.get().register_cache(layers, styles, self.cachename)

        self.cache = conn


    @classmethod
    def shave_cache(self, filename, bbox):
        """Empties a cache of all records overlapping a certain bounding box so they are regenerated on demand.  For
        supporting minor edits on data"""
        x1,y1,x2,y2 = bbox
        conn = db.connect(filename)
        conn.execute('delete from tiles where Intersects(bounds, BuildMBR({x1},{y1},{x2},{y2}))'.format(**locals()))
        conn.close()


    def fetch_data(self, fmt, width, height, bbox, srs, styles, layers, **kwargs):
        cache_basis_for_spec = cache_entry_name(
            layers, srs, styles,
            bgcolor=kwargs.get('bgcolor', None),
            transparent=kwargs.get('transparent', None),
            query=kwargs.get('query', None)
        )
        filename = "{name}.{bbox}.{width}x{height}.{fmt}".format(
            name=cache_basis_for_spec,
            bbox='_'.join(str(b) for b in bbox),
            width=width,
            height=height,
            fmt=fmt
        )

        c = self.cache.cursor()
        c.execute("UPDATE tile_data last_use = datetime('now') WHERE hash_key=?", filename)
        c.execute('SELECT tile_data FROM tiles WHERE hash_key=?', filename)
        insert_data = """
            INSERT INTO tile_data (hash_key, last_use, tile_data, bounds)
            VALUES (
                ?,
                datetime('now'),
                ?,
                GeomFromText('POLYGON(({x1} {y1}, {x2} {y1}, {x2} {y2}, {x1} {y2}, {x1} {y1})')
            )
        """.format(x1=bbox[0],y1=bbox[1],x2=bbox[2],y2=bbox[3])
        try:
            blob = c.fetchone()[0]
        except:
            dispatch.wms_rendered.send(CacheManager, layers=self.layers, styles=self.styles)
            tile_id, blob = render('png', width, height, bbox, self.srs, self.styles,
                                   self.layers, **self.kwargs)

            with self.cache.cursor() as d:
                d.execute(insert_data, filename, blob)
        return blob