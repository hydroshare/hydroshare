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
import zipfile, json
from hs_core.hydroshare.resource import ResourceFile

def is_shapefiles(files):
#check if uploaded files are valid shapefiles (shp, shx, dbf)
    fn_list=[]
    for file in files:
        fn_list.append(file.name)
    return check_fn_for_shp(fn_list)


def check_fn_for_shp(files):
#used by is_shapefiles
#check a list of filenames contains valid shapefiles (shp, shx, dbf)
    shp, shx, dbf = False , False, False
    all_have_same_filename = False
    shp_filename, shx_filename, dbf_filename =None, None, None
    if len(files) >= 3: # at least have 3 files: shp, shx, dbf
        for file in files:
            fileName, fileExtension = os.path.splitext(file)
            if ".shp" == fileExtension:
                shp_filename = fileName
                shp=True
            elif ".shx" == fileExtension:
                shx_filename = fileName
                shx=True
            elif ".dbf" == fileExtension:
                dbf_filename = fileName
                dbf=True

        if shp_filename == shx_filename and shp_filename == dbf_filename:
            all_have_same_filename = True

    if shp & shx & dbf & all_have_same_filename:
        return True
    else:
        return False


def is_zipped_shapefiles(files):
#check if the uploaded zip files contains valid shapefiles (shp, shx, dbf)
    if(len(files) == 1) and '.zip' in files[0].name:
        zipfile_path=files[0].file.name
        if zipfile.is_zipfile(zipfile_path):
            zf = zipfile.ZipFile(zipfile_path, 'r')
            content_fn_list = zf.namelist()
            return check_fn_for_shp(content_fn_list)
    return False



