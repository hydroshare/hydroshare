import tempfile
import os
import subprocess
import shutil
import zipfile
from collections import OrderedDict
import xml.etree.ElementTree as ET

import gdal
from gdalconst import GA_ReadOnly

from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.hydroshare import utils
from hs_core.models import GenericResource
from hs_geo_raster_resource.models import RasterResource

import raster_meta_extract
from models import GeoRasterLogicalFile, GeoRasterFileMetaData


def raster_extract_metadata(resource, file_name):
    # get the file from irods
    res_file = utils.get_resource_file_by_name(resource, file_name)
    metadata = []
    if res_file is not None and res_file.metadata is not None:
        # get the file from irods to temp dir
        temp_file = utils.get_file_from_irods(res_file)
        temp_file_obj = open(temp_file)
        files = [UploadedFile(file=temp_file_obj, name=file_name)]
        # validate the file
        error_info, vrt_file_path, temp_dir = raster_file_validation(files)
        if not error_info:
            # extract metadata
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
            res_md_dict['cell_info']['name'] = os.path.basename(vrt_file_path)
            metadata.append({'CellInformation': res_md_dict['cell_info']})

            # Save extended meta band info
            for band_info in res_md_dict['band_info'].values():
                metadata.append({'BandInformation': band_info})

        # remove temp vrt file
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)

        if os.path.exists(temp_file):
            shutil.rmtree(os.path.dirname(temp_file))

        if error_info:
            err_msg = 'Raster validation error. {0}'.format(' '.join(error_info))
            raise ValidationError(err_msg)

        # set the logical file for the resource file for which metadata
        # was extracted
        logical_file = GeoRasterLogicalFile.objects.create()
        logical_file.metadata = GeoRasterFileMetaData.objects.create()
        logical_file.save()
        res_file.logical_file_content_object = logical_file
        # use the extracted metadata to populate file metadata
        for element in metadata:
            # here k is the name of the element
            # v is a dict of all element attributes/field names and field values
            k, v = element.items()[0]
            res_file.metadata.create_element(k, **v)


def raster_pre_create_resource_handler(resource_type, **kwargs):
    if resource_type != GenericResource or RasterResource:
        return
    if kwargs['hs_file_type'] != GeoRasterLogicalFile:
        return

    files = kwargs['files']
    title = kwargs['title']
    validate_files_dict = kwargs['validate_files']
    metadata = kwargs['metadata']
    fed_res_fnames = kwargs['fed_res_file_names']
    fed_res_path = kwargs['fed_res_path']
    file_selected = False

    if files:
        file_selected = True
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(files)
    elif fed_res_fnames:
        ref_tmpfiles = utils.get_fed_zone_files(fed_res_fnames)
        fed_tmpfile_name = ref_tmpfiles[0]
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(files, ref_tmp_file_names=ref_tmpfiles)
        ext = os.path.splitext(fed_res_fnames[0])[1]
        if ext == '.zip':
            # clear up the original zip file so that it will not be added into the resource
            fed_res_path.append(utils.get_federated_zone_home_path(fed_res_fnames[0]))
            # remove the temp zip file retrieved from federated zone
            shutil.rmtree(os.path.dirname(fed_tmpfile_name))
            del fed_res_fnames[0]

        file_selected = True

    if file_selected:
        # metadata extraction
        if not error_info:
            temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if '.vrt' == os.path.splitext(f)[1]].pop()
            res_md_dict = raster_meta_extract.get_raster_meta_dict(temp_vrt_file_path)
            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            # add core metadata coverage - box
            if wgs_cov_info:
                box = {'coverage': {'type': 'box', 'value': wgs_cov_info}}
                metadata.append(box)

            # Save extended meta spatial reference
            ori_cov = {'OriginalCoverage': {'value': res_md_dict['spatial_coverage_info']['original_coverage_info'] }}
            metadata.append(ori_cov)

            # Save extended meta cell info
            res_md_dict['cell_info']['name'] = os.path.basename(vrt_file_path)
            metadata.append({'CellInformation': res_md_dict['cell_info']})

            # Save extended meta band info
            for band_info in res_md_dict['band_info'].values():
                metadata.append({'BandInformation': band_info})
        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Raster validation error. {0}'.format(' '.join(error_info))

        # remove temp vrt file
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        # remove temp file retrieved from federated zone for metadata extraction
        if fed_res_fnames and fed_tmpfile_name:
            shutil.rmtree(os.path.dirname(fed_tmpfile_name))
    else:
        # initialize required raster metadata to be place holders to be edited later by users
        cell_info = OrderedDict([
            ('name', title),
            ('rows', None),
            ('columns', None),
            ('cellSizeXValue', None),
            ('cellSizeYValue', None),
            ('cellDataType', None),
        ])
        metadata.append({'CellInformation': cell_info})

        band_info = {
                'name': 'Band_1',
                'variableName': None,
                'variableUnit': None,
                'noDataValue': None,
                'maximumValue': None,
                'minimumValue': None,
        }
        metadata.append({'BandInformation': band_info})

        spatial_coverage_info = OrderedDict([
             ('units', None),
             ('projection', None),
             ('northlimit', None),
             ('southlimit', None),
             ('eastlimit', None),
             ('westlimit', None)
        ])

        # Save extended meta to metadata variable
        ori_cov = {'OriginalCoverage': {'value': spatial_coverage_info}}
        metadata.append(ori_cov)

