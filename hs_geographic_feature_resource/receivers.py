import os
import tempfile
import shutil
import zipfile
import json
import logging

from django.dispatch import receiver
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import ResourceFile, \
    get_resource_file_name, delete_resource_file_only
from hs_core.signals import pre_create_resource, pre_metadata_element_create,\
                            pre_metadata_element_update, pre_delete_file_from_resource,\
                            pre_add_files_to_resource, post_add_files_to_resource

from hs_geographic_feature_resource.parse_lib import parse_shp, UNKNOWN_STR, parse_shp_xml
from hs_geographic_feature_resource.forms import OriginalCoverageValidationForm,\
                                                 GeometryInformationValidationForm,\
                                                 FieldInformationValidationForm
from hs_geographic_feature_resource.models import GeographicFeatureResource

logger = logging.getLogger(__name__)


def is_shapefiles(file_info_list):
    # check if uploaded files are valid shapefiles (shp, shx, dbf)
    fn_list = []
    for f_info in file_info_list:
        fn_list.append(f_info[0])
    return check_fn_for_shp(fn_list)


def is_zipped_shapefiles(file_info_list):
    # check if the uploaded zip files contains valid shapefiles (shp, shx, dbf)
    if(len(file_info_list) == 1) and file_info_list[0][0].lower().endswith(".zip"):
        zipfile_path = file_info_list[0][1]
        if zipfile.is_zipfile(zipfile_path):
            zf = zipfile.ZipFile(zipfile_path, 'r')
            content_fn_list = zf.namelist()
            return check_fn_for_shp(content_fn_list)
    return False


def check_fn_for_shp(files):
    # used by is_shapefiles
    # check a list of filenames for valid shapefiles (shp, shx, dbf)
    shp, shx, dbf = False, False, False
    all_have_same_filename = False
    shp_filename, shx_filename, dbf_filename = None, None, None
    dir_count = 0  # can have 0 or 1 folder
    if len(files) >= 3:  # at least have 3 mandatory files: shp, shx, dbf
        for f in files:
            if f.endswith('/'):
                dir_count += 1
            else:
                fullName = f[f.rfind('/')+1:]
                fileName, fileExtension = os.path.splitext(fullName.lower())
                if ".shp" == fileExtension:
                    shp_filename = fileName
                    if not shp:
                        shp = True
                    else:
                        return False
                elif ".shx" == fileExtension:
                    shx_filename = fileName
                    if not shx:
                        shx = True
                    else:
                        return False
                elif ".dbf" == fileExtension:
                    dbf_filename = fileName
                    if not dbf:
                        dbf = True
                    else:
                        return False

        if shp_filename == shx_filename and shp_filename == dbf_filename:
            all_have_same_filename = True

    if shp and shx and dbf and all_have_same_filename and (dir_count <= 1):
        return True
    else:
        return False


