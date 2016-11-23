import os
import subprocess
import shutil
import zipfile
import json
from dateutil import parser
from operator import lt, gt

import xml.etree.ElementTree as ET
import logging

import gdal
from gdalconst import GA_ReadOnly

from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import delete_resource_file_only
from hs_core.views.utils import create_folder, move_or_rename_file_or_folder

import raster_meta_extract
from models import GeoRasterLogicalFile


def set_file_to_geo_raster_file_type(resource, file_id, user):
    """
    Sets a tif or zip raster resource file to GeoRasterFile type
    :param resource: an instance of resource type CompositeResource
    :param file_id: id of the resource file to be set as GeoRasterFile type
    :param user: user who is setting the file type
    :return:
    """
    log = logging.getLogger()

    # get the file from irods
    res_file = utils.get_resource_file_by_id(resource, file_id)

    # base file name (no path included)
    file_name = utils.get_resource_file_name_and_extension(res_file)[1]
    # file name without the extension
    file_name = file_name.split(".")[0]

    metadata = []
    if res_file is not None and res_file.has_generic_logical_file:
        # get the file from irods to temp dir
        temp_file = utils.get_file_from_irods(res_file)
        # validate the file
        error_info, files_to_add_to_resource = raster_file_validation(raster_file=temp_file)
        if not error_info:
            log.info("Geo raster file type file validation successful.")
            # extract metadata
            temp_dir = os.path.dirname(temp_file)
            temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if
                                  '.vrt' == os.path.splitext(f)[1]].pop()
            res_md_dict = raster_meta_extract.get_raster_meta_dict(temp_vrt_file_path)
            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            # add core metadata coverage - box
            if wgs_cov_info:
                box = {'coverage': {'type': 'box', 'value': wgs_cov_info}}
                metadata.append(box)

            # Save extended meta spatial reference
            ori_cov = {'OriginalCoverage': {
                'value': res_md_dict['spatial_coverage_info']['original_coverage_info']}}
            metadata.append(ori_cov)

            # Save extended meta cell info
            res_md_dict['cell_info']['name'] = os.path.basename(temp_vrt_file_path)
            metadata.append({'CellInformation': res_md_dict['cell_info']})

            # Save extended meta band info
            for band_info in res_md_dict['band_info'].values():
                metadata.append({'BandInformation': band_info})

            log.info("Geo raster file type metadata extraction was successful.")
            # first delete the raster file that we retrieved from irods
            logical_file_to_delete = res_file.logical_file
            delete_resource_file_only(resource, res_file)
            if logical_file_to_delete is not None:
                logical_file_to_delete.logical_delete(user)

            # TODO: modify delete_resource_file_only() to delete logical file

            # create a geo raster logical file object to be associated with resource files
            logical_file = GeoRasterLogicalFile.create()
            logical_file.dataset_name = file_name
            logical_file.save()

            try:
                # create a folder for the raster file type using the base file name as the
                # name for the new folder
                new_folder_path = 'data/contents/{}'.format(file_name)
                # To avoid folder creation failure when there is already matching
                # directory path, first check that the folder does not exist
                # If folder path exists then change the folder name by adding a number to the end
                istorage = resource.get_irods_storage()
                counter = 0
                while istorage.exists(os.path.join(resource.short_id, new_folder_path)):
                    new_file_name = file_name + "_{}".format(counter)
                    new_folder_path = 'data/contents/{}'.format(new_file_name)
                    counter += 1

                create_folder(resource.short_id, new_folder_path)
                log.info("Folder created:{}".format(new_folder_path))

                # add all new files to the resource
                resource_files = []
                for f in files_to_add_to_resource:
                    uploaded_file = UploadedFile(file=open(f, 'rb'), name=os.path.basename(f))
                    new_res_file = utils.add_file_to_resource(resource, uploaded_file)
                    # set the logical file for each resource file we added
                    new_res_file.logical_file_content_object = logical_file
                    new_res_file.save()

                    resource_files.append(new_res_file)
                    new_res_file_base_name = utils.get_resource_file_name_and_extension(
                        new_res_file)[1]

                    # rename/move the file to the new folder - keep the original file name
                    src_path = 'data/contents/{}'.format(new_res_file_base_name)
                    tgt_path = os.path.join(new_folder_path, os.path.basename(f))
                    move_or_rename_file_or_folder(user, resource.short_id, src_path, tgt_path,
                                                  validate_move_rename=False)

                log.info("Geo raster file type - new files were added to the resource.")
            except Exception as ex:
                msg = "Geo raster file type. Error when setting file type. Error:{}"
                msg = msg.format(ex.message)
                log.exception(msg)
                raise ex
            finally:
                # remove temp dir
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)

            log.info("Geo raster file type was created.")

            # use the extracted metadata to populate file metadata
            for element in metadata:
                # here k is the name of the element
                # v is a dict of all element attributes/field names and field values
                k, v = element.items()[0]
                logical_file.metadata.create_element(k, **v)
            log.info("Geo raster file type - metadata was saved to DB")
        else:
            err_msg = "Geo raster file type file validation failed.{}".format(' '.join(error_info))
            log.info(err_msg)
            raise ValidationError(err_msg)
    else:
        if res_file is None:
            err_msg = "Failed to set Geo raster file type. " \
                      "Resource doesn't have the specified file."
            log.error(err_msg)
            raise ValidationError(err_msg)
        else:
            err_msg = "Failed to set Geo raster file type." \
                      "The specified file doesn't have a generic logical file type."
            log.error(err_msg)
            raise ValidationError(err_msg)


