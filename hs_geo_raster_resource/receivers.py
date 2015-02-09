__author__ = 'Hong Yi'
## Note: this module has been imported in the models.py in order to receive signals
## at the end of the models.py for the import of this module
from django.dispatch import receiver
from hs_core.signals import *
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource.models import BandInformation

# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page
@receiver(pre_create_resource, sender=RasterResource)
def raster_pre_create_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        files = kwargs['files']
        title = kwargs['title']

        metadata = kwargs['metadata']
        from collections import OrderedDict
        if(files):
            # Assume only one file in files, and that that file is a zipfile
            infile = files[0]
            import raster_meta_extract
            res_md_dict = raster_meta_extract.get_raster_meta_dict(infile.file.name)

            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': res_md_dict['spatial_coverage_info']['wgs84_coverage_info'] }}
            metadata.append(box)

            # Save extended meta to metadata variable
            cellInfo = OrderedDict([
                ('name', infile.name),
                ('rows', res_md_dict['cell_and_band_info']['rows']),
                ('columns', res_md_dict['cell_and_band_info']['columns']),
                ('cellSizeXValue', res_md_dict['cell_and_band_info']['cellSizeXValue']),
                ('cellSizeYValue', res_md_dict['cell_and_band_info']['cellSizeYValue']),
                ('cellSizeUnit', res_md_dict['cell_and_band_info']['cellSizeUnit']),
                ('cellDataType', res_md_dict['cell_and_band_info']['cellDataType']),
                ('noDataValue', res_md_dict['cell_and_band_info']['noDataValue'])
                ])
            metadata.append({'CellInformation': cellInfo})
            bcount = res_md_dict['cell_and_band_info']['bandCount']
        else:
            # initialize required raster metadata to be place holders to be edited later by users
            spatial_coverage_info = OrderedDict([
                ('units', "Unnamed"),
                ('northlimit', 0),
                ('southlimit', 0),
                ('eastlimit', 0),
                ('westlimit', 0)
            ])
            cell_info = OrderedDict([
                ('name', title),
                ('rows', 0),
                ('columns', 0),
                ('cellSizeXValue', 0),
                ('cellSizeYValue', 0),
                ('cellSizeUnit', "Unnamed"),
                ('cellDataType', "Unnamed"),
                ('noDataValue', 0)
            ])
            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': spatial_coverage_info}}
            metadata.append(box)

            # Save extended meta to metadata variable
            metadata.append({'CellInformation': cell_info})
            bcount = 1

        for i in range(bcount):
            band_dict = OrderedDict()
            band_dict['name'] = 'Band_' + str(i+1)
            band_dict['variableName'] = 'Unnamed'
            band_dict['variableUnit'] = 'Unnamed'
            band_dict['method'] = ''
            band_dict['comment'] = ''
            metadata.append({'BandInformation': band_dict})
