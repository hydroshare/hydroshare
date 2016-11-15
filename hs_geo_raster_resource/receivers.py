# Note: this module has been imported in the models.py in order to receive signals
# at the end of the models.py for the import of this module

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
from django.dispatch import receiver

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import ResourceFile, \
    get_resource_file_name, delete_resource_file_only
from hs_core.signals import pre_create_resource, pre_add_files_to_resource, \
    pre_delete_file_from_resource, pre_metadata_element_create, pre_metadata_element_update
from forms import CellInfoValidationForm, BandInfoValidationForm, OriginalCoverageSpatialForm
from models import RasterResource
import raster_meta_extract


# signal handler to extract metadata from uploaded geotiff file and return template contexts
# to populate create-resource.html template page

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
                files.append(UploadedFile(file=open(temp_vrt_file_path, 'r'),
                                          name=os.path.basename(temp_vrt_file_path)))

        elif ext == '.zip':
            extract_file_paths, temp_dir = explode_zip_file(in_filename, file)
            if extract_file_paths:
                if len(files) == 1:
                    del files[0]
                if len(ref_tmp_file_names) == 1:
                    del ref_tmp_file_names[0]
                for file_path in extract_file_paths:
                    files.append(UploadedFile(file=open(file_path, 'r'),
                                              name=os.path.basename(file_path)))

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
            error_info.append('Please remove the extra raster files which '
                              'are not specified in the .vrt file.')
        else:
            for vrt_ref_raster_name in raster_file_names:
                if vrt_ref_raster_name in files_names \
                        or (os.path.split(vrt_ref_raster_name)[0] == '.' and
                            os.path.split(vrt_ref_raster_name)[1] in files_names):
                    continue
                elif os.path.basename(vrt_ref_raster_name) in files_names:
                    error_info.append('Please specify {} as {} in the .vrt file, '
                                      'because it will be saved in the same '
                                      'folder with .vrt file in HydroShare'.
                                      format(vrt_ref_raster_name,
                                             os.path.basename(vrt_ref_raster_name)))
                    break
                else:
                    error_info.append('Pleas provide the missing raster file {} '
                                      'which is specified in the .vrt file'.
                                      format(os.path.basename(vrt_ref_raster_name)))
                    break

    elif files_ext.count('.tif') == 1 and files_ext.count('.vrt') == 0:
        error_info.append('Please define the .tif file with raster size, '
                          'band, and georeference information.')
    else:
        error_info.append('The uploaded files should contain only one .vrt file and .tif files '
                          'referenced by the .vrt file.')

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
            subprocess.Popen(['gdal_translate', '-of', 'VRT', file.file.name, vrt_file_path],
                             stdout=fp, stderr=fp).wait()  # remember to add .wait()
        else:
            subprocess.Popen(['gdal_translate', '-of', 'VRT', tif_file_name, vrt_file_path],
                             stdout=fp, stderr=fp).wait()  # remember to add .wait()

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
        for dirpath, _, filenames in os.walk(temp_dir):
            for name in filenames:
                file_path = os.path.abspath(os.path.join(dirpath, name))
                if os.path.splitext(os.path.basename(file_path))[1] in ['.vrt', '.tif']:
                    shutil.move(file_path, os.path.join(temp_dir,name))
                    extract_file_paths.append(os.path.join(temp_dir, os.path.basename(file_path)))

    except Exception:
        extract_file_paths = []
        shutil.rmtree(temp_dir)

    return extract_file_paths, temp_dir


@receiver(pre_create_resource, sender=RasterResource)
def raster_pre_create_resource_trigger(sender, **kwargs):
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
        error_info, vrt_file_path, temp_dir = raster_file_validation(
            files,  ref_tmp_file_names=ref_tmpfiles)
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
            temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
                                  if '.vrt' == os.path.splitext(f)[1]].pop()
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
        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Raster validation error. {0}'.\
                format(' '.join(error_info))

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
             ('westlimit', None),
             ('projection_string', None),
             ('datum', None),
        ])

        # Save extended meta to metadata variable
        ori_cov = {'OriginalCoverage': {'value': spatial_coverage_info}}
        metadata.append(ori_cov)