def raster_file_validation(raster_file):
    """ raster_file is the temp file retrieved from irods and stored on temp dir in django """

    error_info = []
    new_resource_files_to_add = []

    file_name_part, ext = os.path.splitext(os.path.basename(raster_file))
    if ext == '.tif':
        # create the .vrt file
        try:
            temp_vrt_file_path = create_vrt_file(raster_file)
        except Exception as ex:
            error_info.append(ex.message)
        else:
            if os.path.isfile(temp_vrt_file_path):
                new_resource_files_to_add.append(temp_vrt_file_path)
                new_resource_files_to_add.append(raster_file)
    elif ext == '.zip':
        try:
            extract_file_paths = explode_zip_file(raster_file)
        except Exception as ex:
            error_info.append(ex.message)
        else:
            if extract_file_paths:
                for file_path in extract_file_paths:
                    new_resource_files_to_add.append(file_path)
    else:
        error_info.append("Invalid file mime type found.")

    if not error_info:
        files_ext = [os.path.splitext(path)[1] for path in new_resource_files_to_add]

        if set(files_ext) == {'.vrt', '.tif'} and files_ext.count('.vrt') == 1:
            vrt_file_path = new_resource_files_to_add[files_ext.index('.vrt')]
            raster_dataset = gdal.Open(vrt_file_path, GA_ReadOnly)

            # check if the vrt file is valid
            try:
                raster_dataset.RasterXSize
                raster_dataset.RasterYSize
                raster_dataset.RasterCount
            except AttributeError:
                error_info.append('Please define the raster with raster size and band information.')

            # check if the raster file numbers and names are valid in vrt file
            with open(vrt_file_path, 'r') as vrt_file:
                vrt_string = vrt_file.read()
                root = ET.fromstring(vrt_string)
                raster_file_names = [file_name.text for file_name in root.iter('SourceFilename')]

            file_names = [os.path.basename(path) for path in new_resource_files_to_add]
            file_names.pop(files_ext.index('.vrt'))

            if len(file_names) > len(raster_file_names):
                error_info.append('Please remove the extra raster files which are not specified in '
                                  'the .vrt file.')
            else:
                for vrt_ref_raster_name in raster_file_names:
                    if vrt_ref_raster_name in file_names \
                            or (os.path.split(vrt_ref_raster_name)[0] == '.' and
                                os.path.split(vrt_ref_raster_name)[1] in file_names):
                        continue
                    elif os.path.basename(vrt_ref_raster_name) in file_names:
                        msg = "Please specify {} as {} in the .vrt file, because it will " \
                              "be saved in the same folder with .vrt file in HydroShare."
                        msg = msg.format(vrt_ref_raster_name, os.path.basename(vrt_ref_raster_name))
                        error_info.append(msg)
                        break
                    else:
                        msg = "Pleas provide the missing raster file {} which is specified " \
                              "in the .vrt file"
                        msg = msg.format(os.path.basename(vrt_ref_raster_name))
                        error_info.append(msg)
                        break

        elif files_ext.count('.tif') == 1 and files_ext.count('.vrt') == 0:
            msg = "Please define the .tif file with raster size, band, and " \
                  "georeference information."
            error_info.append(msg)
        else:
            msg = "The uploaded files should contain only one .vrt file and .tif files " \
                  "referenced by the .vrt file."
            error_info.append(msg)

    return error_info, new_resource_files_to_add


def create_vrt_file(tif_file):
    """ tif_file exists in temp directory - retrieved from irods """

    log = logging.getLogger()

    # create vrt file
    temp_dir = os.path.dirname(tif_file)
    tif_file_name = os.path.basename(tif_file)
    vrt_file_path = os.path.join(temp_dir, os.path.splitext(tif_file_name)[0] + '.vrt')

    with open(os.devnull, 'w') as fp:
        subprocess.Popen(['gdal_translate', '-of', 'VRT', tif_file, vrt_file_path],
                         stdout=fp,
                         stderr=fp).wait()  # need to wait

    # edit VRT contents
    try:
        tree = ET.parse(vrt_file_path)
        root = tree.getroot()
        for element in root.iter('SourceFilename'):
            element.text = tif_file_name
            element.attrib['relativeToVRT'] = '1'

        tree.write(vrt_file_path)

    except Exception as ex:
        log.exception("Failed to create/write to vrt file. Error:{}".format(ex.message))
        raise Exception("Failed to create/write to vrt file")

    return vrt_file_path