def is_spatialite(files):
# check for sqlite
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
        uploaded_file_type = None
        baseFilename=None
        uploadedFileCount=0
        uploadedFilenameString=None

        if files:
            if is_shapefiles(files):
                uploaded_file_type = "shp"
                #create a temp foler and copy shapefiles
                tmp_dir=tempfile.mkdtemp()
                files_list_for_extract_metadata = []
                for file in files:
                    source = file.file.name
                    fileName, fileExtension = os.path.splitext(file.name.lower())
                    #target = tmp_dir + "/" + res_titile_fn + fileExtension
                    target = tmp_dir + "/" + fileName + fileExtension
                    shutil.copy(source, target)

                #shp_full_path = tmp_dir + "/" + res_titile_fn + ".shp"
                shp_full_path = tmp_dir + "/" + fileName + ".shp"
                baseFilename=fileName
                uploadedFileCount=len(files)
                uploadedFilenameString_dict={}
                for i in range(len(files)):
                    uploadedFilenameString_dict[files[i].name]=str(i)
                uploadedFilenameString = json.dumps(uploadedFilenameString_dict)

            elif is_zipped_shapefiles(files):
                uploaded_file_type = "zipped_shp"
                tmp_dir=tempfile.mkdtemp()
                zipfile_path=files[0].file.name
                zf = zipfile.ZipFile(zipfile_path, 'r')
                fn_list = zf.namelist()
                zf.extractall(path=tmp_dir)
                zf.close()
                from django.core.files.uploadedfile import UploadedFile
                del files[:]
                for old_fn in fn_list:
                    source = tmp_dir + '/' +old_fn
                    fileName, fileExtension = os.path.splitext(old_fn)
                    #target = tmp_dir + "/" + res_titile_fn + fileExtension
                    target = tmp_dir + "/" + fileName + fileExtension
                    #shutil.copy(source, target)
                    #files.append(UploadedFile(file=open(target, 'r'), name=res_titile_fn + fileExtension))
                    files.append(UploadedFile(file=open(target, 'r'), name=fileName + fileExtension))

                #shp_full_path = tmp_dir + "/" + res_titile_fn + ".shp"
                shp_full_path = tmp_dir + "/" + fileName + ".shp"
                baseFilename = fileName
                uploadedFileCount=len(fn_list)
                uploadedFilenameString_dict={}
                for i in range(len(fn_list)):
                    uploadedFilenameString_dict[fn_list[i]]=str(i)
                uploadedFilenameString = json.dumps(uploadedFilenameString_dict)

            else:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = 'Please upload valid file(s).'

            if uploaded_file_type == "shp" or uploaded_file_type == "zipped_shp":
                try:

                    #fileTypeInfo_dict
                    originalFileInfo_dict={}
                    originalFileInfo_dict["fileType"]="SHP" if uploaded_file_type == "shp" else "ZSHP"
                    originalFileInfo_dict["baseFilename"] = baseFilename
                    originalFileInfo_dict["fileCount"]= uploadedFileCount
                    originalFileInfo_dict["filenameString"]=uploadedFilenameString
                    metadata.append({"OriginalFileInfo": originalFileInfo_dict})

                    # wgs84 extent
                    parsed_md_dict = parse_shp(shp_full_path)
                    if parsed_md_dict["wgs84_extent_dict"]["westlimit"]!=UNKNOWN_STR:
                        coverage_dict={"coverage": {"type": "box", "value": parsed_md_dict["wgs84_extent_dict"]}}
                        metadata.append(coverage_dict)

                    #original extent
                    original_coverage_dict ={}
                    original_coverage_dict["originalcoverage"]={"northlimit":parsed_md_dict["origin_extent_dict"]["northlimit"],
                                                                "southlimit":parsed_md_dict["origin_extent_dict"]["southlimit"],
                                                                "westlimit":parsed_md_dict["origin_extent_dict"]["westlimit"],
                                                                "eastlimit":parsed_md_dict["origin_extent_dict"]["eastlimit"],
                                                                "projection_string":parsed_md_dict["origin_projection_string"],
                                                                "projection_name":parsed_md_dict["origin_projection_name"],
                                                                "datum":parsed_md_dict["origin_datum"],
                                                                "unit":parsed_md_dict["origin_unit"]
                                                                }
                    metadata.append(original_coverage_dict)

                    #field
                    field_name_list=parsed_md_dict["field_meta_dict"]['field_list']
                    for field_name in field_name_list:
                        field_info_dict_item={}
                        field_info_dict_item['fieldinformation']=parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
                        metadata.append(field_info_dict_item)

                    #geometry
                    geometryinformation={"featureCount":parsed_md_dict["feature_count"],"geometryType":parsed_md_dict["geometry_type"]}
                    metadata.append({"geometryinformation": geometryinformation})



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
    elif element_name == 'fieldinformation':
        element_form = FieldInformationValidationForm(data=request.POST)
    elif element_name == 'geometryinformation':
        element_form = GeometryInformationValidationForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=GeographicFeatureResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == 'originalcoverage':
        element_form = OriginalCoverageValidationForm(data=request.POST)
    elif element_name == 'fieldinformation':
        element_form = FieldInformationValidationForm(data=request.POST)
    elif element_name == 'geometryinformation':
        element_form = GeometryInformationValidationForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_delete_file_from_resource, sender=GeographicFeatureResource)
def geofeature_pre_delete_file_from_resource(sender, **kwargs):
    if sender is GeographicFeatureResource:
        res_obj = kwargs['resource']
        del_file = kwargs['file']
        validate_files_dict = kwargs['validate_files']
        one_file_removed=True
        ori_file_info=res_obj.metadata.originalfileinfo.all().first()
        if ori_file_info.fileType == "SHP" or ori_file_info.fileType=="ZSHP":
            del_f_fullname=del_file.resource_file.name.lower()
            del_f_fullname= del_f_fullname[del_f_fullname.rfind('/')+1:]
            del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
            if del_f_ext in [".shp", ".shx", ".dbf"]:
                #error_message = " The shp, shx or dbf files can not be removed."
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = " The shp, shx or dbf files can not be removed."
                one_file_removed=False
                #raise ResourceFileValidationException(error_message)
            elif del_f_ext == ".prj":
                originalcoverage_obj=res_obj.metadata.originalcoverage.all().first()
                res_obj.metadata.update_element('OriginalCoverage', element_id=originalcoverage_obj.id, projection_string=UNKNOWN_STR, projection_name =UNKNOWN_STR, datum =UNKNOWN_STR, unit =UNKNOWN_STR)

                # wgs84_extent_dict={}
                # wgs84_extent_dict["westlimit"]=UNKNOWN_STR
                # wgs84_extent_dict["northlimit"]=UNKNOWN_STR
                # wgs84_extent_dict["eastlimit"]=UNKNOWN_STR
                # wgs84_extent_dict["southlimit"]=UNKNOWN_STR
                # wgs84_extent_dict["projection"]=UNKNOWN_STR
                # wgs84_extent_dict["units"]=UNKNOWN_STR
                # coverage_obj=res_obj.metadata.coverages.all().first()
                # res_obj.metadata.update_element('coverage', element_id=coverage_obj.id, type='box', value=wgs84_extent_dict)
                res_obj.metadata.coverages.all().delete()

            if one_file_removed:
                ori_fn_dict=json.loads(ori_file_info.filenameString)
                if del_f_fullname in ori_fn_dict:
                    del ori_fn_dict[del_f_fullname]
                    res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,filenameString=json.dumps(ori_fn_dict))

    pass