@receiver(pre_add_files_to_resource, sender=RasterResource)
def raster_pre_add_files_to_resource_trigger(sender, **kwargs):
    files = kwargs['files']
    res = kwargs['resource']
    fed_res_fnames = kwargs['fed_res_file_names']
    validate_files_dict = kwargs['validate_files']
    file_selected = False

    if files:
        file_selected = True
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(files)
    elif fed_res_fnames:
        ref_tmpfiles = utils.get_fed_zone_files(fed_res_fnames)
        fed_tmpfile_name = ref_tmpfiles[0]
        # raster file validation
        error_info, vrt_file_path, temp_dir = raster_file_validation(
            files, ref_tmp_file_names=ref_tmpfiles)
        ext = os.path.splitext(fed_res_fnames[0])[1]
        if ext == '.zip':
            # remove the temp zip file retrieved from federated zone
            shutil.rmtree(os.path.dirname(fed_tmpfile_name))
            # clear up the original zip file so that it will not be added into the resource
            del fed_res_fnames[0]
        file_selected = True

    if file_selected:
        # metadata extraction
        if not error_info:
            temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
                                  if '.vrt' == os.path.splitext(f)[1]].pop()
            res_md_dict = raster_meta_extract.get_raster_meta_dict(temp_vrt_file_path)

            # update core metadata coverage - box
            wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
            if wgs_cov_info:
                res.metadata.create_element(
                    'Coverage', type='box',
                    value=res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
                )

            # update extended original box coverage
            if res.metadata.originalCoverage:
                res.metadata.originalCoverage.delete()
            v = {'value': res_md_dict['spatial_coverage_info']['original_coverage_info']}
            res.metadata.create_element('OriginalCoverage', **v)

            # update extended metadata CellInformation
            res.metadata.cellInformation.delete()
            res.metadata.create_element('CellInformation', name=os.path.basename(vrt_file_path),
                                        rows=res_md_dict['cell_info']['rows'],
                                        columns=res_md_dict['cell_info']['columns'],
                                        cellSizeXValue=res_md_dict['cell_info']['cellSizeXValue'],
                                        cellSizeYValue=res_md_dict['cell_info']['cellSizeYValue'],
                                        cellDataType=res_md_dict['cell_info']['cellDataType'],
                                        )

            # update extended metadata BandInformation
            for band in res.metadata.bandInformation:
                band.delete()

            band_info = res_md_dict['band_info']
            for band in band_info.values():
                res.metadata.create_element('BandInformation', name=band['name'], variableName='',
                                            variableUnit=band['variableUnit'], method='',
                                            comment='', noDataValue=band['noDataValue'],
                                            maximumValue=band['maximumValue'],
                                            minimumValue=band['minimumValue']
                                            )

        else:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Raster validation error. {0}' \
                                             'See http://www.gdal.org/gdal_vrttut.html ' \
                                             'for information on the .vrt format.'.\
                                             format(' '.join(error_info))

        # remove temp dir
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        # remove the temp file retrieved from federated zone for metadata extraction
        if fed_res_fnames and fed_tmpfile_name:
            shutil.rmtree(os.path.dirname(fed_tmpfile_name))


@receiver(pre_delete_file_from_resource, sender=RasterResource)
def raster_pre_delete_file_from_resource_trigger(sender, **kwargs):
    res = kwargs['resource']
    del_file = kwargs['file']
    del_res_fname = get_resource_file_name(del_file)
    # delete core metadata coverage now that the only file is deleted
    res.metadata.coverages.all().delete()

    # delete extended OriginalCoverage now that the only file is deleted
    res.metadata.originalCoverage.delete()

    # reset extended metadata CellInformation now that the only file is deleted
    res.metadata.cellInformation.delete()
    res.metadata.create_element('CellInformation', name=res.metadata.title.value,
                                rows=None, columns=None,
                                cellSizeXValue=None, cellSizeYValue=None,
                                cellDataType=None
                                )

    # reset extended metadata BandInformation now that the only file is deleted
    for band in res.metadata.bandInformation:
        band.delete()
    res.metadata.create_element('BandInformation', name='Band_1', variableName='', variableUnit='',
                                method='', comment='', noDataValue=None,
                                maximumValue=None, minimumValue=None)

    # delete all the files that is not the user selected file
    for f in ResourceFile.objects.filter(object_id=res.id):
        fname = get_resource_file_name(f)
        if fname != del_res_fname:
            delete_resource_file_only(res, f)

    # delete the format of the files that is not the user selected delete file
    del_file_format = utils.get_file_mime_type(del_res_fname)
    for format_element in res.metadata.formats.all():
        if format_element.value != del_file_format:
            res.metadata.delete_element(format_element.term, format_element.id)


@receiver(pre_metadata_element_create, sender=RasterResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        element_form = BandInfoValidationForm(request.POST)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(pre_metadata_element_update, sender=RasterResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        form_data = {}
        for field_name in BandInfoValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]
        element_form = BandInfoValidationForm(form_data)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}
"""
Since each of the Raster metadata element is required no need to listen to any delete signal
The Raster landing page should not have delete UI functionality for the resource
specific metadata elements
"""