def check_uploaded_files_type(file_info_list):
    files_type_dict = {}
    files_new = []
    if is_shapefiles(file_info_list):
        uploaded_file_type = "shp"
        files_type_dict["uploaded_file_type"] = uploaded_file_type
        # create a temp folder and copy shapefiles
        tmp_dir = tempfile.mkdtemp()
        files_type_dict["tmp_dir"] = tmp_dir
        baseFilename = None
        for f_info in file_info_list:
            source = f_info[1]
            fileName, fileExtension = os.path.splitext(f_info[0].lower())
            if fileExtension == ".shp":
                baseFilename = fileName
            # target shapefile names are all in lower case
            target = tmp_dir + "/" + f_info[0].lower()
            shutil.copy(source, target)
        shp_full_path = tmp_dir + "/" + fileName + ".shp"
        files_type_dict['shp_full_path'] = shp_full_path
        files_type_dict["baseFilename"] = baseFilename
        # Expected fullpath of ESRI Shapefile Metadat XML file
        # This file may not exist, should check existence before reading
        shp_xml_full_path = tmp_dir + "/" + baseFilename + ".shp.xml"
        files_type_dict['shp_xml_full_path'] = shp_xml_full_path

        uploadedFileCount = len(file_info_list)
        files_type_dict["uploadedFileCount"] = uploadedFileCount
        uploadedFilenameString_dict = {}
        for i in range(len(file_info_list)):
            uploadedFilenameString_dict[file_info_list[i][0].lower()] = str(i)
        uploadedFilenameString = json.dumps(uploadedFilenameString_dict)
        files_type_dict["uploadedFilenameString"] = uploadedFilenameString
        files_type_dict["are_files_valid"] = True
        files_type_dict['message'] = 'All files are validated.'

    elif is_zipped_shapefiles(file_info_list):
        uploaded_file_type = "zipped_shp"
        files_type_dict["uploaded_file_type"] = uploaded_file_type
        tmp_dir = tempfile.mkdtemp()
        files_type_dict["tmp_dir"] = tmp_dir
        zipfile_path = file_info_list[0][1]
        zf = zipfile.ZipFile(zipfile_path, 'r')
        fn_list = zf.namelist()
        # extract all zip contents (files and folders) to tmp_dir (/tmp/tmpXXXXXX/)
        zf.extractall(path=tmp_dir)
        zf.close()
        baseFilename = None
        shp_full_path = None
        uploadedFileCount = 0

        uploadedFilenameString_dict = {}
        for fn in fn_list:
            source = tmp_dir + '/' + fn
            target = tmp_dir
            if os.path.isfile(source):
                # only add files, filter out folders (should be 0 or 1 folder)
                fileName, fileExtension = os.path.splitext(fn)
                if '/' in fileName:
                    # if the file is inside a folder, move it to the root of tmp_dir
                    path_and_filename = fileName.split('/')
                    fileName = path_and_filename[len(path_and_filename)-1]
                target = tmp_dir + '/' + fileName.lower() + fileExtension.lower()
                # move file from folder (if any) to tmp root and rename it into lower case
                shutil.move(source, target)

                if fileExtension.lower() == ".shp":  # save the real path to .shp file
                    baseFilename = fileName.lower()  # save the name of .shp as the baseFileName
                    shp_full_path = target
                files_new.append(UploadedFile(file=open(target, 'r'),
                                              name=fileName + fileExtension))
                uploadedFileCount += 1
                # -1: unzipped file
                uploadedFilenameString_dict[(fileName + fileExtension).lower()] = str(-1)

        files_type_dict['shp_full_path'] = shp_full_path
        files_type_dict["baseFilename"] = baseFilename
        # Expected fullpath of ESRI Shapefile Metadat XML file
        # This file may not exist, should check existence before reading
        shp_xml_full_path = tmp_dir + "/" + baseFilename + ".shp.xml"
        files_type_dict['shp_xml_full_path'] = shp_xml_full_path

        files_type_dict["uploadedFileCount"] = uploadedFileCount
        uploadedFilenameString = json.dumps(uploadedFilenameString_dict)
        files_type_dict["uploadedFilenameString"] = uploadedFilenameString
        files_type_dict["files_new"] = files_new
        files_type_dict["are_files_valid"] = True
        files_type_dict['message'] = 'All files are validated.'
    else:
        files_type_dict["are_files_valid"] = False
        files_type_dict['message'] = "Invalid files uploaded. You may upload only one " \
                                     "ESRI shapefile that includes at least three " \
                                     "mandatory files (.shp, .shx, .dfb) or " \
                                     "upload one zipped shapefile."

    return files_type_dict