@receiver(pre_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_pre_add_files_to_resource(sender, **kwargs):
    if sender is GeographicFeatureResource:
        res_obj = kwargs['resource']
        files = kwargs['files']
        validate_files_dict = kwargs['validate_files']
        ori_file_info=res_obj.metadata.originalfileinfo.all().first()
        crt_f_str=ori_file_info.filenameString.lower()
        some_new_files_added=True
        # res_file_list=ResourceFile.objects.filter(object_id=res_obj.id)
        # for res_f in res_file_list:
        #     n=res_f.resource_file.name

        #for crt_f
        for f in files:
            new_f_fullname=f.name.lower()
            new_f_name, new_f_ext=os.path.splitext(new_f_fullname)

            if new_f_ext in  [".shp", ".shx", ".dbf"]:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = "No more shp, shx, dbf files can be uploaded."
                some_new_files_added=False
                break
            elif new_f_name!=ori_file_info.baseFilename:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = "At least one filename does not match this shapefiles resource."
                some_new_files_added=False
                break
            elif crt_f_str.find(new_f_fullname)!=-1:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = "At least one file already exits."
                some_new_files_added=False
                break
        if some_new_files_added:
            for f in files:
                new_f_fullname=f.name.lower()
                ori_fn_dict=json.loads(ori_file_info.filenameString)
                ori_fn_dict[new_f_fullname]="new"
            res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,filenameString=json.dumps(ori_fn_dict))




        #if ori_file_info.fileType=="SHP" or ori_file_info.fileType=="ZSHP":


    pass

@receiver(post_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_post_add_files_to_resource_handler(sender, **kwargs):
    tmp_dir=None

    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    user = kwargs['user']

    res_file_list = resource.files.all() if resource.files.all() else None
    if res_file_list:
        tmp_dir=tempfile.mkdtemp()
        for res_f in res_file_list:
            source = res_f.resource_file.file.name
            f_fullname=res_f.resource_file.name.lower()
            f_fullname= f_fullname[f_fullname.rfind('/')+1:]

            fileName, fileExtension = os.path.splitext(f_fullname)
            target = tmp_dir + "/" + fileName + fileExtension
            shutil.copy(source, target)
        shp_full_path = tmp_dir + "/" + fileName + ".shp"
        parsed_md_dict = parse_shp(shp_full_path)

        originalcoverage_obj=resource.metadata.originalcoverage.all().first()
        resource.metadata.update_element('OriginalCoverage', element_id=originalcoverage_obj.id,
                                         projection_string=parsed_md_dict["origin_projection_string"],
                                         projection_name =parsed_md_dict["origin_projection_name"],
                                         datum =parsed_md_dict["origin_datum"],
                                         unit =parsed_md_dict["origin_unit"])
        coverage_obj=resource.metadata.coverages.all().first()
        if coverage_obj:
            resource.metadata.update_element('coverage', element_id=coverage_obj.id,
                                         type='box',
                                         value=parsed_md_dict["wgs84_extent_dict"])
        else:
            resource.metadata.create_element('Coverage', type='box', value=parsed_md_dict["wgs84_extent_dict"])

        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
            temp_dir = None
        pass

@receiver(post_create_resource, sender=GeographicFeatureResource)
def geofeature_post_create_resource_handler(sender, **kwargs):
    pass