import os
import logging

from django.db import models
from django.template import Template, Context

from dominate.tags import div, form, button, hr, i

from hs_core.forms import CoverageTemporalForm, CoverageSpatialForm
from hs_core.signals import post_add_generic_aggregation

from .base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext
from ..enums import AggregationMetaFilePath


class GenericFileMetaDataMixin(AbstractFileMetaData):
    # the metadata element models are from the hs_core type app
    model_app_label = 'hs_core'

    class Meta:
        abstract = True

    def create_element(self, element_model_name, **kwargs):
        element = super(GenericFileMetaDataMixin, self).create_element(element_model_name, **kwargs)
        self.is_dirty = True
        return element

    def delete_element(self, element_model_name, element_id):
        """Overriding the base class method to allow deleting any metadata element that's part of
        generic aggregation (single file aggregation or file set aggregation) metadata"""
        model_type = self._get_metadata_element_model_type(element_model_name)
        meta_element = model_type.model_class().objects.get(id=element_id)
        meta_element.delete()
        self.is_dirty = True
        self.save()

    @property
    def has_modified_metadata(self):
        """Identifies whether a user has updated metadata."""

        if self.coverages.all():
            return True
        if self.extra_metadata:
            return True
        if self.logical_file.files.count() != 1:
            return True
        # the dataset_name is generated from the filename.
        # if dataset_name is different than the filename, the user must have updated metadata.
        res_file = self.logical_file.files.first()
        file_name = res_file.file_name[:-len(res_file.extension)]
        if self.logical_file.dataset_name and file_name != self.logical_file.dataset_name:
            return True
        return False

    def get_html(self, **kwargs):
        """overrides the base class function"""

        skip_coverage = kwargs.get('skip_coverage', False)
        html_string = super(GenericFileMetaDataMixin, self).get_html()
        if not self.has_metadata:
            no_metadata_message = div(id="#fb-metadata-default", cls="text-center text-muted",
                                      role="alert")
            with no_metadata_message:
                div("No file level metadata exists for the selected file.")
                hr()
                i_tag = i(cls="fa fa-eye-slash fa-2x")
                i_tag['aria-hidden'] = 'true'
            html_string = no_metadata_message.render()
        elif not skip_coverage:
            if self.temporal_coverage:
                html_string += self.temporal_coverage.get_html()

            if self.spatial_coverage:
                html_string += self.spatial_coverage.get_html()

        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, render=True, **kwargs):
        """overrides the base class function"""

        skip_coverage = kwargs.get('skip_coverage', False)
        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(GenericFileMetaDataMixin, self).get_html_forms(skip_coverage=skip_coverage)
            if not skip_coverage:
                with div():
                    with form(id="id-coverage-spatial-filetype", action="{{ spatial_form.action }}",
                              method="post", enctype="multipart/form-data", cls='hs-coordinates-picker',
                              data_coordinates_type="point"):
                        div("{% crispy spatial_form %}")
                        with div(cls="row", style="margin-top:10px;"):
                            with div(cls="col-md-offset-10 col-xs-offset-6 "
                                         "col-md-2 col-xs-6"):
                                button("Save changes", type="button",
                                       cls="btn btn-primary pull-right btn-form-submit",
                                       style="display: none;")  # TODO: TESTING
                    # for aggregation that contains other aggregations with spatial data,
                    # show option to update spatial coverage from contained aggregations
                    if self.logical_file.has_children_spatial_data:
                        with div(cls="control-group", style="margin-top:10px;"):
                            with div(cls="row", style="margin-right: 2px; margin-bottom: 5px;"):
                                button("Set spatial coverage from folder contents", type="button",
                                       cls="btn btn-primary pull-right",
                                       id="btn-update-aggregation-spatial-coverage")

        template = Template(root_div.render())
        context_dict = dict()
        if not skip_coverage:
            temp_cov_form = self.get_temporal_coverage_form()
            spatial_cov_form = self.get_spatial_coverage_form(allow_edit=True)
            update_action = "/hsapi/_internal/{0}/{1}/{2}/{3}/update-file-metadata/"
            create_action = "/hsapi/_internal/{0}/{1}/{2}/add-file-metadata/"

            element_name = "coverage"
            logical_file_class_name = self.logical_file.__class__.__name__
            temporal_coverage = self.temporal_coverage
            spatial_coverage = self.spatial_coverage

            if temporal_coverage or spatial_coverage:
                if temporal_coverage:
                    temp_action = update_action.format(logical_file_class_name, self.logical_file.id,
                                                       element_name, temporal_coverage.id)
                    temp_cov_form.action = temp_action
                else:
                    temp_action = create_action.format(logical_file_class_name, self.logical_file.id,
                                                       element_name)
                    temp_cov_form.action = temp_action

                if spatial_coverage:
                    spatial_action = update_action.format(logical_file_class_name, self.logical_file.id,
                                                          element_name, spatial_coverage.id)
                    spatial_cov_form.action = spatial_action
                else:
                    spatial_action = create_action.format(logical_file_class_name, self.logical_file.id,
                                                          element_name)
                    spatial_cov_form.action = spatial_action
            else:
                action = create_action.format(logical_file_class_name, self.logical_file.id,
                                              element_name)
                temp_cov_form.action = action
                spatial_cov_form.action = action

            context_dict["temp_form"] = temp_cov_form
            context_dict["spatial_form"] = spatial_cov_form

        context = Context(context_dict)
        if render:
            rendered_html = template.render(context)
            return rendered_html
        return root_div, context

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Generic file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}
        element_name = element_name.lower()
        if element_name == "coverage":
            if 'type' in request.POST:
                if request.POST['type'].lower() == 'point' or request.POST['type'].lower() == 'box':
                    element_form = CoverageSpatialForm(data=request.POST)
                else:
                    element_form = CoverageTemporalForm(data=request.POST)
            else:
                element_form = CoverageTemporalForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


