
import os
import tempfile
import shutil
import zipfile
import json

from django.dispatch import receiver
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare.resource import ResourceFile
from hs_core.signals import pre_create_resource, pre_metadata_element_create,\
                            pre_metadata_element_update, pre_delete_file_from_resource,\
                            pre_add_files_to_resource, post_add_files_to_resource


from hs_geographic_feature_resource.parse_lib import parse_shp, UNKNOWN_STR
from hs_geographic_feature_resource.forms import OriginalCoverageValidationForm,\
                                                 GeometryInformationValidationForm,\
                                                 FieldInformationValidationForm
from hs_geographic_feature_resource.models import GeographicFeatureResource

def is_shapefiles(files):
    # check if uploaded files are valid shapefiles (shp, shx, dbf)
    fn_list = []
    for f in files:
        fn_list.append(f.name)
    return check_fn_for_shp(fn_list)

def check_fn_for_shp(files):
    # used by is_shapefiles
    # check a list of filenames for valid shapefiles (shp, shx, dbf)
    shp, shx, dbf = False, False, False
    all_have_same_filename = False
    shp_filename, shx_filename, dbf_filename = None, None, None
    dir_count = 0 # can have 0 or 1 folder
    if len(files) >= 3: # at least have 3 files: shp, shx, dbf
        for f in files:
            if str(f).endswith('/'):
                dir_count += 1
            else:
                fileName, fileExtension = os.path.splitext(f.lower())
                if ".shp" == fileExtension:
                    shp_filename = fileName
                    shp = True
                elif ".shx" == fileExtension:
                    shx_filename = fileName
                    shx = True
                elif ".dbf" == fileExtension:
                    dbf_filename = fileName
                    dbf = True

        if shp_filename == shx_filename and shp_filename == dbf_filename:
            all_have_same_filename = True

    if shp and shx and dbf and all_have_same_filename and (dir_count <= 1):
        return True
    else:
        return False

def is_zipped_shapefiles(files):
    # check if the uploaded zip files contains valid shapefiles (shp, shx, dbf)
    if(len(files) == 1) and files[0].name.lower().endswith(".zip"):
        zipfile_path = files[0].file.name
        if zipfile.is_zipfile(zipfile_path):
            zf = zipfile.ZipFile(zipfile_path, 'r')
            content_fn_list = zf.namelist()
            return check_fn_for_shp(content_fn_list)
    return False

def lower_filenames(files):
    for f in files:
        f.name = f.name.lower()

