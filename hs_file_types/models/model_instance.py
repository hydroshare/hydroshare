import json

import jsonschema
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import PermissionDenied
from django.db import models
from django.template import Template, Context
from dominate import tags as dom_tags
from lxml import etree

from hs_core.models import CoreMetaData
from .base_model_program_instance import AbstractModelLogicalFile
from .generic import GenericFileMetaDataMixin
from .model_program import ModelProgramLogicalFile


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="mi_metadata_objects")
    # additional metadata in json format based on metadata schema of the related (executed_by)
    # model program aggregation
    metadata_json = JSONField(default=dict)

    def get_html(self, include_extra_metadata=True, **kwargs):
        html_string = super(ModelInstanceFileMetaData, self).get_html()
        includes_model_outputs_div = dom_tags.div(cls="content-block")
        with includes_model_outputs_div:
            dom_tags.legend("Model Output")
            display_string = "Includes model output files: {}"
            if self.has_model_output:
                display_string = display_string.format("Yes")
            else:
                display_string = display_string.format("No")
            dom_tags.p(display_string)
        html_string += includes_model_outputs_div.render()
        executed_by_div = dom_tags.div(cls="content-block")
        with executed_by_div:
            dom_tags.legend("Executed By (Model Program)")
            if self.executed_by:
                mp_aggr = self.executed_by
                resource = mp_aggr.resource
                this_resource = self.logical_file.resource
                if this_resource.short_id != resource.short_id:
                    # show resource title if the model program aggregation is from a different resource
                    display_string = "{} ({}) - (Resource: {})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name,
                                                                       resource.title)
                else:
                    display_string = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                dom_tags.p(display_string)
            else:
                dom_tags.p("Unspecified")
            if self.metadata_json:
                dom_tags.legend("Schema Based Metadata)")
                json_data = json.dumps(self.metadata_json, indent=4)
                dom_tags.textarea(json_data, rows=10, cols=50, readonly="readonly", cls="form-control")

        html_string += executed_by_div.render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """This generates html form code to add/update the following metadata attributes
        has_model_output
        executed_by
        metadata_json
        """
        from hs_file_types import utils

        form_action = "/hsapi/_internal/{}/update-modelinstance-metadata/"
        form_action = form_action.format(self.logical_file.id)
        root_div = dom_tags.div("{% load crispy_forms_tags %}")
        base_div, context = super(ModelInstanceFileMetaData, self).get_html_forms(render=False)
        user = kwargs['user']

        def get_schema_based_form():
            json_form_action = "/hsapi/_internal/{}/update-modelinstance-metadata-json/"
            json_form_action = json_form_action.format(self.logical_file.id)
            schema_div = dom_tags.div()
            with schema_div:
                with dom_tags.form(id="id-schema-based-form", action=json_form_action,
                                   method="post", enctype="multipart/form-data"):
                    with dom_tags.fieldset():
                        dom_tags.legend("Schema Based Metadata")
                        json_schema = json.dumps(self.executed_by.mi_schema_json)
                        json_data = "{}"
                        if self.metadata_json:
                            json_data = json.dumps(self.metadata_json, indent=4)
                        if invalid_metadata:
                            dom_tags.div("Existing metadata is invalid as per the schema", cls="alert alert-danger")
                            dom_tags.textarea(json_data, rows=10, cols=50, readonly="readonly", cls="form-control")
                            json_data = "{}"
                        dom_tags.input(value=json_schema, id="id-json-schema", type="hidden")
                        dom_tags.input(value=json_data, id="id-metadata-json", name="metadata_json", type="hidden")
                        dom_tags.input(value="loading", id="id-json-editor-load-status", type="hidden")
                        # front-end JS code uses 'editor-holder' to host JSONEditor form component
                        dom_tags.div(id="editor-holder")
                        with dom_tags.div(cls="row", style="margin-top:10px; padding-bottom: 20px;"):
                            with dom_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                                dom_tags.button("Save changes", type="button", id="id-schema-form-submit",
                                                cls="btn btn-primary pull-right btn-form-submit",
                                                style="display: none;")
            return schema_div

        def get_executed_by_form():
            executed_by_div = dom_tags.div()
            with executed_by_div:
                dom_tags.label('Select a Model Program', fr="id_executed_by",
                               cls="control-label")
                with dom_tags.select(cls="form-control", id="id_executed_by", name="executed_by"):
                    dom_tags.option("Select a model program", value="0")
                    for mp_aggr in utils.get_model_program_aggregations(user):
                        res = mp_aggr.resource
                        this_resource = self.logical_file.resource
                        if this_resource.short_id != res.short_id:
                            option = "{} ({}) - (Resource: {})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name,
                                                                       res.title)
                        else:
                            option = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                        if self.executed_by:
                            if self.executed_by.id == mp_aggr.id:
                                dom_tags.option(option, selected="selected",
                                                value=mp_aggr.id)
                            else:
                                dom_tags.option(option, value=mp_aggr.id)
                        else:
                            dom_tags.option(option, value=mp_aggr.id)
            return executed_by_div

        with root_div:
            dom_tags.div().add(base_div)
            with dom_tags.div():
                with dom_tags.form(action=form_action, id="filetype-model-instance",
                                   method="post", enctype="multipart/form-data"):
                    dom_tags.div("{% csrf_token %}")
                    with dom_tags.fieldset(cls="fieldset-border"):
                        with dom_tags.div(cls="form-group"):
                            with dom_tags.div(cls="control-group"):
                                with dom_tags.div(id="mi_includes_output"):
                                    dom_tags.label('Includes Output Files*', fr="id_mi_includes_output_yes",
                                                   cls="control-label")
                                    with dom_tags.div(cls='control-group'):
                                        with dom_tags.div(cls="controls"):
                                            with dom_tags.label('Yes', fr="id_mi_includes_output_yes",
                                                                cls="radio"):
                                                if self.logical_file.metadata.has_model_output:
                                                    dom_tags.input(type="radio", id="id_mi_includes_output_yes",
                                                                   name="has_model_output",
                                                                   cls="inline",
                                                                   checked='checked',
                                                                   value="true")
                                                else:
                                                    dom_tags.input(type="radio", id="id_mi_includes_output_yes",
                                                                   name="has_model_output",
                                                                   cls="inline",
                                                                   value="true")
                                            with dom_tags.label('No', fr="id_mi_includes_output_no",
                                                                cls="radio"):
                                                if self.logical_file.metadata.has_model_output:
                                                    dom_tags.input(type="radio", id="id_mi_includes_output_no",
                                                                   name="has_model_output",
                                                                   cls="inline",
                                                                   value="false")
                                                else:
                                                    dom_tags.input(type="radio", id="id_mi_includes_output_no",
                                                                   name="has_model_output",
                                                                   cls="inline",
                                                                   checked='checked',
                                                                   value="false")
                                with dom_tags.div(id="mi_executed_by", cls="control-group"):
                                    with dom_tags.div(cls="controls"):
                                        dom_tags.legend('Model Program Used for Execution')
                                        get_executed_by_form()

                    with dom_tags.div(cls="row", style="margin-top:10px; padding-bottom: 20px;"):
                        with dom_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                            dom_tags.button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                                            style="display: none;", type="button")

                show_schema_based_form = True
                invalid_metadata = False
                if self.executed_by and self.executed_by.mi_schema_json:
                    if self.metadata_json:
                        # validate metadata against the associated schema
                        try:
                            jsonschema.Draft4Validator(self.executed_by.mi_schema_json).validate(self.metadata_json)
                        except jsonschema.ValidationError:
                            invalid_metadata = True
                elif self.executed_by and self.metadata_json:
                    # no metadata schema exists - so no way to validate the existing metadata
                    invalid_metadata = True
                else:
                    show_schema_based_form = False

                if show_schema_based_form:
                    with dom_tags.div():
                        get_schema_based_form()

        template = Template(root_div.render())
        rendered_html = template.render(context)
        return rendered_html

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(ModelInstanceFileMetaData, self)._get_xml_containers()

        if self.has_model_output:
            includes_output = 'Yes'
        else:
            includes_output = 'No'
        model_output = etree.SubElement(container_to_add_to,
                                        '{%s}includesModelOutput' % CoreMetaData.NAMESPACES['hsterms'])
        model_output.text = includes_output
        if self.executed_by:
            executed_by = etree.SubElement(container_to_add_to,
                                           '{%s}executedByModelProgram' % CoreMetaData.NAMESPACES['hsterms'])
            executed_by.text = self.executed_by.aggregation_path

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, encoding='UTF-8',
                                                               pretty_print=pretty_print).decode()