class GenericFileMetaData(GenericFileMetaDataMixin):
    pass


class GenericLogicalFile(AbstractLogicalFile):
    """ Any resource file can be part of this aggregation """
    metadata = models.OneToOneField(GenericFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "genericData"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        generic_metadata = GenericFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=generic_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Single File Content: A single file with file specific metadata'

    @staticmethod
    def get_aggregation_term_label():
        return "Single File Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "SingleFileAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "Generic Data"

    @property
    def is_single_file_aggregation(self):
        """This aggregation supports only one file"""
        return True

    @property
    def redirect_url(self):
        """
        return redirect_url if this logical file is a referenced web url file, None otherwise
        """
        if 'url' in self.extra_data:
            return self.extra_data['url']
        else:
            return None

    @property
    def metadata_json_file_path(self):
        """Returns the storage path of the aggregation metadata json file"""

        meta_file_path = self.files.first().storage_path + AggregationMetaFilePath.METADATA_JSON_FILE_ENDSWITH.value
        return meta_file_path

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path='', extra_data={}):
        """
        Makes any physical file part of a generic aggregation type. The physical file must
        not already be a part of any aggregation.
        :param resource:
        :param user:
        :param file_id: id of the resource file to set logical file type
        :param folder_path: ignored here and a value for file_id is required
        :param extra_data: a dict that, if not empty, will be passed on to extra_data of
        corresponding logical file of the resource file
        :return:
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=post_add_generic_aggregation,
                             is_temp_file=False) as ft_ctx:

            res_file = ft_ctx.res_file
            upload_folder = res_file.file_folder
            dataset_name, _ = os.path.splitext(res_file.file_name)
            # create a generic logical file object
            logical_file = cls.create_aggregation(dataset_name=dataset_name,
                                                  resource=resource,
                                                  res_files=[res_file],
                                                  new_files_to_upload=[],
                                                  folder_path=upload_folder)

            if extra_data:
                logical_file.extra_data = extra_data
                logical_file.save()

            ft_ctx.logical_file = logical_file
            log.info("Generic aggregation was created for file:{}.".format(res_file.storage_path))
            return logical_file

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets any resource file as the primary file  from the list of files *resource_files* """

        return resource_files[0] if resource_files else None

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(GenericLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()

    @classmethod
    def get_main_file_type(cls):
        # a single file extension in the group which is considered the main file
        # - subclass needs to override this
        return ".*"
