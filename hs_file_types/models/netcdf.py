import os
import shutil
import logging

from functools import partial, wraps
import netCDF4

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.template import Template, Context
from django.forms.models import formset_factory, BaseFormSet

from dominate.tags import div, legend, form, button, p, textarea

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import delete_resource_file
from hs_core.models import Coverage
from hs_core.forms import CoverageTemporalForm

from hs_app_netCDF.models import NetCDFMetaDataMixin, OriginalCoverage, Variable
from hs_app_netCDF.forms import VariableForm, VariableValidationForm, OriginalCoverageForm

from base import AbstractFileMetaData, AbstractLogicalFile
import hs_file_types.nc_functions.nc_utils as nc_utils
import hs_file_types.nc_functions.nc_dump as nc_dump
import hs_file_types.nc_functions.nc_meta as nc_meta


class NetCDFFileMetaData(NetCDFMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the netcdf resource type app
    model_app_label = 'hs_app_netCDF'

    def get_metadata_elements(self):
        elements = super(NetCDFFileMetaData, self).get_metadata_elements()
        elements += [self.ori_coverage]
        elements += list(self.variables.all())
        return elements

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(NetCDFFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverage'] = OriginalCoverage
        metadata_model_classes['variable'] = Variable
        return metadata_model_classes

    @property
    def original_coverage(self):
        return self.ori_coverage.all().first()

    def get_html(self):
        """overrides the base class function"""

        html_string = super(NetCDFFileMetaData, self).get_html()
        html_string += self.spatial_coverage.get_html()
        html_string += self.originalCoverage.get_html()
        if self.temporal_coverage:
            html_string += self.temporal_coverage.get_html()
        variable_legend = legend("Variables", cls="pull-left", style="margin-top:20px;")
        html_string += variable_legend.render()
        for variable in self.variables.all():
            html_string += variable.get_html()

        # ncdump text from the txt file
        html_string += self.get_ncdump_html().render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, datatset_name_form=True):
        """overrides the base class function"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(NetCDFFileMetaData, self).get_html_forms()
            with div(cls="well", id="temporal-coverage"):
                with div(cls="col-lg-12 col-xs-12"):
                    with form(id="id-coverage_temporal-file-type", action="{{ temp_form.action }}",
                              method="post", enctype="multipart/form-data"):
                        div("{% crispy temp_form %}")
                        with div(cls="row", style="margin-top:10px;"):
                            with div(cls="col-md-offset-10 col-xs-offset-6 "
                                         "col-md-2 col-xs-6"):
                                button("Save changes", type="button",
                                       cls="btn btn-primary pull-right",
                                       style="display: none;",
                                       onclick="metadata_update_ajax_submit("
                                               "'id-coverage_temporal-file-type'); return false;")
            with div(cls="col-lg-6 col-xs-12"):
                with form(id="id-origcoverage-file-type",
                          action="{{ orig_coverage_form.action }}",
                          method="post", enctype="multipart/form-data"):
                    div("{% crispy orig_coverage_form %}")
                    with div(cls="row", style="margin-top:10px;"):
                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                     "col-md-2 col-xs-6"):
                            button("Save changes", type="button",
                                   cls="btn btn-primary pull-right",
                                   style="display: none;",
                                   onclick="metadata_update_ajax_submit("
                                           "'id-origcoverage-file-type'); return false;")

            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy spatial_coverage_form %}")

            with div(cls="pull-left col-sm-12"):
                with div(cls="well", id="variables"):
                    with div(cls="row"):
                        div("{% for form in variable_formset_forms %}")
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

            self.get_ncdump_html()

        template = Template(root_div.render())
        temp_cov_form = self.get_temporal_coverage_form()
        update_action = "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/add-file-metadata/"
        if self.temporal_coverage:
            temp_action = update_action.format(self.logical_file.id, "coverage",
                                               self.temporal_coverage.id)
        else:
            temp_action = create_action.format(self.logical_file.id, "coverage")

        temp_cov_form.action = temp_action

        orig_cov_form = self.originalCoverage.get_html_form(resource=None)
        update_action = "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/NetCDFLogicalFile/{0}/{1}/add-file-metadata/"
        if self.originalCoverage:
            temp_action = update_action.format(self.logical_file.id, "originalcoverage",
                                               self.originalCoverage.id)
        else:
            temp_action = create_action.format(self.logical_file.id, "originalcoverage")

        orig_cov_form.action = temp_action

        # TODO: No editing allowed for spatial coverage - check with Tian if editing should be
        # allowed
        spatial_cov_form = self.get_spatial_coverage_form()

        context_dict = dict()
        context_dict["temp_form"] = temp_cov_form
        context_dict["orig_coverage_form"] = orig_cov_form
        context_dict["spatial_coverage_form"] = spatial_cov_form
        context_dict["variable_formset_forms"] = self.get_variable_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)
        rendered_html = self.update_coverage_forms_ids(rendered_html)
        return rendered_html

    def get_spatial_coverage_form(self):
        return Coverage.get_spatial_html_form(resource=None, element=self.spatial_coverage,
                                              allow_edit=False)

    def get_temporal_coverage_form(self):
        return Coverage.get_temporal_html_form(resource=None, element=self.temporal_coverage)

    def get_variable_formset(self):
        VariableFormSetEdit = formset_factory(
            wraps(VariableForm)(partial(VariableForm, allow_edit=True)),
            formset=BaseFormSet, extra=0)
        variable_formset = VariableFormSetEdit(
            initial=self.variables.all().values(), prefix='Variable')

        for frm in variable_formset.forms:
            if len(frm.initial) > 0:
                frm.action = "/hsapi/_internal/%s/%s/variable/%s/update-file-metadata/" % (
                    "NetCDFLogicalFile", self.logical_file.id, frm.initial['id'])
                frm.number = frm.initial['id']

        return variable_formset

    def get_ncdump_html(self):
        # ncdump text from the txt file
        # the generated html used both in view and edit mode
        nc_dum_div = div()
        nc_dump_res_file = None
        for f in self.logical_file.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        if nc_dump_res_file is not None:
            nc_dum_div = div(style="clear: both", cls="col-xs-12")
            with nc_dum_div:
                legend("NetCDF Header Information")
                p(nc_dump_res_file.full_path[33:])
                textarea(nc_dump_res_file.resource_file.read(), readonly="", rows="15",
                         cls="input-xlarge", style="min-width: 100%")

        return nc_dum_div

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for NetCDF file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == 'variable':
            form_data = {}
            for field_name in VariableValidationForm().fields:
                matching_key = [key for key in request.POST if '-' + field_name in key][0]
                form_data[field_name] = request.POST[matching_key]
            element_form = VariableValidationForm(form_data)
        elif element_name == 'originalcoverage':
            element_form = OriginalCoverageForm(data=request.POST)

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

        container_to_add_to = super(NetCDFFileMetaData, self).add_to_xml_container(container)
        if self.originalCoverage:
            self.originalCoverage.add_to_xml_container(container_to_add_to)

        # TODO: check with Tian if we have to add the spatial coverage

        for variable in self.variables.all():
            variable.add_to_xml_container(container_to_add_to)


class NetCDFLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(NetCDFFileMetaData, related_name="logical_file")
    data_type = "NetCDF data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .nc file can be set to this logical file group"""
        return [".nc"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .nc and .txt"""
        return [".nc", ".txt"]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        netcdf_metadata = NetCDFFileMetaData.objects.create()
        return cls.objects.create(metadata=netcdf_metadata)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
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

        if res_file is None:
            raise ValidationError("File not found.")

        if res_file.extension != '.nc':
            raise ValidationError("Not a NetCDF file.")

        # base file name (no path included)
        file_name = res_file.file_name
        # file name without the extension
        nc_file_name = file_name.split(".")[0]

        resource_metadata = []
        file_type_metadata = []
        files_to_add_to_resource = []
        if res_file.has_generic_logical_file:
            # get the file from irods to temp dir
            temp_file = utils.get_file_from_irods(res_file)
            temp_dir = os.path.dirname(temp_file)
            files_to_add_to_resource.append(temp_file)
            # file validation and metadata extraction
            nc_dataset = nc_utils.get_nc_dataset(temp_file)
            if isinstance(nc_dataset, netCDF4.Dataset):
                # Extract the metadata from netcdf file
                try:
                    res_md_dict = nc_meta.get_nc_meta_dict(temp_file)
                    res_dublin_core_meta = res_md_dict['dublin_core_meta']
                    res_type_specific_meta = res_md_dict['type_specific_meta']
                except:
                    res_dublin_core_meta = {}
                    res_type_specific_meta = {}

                # add creator:
                if res_dublin_core_meta.get('creator_name'):
                    name = res_dublin_core_meta['creator_name']
                    email = res_dublin_core_meta.get('creator_email', '')
                    url = res_dublin_core_meta.get('creator_url', '')
                    creator = {'creator': {'name': name, 'email': email, 'homepage': url}}
                    resource_metadata.append(creator)

                # add contributor:
                if res_dublin_core_meta.get('contributor_name'):
                    name_list = res_dublin_core_meta['contributor_name'].split(',')
                    for name in name_list:
                        contributor = {'contributor': {'name': name}}
                        resource_metadata.append(contributor)

                # add title
                if resource.metadata.title.value.lower() == 'untitled resource':
                    if res_dublin_core_meta.get('title'):
                        res_title = {'title': {'value': res_dublin_core_meta['title']}}
                        resource_metadata.append(res_title)

                # add description
                if resource.metadata.description is None:
                    if res_dublin_core_meta.get('description'):
                        description = {'description': {'abstract':
                                                       res_dublin_core_meta['description']}}
                        resource_metadata.append(description)

                # add keywords
                if res_dublin_core_meta.get('subject'):
                    keywords = res_dublin_core_meta['subject'].split(',')
                    file_type_metadata.append({'subject': keywords})

                # add source element - we can't add this resource level metadata as there can be
                # multiple netcdf files in composite resource

                # add relation element - we can't add this resource level metadata as there can be
                # multiple netcdf files in composite resource

                # add coverage - period
                if res_dublin_core_meta.get('period'):
                    period = {
                        'coverage': {'type': 'period', 'value': res_dublin_core_meta['period']}}
                    file_type_metadata.append(period)

                # add coverage - box
                if res_dublin_core_meta.get('box'):
                    box = {'coverage': {'type': 'box', 'value': res_dublin_core_meta['box']}}
                    file_type_metadata.append(box)

                # add rights
                # After discussion with dtarb decided not to override the resource level
                # rights metadata with netcdf extracted rights metadata

                # Save extended meta to metadata variable
                for var_name, var_meta in res_type_specific_meta.items():
                    meta_info = {}
                    for element, value in var_meta.items():
                        if value != '':
                            meta_info[element] = value
                    file_type_metadata.append({'variable': meta_info})

                # Save extended meta to original spatial coverage
                if res_dublin_core_meta.get('original-box'):
                    coverage_data = res_dublin_core_meta['original-box']
                    projection_string_type = ""
                    projection_string_text = ""
                    datum = ""
                    if res_dublin_core_meta.get('projection-info'):
                        projection_string_type = res_dublin_core_meta[
                            'projection-info']['type']
                        projection_string_text = res_dublin_core_meta[
                            'projection-info']['text']
                        datum = res_dublin_core_meta['projection-info']['datum']

                    ori_cov = {'originalcoverage':
                               {'value': coverage_data,
                                'projection_string_type': projection_string_type,
                                'projection_string_text': projection_string_text,
                                'datum': datum
                                }
                               }
                    file_type_metadata.append(ori_cov)

                # create the ncdump text file
                if nc_dump.get_nc_dump_string_by_ncdump(temp_file):
                    dump_str = nc_dump.get_nc_dump_string_by_ncdump(temp_file)
                else:
                    dump_str = nc_dump.get_nc_dump_string(temp_file)

                if dump_str:
                    # refine dump_str first line
                    first_line = list('netcdf {0} '.format(nc_file_name))
                    first_line_index = dump_str.index('{')
                    dump_str_list = first_line + list(dump_str)[first_line_index:]
                    dump_str = "".join(dump_str_list)
                    dump_file_name = nc_file_name + '_header_info.txt'
                    dump_file = os.path.join(temp_dir, dump_file_name)
                    with open(dump_file, 'w') as dump_file_obj:
                        dump_file_obj.write(dump_str)

                    files_to_add_to_resource.append(dump_file)

                with transaction.atomic():
                    # first delete the netcdf file that we retrieved from irods
                    # for setting it to netcdf file type
                    delete_resource_file(resource.short_id, res_file.id, user)
                    # delete_resource_file(resource.short_id, res_file.id, user)
                    # create a netcdf logical file object to be associated with
                    # resource files
                    logical_file = cls.create()
                    # by default set the dataset_name attribute of the logical file to the
                    # name of the file selected to set file type
                    logical_file.dataset_name = nc_file_name
                    logical_file.save()

                    try:
                        # create a folder for the raster file type using the base file
                        # name as the name for the new folder
                        new_folder_path = 'data/contents/{}'.format(nc_file_name)
                        # To avoid folder creation failure when there is already matching
                        # directory path, first check that the folder does not exist
                        # If folder path exists then change the folder name by adding a number
                        # to the end
                        istorage = resource.get_irods_storage()
                        counter = 0
                        new_file_name = nc_file_name
                        while istorage.exists(os.path.join(resource.short_id, new_folder_path)):
                            new_file_name = nc_file_name + "_{}".format(counter)
                            new_folder_path = 'data/contents/{}'.format(new_file_name)
                            counter += 1

                        fed_file_full_path = ''
                        if resource.resource_federation_path:
                            fed_file_full_path = os.path.join(resource.root_path,
                                                              new_folder_path)

                        create_folder(resource.short_id, new_folder_path)
                        log.info("Folder created:{}".format(new_folder_path))

                        # add all new files to the resource
                        for f in files_to_add_to_resource:
                            uploaded_file = UploadedFile(file=open(f, 'rb'),
                                                         name=os.path.basename(f))
                            new_res_file = utils.add_file_to_resource(
                                resource, uploaded_file, folder=new_file_name,
                                fed_res_file_name_or_path=fed_file_full_path
                            )
                            # make each resource file we added as part of the logical file
                            logical_file.add_resource_file(new_res_file)

                        log.info("NetCDF file type - new files were added to the resource.")
                    except Exception as ex:
                        msg = "NetCDF file type. Error when setting file type. Error:{}"
                        msg = msg.format(ex.message)
                        log.exception(msg)
                        # TODO: in case of any error we should put the original file back and
                        # delete the folder that was created
                        raise ValidationError(msg)
                    finally:
                        # remove temp dir
                        if os.path.isdir(temp_dir):
                            shutil.rmtree(temp_dir)

                    log.info("NetCDF file type was created.")

                    # use the extracted metadata to populate resource metadata
                    for element in resource_metadata:
                        # here k is the name of the element
                        # v is a dict of all element attributes/field names and field values
                        k, v = element.items()[0]
                        resource.metadata.create_element(k, **v)

                    log.info("Resource - metadata was saved to DB")

                    # use the extracted metadata to populate file metadata
                    for element in file_type_metadata:
                        # here k is the name of the element
                        # v is a dict of all element attributes/field names and field values
                        k, v = element.items()[0]
                        if k == 'subject':
                            logical_file.metadata.keywords = v
                            logical_file.metadata.save()
                        else:
                            logical_file.metadata.create_element(k, **v)
                    log.info("NetCDF file type - metadata was saved to DB")
            else:
                err_msg = "Not a valid NetCDF file. File type file validation failed."
                log.info(err_msg)
                # remove temp dir
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)
                raise ValidationError(err_msg)
