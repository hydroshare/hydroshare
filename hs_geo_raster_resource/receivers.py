__author__ = 'Hong Yi'
## Note: this module has been imported in the models.py in order to receive signals
## at the end of the models.py for the import of this module
from django.dispatch import receiver
from hs_core.hydroshare import pre_create_resource, post_create_resource
from hs_core.signals import *
from hs_geo_raster_resource.models import RasterResource
from hs_geo_raster_resource.models import BandInformation

res_md_dict = {}
# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page
@receiver(pre_describe_resource, sender=RasterResource)
def raster_describe_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        files = kwargs['files']
        if(files):
            # Assume only one file in files, and that that file is a zipfile
            infile = files[0]
            import raster_meta_extract
            global res_md_dict

            res_md_dict = raster_meta_extract.get_raster_meta_dict(infile.file.name)
            bcount = res_md_dict['cell_and_band_info']['bandCount']
        else:
            # initialize required raster metadata to be place holders to be entered later by users
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
            res_md_dict = {
                'spatial_coverage_info': spatial_coverage_info,
                'cell_and_band_info': cell_and_band_info,
            }
            bcount = 1
        for i in range(bcount):
            res_md_dict['cell_and_band_info']['name (band '+str(i+1)+')'] = 'Band_' + str(i+1)
            res_md_dict['cell_and_band_info']['variable (band '+str(i+1)+')'] = 'Unnamed'
            res_md_dict['cell_and_band_info']['units (band '+str(i+1)+')'] = 'Unnamed'
            res_md_dict['cell_and_band_info']['method (band '+str(i+1)+')'] = ''
            res_md_dict['cell_and_band_info']['comment (band '+str(i+1)+')'] = ''

        # have to set a name for spatial coverage since name is a required field in core metadata models.py
        res_md_dict['spatial_coverage_info']['place/area name']= "Unnamed"
        res_sci_md = {'Coverage': res_md_dict['spatial_coverage_info'],}
        res_ext_md = {'Cell and band info': res_md_dict['cell_and_band_info'],}
        return {"res_sci_metadata": res_sci_md,
                "res_add_metadata": res_ext_md}

# signal handler to validate resource metadata, and if valid, retrieve raster resource type specific metadata
# values from create-resource.html page and return a dictionary of metadata_terms to be passed on to
# hydroshare.create_resource() call to use when creating the resource; band_terms is a global dict variable
# that holds all band-related variables for use by post_create_resource() signal handler to create band(s)
# metadata as part of the created resource
band_terms = {}
@receiver(pre_call_create_resource, sender=RasterResource)
def raster_pre_call_resource_trigger(sender, **kwargs):
    if(sender is RasterResource):
        from hs_geo_raster_resource.forms import ValidateMetadataForm
        from django.core.exceptions import ValidationError
        qrylst = kwargs['request_post']
        metadata = kwargs['metadata']
        # add the corresponding names for form validation
        for k, v in qrylst.items():
            if k.startswith('name (band'):
                qrylst['bandName_' + k[-2:-1]] = v
            elif k.startswith('variable (band'):
                qrylst['variableName_' + k[-2:-1]] = v
            elif k.startswith('units (band'):
                qrylst['variableUnit_' + k[-2:-1]] = v
            elif k.startswith('method (band'):
                qrylst['method_' + k[-2:-1]] = v
            elif k.startswith('comment (band'):
                qrylst['comment_' + k[-2:-1]] = v
        if res_md_dict:
            res_md_dict['spatial_coverage_info']['name'] = qrylst['place/area name']
            res_md_dict['spatial_coverage_info'].pop('place/area name', None)

        box = {'coverage': {'type': 'box', 'value': res_md_dict['spatial_coverage_info']}}
        metadata.append(box)

        resource = kwargs['resource']
        #create form and do metadata validation
        frm = ValidateMetadataForm(qrylst)
        if frm.is_valid():
            global band_terms
            for k, v in qrylst.items():
                if k=='rows':
                    resource.rows = v
                elif k=='columns':
                    resource.columns = v
                elif k=='cellSizeXValue':
                    resource.cellSizeXValue = v
                elif k=='cellSizeYValue':
                    resource.cellSizeYValue = v
                elif k=='cellSizeUnit':
                    resource.cellSizeUnit = v
                elif k=='cellDataType':
                    resource.cellDataType = v
                elif k=='noDataValue':
                    resource.noDataValue = v
                elif k=='bandCount':
                    resource.bandCount = v
                elif k.startswith('bandName') or k.startswith('variableName') or k.startswith('variableUnit')\
                        or k.startswith('method') or k.startswith('comment'):
                    band_terms[k] = v
            for i in range(int(resource.bandCount)):
                meta_info = {}
                meta_info['name'] = band_terms['bandName_'+str(i+1)]
                meta_info['variableName'] = band_terms['variableName_'+str(i+1)]
                meta_info['variableUnit'] = band_terms['variableUnit_'+str(i+1)]
                meta_info['method'] = band_terms['method_'+str(i+1)]
                meta_info['comment'] = band_terms['comment_'+str(i+1)]
                metadata.append({'bandInformation': meta_info})
        else:
            raise ValidationError(frm.errors)