def parse_shp_zshp(uploadedFileType, baseFilename,
                   uploadedFileCount, uploadedFilenameString, shpFullPath):
    try:
        metadata_array = []
        metadata_dict = {}

        # fileTypeInfo_dict
        originalFileInfo_dict = {}
        originalFileInfo_dict["fileType"] = "SHP" if uploadedFileType == "shp" else "ZSHP"
        originalFileInfo_dict["baseFilename"] = baseFilename
        originalFileInfo_dict["fileCount"] = uploadedFileCount
        originalFileInfo_dict["filenameString"] = uploadedFilenameString
        metadata_array.append({"OriginalFileInfo": originalFileInfo_dict})
        metadata_dict["originalfileinfo"] = originalFileInfo_dict

        # wgs84 extent
        parsed_md_dict = parse_shp(shpFullPath)
        if parsed_md_dict["wgs84_extent_dict"]["westlimit"] != UNKNOWN_STR:
            wgs84_dict = parsed_md_dict["wgs84_extent_dict"]
            # if extent is a point, create point type coverage
            if wgs84_dict["westlimit"] == wgs84_dict["eastlimit"] \
               and wgs84_dict["northlimit"] == wgs84_dict["southlimit"]:
                coverage_dict = {"Coverage": {"type": "point",
                                 "value": {"east": wgs84_dict["eastlimit"],
                                           "north": wgs84_dict["northlimit"],
                                           "units": wgs84_dict["units"],
                                           "projection": wgs84_dict["projection"]}
                                }}
            else:  # otherwise, create box type coverage
                coverage_dict = {"Coverage": {"type": "box",
                                              "value": parsed_md_dict["wgs84_extent_dict"]}}
            metadata_array.append(coverage_dict)
            metadata_dict["coverage"] = coverage_dict

        # original extent
        original_coverage_dict = {}
        original_coverage_dict["originalcoverage"] = {"northlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["northlimit"],
                                                      "southlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["southlimit"],
                                                      "westlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["westlimit"],
                                                      "eastlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["eastlimit"],
                                                      "projection_string":
                                                      parsed_md_dict
                                                      ["origin_projection_string"],
                                                      "projection_name":
                                                      parsed_md_dict["origin_projection_name"],
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
            field_info_dict_item['fieldinformation'] = \
                parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
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
        source_names = kwargs['source_names']

        if __debug__:
            assert(isinstance(source_names, list))

        fed_res_path = kwargs['fed_res_path']
        metadata = kwargs['metadata']
        validate_files_dict = kwargs['validate_files']

        if files and source_names:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Please upload files from ' \
                                             'either local disk or irods, not both.'
            return

        if files or source_names:
            file_info_list = []  # [[full_name1, full_path1], [full_name2, full_path2], ...]
            for f in files:
                f_info = [f.name, f.file.name]
                file_info_list.append(f_info)
            if source_names:
                # copy all irods files to django server to extract metadata
                irods_file_path_list = utils.get_fed_zone_files(source_names)
                fed_tmpfile_name_list = []
                for file_path in irods_file_path_list:
                    fed_tmpfile_name_list.append(file_path)
                    file_full_name = os.path.basename(file_path)
                    f_info = [file_full_name, file_path]
                    file_info_list.append(f_info)

            files_type = check_uploaded_files_type(file_info_list)
            validate_files_dict['are_files_valid'] = files_type['are_files_valid']
            validate_files_dict['message'] = files_type['message']

            if validate_files_dict['are_files_valid']:
                tmp_dir = files_type['tmp_dir']
                baseFilename = files_type['baseFilename']
                uploaded_file_type = files_type['uploaded_file_type']

                if uploaded_file_type == "shp" or uploaded_file_type == "zipped_shp":
                    shp_full_path = files_type['shp_full_path']  # local full-path to file.shp
                    uploadedFileCount = files_type['uploadedFileCount']  # number of files uploaded
                    uploadedFilenameString = files_type['uploadedFilenameString']
                    meta_array, meta_dict = parse_shp_zshp(uploaded_file_type,
                                                           baseFilename,
                                                           uploadedFileCount,
                                                           uploadedFilenameString,
                                                           shp_full_path)
                    metadata.extend(meta_array)
                    metadata.extend(parse_shp_xml(files_type['shp_xml_full_path']))

                    if source_names:
                        # as long as there is a file uploaded from a fed'd
                        # irod zone, the res should be created in that fed'd zone
                        # TODO: If fed_res_path is already set, this will break.
                        fed_res_path.append(utils.get_federated_zone_home_path(source_names[0]))

                    if uploaded_file_type == "zipped_shp":
                        if source_names:
                            # remove the temp zip file retrieved from federated zone
                            if fed_tmpfile_name_list:
                                shutil.rmtree(os.path.dirname(fed_tmpfile_name_list[0]))
                            # zip file from fed'd irods zone should be extracted on django sever
                            # the original zip file should NOT be stored in res
                            # instead, those unzipped files should be stored
                            del source_names[:]

                        del kwargs['files'][:]
                        kwargs['files'].extend(files_type["files_new"])

                elif uploaded_file_type == "kml":
                    pass
        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = "Invalid files uploaded. Please note the " \
                                             "three mandatory files (.shp, .shx, .dbf) " \
                                             "of ESRI Shapefiles should be uploaded at the " \
                                             "same time (or in a zip file)."
    except Exception as ex:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Uploaded files are invalid or corrupt.'
        logger.exception("geofeature_pre_create_resource: {0} ".format(ex.message))
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
        # remove all temp files retrieved from federated zone
        if source_names and fed_tmpfile_name_list:
            for file_path in fed_tmpfile_name_list:
                shutil.rmtree(os.path.dirname(file_path))


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
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(pre_delete_file_from_resource, sender=GeographicFeatureResource)
def geofeature_pre_delete_file_from_resource(sender, **kwargs):

    res_obj = kwargs['resource']
    del_file = kwargs['file']
    all_file_removed = False
    del_res_fname = get_resource_file_name(del_file)

    ori_file_info = res_obj.metadata.originalfileinfo.all().first()
    if ori_file_info.fileType == "SHP" or ori_file_info.fileType == "ZSHP":
        del_f_fullname = del_res_fname[del_res_fname.rfind('/')+1:].lower()
        del_f_name, del_f_ext = os.path.splitext(del_f_fullname)
        if del_f_ext in [".shp", ".shx", ".dbf"]:
            # The shp, shx or dbf files cannot be removed.
            all_file_removed = True

            # remove all files in this res right now except for
            # the file user just clicked to remove (hs_core will remove it later)
            for f in ResourceFile.objects.filter(object_id=res_obj.id):
                fname = get_resource_file_name(f)
                if fname != del_res_fname:
                    delete_resource_file_only(res_obj, f)

        elif del_f_ext == ".prj":
            originalcoverage_obj = res_obj.metadata.originalcoverage.all().first()
            res_obj.metadata.update_element('OriginalCoverage',
                                            element_id=originalcoverage_obj.id,
                                            projection_string=UNKNOWN_STR,
                                            projection_name=UNKNOWN_STR,
                                            datum=UNKNOWN_STR,
                                            unit=UNKNOWN_STR)
            res_obj.metadata.coverages.all().delete()

        if not all_file_removed:
            ori_fn_dict = json.loads(ori_file_info.filenameString)
            if del_f_fullname in ori_fn_dict:
                del ori_fn_dict[del_f_fullname]
                res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,
                                                filenameString=json.dumps(ori_fn_dict))
        else:
            res_obj.metadata.originalfileinfo.all().delete()
            res_obj.metadata.geometryinformation.all().delete()
            res_obj.metadata.fieldinformation.all().delete()
            res_obj.metadata.originalcoverage.all().delete()
            res_obj.metadata.coverages.all().delete()