class ModelInstanceLogicalFile(AbstractModelLogicalFile):
    """ One file or more than one file in a specific folder can be part of this aggregation """

    # attribute to store type of model instance (SWAT, UEB etc)
    model_instance_type = models.CharField(max_length=255, default="Unknown Model Instance")
    metadata = models.OneToOneField(ModelInstanceFileMetaData, related_name="logical_file")
    data_type = "Model Instance"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mi_metadata = ModelInstanceFileMetaData.objects.create(keywords=[])
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mi_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Instance Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    # used in discovery faceting to aggregate native and composite content types
    def get_discovery_content_type(self):
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return self.model_instance_type

    def set_link_to_model_program(self, user, model_prog_aggr):
        """Creates a link to the specified model program aggregation *model_prog_aggr* using the
        executed_by metadata field.

        :param  user: user who is associating this (self) model instance aggregation to a model program aggregation
        :param  model_prog_aggr: an instance of ModelProgramLogicalFile to be associated with
        :raises PermissionDenied exception if the user does not have edit permission for the resource to which this
        model instance aggregation belongs or doesn't have view permission for the resource that contains the model
        program aggregation.
        """

        # check if user has edit permission for the resources
        mi_res = self.resource
        mp_res = model_prog_aggr.resource
        authorized = user.uaccess.can_change_resource(mi_res)
        if not authorized:
            raise PermissionDenied("You don't have permission to edit resource(ID:{})".format(mi_res.short_id))
        if mi_res.short_id != mp_res.short_id:
            authorized = user.uaccess.can_view_resource(mp_res)
            if not authorized:
                raise PermissionDenied("You don't have permission to view resource(ID:{})".format(mp_res.short_id))

        self.metadata.executed_by = model_prog_aggr
        self.metadata.save()

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelInstanceLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()