def check_uploaded_files_type(files):
        files_type_dict = {}
        if is_shapefiles(files):
            lower_filenames(files) # change all uploaded shapefile names to lower case
            uploaded_file_type = "shp"
            files_type_dict["uploaded_file_type"] = uploaded_file_type
            # create a temp folder and copy shapefiles
            tmp_dir = tempfile.mkdtemp()
            files_type_dict["tmp_dir"] = tmp_dir
            baseFilename = None
            for f in files:
                source = f.file.name
                fileName, fileExtension = os.path.splitext(f.name)
                if fileExtension == ".shp":
                    baseFilename = fileName
                target = tmp_dir + "/" + fileName + fileExtension
                shutil.copy(source, target)
            shp_full_path = tmp_dir + "/" + fileName + ".shp"
            files_type_dict['shp_full_path'] = shp_full_path
            files_type_dict["baseFilename"] = baseFilename
            uploadedFileCount = len(files)
            files_type_dict["uploadedFileCount"] = uploadedFileCount
            uploadedFilenameString_dict = {}
            for i in range(len(files)):
                uploadedFilenameString_dict[files[i].name] = str(i)
            uploadedFilenameString = json.dumps(uploadedFilenameString_dict)
            files_type_dict["uploadedFilenameString"] = uploadedFilenameString
            files_type_dict["are_files_valid"] = True
            files_type_dict['message'] = 'All files are validated.'

        elif is_zipped_shapefiles(files):
            uploaded_file_type = "zipped_shp"
            files_type_dict["uploaded_file_type"] = uploaded_file_type
            tmp_dir = tempfile.mkdtemp()
            files_type_dict["tmp_dir"] = tmp_dir
            zipfile_path = files[0].file.name
            zf = zipfile.ZipFile(zipfile_path, 'r')
            fn_list = zf.namelist()
            # extract all zip contents (files and folders) to tmp_dir (/tmp/tmpXXXXXX/)
            zf.extractall(path=tmp_dir)
            zf.close()
            baseFilename = None
            shp_full_path = None
            dir_count = 0
            uploadedFileCount = 0

            del files[:]
            uploadedFilenameString_dict = {}
            for old_fn in fn_list:
                source = tmp_dir + '/' + old_fn
                target = tmp_dir
                if os.path.isfile(source): # only add files, filter out folders (should be 0 or 1 folder)
                    fileName, fileExtension = os.path.splitext(old_fn.lower())
                    if '/' in fileName: # if the file is inside a folder, move it to the root of tmp_dir
                        path_and_filename = fileName.split('/')
                        fileName = path_and_filename[len(path_and_filename)-1]
                    target = tmp_dir + '/' + fileName + fileExtension
                    shutil.move(source, target) # move file from folder (if any) to tmp root and rename it into lower case

                    if fileExtension == ".shp": # save the real path to .shp file
                        baseFilename = fileName # save the name of .shp as the baseFileName
                        shp_full_path = target
                    files.append(UploadedFile(file=open(target, 'r'), name=fileName + fileExtension))
                    uploadedFileCount += 1
                    uploadedFilenameString_dict[fileName + fileExtension] = str(1)
                else:
                    dir_count += 1 # folder count +1 (should be 0 or 1 folder)

            files_type_dict['shp_full_path'] = shp_full_path

            files_type_dict["baseFilename"] = baseFilename
            files_type_dict["uploadedFileCount"] = uploadedFileCount
            uploadedFilenameString = json.dumps(uploadedFilenameString_dict)
            files_type_dict["uploadedFilenameString"] = uploadedFilenameString
            files_type_dict["are_files_valid"] = True
            files_type_dict['message'] = 'All files are validated.'
        else:
            files_type_dict["are_files_valid"] = False
            files_type_dict['message'] = 'Please upload valid file(s).'

        return files_type_dict

def parse_shp_zshp(uploaded_file_type, baseFilename, uploadedFileCount, uploadedFilenameString, shp_full_path):
    try:
        metadata_array = []
        metadata_dict = {}

        # fileTypeInfo_dict
        originalFileInfo_dict = {}
        originalFileInfo_dict["fileType"] = "SHP" if uploaded_file_type == "shp" else "ZSHP"
        originalFileInfo_dict["baseFilename"] = baseFilename
        originalFileInfo_dict["fileCount"] = uploadedFileCount
        originalFileInfo_dict["filenameString"] = uploadedFilenameString
        metadata_array.append({"OriginalFileInfo": originalFileInfo_dict})
        metadata_dict["originalfileinfo"] = originalFileInfo_dict

        # wgs84 extent
        parsed_md_dict = parse_shp(shp_full_path)
        if parsed_md_dict["wgs84_extent_dict"]["westlimit"] != UNKNOWN_STR:
            coverage_dict = {"Coverage": {"type": "box", "value": parsed_md_dict["wgs84_extent_dict"]}}
            metadata_array.append(coverage_dict)
            metadata_dict["coverage"] = coverage_dict

        # original extent
        original_coverage_dict = {}
        original_coverage_dict["originalcoverage"] = {"northlimit": parsed_md_dict["origin_extent_dict"]["northlimit"],
                                                      "southlimit": parsed_md_dict["origin_extent_dict"]["southlimit"],
                                                      "westlimit": parsed_md_dict["origin_extent_dict"]["westlimit"],
                                                      "eastlimit": parsed_md_dict["origin_extent_dict"]["eastlimit"],
                                                      "projection_string": parsed_md_dict["origin_projection_string"],
                                                      "projection_name": parsed_md_dict["origin_projection_name"],
                                                      "datum": parsed_md_dict["origin_datum"],
                                                      "unit": parsed_md_dict["origin_unit"]
                                                      }
        metadata_array.append(original_coverage_dict)
        metadata_dict["originalcoverage"] = original_coverage_dict

        # field
        field_info_array = []
        field_name_list = parsed_md_dict["field_meta_dict"]['field_list']
        for field_name in field_name_list:
            field_info_dict_item = {}
            field_info_dict_item['fieldinformation'] = parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
            field_info_array.append(field_info_dict_item)
        metadata_array.extend(field_info_array)
        metadata_dict['field_info_array'] = field_info_array

        # geometry
        geometryinformation = {"featureCount": parsed_md_dict["feature_count"],
                               "geometryType": parsed_md_dict["geometry_type"]}
        metadata_array.append({"geometryinformation": geometryinformation})
        metadata_dict["geometryinformation"] = geometryinformation
        return(metadata_array, metadata_dict)
    except:
        raise Exception("Parse Shapefiles Failed!")