@receiver(pre_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_pre_add_files_to_resource(sender, **kwargs):

    res_obj = kwargs['resource']
    res_id = res_obj.short_id
    files = kwargs['files']
    source_names = kwargs['source_names']

    if __debug__:
        assert(isinstance(source_names, list))

    validate_files_dict = kwargs['validate_files']
    if files and source_names:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Please upload files from ' \
                                         'either local disk or irods, not both.'
        return

    ori_file_info = res_obj.metadata.originalfileinfo.all().first()
    some_new_files_added = True

    file_info_list = []  # [[full_name1, full_path1], [full_name2, full_path2], ...]
    for f in files:
        f_info = [f.name, f.file.name]
        file_info_list.append(f_info)
    if source_names:
        # TODO: This copy is done *twice*; once in pre-add and once in post-add.
        # copy all irods files to django server to extract metadata
        irods_file_path_list = utils.get_fed_zone_files(source_names)
        fed_tmpfile_name_list = []
        for file_path in irods_file_path_list:
            fed_tmpfile_name_list.append(file_path)
            file_full_name = os.path.basename(file_path)
            f_info = [file_full_name, file_path]
            file_info_list.append(f_info)

    try:
        if ori_file_info and ResourceFile.objects.filter(object_id=res_obj.id).count() > 0:
            # just add non-required files (not shp, shx or dfb)
            crt_f_str = ori_file_info.filenameString
            for f_info in file_info_list:
                new_f_fullname = f_info[0].lower()
                new_f_name, new_f_ext = os.path.splitext(new_f_fullname)

                if new_f_ext in [".shp", ".shx", ".dbf"]:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "No more shp, shx, dbf files can be added."
                    some_new_files_added = False
                    break
                elif (new_f_name != ori_file_info.baseFilename) and \
                        (not (new_f_name == ori_file_info.
                         baseFilename + ".shp" and new_f_ext == ".xml")):
                    # need to check is it ShapefileBaseName.shp.xml
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "At least one file does not " \
                                                     "follow the ESRI Shapefile naming " \
                                                     "convention."
                    some_new_files_added = False
                    break
                elif crt_f_str.find(new_f_fullname) != -1:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = "At least one file already exists."
                    some_new_files_added = False
                    break
            if some_new_files_added:
                ori_fn_dict = json.loads(ori_file_info.filenameString)
                for f_info in file_info_list:
                    new_f_fullname = f_info[0].lower()
                    ori_fn_dict[new_f_fullname] = "new"
                res_obj.metadata.update_element('OriginalFileInfo', element_id=ori_file_info.id,
                                                filenameString=json.dumps(ori_fn_dict))
        else:  # all files have been removed, start it over
            files_type = check_uploaded_files_type(file_info_list)
            tmp_dir = None
            uploaded_file_type = None
            baseFilename = None
            uploadedFileCount = 0
            uploadedFilenameString = None
            shp_full_path = None
            validate_files_dict['are_files_valid'] = files_type['are_files_valid']
            validate_files_dict['message'] = files_type['message']

            if validate_files_dict['are_files_valid']:

                res_obj.metadata.originalfileinfo.all().delete()
                res_obj.metadata.geometryinformation.all().delete()
                res_obj.metadata.fieldinformation.all().delete()
                res_obj.metadata.originalcoverage.all().delete()
                res_obj.metadata.coverages.all().delete()

                tmp_dir = files_type['tmp_dir']
                baseFilename = files_type['baseFilename']
                uploaded_file_type = files_type['uploaded_file_type']
                uploadedFileCount = files_type['uploadedFileCount']
                uploadedFilenameString = files_type['uploadedFilenameString']
                shp_full_path = files_type['shp_full_path']
                shp_xml_full_path = files_type['shp_xml_full_path']
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
                res_obj.metadata.\
                    create_element('OriginalFileInfo',
                                   fileType=originalfileinfo_dict['fileType'],
                                   baseFilename=originalfileinfo_dict['baseFilename'],
                                   fileCount=originalfileinfo_dict['fileCount'],
                                   filenameString=originalfileinfo_dict['filenameString'])

                originalcoverage_dict = meta_dict["originalcoverage"]['originalcoverage']
                res_obj.metadata.\
                    create_element('OriginalCoverage',
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
                    res_obj.metadata.\
                        create_element('FieldInformation',
                                       fieldName=field_info_dict['fieldName'],
                                       fieldType=field_info_dict['fieldType'],
                                       fieldTypeCode=field_info_dict['fieldTypeCode'],
                                       fieldWidth=field_info_dict['fieldWidth'],
                                       fieldPrecision=field_info_dict['fieldPrecision'])

                geometryinformation_dict = meta_dict["geometryinformation"]
                res_obj.metadata.\
                    create_element('GeometryInformation',
                                   featureCount=geometryinformation_dict['featureCount'],
                                   geometryType=geometryinformation_dict['geometryType'])

                shp_xml_metadata_list = parse_shp_xml(shp_xml_full_path)
                for shp_xml_metadata in shp_xml_metadata_list:
                    if 'description' in shp_xml_metadata:
                        # overwrite existing description metadata
                        if res_obj.metadata.description:
                            res_obj.metadata.description.delete()
                        res_obj.metadata.create_element('description',
                                                        abstract=shp_xml_metadata
                                                        ['description']['abstract'])
                    elif 'title' in shp_xml_metadata:
                        # overwrite existing title metadata
                        if res_obj.metadata.title:
                            res_obj.metadata.title.delete()
                        res_obj.metadata.create_element('title',
                                                        value=shp_xml_metadata
                                                        ['title']['value'])
                    elif 'subject' in shp_xml_metadata:
                        # append new keywords to existing keywords
                        existing_keywords = [subject.value for
                                             subject in res_obj.metadata.subjects.all()]
                        if shp_xml_metadata['subject']['value'] not in existing_keywords:
                            res_obj.metadata.create_element('subject',
                                                            value=shp_xml_metadata
                                                            ['subject']['value'])

                if uploaded_file_type == "zipped_shp":
                        if source_names:
                            # remove the temp zip file retrieved from federated zone
                            if fed_tmpfile_name_list:
                                shutil.rmtree(os.path.dirname(fed_tmpfile_name_list[0]))
                            del kwargs['source_names'][:]
                        del kwargs['files'][:]
                        kwargs['files'].extend(files_type["files_new"])

            else:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = "Invalid files uploaded. " \
                                                 "Please note the three mandatory files " \
                                                 "(.shp, .shx, .dbf) of ESRI Shapefiles " \
                                                 "should be uploaded at the same time " \
                                                 "(or in a zip file)."
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir)
            # remove all temp files retrieved from federated zone
            if source_names and fed_tmpfile_name_list:
                for file_path in fed_tmpfile_name_list:
                    shutil.rmtree(os.path.dirname(file_path))
    except Exception as ex:
        logger.exception("geofeature_pre_add_files_to_resource: {0}. Error:{1} ".
                         format(res_id, ex.message))
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = "Invalid files uploaded. " \
                                         "Please note the three mandatory files " \
                                         "(.shp, .shx, .dbf) of ESRI Shapefiles should " \
                                         "be uploaded at the same time (or in a zip file)."


@receiver(post_add_files_to_resource, sender=GeographicFeatureResource)
def geofeature_post_add_files_to_resource_handler(sender, **kwargs):
    tmp_dir = None
    resource = kwargs['resource']
    res_id = resource.short_id
    validate_files_dict = kwargs['validate_files']
    try:
        files = kwargs.get('files', [])  # array of type File
        source_names = kwargs.get('source_names', [])  # array of type str

        if __debug__:
            assert(isinstance(source_names, list))

        found_shp = False
        found_prj = False

        # make a list of all input files: uploaded and/or iRODS
        files_full_name_list = [f.name.lower() for f in files]
        for file_path in source_names:
            file_full_name = os.path.basename(file_path)
            files_full_name_list.append(file_full_name.lower())

        # determine which files are
        for fn in files_full_name_list:
            if fn.endswith(".shp"):
                found_shp = True
            elif fn.endswith(".prj"):
                found_prj = True

        # ALVA: My understanding of this is that the .shp file is parsed before inclusion
        # in the pre_add signal if the file is uploaded, but is not parsed if the file is
        # from a federated user account. In that case, it must be parsed after inclusion.
        # Thus this script looks for that file in federated space only. Is this correct?
        # If it is, then I would propose moving all of this to the pre_add script and doing
        # the download there, for cohesion.
        if found_prj and (not found_shp):
            res_file_list = resource.files.all()
            if res_file_list:
                tmp_dir = tempfile.mkdtemp()
                for res_f in res_file_list:
                    if res_f.resource_file:
                        # file is stored on hs irods but 'source' points to a temporary
                        # (local) location that persists only for this request.
                        source = res_f.resource_file.file.name
                        f_fullname = res_f.resource_file.name
                    elif res_f.fed_resource_file:
                        # file is stored on fed'd user irods
                        source = utils.get_fed_zone_files(res_f.fed_resource_file.storage_path)
                        f_fullname = source
                    # in either case, source now points to a local file.
                    f_fullname = f_fullname[f_fullname.rfind('/')+1:]
                    fileName, fileExtension = os.path.splitext(f_fullname.lower())
                    target = tmp_dir + "/" + fileName + fileExtension
                    shutil.copy(source, target)
                    # for temp file retrieved from federation zone,
                    # it should be deleted after it is copied
                    if res_f.fed_resource_file:
                        shutil.rmtree(source)
                # parse the .shp file from that copy.
                # TODO: why copy the files other than .shp? Are they accessed in parse_shp?
                ori_file_info = resource.metadata.originalfileinfo.all().first()
                shp_full_path = tmp_dir + "/" + ori_file_info.baseFilename + ".shp"

                parsed_md_dict = parse_shp(shp_full_path)
                originalcoverage_obj = resource.metadata.originalcoverage.all().first()
                if originalcoverage_obj:
                    resource.metadata.\
                        update_element('OriginalCoverage',
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
                    resource.metadata.create_element('Coverage',
                                                     type='box',
                                                     value=parsed_md_dict["wgs84_extent_dict"])

    except Exception as ex:
        logger.exception("geofeature_post_add_files_to_resource_handler: "
                         "{0}. Error:{1} ".format(res_id, ex.message))
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = "Invalid files uploaded."
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
