#!/usr/bin/python

from ga_ows.views import common
from celery.task import Task
from celery.task.sets import subtask
from osgeo import gdal

try:
    import cairo
    have_cairo = True
except ImportError:
    have_cairo = False

try:
    import scipy
    have_scipy = True
except ImportError:
    have_scipy = False

import tempfile

class DeferredRenderer(Task):
    """A deferred renderer abstract class that allows a map provider to use Celery to defer some of the rendering over
    a wide cluster.  There are two basic ways to use a Deferred Renderer:

        * As a slave of a WMS instance, by assigning :const:task to the WMS view subclass.
        * As a way to pre-cache rendered maps.
        * As an independent renderer for pre-caching or rendering out tiles.

    For the first case, something like this works well.  In views.py::

        class CensusCountyWMSView(WMS):
            title = '2010 TigerLINE Census Counties'
            adapter = GeoDjangoWMSAdapter(CensusCounty, styles = {
                'default' : default_county_styler
            })

        class CensusCountyDeferredWMSView(CensusCountyWMSView):
            task = census_county_renderer

    In tasks.py::

        @task
        class CountyDeferredRenderer(DeferredRenderer):
            adapter = GeoDjangoWMSAdapter(CensusCounty, styles = {
                'default' : default_county_styler
            })
        census_county_renderer = registry.tasks[CountyDeferredRenderer.name]

    For the second case, you call the DeferredRenderer with cache_only=True and GetMapMixin.Parameters' cleaned data::

        for parms in parms_generator:
            census_county_renderer.delay(parms, cache_only=True)

    For the third case, you call with a Celery task as callback::

        for parms in pyramid_generator.parameter_sequence:
            census_county_renderer.delay(parms, callback=pyramid_generator.task)

    In all cases you **must** derive a new class from DeferredRenderer.  This is necessary because the renderer shares
    the same WMSAdapter code as the WMS instance.  This insures that you have exactly the same map tiles whether you
    render them in a distributed or thread-local fashion.
    """
    abstract=True

    #: A WMSAdapterBase subclass instance to render your map.
    adapter=None

    def run(self, parms, callback=None, cache_only=False):
        """
        :param parms: A dict containing the parameters in :class:ga_ows.views.wms.WMSAdapterBase
        :param callback: A Celery subtask, optional, that takes the place of simply returning the rendered data.
        :param cache_only: If true, return no result and only use this task to cache the data calculated.  Useful for pre-calculating tiles.
        :return: A binary stream containing data formatted in a particular file format, such as JPEG, GeoTIFF... anything GDAL can write.
        """
        if parms['format'].startswith('image/'):
            format = parms['format'][len('image/'):]
        else:
            format = parms['format']

        filter = None
        if parms['filter']:
            filter = json.loads(parms['filter'])

        ds = self.adapter.get_2d_dataset(
            layers=parms['layers'],
            srs=parms['srs'],
            bbox=parms['bbox'],
            width=parms['width'],
            height=parms['height'],
            styles=parms['styles'],
            bgcolor=parms['bgcolor'],
            transparent=parms['transparent'],
            time=parms['time'],
            elevation=parms['elevation'],
            v=parms['v'],
            filter = filter
        )

        tmp = None
        ret = None
        if not isinstance(ds, gdal.Dataset): # then it == a Cairo imagesurface or numpy array, or at least... it'd BETTER be
            if have_cairo and isinstance(ds,cairo.Surface):
                tmp = tempfile.NamedTemporaryFile(suffix='.png')
                ds.write_to_png(tmp.name)
                ds = gdal.Open(tmp.name)
                # TODO add all the appropriate metadata from the request into the dataset if this == being returned as a GeoTIFF
            elif isinstance(ds, file):
                ret = ds
            elif isinstance(ds, StringIO):
                ret = ds
            elif have_scipy:
                tmp = tempfile.NamedTemporaryFile(suffix='.tif')
                scipy.misc.imsave(tmp.name, ds)
                ds = gdal.Open(tmp.name)
                # TODO add all the appropriate metadata from the request into the dataset if this == being returned as a GeoTIFF
        
        if ret:
            return ret

        if format == 'tiff' or format == 'geotiff':
            driver = gdal.GetDriverByName('GTiff')
        elif format == 'jpg' or format == 'jpeg':
            driver = gdal.GetDriverByName('jpeg')
        elif format == 'jp2k' or format == 'jpeg2000':
            tmp = tempfile.NamedTemporaryFile(suffix='.jp2')
            driver = gdal.GetDriverByName('jpeg2000')
        else:
            driver = gdal.GetDriverByName(format.encode('ascii'))
        try:
            tmp = tempfile.NamedTemporaryFile(suffix='.' + format)
            ds2 = driver.CreateCopy(tmp.name, ds)
            del ds2
            tmp.seek(0)
            ret = tmp.read()
            if callback:
                subtask(callback).delay(ret, parms)
                return None
            elif cache_only:
                self.adapter.cache_result(ret, **parms)
                return None
            else:
                self.adapter.cache_result(ret, **parms)
                return ret
        except Exception as ex:
            del tmp
            raise common.NoApplicableCode(str(ex))