# receiver used to extract metadata after user click on "create resource"
@receiver(pre_create_resource, sender=GeographicFeatureResource)
def geofeature_pre_create_resource(sender, **kwargs):

    tmp_dir = None
    try:
        files = kwargs['files']
        metadata = kwargs['metadata']
        validate_files_dict = kwargs['validate_files']

        if files:
            files_type = check_uploaded_files_type(files)
            validate_files_dict['are_files_valid'] = files_type['are_files_valid']
            validate_files_dict['message'] = files_type['message']

            if validate_files_dict['are_files_valid']:
                tmp_dir = files_type['tmp_dir']
                baseFilename = files_type['baseFilename']
                uploaded_file_type = files_type['uploaded_file_type']
                uploadedFileCount = files_type['uploadedFileCount']
                uploadedFilenameString = files_type['uploadedFilenameString']
                shp_full_path = files_type['shp_full_path']
                if uploaded_file_type == "shp" or uploaded_file_type == "zipped_shp":
                    meta_array, meta_dict = parse_shp_zshp(uploaded_file_type,
                                                           baseFilename,
                                                           uploadedFileCount,
                                                           uploadedFilenameString,
                                                           shp_full_path)
                    metadata.extend(meta_array)
        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Please upload valid file(s).'
    except:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Uploaded files are invalid or corrupt.'
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
            tmp_dir = None

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_create, sender=GeographicFeatureResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return validate_form(request, element_name)

# This handler is executed only when a metadata element is updated as part of editing a resource
@receiver(pre_metadata_element_update, sender=GeographicFeatureResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return validate_form(request, element_name)


def validate_form(request, element_name):
    element_form = None
    if element_name == 'originalcoverage':
        element_form = OriginalCoverageValidationForm(data=request.POST)
    elif element_name == 'geometryinformation':
        element_form = GeometryInformationValidationForm(data=request.POST)
    elif element_name == 'fieldinformation':
        element_form = FieldInformationValidationForm(data=request.POST)

    if element_form is not None and element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_delete_file_from_resource, sender=GeographicFeatureResource)
def geofeature_pre_delete_file_from_resource(sender, **kwargs):

    res_obj = kwargs['resource']
    del_file = kwargs['file']
    one_file_removed = True
    all_file_removed = False
    ori_file_info = res_obj.metadata.originalfileinfo.all().first()
    if ori_file_info.fileType == "SHP" or ori_file_info.fileType == "ZSHP":
        del_f_fullname = del_file.resource_file.name
        del_f_fullname = del_f_fullname[del_f_fullname.rfind('/')+1:]
        del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
        if del_f_ext in [".shp", ".shx", ".dbf"]:
            # The shp, shx or dbf files cannot be removed.
            all_file_removed = True
            one_file_removed = False

            for f in ResourceFile.objects.filter(object_id=res_obj.id):
                res_f_fullname = f.resource_file.name
                res_f_fullname = res_f_fullname[res_f_fullname.rfind('/')+1:]
                if res_f_fullname != del_f_fullname:
                    f.resource_file.delete()
                    f.delete()

        elif del_f_ext == ".prj":
            originalcoverage_obj = res_obj.metadata.originalcoverage.all().first()
            res_obj.metadata.update_element('OriginalCoverage', element_id=originalcoverage_obj.id,
                                            projection_string=UNKNOWN_STR, projection_name=UNKNOWN_STR,
                                            datum=UNKNOWN_STR, unit=UNKNOWN_STR)
            res_obj.metadata.coverages.all().delete()

        if one_file_removed:
            ori_fn_dict = json.loads(ori_file_info.filenameString)
            if del_f_fullname in ori_fn_dict:
                del ori_fn_dict[del_f_fullname]
                res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,
                                                filenameString=json.dumps(ori_fn_dict))
        elif all_file_removed:
            res_obj.metadata.originalfileinfo.all().delete()
            res_obj.metadata.geometryinformation.all().delete()
            res_obj.metadata.fieldinformation.all().delete()
            res_obj.metadata.originalcoverage.all().delete()
            res_obj.metadata.coverages.all().delete()