def raster_file_validation(files, ref_tmp_file_names=[]):
    error_info = []
    vrt_file_path = ''

    # process uploaded .tif or .zip file or file retrieved from iRODS user zone
    in_filename = ''
    if len(files) >= 1:
        in_filename = files[0].name
        file = files[0]
    elif len(ref_tmp_file_names) >= 1:
        in_filename = ref_tmp_file_names[0]
        file = None

    if in_filename:
        ext = os.path.splitext(in_filename)[1]
        if ext == '.tif':
            temp_vrt_file_path, temp_dir = create_vrt_file(in_filename, file)
            if os.path.isfile(temp_vrt_file_path):
                files.append(UploadedFile(file=open(temp_vrt_file_path, 'r'), name=os.path.basename(temp_vrt_file_path)))

        elif ext == '.zip':
            extract_file_paths, temp_dir = explode_zip_file(in_filename, file)
            if extract_file_paths:
                if len(files) == 1:
                    del files[0]
                if len(ref_tmp_file_names) == 1:
                    del ref_tmp_file_names[0]
                for file_path in extract_file_paths:
                    files.append(UploadedFile(file=open(file_path, 'r'), name=os.path.basename(file_path)))

    # check if raster is valid in format and data
    if len(files) >= 1:
        files_names = [f.name for f in files]
        files_path = [f.file.name for f in files]
    if len(ref_tmp_file_names) >= 1:
        for fname in ref_tmp_file_names:
            files_names.append(os.path.split(fname)[1])

    files_ext = [os.path.splitext(path)[1] for path in files_names]

    if set(files_ext) == {'.vrt', '.tif'} and files_ext.count('.vrt') == 1:
        vrt_file_path = files_path[files_ext.index('.vrt')]
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
        files_names.pop(files_ext.index('.vrt'))

        if len(files_names) > len(raster_file_names):
            error_info.append('Please remove the extra raster files which are not specified in the .vrt file.')
        else:
            for vrt_ref_raster_name in raster_file_names:
                if vrt_ref_raster_name in files_names \
                        or (os.path.split(vrt_ref_raster_name)[0] == '.' and
                            os.path.split(vrt_ref_raster_name)[1] in files_names):
                    continue
                elif os.path.basename(vrt_ref_raster_name) in files_names:
                    error_info.append('Please specify {} as {} in the .vrt file, '
                                      'because it will be saved in the same folder with .vrt file in HydroShare'.
                                      format(vrt_ref_raster_name, os.path.basename(vrt_ref_raster_name)))
                    break
                else:
                    error_info.append('Pleas provide the missing raster file {} which is specified in the .vrt file'.
                                      format(os.path.basename(vrt_ref_raster_name)))
                    break

    elif files_ext.count('.tif') == 1 and files_ext.count('.vrt') == 0:
        error_info.append('Please define the .tif file with raster size, band, and georeference information.')
    else:
        error_info.append('The uploaded files should contain only one .vrt file and .tif files referenced by the .vrt file.')

    return error_info, vrt_file_path, temp_dir


def create_vrt_file(tif_file_name, file):
    # create vrt file
    temp_dir = tempfile.mkdtemp()
    tif_base_name = os.path.basename(tif_file_name)
    if file:
        shutil.copy(file.file.name, os.path.join(temp_dir, tif_base_name))
    else:
        shutil.copy(tif_file_name, os.path.join(temp_dir, tif_base_name))
    vrt_file_path = os.path.join(temp_dir, os.path.splitext(tif_base_name)[0]+'.vrt')

    with open(os.devnull, 'w') as fp:
        if file:
            subprocess.Popen(['gdal_translate', '-of', 'VRT', file.file.name, vrt_file_path], stdout=fp,
                             stderr=fp).wait()  # remember to add .wait()
        else:
            subprocess.Popen(['gdal_translate', '-of', 'VRT', tif_file_name, vrt_file_path], stdout=fp,
                             stderr=fp).wait()  # remember to add .wait()

    # edit VRT contents
    try:
        tree = ET.parse(vrt_file_path)
        root = tree.getroot()
        for element in root.iter('SourceFilename'):
            element.text = tif_base_name
            element.attrib['relativeToVRT'] = '1'

        tree.write(vrt_file_path)

    except Exception:
        shutil.rmtree(temp_dir)

    return vrt_file_path, temp_dir


def explode_zip_file(zip_file_name, file):
    temp_dir = tempfile.mkdtemp()
    try:
        if file:
            zf = zipfile.ZipFile(file.file.name, 'r')
        else:
            zf = zipfile.ZipFile(zip_file_name, 'r')
        zf.extractall(temp_dir)
        zf.close()

        # get all the file abs names in temp_dir
        extract_file_paths = []
        for dirpath,_,filenames in os.walk(temp_dir):
            for name in filenames:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                if os.path.splitext(os.path.basename(file_path))[1] in ['.vrt', '.tif']:
                    shutil.move(file_path, os.path.join(temp_dir,name))
                    extract_file_paths.append(os.path.join(temp_dir, os.path.basename(file_path)))

    except Exception:
        extract_file_paths = []
        shutil.rmtree(temp_dir)

    return extract_file_paths, temp_dir