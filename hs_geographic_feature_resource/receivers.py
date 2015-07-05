__author__ = 'drew'


from django.dispatch import receiver
from hs_core.signals import *
from hs_geographic_feature_resource.models import GeographicFeatureResource, OriginalCoverage, GeographicFeatureMetaData
from hs_core import hydroshare
import tempfile
import shutil
import os
from hs_geographic_feature_resource.parse_lib import *
from hs_geographic_feature_resource.forms import *
def is_shapefiles(files):
#check if uploaded files are valid shapefiles (shp, shx, dbf)
    shp, shx, dbf = False , False, False
    for file in files:
        if ".shp" in file.name:
            shp=True
        elif ".shx" in file.name:
            shx=True
        elif ".dbf" in file.name:
            dbf=True

    if shp & shx & dbf:
        return True
    else:
        return False

def is_spatialite(files):
    for file in files:
        if ".sqlite" in file.name:
            return True
    return False

# receiver used to extract metadata after user click on "create resource"
@receiver(pre_create_resource, sender=GeographicFeatureResource)
def geofeature_pre_create_resource(sender, **kwargs):
    if sender is GeographicFeatureResource:
        files = kwargs['files']
        metadata = kwargs['metadata']
        validate_files_dict = kwargs['validate_files']
        res_title = kwargs['title']
        res_titile_fn = res_title.replace(" ", "_")
        tmp_dir = None

        if files:
            if is_shapefiles(files):
                #create a temp foler and copy shapefiles
                tmp_dir=tempfile.mkdtemp()
                files_list_for_extract_metadata = []
                for file in files:
                    source = file.file.name
                    fileName, fileExtension = os.path.splitext(file.name)
                    target = tmp_dir + "/" + res_titile_fn + fileExtension
                    shutil.copy(source,target)

                shp_full_path = tmp_dir + "/" + res_titile_fn + ".shp"
                try:

                    # wgs84 extent
                    parsed_md_dict = parse_shp(shp_full_path)
                    coverage_dict={"coverage":{"type":"box", "value":parsed_md_dict["wgs84_extent_dict"]}}
                    metadata.append(coverage_dict)

                    #original extent
                    original_coverage_dict ={}
                    original_coverage_dict["originalcoverage"]={"extent":parsed_md_dict["origin_extent_dict"],
                                                                "projection_string":parsed_md_dict["origin_projection_string"],
                                                                "projection_name":parsed_md_dict["origin_projection_name"],
                                                                "datum":parsed_md_dict["origin_datum"],
                                                                "unit":parsed_md_dict["origin_unit"]
                                                                }
                    metadata.append(original_coverage_dict)

                    field_name_list=parsed_md_dict["field_meta_dict"]['field_list']

                    for field_name in field_name_list:
                        field_info_dict_item={}
                        field_info_dict_item['fieldinformation']=parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
                        metadata.append(field_info_dict_item)
                except:
                    res_dublin_core_meta = {}
                    res_type_specific_meta = {}


        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'No files are uploaded.'
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
            temp_dir = None

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_create, sender=GeographicFeatureResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == 'originalcoverage':
        element_form = OriginalCoverageValidationForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

    # request = kwargs['request']
    # element_name = kwargs['element_name']
    #
    # if element_name == 'originalcoverage':
    #     element_form = OriginalCoverageForm(data=request.POST)
    #
    # if element_form.is_valid():
    #     return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    # else:
    #     return {'is_valid': False, 'element_data_dict': None}

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=GeographicFeatureResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == 'originalcoverage':
        element_form = OriginalCoverageValidationForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}