def explode_zip_file(zip_file):
    """ zip_file exists in temp directory - retrieved from irods """

    log = logging.getLogger()
    temp_dir = os.path.dirname(zip_file)
    try:
        zf = zipfile.ZipFile(zip_file, 'r')
        zf.extractall(temp_dir)
        zf.close()

        # get all the file abs names in temp_dir
        extract_file_paths = []
        for dirpath, _, filenames in os.walk(temp_dir):
            for name in filenames:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                if os.path.splitext(os.path.basename(file_path))[1] in ['.vrt', '.tif']:
                    shutil.move(file_path, os.path.join(temp_dir, name))
                    extract_file_paths.append(os.path.join(temp_dir, os.path.basename(file_path)))

    except Exception as ex:
        log.exception("Failed to unzip. Error:{}".format(ex.message))
        raise ex

    return extract_file_paths


def update_resource_coverage_element(resource):
    # TODO: This needs to be unit tested
    # update resource spatial coverage
    spatial_coverages = [lf.metadata.spatial_coverage for lf in resource.logical_files
                         if lf.metadata.spatial_coverage is not None]

    bbox_limits = {'box': {'northlimit': 'northlimit', 'southlimit': 'southlimit',
                           'eastlimit': 'eastlimit', 'westlimit': 'westlimit'},
                   'point': {'northlimit': 'north', 'southlimit': 'north',
                             'eastlimit': 'east', 'westlimit': 'east'}
                   }

    def set_coverage_data(coverage_value, coverage_element, box_limits):
        comparison_operator = {'northlimit': lt, 'southlimit': gt, 'eastlimit': lt,
                               'westlimit': gt}
        for key in comparison_operator.keys():
            if comparison_operator[key](coverage_value[box_limits[key]],
                                        coverage_element.value[box_limits[key]]):
                coverage_value[box_limits[key]] = coverage_element.value[box_limits[key]]

    cov_type = "point"
    bbox_value = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                  'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}
    point_value = {'north': -90, 'east': -180,
                   'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}
    if len(spatial_coverages) > 1:
        cov_type = 'box'
        for sp_cov in spatial_coverages:
            if sp_cov.type == "box":
                box_limits = bbox_limits['box']
                set_coverage_data(bbox_value, sp_cov, box_limits)
            else:
                # point type coverage
                box_limits = bbox_limits['point']
                set_coverage_data(point_value, sp_cov, box_limits)

    elif len(spatial_coverages) == 1:
        sp_cov = spatial_coverages[0]
        if sp_cov.type == "box":
            box_limits = bbox_limits['box']
            cov_type = 'box'
        else:
            # point type coverage
            cov_type = "point"
            box_limits = bbox_limits['point']
            bbox_value = dict()
            bbox_value['projection'] = 'WGS 84 EPSG:4326'
            bbox_value['units'] = 'Decimal degrees'
            bbox_value['north'] = sp_cov.value['north']
            bbox_value['east'] = sp_cov.value['east']

        set_coverage_data(bbox_value, sp_cov, box_limits)

    spatial_cov = resource.metadata.coverages.all().exclude(type='period').first()
    if len(spatial_coverages) > 0:
        if spatial_cov:
            spatial_cov.type = cov_type
            spatial_cov._value = json.dumps(bbox_value)
            spatial_cov.save()
        else:
            resource.metadata.create_element("coverage", type=cov_type, value=bbox_value)
    else:
        # delete spatial coverage element for the resource since the content files don't have any
        # spatial coverage
        if spatial_cov:
            spatial_cov.delete()

    # update resource temporal coverage
    temporal_coverages = [lf.metadata.temporal_coverage for lf in resource.logical_files
                          if lf.metadata.temporal_coverage is not None]

    date_data = {'start': None, 'end': None}

    def set_date_value(date_data, coverage_element, key):
        comparison_operator = gt if key == 'start' else lt
        if date_data[key] is None:
            date_data[key] = coverage_element.value[key]
        else:
            if comparison_operator(parser.parse(date_data[key]),
                                   parser.parse(coverage_element.value[key])):
                date_data[key] = coverage_element.value[key]

    for temp_cov in temporal_coverages:
        set_date_value(date_data, temp_cov, 'start')
        set_date_value(date_data, temp_cov, 'end')

    temp_cov = resource.metadata.coverages.all().filter(type='period').first()
    if date_data['start'] is not None and date_data['end'] is not None:
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            resource.metadata.create_element("coverage", type='period', value=date_data)
    elif temp_cov:
        # delete the temporal coverage for the resource since the content files don't have
        # temporal coverage
        temp_cov.delete()
