import os
import logging
import shutil
import subprocess
import zipfile

import xml.etree.ElementTree as ET
import gdal
from gdalconst import GA_ReadOnly

from functools import partial, wraps

from django.db import models, transaction
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.forms.models import formset_factory
from django.template import Template, Context

from dominate.tags import div, legend, form, button

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import delete_resource_file
from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm

from hs_geo_raster_resource.models import CellInformation, BandInformation, OriginalCoverage, \
    GeoRasterMetaDataMixin
from hs_geo_raster_resource.forms import BandInfoForm, BaseBandInfoFormSet, BandInfoValidationForm

from hs_file_types import raster_meta_extract
from base import AbstractFileMetaData, AbstractLogicalFile


class GeoRasterFileMetaData(GeoRasterMetaDataMixin, AbstractFileMetaData):
    # the metadata element models used for this file type are from the raster resource type app
    # use the 'model_app_label' attribute with ContentType, do dynamically find the right element
    # model class from element name (string)
    model_app_label = 'hs_geo_raster_resource'

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(GeoRasterFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverage'] = OriginalCoverage
        metadata_model_classes['bandinformation'] = BandInformation
        metadata_model_classes['cellinformation'] = CellInformation
        return metadata_model_classes

    def get_metadata_elements(self):
        elements = super(GeoRasterFileMetaData, self).get_metadata_elements()
        elements += [self.cellInformation, self.originalCoverage]
        elements += list(self.bandInformations.all())
        return elements

    def get_html(self):
        """overrides the base class function to generate html needed to display metadata
        in view mode"""

        html_string = super(GeoRasterFileMetaData, self).get_html()
        if self.spatial_coverage:
            html_string += self.spatial_coverage.get_html()
        if self.originalCoverage:
            html_string += self.originalCoverage.get_html()

        html_string += self.cellInformation.get_html()
        if self.temporal_coverage:
            html_string += self.temporal_coverage.get_html()
        band_legend = legend("Band Information", cls="pull-left", style="margin-left:10px;")
        html_string += band_legend.render()
        for band_info in self.bandInformations:
            html_string += band_info.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True):
        """overrides the base class function to generate html needed for metadata editing"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(GeoRasterFileMetaData, self).get_html_forms()
            with div(cls="col-lg-6 col-xs-12", id="spatial-coverage-filetype"):
                with form(id="id-spatial-coverage-file-type",
                          action="{{ coverage_form.action }}",
                          method="post", enctype="multipart/form-data"):
                    div("{% crispy coverage_form %}")
                    with div(cls="row", style="margin-top:10px;"):
                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                     "col-md-2 col-xs-6"):
                            button("Save changes", type="button",
                                   cls="btn btn-primary pull-right",
                                   style="display: none;")

            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy orig_coverage_form %}")
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy cellinfo_form %}")

            with div(cls="pull-left col-sm-12"):
                with div(cls="well", id="variables"):
                    with div(cls="row"):
                        div("{% for form in bandinfo_formset_forms %}")
                        with div(cls="col-sm-6 col-xs-12"):
                            with form(id="{{ form.form_id }}", action="{{ form.action }}",
                                      method="post", enctype="multipart/form-data"):
                                div("{% crispy form %}")
                                with div(cls="row", style="margin-top:10px;"):
                                    with div(cls="col-md-offset-10 col-xs-offset-6 "
                                                 "col-md-2 col-xs-6"):
                                        button("Save changes", type="button",
                                               cls="btn btn-primary pull-right",
                                               style="display: none;",
                                               onclick="metadata_update_ajax_submit({{ "
                                                       "form.form_id_button }}); return false;")
                        div("{% endfor %}")

        template = Template(root_div.render())
        context_dict = dict()

        context_dict["orig_coverage_form"] = self.get_original_coverage_form()
        context_dict["cellinfo_form"] = self.get_cellinfo_form()
        temp_cov_form = self.get_temporal_coverage_form()

        update_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/GeoRasterLogicalFile/{0}/{1}/add-file-metadata/"
        spatial_cov_form = self.get_spatial_coverage_form(allow_edit=True)
        if self.spatial_coverage:
            form_action = update_action.format(self.logical_file.id, "coverage",
                                               self.spatial_coverage.id)
        else:
            form_action = create_action.format(self.logical_file.id, "coverage")

        spatial_cov_form.action = form_action

        if self.temporal_coverage:
            form_action = update_action.format(self.logical_file.id, "coverage",
                                               self.temporal_coverage.id)
            temp_cov_form.action = form_action
        else:
            form_action = create_action.format(self.logical_file.id, "coverage")
            temp_cov_form.action = form_action

        context_dict["coverage_form"] = spatial_cov_form
        context_dict["temp_form"] = temp_cov_form
        context_dict["bandinfo_formset_forms"] = self.get_bandinfo_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_cellinfo_form(self):
        return self.cellInformation.get_html_form(resource=None)

    def get_original_coverage_form(self):
        return OriginalCoverage.get_html_form(resource=None, element=self.originalCoverage,
                                              file_type=True, allow_edit=False)

    def get_bandinfo_formset(self):
        BandInfoFormSetEdit = formset_factory(
            wraps(BandInfoForm)(partial(BandInfoForm, allow_edit=True)),
            formset=BaseBandInfoFormSet, extra=0)
        bandinfo_formset = BandInfoFormSetEdit(
            initial=self.bandInformations.values(), prefix='BandInformation')

        for frm in bandinfo_formset.forms:
            if len(frm.initial) > 0:
                frm.action = "/hsapi/_internal/%s/%s/bandinformation/%s/update-file-metadata/" % (
                    "GeoRasterLogicalFile", self.logical_file.id, frm.initial['id'])
                frm.number = frm.initial['id']

        return bandinfo_formset

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Geo Raster file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == 'bandinformation':
            form_data = {}
            for field_name in BandInfoValidationForm().fields:
                matching_key = [key for key in request.POST if '-' + field_name in key][0]
                form_data[field_name] = request.POST[matching_key]
            element_form = BandInfoValidationForm(form_data)
        elif element_name == 'coverage' and 'start' not in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            # element_name must be coverage
            # here we are assuming temporal coverage
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of all metadata elements associated with this
        logical file type instance"""

        container_to_add_to = super(GeoRasterFileMetaData, self).add_to_xml_container(container)
        if self.originalCoverage:
            self.originalCoverage.add_to_xml_container(container_to_add_to)
        if self.cellInformation:
            self.cellInformation.add_to_xml_container(container_to_add_to)
        for bandinfo in self.bandInformations:
            bandinfo.add_to_xml_container(container_to_add_to)


class GeoRasterLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoRasterFileMetaData, related_name="logical_file")
    data_type = "geoRasterData"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .zip and .tif file can be set to this logical file group"""
        return [".zip", ".tif"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .tif and .vrt"""
        return [".tif", ".vrt"]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        raster_metadata = GeoRasterFileMetaData.objects.create()
        return cls.objects.create(metadata=raster_metadata)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_add(self):
        """doesn't allow a resource file to be added"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False

    @classmethod
    def set_file_type(cls, resource, file_id, user):
        """
            Sets a tif or zip raster resource file to GeoRasterFile type
            :param resource: an instance of resource type CompositeResource
            :param file_id: id of the resource file to be set as GeoRasterFile type
            :param user: user who is setting the file type
            :return:
            """

        # had to import it here to avoid import loop
        from hs_core.views.utils import create_folder

        log = logging.getLogger()

        # get the file from irods
        res_file = utils.get_resource_file_by_id(resource, file_id)

        # base file name (no path included)
        file_name = utils.get_resource_file_name_and_extension(res_file)[1]
        # file name without the extension
        file_name = file_name.split(".")[0]
        file_folder = res_file.file_folder

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
                metadata = extract_metadata(temp_vrt_file_path)
                log.info("Geo raster file type metadata extraction was successful.")
                with transaction.atomic():
                    # first delete the raster file that we retrieved from irods
                    # for setting it to raster file type
                    delete_resource_file(resource.short_id, res_file.id, user)
                    # create a geo raster logical file object to be associated with resource files
                    logical_file = cls.create()
                    # by default set the dataset_name attribute of the logical file to the
                    # name of the file selected to set file type
                    logical_file.dataset_name = file_name
                    logical_file.save()

                    try:
                        # create a folder for the raster file type using the base file name as the
                        # name for the new folder
                        new_folder_path = cls.compute_file_type_folder(resource, file_folder,
                                                                       file_name)

                        # Alva: This does nothing.
                        # fed_file_full_path = ''
                        # if resource.resource_federation_path:
                        #     fed_file_full_path = os.path.join(resource.root_path, new_folder_path)

                        log.info("Folder created:{}".format(new_folder_path))
                        create_folder(resource.short_id, new_folder_path)

                        new_folder_name = new_folder_path.split('/')[-1]
                        if file_folder is None:
                            upload_folder = new_folder_name
                        else:
                            upload_folder = os.path.join(file_folder, new_folder_name)

                        # add all new files to the resource
                        for f in files_to_add_to_resource:
                            uploaded_file = UploadedFile(file=open(f, 'rb'),
                                                         name=os.path.basename(f))
                            new_res_file = utils.add_file_to_resource(
                                resource, uploaded_file, folder=upload_folder)

                            # make each resource file we added as part of the logical file
                            logical_file.add_resource_file(new_res_file)

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
                    # set resource to private if logical file is missing required metadata
                    if not logical_file.metadata.has_all_required_elements():
                        resource.raccess.public = False
                        resource.raccess.discoverable = False
                        resource.raccess.save()
            else:
                err_msg = "Geo raster file type file validation failed.{}".format(
                    ' '.join(error_info))
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
            extract_file_paths = _explode_raster_zip_file(raster_file)
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


def extract_metadata(temp_vrt_file_path):
    metadata = []
    res_md_dict = raster_meta_extract.get_raster_meta_dict(temp_vrt_file_path)
    wgs_cov_info = res_md_dict['spatial_coverage_info']['wgs84_coverage_info']
    # add core metadata coverage - box
    if wgs_cov_info:
        box = {'coverage': {'type': 'box', 'value': wgs_cov_info}}
        metadata.append(box)

    # Save extended meta spatial reference
    orig_cov_info = res_md_dict['spatial_coverage_info']['original_coverage_info']

    # Here the assumption is that if there is no value for the 'northlimit' then there is no value
    # for the bounding box
    if orig_cov_info['northlimit'] is not None:
        ori_cov = {'OriginalCoverage': {'value': orig_cov_info}}
        metadata.append(ori_cov)

    # Save extended meta cell info
    res_md_dict['cell_info']['name'] = os.path.basename(temp_vrt_file_path)
    metadata.append({'CellInformation': res_md_dict['cell_info']})

    # Save extended meta band info
    for band_info in res_md_dict['band_info'].values():
        metadata.append({'BandInformation': band_info})
    return metadata


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


def _explode_raster_zip_file(zip_file):
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
                if os.path.splitext(os.path.basename(file_path))[1] in \
                        GeoRasterLogicalFile.get_allowed_storage_file_types():
                    shutil.move(file_path, os.path.join(temp_dir, name))
                    extract_file_paths.append(os.path.join(temp_dir, os.path.basename(file_path)))

    except Exception as ex:
        log.exception("Failed to unzip. Error:{}".format(ex.message))
        raise ex

    return extract_file_paths
