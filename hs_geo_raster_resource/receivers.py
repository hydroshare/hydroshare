__author__ = 'Hong Yi'
## Note: this module has been imported in the models.py in order to receive signals
## at the end of the models.py for the import of this module
from django.dispatch import receiver
from hs_core.signals import *
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource.models import BandInformation

res_md_dict = {}
# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page
@receiver(pre_create_resource, sender=RasterResource)
def raster_pre_create_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        files = kwargs['files']
        metadata = kwargs['metadata']
        if(files):
            # Assume only one file in files, and that that file is a zipfile
            infile = files[0]
            import raster_meta_extract
            global res_md_dict

            res_md_dict = raster_meta_extract.get_raster_meta_dict(infile.file.name)

            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': res_md_dict['spatial_coverage_info']['wgs84_coverage_info'] }}
            metadata.append(box)

            # Save extended meta to metadata variable
            metadata.append({'cell_and_band_info': res_md_dict['cell_and_band_info']})
        else:
            # initialize required raster metadata to be place holders to be edited later by users
            from collections import OrderedDict
            spatial_coverage_info = OrderedDict([
                ('projection', "Unnamed"),
                ('units', "Unnamed"),
                ('northlimit', 0),
                ('southlimit', 0),
                ('eastlimit', 0),
                ('westlimit', 0)
            ])
            cell_and_band_info = OrderedDict([
                ('rows', 0),
                ('columns', 0),
                ('cellSizeXValue', 0),
                ('cellSizeYValue', 0),
                ('cellSizeUnit', "Unnamed"),
                ('cellDataType', "Unnamed"),
                ('noDataValue', 0),
                ('bandCount', 1)
            ])
            # add core metadata coverage - box
            box = {'coverage': {'type': 'box', 'value': spatial_coverage_info}}
            metadata.append(box)

            # Save extended meta to metadata variable
            metadata.append({'cell_and_band_info': cell_and_band_info})

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=RasterResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == 'cell_and_band_info':
        form_data = {}
        for field_name in VariableValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]
        element_form = VariableValidationForm(form_data)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}