@receiver(pre_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_pre_add_files_to_resource(sender, **kwargs):

    res_obj = kwargs['resource']
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']
    ori_file_info = res_obj.metadata.originalfileinfo.all().first()
    some_new_files_added = True

    try:
        if ori_file_info and ResourceFile.objects.filter(object_id=res_obj.id).count() > 0: # just add non-required files
            crt_f_str = ori_file_info.filenameString
            lower_filenames(files)
            for f in files:
                new_f_fullname = f.name
                new_f_name, new_f_ext = os.path.splitext(new_f_fullname)

                if new_f_ext in  [".shp", ".shx", ".dbf"]:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "No more shp, shx, dbf files can be added."
                    some_new_files_added = False
                    break
                elif (new_f_name != ori_file_info.baseFilename) and \
                        (not (new_f_name == ori_file_info.baseFilename + ".shp" and new_f_ext == ".xml")):
                    # need to check is it ShapefileBaseName.shp.xml
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "At least one file does not follow the ESRI Shapefile naming convention."
                    some_new_files_added = False
                    break
                elif crt_f_str.find(new_f_fullname) != -1:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "At least one file already exists."
                    some_new_files_added = False
                    break
            if some_new_files_added:
                ori_fn_dict = json.loads(ori_file_info.filenameString)
                for f in files:
                    new_f_fullname = f.name
                    ori_fn_dict[new_f_fullname] = "new"
                res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,
                                                filenameString=json.dumps(ori_fn_dict))
        else: # all files have been removed, start it over
            if files:
                files_type = check_uploaded_files_type(files)
                tmp_dir = None
                uploaded_file_type = None
                baseFilename = None
                uploadedFileCount = 0
                uploadedFilenameString = None
                shp_full_path = None
                validate_files_dict['are_files_valid'] = files_type['are_files_valid']
                validate_files_dict['message'] = files_type['message']

                if validate_files_dict['are_files_valid']:

                    if res_obj.metadata.originalfileinfo.all().first():
                        res_obj.metadata.originalfileinfo.all().delete()
                    if res_obj.metadata.geometryinformation.all().first():
                        res_obj.metadata.geometryinformation.all().delete()
                    if res_obj.metadata.fieldinformation.all().first():
                        res_obj.metadata.fieldinformation.all().delete()
                    if res_obj.metadata.originalcoverage.all().first():
                        res_obj.metadata.originalcoverage.all().delete()
                    if res_obj.metadata.coverages.all().first():
                        res_obj.metadata.coverages.all().delete()

                    tmp_dir = files_type['tmp_dir']
                    baseFilename = files_type['baseFilename']
                    uploaded_file_type = files_type['uploaded_file_type']
                    uploadedFileCount = files_type['uploadedFileCount']
                    uploadedFilenameString = files_type['uploadedFilenameString']
                    shp_full_path = files_type['shp_full_path']
                    parsed_md_dict = None
                    if uploaded_file_type == "shp" or uploaded_file_type == "zipped_shp":
                        meta_array, meta_dict = parse_shp_zshp(uploaded_file_type,
                                                               baseFilename,
                                                               uploadedFileCount,
                                                               uploadedFilenameString,
                                                               shp_full_path)

                    # create metadat objects
                    if "coverage" in meta_dict.keys():
                        coverage_dict = meta_dict["coverage"]['Coverage']
                        res_obj.metadata.create_element('Coverage', type=coverage_dict['type'],
                                                        value=coverage_dict['value'])

                    originalfileinfo_dict = meta_dict["originalfileinfo"]
                    res_obj.metadata.create_element('OriginalFileInfo',
                                                    fileType=originalfileinfo_dict['fileType'],
                                                    baseFilename=originalfileinfo_dict['baseFilename'],
                                                    fileCount=originalfileinfo_dict['fileCount'],
                                                    filenameString=originalfileinfo_dict['filenameString'])

                    originalcoverage_dict = meta_dict["originalcoverage"]['originalcoverage']
                    res_obj.metadata.create_element('OriginalCoverage',
                                                    northlimit=originalcoverage_dict['northlimit'],
                                                    southlimit=originalcoverage_dict['southlimit'],
                                                    westlimit=originalcoverage_dict['westlimit'],
                                                    eastlimit=originalcoverage_dict['eastlimit'],
                                                    projection_string=originalcoverage_dict['projection_string'],
                                                    projection_name=originalcoverage_dict['projection_name'],
                                                    datum=originalcoverage_dict['datum'],
                                                    unit=originalcoverage_dict['unit'])

                    field_info_array = meta_dict["field_info_array"]
                    for field_info in field_info_array:
                        field_info_dict = field_info["fieldinformation"]
                        res_obj.metadata.create_element('FieldInformation',
                                                    fieldName=field_info_dict['fieldName'],
                                                    fieldType=field_info_dict['fieldType'],
                                                    fieldTypeCode=field_info_dict['fieldTypeCode'],
                                                    fieldWidth=field_info_dict['fieldWidth'],
                                                    fieldPrecision=field_info_dict['fieldPrecision'])

                    geometryinformation_dict = meta_dict["geometryinformation"]
                    res_obj.metadata.create_element('GeometryInformation',
                                                    featureCount=geometryinformation_dict['featureCount'],
                                                    geometryType=geometryinformation_dict['geometryType']
                                                    )

                else:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = 'Please upload valid file(s).'
                if tmp_dir is not None:
                    shutil.rmtree(tmp_dir)
                    tmp_dir = None
    except:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = "Please upload valid file(s)."

