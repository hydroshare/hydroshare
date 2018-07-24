import os
import shutil
import logging
import re

from functools import partial, wraps
import netCDF4
import numpy as np
from lxml import etree

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.template import Template, Context
from django.forms.models import formset_factory, BaseFormSet

from dominate.tags import div, legend, form, button, p, textarea, strong, input

from hs_core.hydroshare import utils
from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm
from hs_core.models import Creator, Contributor, CoreMetaData

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
        elements += [self.original_coverage]
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
        # There can be at most only one instance of type OriginalCoverage associated
        # with this metadata object
        return self.ori_coverage.all().first()

    def get_html(self):
        """overrides the base class function"""

        html_string = super(NetCDFFileMetaData, self).get_html()
        if self.spatial_coverage:
            html_string += self.spatial_coverage.get_html()
        if self.originalCoverage:
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

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """overrides the base class function"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            self.get_update_netcdf_file_html_form()
            super(NetCDFFileMetaData, self).get_html_forms()
            with div(cls="row"):
                with div(cls="col-lg-6 col-xs-12", id="original-coverage-filetype"):
                    with form(id="id-origcoverage-file-type",
                              action="{{ orig_coverage_form.action }}",
                              method="post", enctype="multipart/form-data"):
                        div("{% crispy orig_coverage_form %}")
                        with div(cls="row", style="margin-top:10px;"):
                            with div(cls="col-md-offset-10 col-xs-offset-6 "
                                         "col-md-2 col-xs-6"):
                                button("Save changes", type="button",
                                       cls="btn btn-primary pull-right",
                                       style="display: none;")

                with div(cls="col-lg-6 col-xs-12", id="spatial-coverage-filetype"):
                    with form(id="id-spatial-coverage-file-type",
                              action="{{ spatial_coverage_form.action }}",
                              method="post", enctype="multipart/form-data"):
                        div("{% crispy spatial_coverage_form %}")
                        with div(cls="row", style="margin-top:10px;"):
                            with div(cls="col-md-offset-10 col-xs-offset-6 "
                                         "col-md-2 col-xs-6"):
                                button("Save changes", type="button",
                                       cls="btn btn-primary pull-right",
                                       style="display: none;")

            with div(cls="pull-left col-sm-12"):
                # id has to be variables to get the vertical scrollbar
                with div(cls="well", id="variables"):
                    with div(cls="row"):
                        with div("{% for form in variable_formset_forms %}"):
                            with div(cls="col-sm-6 col-xs-12"):
                                with form(id="{{ form.form_id }}", action="{{ form.action }}",
                                          method="post", enctype="multipart/form-data"):
                                    div("{% crispy form %}")
                                    with div(cls="row", style="margin-top:10px;"):
                                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                                     "col-md-2 col-xs-6"):
                                            button("Save changes", type="button",
                                                   cls="btn btn-primary pull-right",
                                                   style="display: none;")
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

        orig_cov_form = self.get_original_coverage_form()
        if self.originalCoverage:
            temp_action = update_action.format(self.logical_file.id, "originalcoverage",
                                               self.originalCoverage.id)
        else:
            temp_action = create_action.format(self.logical_file.id, "originalcoverage")

        orig_cov_form.action = temp_action

        spatial_cov_form = self.get_spatial_coverage_form(allow_edit=True)
        if self.spatial_coverage:
            temp_action = update_action.format(self.logical_file.id, "coverage",
                                               self.spatial_coverage.id)
        else:
            temp_action = create_action.format(self.logical_file.id, "coverage")

        spatial_cov_form.action = temp_action
        context_dict = dict()
        context_dict["temp_form"] = temp_cov_form
        context_dict["orig_coverage_form"] = orig_cov_form
        context_dict["spatial_coverage_form"] = spatial_cov_form
        context_dict["variable_formset_forms"] = self.get_variable_formset().forms
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_update_netcdf_file_html_form(self):
        form_action = "/hsapi/_internal/{}/update-netcdf-file/".format(self.id)
        style = "display:none;"
        if self.is_dirty:
            style = "margin-bottom:10px"
        root_div = div(id="div-netcdf-file-update", cls="row", style=style)

        with root_div:
            with div(cls="col-sm-12"):
                with div(cls="alert alert-warning alert-dismissible", role="alert"):
                    strong("NetCDF file needs to be synced with metadata changes.")
                    input(id="metadata-dirty", type="hidden", value=self.is_dirty)
                    with form(action=form_action, method="post", id="update-netcdf-file"):
                        button("Update NetCDF File", type="button", cls="btn btn-primary",
                               id="id-update-netcdf-file")

        return root_div

    def get_original_coverage_form(self):
        return OriginalCoverage.get_html_form(resource=None, element=self.originalCoverage,
                                              file_type=True)

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
        """
        Generates html code to display the contents of the ncdump text file. The generated html
        is used for netcdf file type metadata view and edit modes.
        :return:
        """

        nc_dump_div = div()
        nc_dump_res_file = None
        for f in self.logical_file.files.all():
            if f.extension == ".txt":
                nc_dump_res_file = f
                break
        if nc_dump_res_file is not None:
            nc_dump_div = div(style="clear: both", cls="col-xs-12")
            with nc_dump_div:
                legend("NetCDF Header Information")
                p(nc_dump_res_file.full_path[33:])
                header_info = nc_dump_res_file.resource_file.read()
                header_info = header_info.decode('utf-8')
                textarea(header_info, readonly="", rows="15",
                         cls="input-xlarge", style="min-width: 100%")

        return nc_dump_div

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
                try:
                    # when the request comes from the UI, the variable attributes have a prefix of
                    # '-'
                    matching_key = [key for key in request.POST if '-' + field_name in key][0]
                except IndexError:
                    if field_name in request.POST:
                        matching_key = field_name
                    else:
                        continue
                form_data[field_name] = request.POST[matching_key]
            element_form = VariableValidationForm(form_data)
        elif element_name == 'originalcoverage':
            element_form = OriginalCoverageForm(data=request.POST)
        elif element_name == 'coverage' and 'start' not in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            # here we are assuming temporal coverage
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(NetCDFFileMetaData, self)._get_xml_containers()
        if self.originalCoverage:
            self.originalCoverage.add_to_xml_container(container_to_add_to)

        for variable in self.variables.all():
            variable.add_to_xml_container(container_to_add_to)

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)


class NetCDFLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(NetCDFFileMetaData, related_name="logical_file")
    data_type = "Multidimensional"
    verbose_content_type = "Multidimensional (NetCDF)"  # used during discovery

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .nc file can be set to this logical file group"""
        return [".nc"]

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".nc"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .nc and .txt"""
        return [".nc", ".txt"]

    @staticmethod
    def get_aggregation_display_name():
        return 'Multidimensional Content: A multidimensional dataset represented by a NetCDF ' \
               'file (.nc) and text file giving its NetCDF header content'

    @staticmethod
    def get_aggregation_type_name():
        return "MultidimensionalAggregation"

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        netcdf_metadata = NetCDFFileMetaData.objects.create(keywords=[])
        return cls.objects.create(metadata=netcdf_metadata)

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

    def update_netcdf_file(self, user):
        """
        writes metadata to the netcdf file associated with this instance of the logical file
        :return:
        """

        log = logging.getLogger()

        nc_res_file = ''
        txt_res_file = ''
        for f in self.files.all():
            if f.extension == '.nc':
                nc_res_file = f
                break

        for f in self.files.all():
            if f.extension == '.txt':
                txt_res_file = f
                break
        if not nc_res_file:
            msg = "No netcdf file exists for this logical file."
            log.exception(msg)
            raise ValidationError(msg)

        netcdf_file_update(self, nc_res_file, txt_res_file, user)

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) != 1:
            # no files or more than 1 file
            return ""

        if files[0].extension not in cls.get_allowed_uploaded_file_types():
            return ""

        return cls.__name__

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """ Creates a NetCDFLogicalFile (aggregation) from a netcdf file (.nc) resource file
        or a folder """

        log = logging.getLogger()
        res_file, folder_path = cls._validate_set_file_type_inputs(resource, file_id, folder_path)

        # base file name (no path included)
        file_name = res_file.file_name
        # file name without the extension - needed for naming the new aggregation folder
        nc_file_name = file_name[:-len(res_file.extension)]

        resource_metadata = []
        file_type_metadata = []
        upload_folder = ''
        res_files_to_delete = []
        # get the file from irods to temp dir
        temp_file = utils.get_file_from_irods(res_file)
        temp_dir = os.path.dirname(temp_file)

        # file validation and metadata extraction
        nc_dataset = nc_utils.get_nc_dataset(temp_file)
        if isinstance(nc_dataset, netCDF4.Dataset):
            msg = "NetCDF aggregation. Error when creating aggregation. Error:{}"
            file_type_success = False
            # extract the metadata from netcdf file
            res_dublin_core_meta, res_type_specific_meta = nc_meta.get_nc_meta_dict(temp_file)
            # populate resource_metadata and file_type_metadata lists with extracted metadata
            add_metadata_to_list(resource_metadata, res_dublin_core_meta,
                                 res_type_specific_meta, file_type_metadata, resource)

            # create the ncdump text file
            dump_file = create_header_info_txt_file(temp_file, nc_file_name)
            file_folder = res_file.file_folder
            aggregation_folder_created = False
            create_new_folder = cls._check_create_aggregation_folder(
                selected_res_file=res_file, selected_folder=folder_path,
                aggregation_file_count=1)

            with transaction.atomic():
                # create a netcdf logical file object to be associated with
                # resource files
                dataset_title = res_dublin_core_meta.get('title', nc_file_name)
                logical_file = cls.initialize(dataset_title)

                try:
                    if folder_path is None:
                        # we are here means aggregation is being created by selecting a file

                        # create a folder for the netcdf file type using the base file
                        # name as the name for the new folder if the file is not already in a folder
                        if create_new_folder:
                            upload_folder = cls._create_aggregation_folder(resource, file_folder,
                                                                           nc_file_name)
                            aggregation_folder_created = True
                            log.info("NetCDF Aggregation creation - folder created:{}".format(
                                upload_folder))
                        else:
                            # selected nc file is already in a folder
                            upload_folder = file_folder

                        if aggregation_folder_created:
                            # copy the nc file to the new aggregation folder and make it part
                            # of the logical file
                            tgt_folder = upload_folder
                            files_to_copy = [res_file]
                            logical_file.copy_resource_files(resource, files_to_copy,
                                                             tgt_folder)
                            res_files_to_delete.append(res_file)
                        else:
                            # make the selected nc file as part of the aggregation/file type
                            logical_file.add_resource_file(res_file)

                    else:
                        # folder has been selected to create aggregation
                        upload_folder = folder_path
                        # make the .nc file part of the aggregation
                        logical_file.add_resource_file(res_file)

                    # add the new dump txt file to the resource
                    uploaded_file = UploadedFile(file=open(dump_file, 'rb'),
                                                 name=os.path.basename(dump_file))

                    new_res_file = utils.add_file_to_resource(
                        resource, uploaded_file, folder=upload_folder
                    )

                    # make this new resource file we added part of the logical file
                    logical_file.add_resource_file(new_res_file)
                    log.info("NetCDF aggregation creation - a new file was added to the resource.")

                    # use the extracted metadata to populate resource metadata
                    for element in resource_metadata:
                        # here k is the name of the element
                        # v is a dict of all element attributes/field names and field values
                        k, v = element.items()[0]
                        if k == 'title':
                            # update title element
                            title_element = resource.metadata.title
                            resource.metadata.update_element('title', title_element.id, **v)
                        else:
                            resource.metadata.create_element(k, **v)

                    log.info("NetCDF Aggregation creation - Resource metadata was saved to DB")

                    # use the extracted metadata to populate file metadata
                    for element in file_type_metadata:
                        # here k is the name of the element
                        # v is a dict of all element attributes/field names and field values
                        k, v = element.items()[0]
                        if k == 'subject':
                            logical_file.metadata.keywords = v
                            logical_file.metadata.save()
                            # update resource level keywords
                            resource_keywords = [subject.value.lower() for subject in
                                                 resource.metadata.subjects.all()]
                            for kw in logical_file.metadata.keywords:
                                if kw.lower() not in resource_keywords:
                                    resource.metadata.create_element('subject', value=kw)
                        else:
                            logical_file.metadata.create_element(k, **v)
                    log.info("NetCDF aggregation - metadata was saved in aggregation")
                    logical_file._finalize(user, resource,
                                           folder_created=aggregation_folder_created,
                                           res_files_to_delete=res_files_to_delete)
                    file_type_success = True
                except Exception as ex:
                    msg = msg.format(ex.message)
                    log.exception(msg)
                finally:
                    # remove temp dir
                    if os.path.isdir(temp_dir):
                        shutil.rmtree(temp_dir)

            if not file_type_success:
                aggregation_from_folder = folder_path is not None
                cls._cleanup_on_fail_to_create_aggregation(user, resource, upload_folder,
                                                           file_folder, aggregation_from_folder)
                raise ValidationError(msg)

        else:
            err_msg = "Not a valid NetCDF file. NetCDF aggregation validation failed."
            log.error(err_msg)
            # remove temp dir
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValidationError(err_msg)

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
        """Gets a resource file that has extension .nc from the list of files *resource_files* """

        res_files = [f for f in resource_files if f.extension.lower() == '.nc']
        return res_files[0] if res_files else None


def add_metadata_to_list(res_meta_list, extracted_core_meta, extracted_specific_meta,
                         file_meta_list=None, resource=None):
    """
    Helper function to populate metadata lists (*res_meta_list* and *file_meta_list*) with
    extracted metadata from the NetCDF file. These metadata lists are then used for creating
    metadata element objects by the caller.
    :param res_meta_list: a list to store data to create metadata elements at the resource level
    :param extracted_core_meta: a dict of extracted dublin core metadata
    :param extracted_specific_meta: a dict of extracted metadata that is NetCDF specific
    :param file_meta_list: a list to store data to create metadata elements at the file type level
    (must be None when this helper function is used for NetCDF resource and must not be None
    when used for NetCDF file type
    :param resource: an instance of BaseResource (must be None when this helper function is used
    for NteCDF resource and must not be None when used for NetCDF file type)
    :return:
    """

    # add title
    if resource is not None and file_meta_list is not None:
        # file type
        if resource.metadata.title.value.lower() == 'untitled resource':
            add_title_metadata(res_meta_list, extracted_core_meta)
    else:
        # resource type
        add_title_metadata(res_meta_list, extracted_core_meta)

    # add abstract (Description element)
    if resource is not None and file_meta_list is not None:
        # file type
        if resource.metadata.description is None:
            add_abstract_metadata(res_meta_list, extracted_core_meta)
    else:
        # resource type
        add_abstract_metadata(res_meta_list, extracted_core_meta)

    # add keywords
    if file_meta_list is not None:
        # file type
        add_keywords_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_keywords_metadata(res_meta_list, extracted_core_meta, file_type=False)

    # add creators:
    if resource is not None:
        # file type
        add_creators_metadata(res_meta_list, extracted_core_meta,
                              resource.metadata.creators.all())
    else:
        # resource type
        add_creators_metadata(res_meta_list, extracted_core_meta,
                              Creator.objects.none())

    # add contributors:
    if resource is not None:
        # file type
        add_contributors_metadata(res_meta_list, extracted_core_meta,
                                  resource.metadata.contributors.all())
    else:
        # resource type
        add_contributors_metadata(res_meta_list, extracted_core_meta,
                                  Contributor.objects.none())

    # add source (applies only to NetCDF resource type)
    if extracted_core_meta.get('source') and file_meta_list is None:
        source = {'source': {'derived_from': extracted_core_meta['source']}}
        res_meta_list.append(source)

    # add relation (applies only to NetCDF resource type)
    if extracted_core_meta.get('references') and file_meta_list is None:
        relation = {'relation': {'type': 'cites',
                                 'value': extracted_core_meta['references']}}
        res_meta_list.append(relation)

    # add rights (applies only to NetCDF resource type)
    if extracted_core_meta.get('rights') and file_meta_list is None:
        raw_info = extracted_core_meta.get('rights')
        b = re.search("(?P<url>https?://[^\s]+)", raw_info)
        url = b.group('url') if b else ''
        statement = raw_info.replace(url, '') if url else raw_info
        rights = {'rights': {'statement': statement, 'url': url}}
        res_meta_list.append(rights)

    # add coverage - period
    if file_meta_list is not None:
        # file type
        add_temporal_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_temporal_coverage_metadata(res_meta_list, extracted_core_meta)

    # add coverage - box
    if file_meta_list is not None:
        # file type
        add_spatial_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_spatial_coverage_metadata(res_meta_list, extracted_core_meta)

    # add variables
    if file_meta_list is not None:
        # file type
        add_variable_metadata(file_meta_list, extracted_specific_meta)
    else:
        # resource type
        add_variable_metadata(res_meta_list, extracted_specific_meta)

    # add original spatial coverage
    if file_meta_list is not None:
        # file type
        add_original_coverage_metadata(file_meta_list, extracted_core_meta)
    else:
        # resource type
        add_original_coverage_metadata(res_meta_list, extracted_core_meta)


def add_original_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the original coverage element to the *metadata_list*
    :param metadata_list: list to  which original coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    ori_cov = {}
    if extracted_metadata.get('original-box'):
        coverage_data = extracted_metadata['original-box']
        projection_string_type = ""
        projection_string_text = ""
        datum = ""
        if extracted_metadata.get('projection-info'):
            projection_string_type = extracted_metadata[
                'projection-info']['type']
            projection_string_text = extracted_metadata[
                'projection-info']['text']
            datum = extracted_metadata['projection-info']['datum']

        ori_cov = {'originalcoverage':
                   {'value': coverage_data,
                    'projection_string_type': projection_string_type,
                    'projection_string_text': projection_string_text,
                    'datum': datum
                    }
                   }
    if ori_cov:
        metadata_list.append(ori_cov)


def add_creators_metadata(metadata_list, extracted_metadata, existing_creators):
    """
    Adds data for creator(s) to the *metadata_list*
    :param metadata_list: list to  which creator(s) data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param existing_creators: a QuerySet object for existing creators
    :return:
    """
    if extracted_metadata.get('creator_name'):
        name = extracted_metadata['creator_name']
        # add creator only if there is no creator already with the same name
        if not existing_creators.filter(name=name).exists():
            email = extracted_metadata.get('creator_email', '')
            url = extracted_metadata.get('creator_url', '')
            creator = {'creator': {'name': name, 'email': email, 'homepage': url}}
            metadata_list.append(creator)


def add_contributors_metadata(metadata_list, extracted_metadata, existing_contributors):
    """
    Adds data for contributor(s) to the *metadata_list*
    :param metadata_list: list to  which contributor(s) data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param existing_contributors: a QuerySet object for existing contributors
    :return:
    """
    if extracted_metadata.get('contributor_name'):
        name_list = extracted_metadata['contributor_name'].split(',')
        for name in name_list:
            # add contributor only if there is no contributor already with the
            # same name
            if not existing_contributors.filter(name=name).exists():
                contributor = {'contributor': {'name': name}}
                metadata_list.append(contributor)


def add_title_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the title element to the *metadata_list*
    :param metadata_list: list to  which title data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('title'):
        res_title = {'title': {'value': extracted_metadata['title']}}
        metadata_list.append(res_title)


def add_abstract_metadata(metadata_list, extracted_metadata):
    """
    Adds data for the abstract (Description) element to the *metadata_list*
    :param metadata_list: list to  which abstract data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """

    if extracted_metadata.get('description'):
        description = {'description': {'abstract': extracted_metadata['description']}}
        metadata_list.append(description)


def add_variable_metadata(metadata_list, extracted_metadata):
    """
    Adds variable(s) related data to the *metadata_list*
    :param metadata_list: list to  which variable data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    for var_name, var_meta in extracted_metadata.items():
        meta_info = {}
        for element, value in var_meta.items():
            if value != '':
                meta_info[element] = value
        metadata_list.append({'variable': meta_info})


def add_spatial_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for one spatial coverage metadata element to the *metadata_list**
    :param metadata_list: list to which spatial coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('box'):
        box = {'coverage': {'type': 'box', 'value': extracted_metadata['box']}}
        metadata_list.append(box)


def add_temporal_coverage_metadata(metadata_list, extracted_metadata):
    """
    Adds data for one temporal metadata element to the *metadata_list*
    :param metadata_list: list to which temporal coverage data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :return:
    """
    if extracted_metadata.get('period'):
        period = {
            'coverage': {'type': 'period', 'value': extracted_metadata['period']}}
        metadata_list.append(period)


def add_keywords_metadata(metadata_list, extracted_metadata, file_type=True):
    """
    Adds data for subject/keywords element to the *metadata_list*
    :param metadata_list: list to which keyword data needs to be added
    :param extracted_metadata: a dict containing netcdf extracted metadata
    :param file_type: If True then this metadata extraction is for netCDF file type, otherwise
    metadata extraction is for NetCDF resource
    :return:
    """
    if extracted_metadata.get('subject'):
        keywords = extracted_metadata['subject'].split(',')
        if file_type:
            metadata_list.append({'subject': keywords})
        else:
            for keyword in keywords:
                metadata_list.append({'subject': {'value': keyword}})


def create_header_info_txt_file(nc_temp_file, nc_file_name):
    """
    Creates the header text file using the *nc_temp_file*
    :param nc_temp_file: the netcdf file copied from irods to django
    for metadata extraction
    :return:
    """

    if nc_dump.get_nc_dump_string_by_ncdump(nc_temp_file):
        dump_str = nc_dump.get_nc_dump_string_by_ncdump(nc_temp_file)
    else:
        dump_str = nc_dump.get_nc_dump_string(nc_temp_file)

    # file name without the extension
    temp_dir = os.path.dirname(nc_temp_file)
    dump_file_name = nc_file_name + '_header_info.txt'
    dump_file = os.path.join(temp_dir, dump_file_name)
    if dump_str:
        # refine dump_str first line
        first_line = list('netcdf {0} '.format(nc_file_name))
        first_line_index = dump_str.index('{')
        dump_str_list = first_line + list(dump_str)[first_line_index:]
        dump_str = "".join(dump_str_list)
        with open(dump_file, 'w') as dump_file_obj:
            dump_file_obj.write(dump_str)
    else:
        with open(dump_file, 'w') as dump_file_obj:
            dump_file_obj.write("")

    return dump_file


def netcdf_file_update(instance, nc_res_file, txt_res_file, user):
    log = logging.getLogger()
    # check the instance type
    file_type = isinstance(instance, NetCDFLogicalFile)

    # get the file from irods to temp dir
    temp_nc_file = utils.get_file_from_irods(nc_res_file)
    nc_dataset = netCDF4.Dataset(temp_nc_file, 'a')

    try:
        # update title
        title = instance.dataset_name if file_type else instance.metadata.title.value

        if title.lower() != 'untitled resource':
            if hasattr(nc_dataset, 'title'):
                delattr(nc_dataset, 'title')
            nc_dataset.title = title

        # update keywords
        keywords = instance.metadata.keywords if file_type \
            else [item.value for item in instance.metadata.subjects.all()]

        if hasattr(nc_dataset, 'keywords'):
            delattr(nc_dataset, 'keywords')

        if keywords:
            nc_dataset.keywords = ', '.join(keywords)

        # update key/value metadata
        extra_metadata_dict = instance.metadata.extra_metadata if file_type \
            else instance.extra_metadata

        if hasattr(nc_dataset, 'hs_extra_metadata'):
            delattr(nc_dataset, 'hs_extra_metadata')

        if extra_metadata_dict:
            extra_metadata = []
            for k, v in extra_metadata_dict.items():
                extra_metadata.append("{}:{}".format(k, v))
            nc_dataset.hs_extra_metadata = ', '.join(extra_metadata)

        # update temporal coverage
        temporal_coverage = instance.metadata.temporal_coverage if file_type \
            else instance.metadata.coverages.all().filter(type='period').first()

        for attr_name in ['time_coverage_start', 'time_coverage_end']:
            if hasattr(nc_dataset, attr_name):
                delattr(nc_dataset, attr_name)

        if temporal_coverage:
            nc_dataset.time_coverage_start = temporal_coverage.value['start']
            nc_dataset.time_coverage_end = temporal_coverage.value['end']

        # update spatial coverage
        spatial_coverage = instance.metadata.spatial_coverage if file_type \
            else instance.metadata.coverages.all().filter(type='box').first()

        for attr_name in ['geospatial_lat_min', 'geospatial_lat_max', 'geospatial_lon_min',
                          'geospatial_lon_max']:
            if hasattr(nc_dataset, attr_name):
                delattr(nc_dataset, attr_name)

        if spatial_coverage:
            nc_dataset.geospatial_lat_min = spatial_coverage.value['southlimit']
            nc_dataset.geospatial_lat_max = spatial_coverage.value['northlimit']
            nc_dataset.geospatial_lon_min = spatial_coverage.value['westlimit']
            nc_dataset.geospatial_lon_max = spatial_coverage.value['eastlimit']

        # update variables
        if instance.metadata.variables.all():
            dataset_variables = nc_dataset.variables
            for variable in instance.metadata.variables.all():
                if variable.name in dataset_variables.keys():
                    dataset_variable = dataset_variables[variable.name]

                    # update units
                    if hasattr(dataset_variable, 'units'):
                        delattr(dataset_variable, 'units')
                    if variable.unit != 'Unknown':
                        dataset_variable.setncattr('units', variable.unit)

                    # update long_name
                    if hasattr(dataset_variable, 'long_name'):
                        delattr(dataset_variable, 'long_name')
                    if variable.descriptive_name:
                        dataset_variable.setncattr('long_name', variable.descriptive_name)

                    # update method
                    if hasattr(dataset_variable, 'comment'):
                        delattr(dataset_variable, 'comment')
                    if variable.method:
                        dataset_variable.setncattr('comment', variable.method)

                    # update missing value
                    if variable.missing_value:
                        if hasattr(dataset_variable, 'missing_value'):
                            missing_value = dataset_variable.missing_value
                            delattr(dataset_variable, 'missing_value')
                        else:
                            missing_value = ''
                        try:
                            dt = np.dtype(dataset_variable.datatype.name)
                            missing_value = np.fromstring(variable.missing_value + ' ',
                                                          dtype=dt.type, sep=" ")
                        except:
                            pass

                        if missing_value:
                            dataset_variable.setncattr('missing_value', missing_value)

        # Update metadata element that only apply to netCDF resource
        if not file_type:

            # update summary
            if hasattr(nc_dataset, 'summary'):
                delattr(nc_dataset, 'summary')
            if instance.metadata.description:
                nc_dataset.summary = instance.metadata.description.abstract

            # update contributor
            if hasattr(nc_dataset, 'contributor_name'):
                delattr(nc_dataset, 'contributor_name')

            contributor_list = instance.metadata.contributors.all()
            if contributor_list:
                res_contri_name = []
                for contributor in contributor_list:
                    res_contri_name.append(contributor.name)

                nc_dataset.contributor_name = ', '.join(res_contri_name)

            # update creator
            for attr_name in ['creator_name', 'creator_email', 'creator_url']:
                if hasattr(nc_dataset, attr_name):
                    delattr(nc_dataset, attr_name)

            creator = instance.metadata.creators.all().filter(order=1).first()
            if creator:
                nc_dataset.creator_name = creator.name if creator.name else creator.organization

                if creator.email:
                    nc_dataset.creator_email = creator.email
                if creator.description or creator.homepage:
                    nc_dataset.creator_url = creator.homepage if creator.homepage \
                        else 'https://www.hydroshare.org' + creator.description

            # update license
            if hasattr(nc_dataset, 'license'):
                delattr(nc_dataset, 'license')
            if instance.metadata.rights:
                nc_dataset.license = "{0} {1}".format(instance.metadata.rights.statement,
                                                      instance.metadata.rights.url)

            # update reference
            if hasattr(nc_dataset, 'references'):
                delattr(nc_dataset, 'references')

            reference_list = instance.metadata.relations.all().filter(type='cites')
            if reference_list:
                res_meta_ref = []
                for reference in reference_list:
                    res_meta_ref.append(reference.value)
                nc_dataset.references = ' \n'.join(res_meta_ref)

            # update source
            if hasattr(nc_dataset, 'source'):
                delattr(nc_dataset, 'source')

            source_list = instance.metadata.sources.all()
            if source_list:
                res_meta_source = []
                for source in source_list:
                    res_meta_source.append(source.derived_from)
                nc_dataset.source = ' \n'.join(res_meta_source)

        # close nc dataset
        nc_dataset.close()

    except Exception as ex:
        log.exception(ex.message)
        if os.path.exists(temp_nc_file):
            shutil.rmtree(os.path.dirname(temp_nc_file))
        raise ex

    # create the ncdump text file
    nc_file_name = os.path.basename(temp_nc_file).split(".")[0]
    temp_text_file = create_header_info_txt_file(temp_nc_file, nc_file_name)

    # push the updated nc file and the txt file to iRODS
    utils.replace_resource_file_on_irods(temp_nc_file, nc_res_file,
                                         user)
    utils.replace_resource_file_on_irods(temp_text_file, txt_res_file,
                                         user)

    metadata = instance.metadata
    if file_type:
        instance.create_aggregation_xml_documents(create_map_xml=False)
    metadata.is_dirty = False
    metadata.save()

    # cleanup the temp dir
    if os.path.exists(temp_nc_file):
        shutil.rmtree(os.path.dirname(temp_nc_file))