@receiver(post_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_post_add_files_to_resource_handler(sender, **kwargs):
    tmp_dir = None
    resource = kwargs['resource']
    files = kwargs['files']
    found_shp = False
    found_prj = False
    found_zip = False
    for f in files:
        if f.name.endswith(".shp"):
            found_shp = True
        elif f.name.endswith(".prj"):
            found_prj = True
        elif f.name.endswith(".zip"):
            found_zip = True

    if found_prj and (not found_shp):
        res_file_list = resource.files.all() if resource.files.all() else None
        if res_file_list:
            tmp_dir = tempfile.mkdtemp()
            for res_f in res_file_list:
                source = res_f.resource_file.file.name
                f_fullname = res_f.resource_file.name
                f_fullname = f_fullname[f_fullname.rfind('/')+1:]

                fileName, fileExtension = os.path.splitext(f_fullname)
                target = tmp_dir + "/" + fileName + fileExtension
                shutil.copy(source, target)
            ori_file_info = resource.metadata.originalfileinfo.all().first()
            shp_full_path = tmp_dir + "/" + ori_file_info.baseFilename + ".shp"
            parsed_md_dict = parse_shp(shp_full_path)
            originalcoverage_obj = resource.metadata.originalcoverage.all().first()
            if originalcoverage_obj:
                resource.metadata.update_element('OriginalCoverage',
                                                 element_id=originalcoverage_obj.id,
                                                 projection_string=parsed_md_dict["origin_projection_string"],
                                                 projection_name=parsed_md_dict["origin_projection_name"],
                                                 datum=parsed_md_dict["origin_datum"],
                                                 unit=parsed_md_dict["origin_unit"])

            coverage_obj = resource.metadata.coverages.all().first()
            if coverage_obj:
                resource.metadata.update_element('coverage',
                                                 element_id=coverage_obj.id,
                                                 type='box',
                                                 value=parsed_md_dict["wgs84_extent_dict"])
            else:
                resource.metadata.create_element('Coverage', type='box', value=parsed_md_dict["wgs84_extent_dict"])

            if tmp_dir is not None:
                shutil.rmtree(tmp_dir)
                tmp_dir = None