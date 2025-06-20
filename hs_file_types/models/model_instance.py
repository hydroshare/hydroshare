import json
import os
import random
import shutil
from uuid import uuid4

import jsonschema
from deepdiff import DeepDiff

from django.db import models
from django.template import Template, Context
from dominate import tags as dom_tags
from rdflib import Literal, URIRef

from hs_core.hs_rdf import HSTERMS
from hs_core.hydroshare.utils import current_site_url
from hs_core.models import ResourceFile
from .base import NestedLogicalFileMixin
from .base_model_program_instance import AbstractModelLogicalFile
from .generic import GenericFileMetaDataMixin
from .model_program import ModelProgramLogicalFile
from ..enums import AggregationMetaFilePath
from hydroshare import settings


class ModelInstanceFileMetaData(GenericFileMetaDataMixin):
    has_model_output = models.BooleanField(default=False)
    executed_by = models.ForeignKey(ModelProgramLogicalFile, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="mi_metadata_objects")

    # additional metadata in json format based on metadata schema of the related (executed_by)
    # model program aggregation
    metadata_json = models.JSONField(default=dict)

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
                # check if the mp aggregation is from another resource (possible only in the case of
                # migrated mi resource)
                if self.logical_file.resource.short_id != mp_aggr.resource.short_id:
                    hs_res_url = os.path.join(current_site_url(), 'resource', mp_aggr.resource.short_id)
                    display_string = "HydroShare resource that contains the Model Program:"
                    with dom_tags.p(display_string):
                        with dom_tags.span():
                            dom_tags.a(hs_res_url, href=hs_res_url)
                    aggr_path = "Aggregation in HydroShare resource that contains the Model Program:"
                    with dom_tags.p(aggr_path):
                        dom_tags.span(mp_aggr.aggregation_name, style="font-weight: bold;")
                else:
                    display_string = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                    dom_tags.p(display_string)
            else:
                dom_tags.p("Unspecified")

        metadata_json_div = dom_tags.div(cls="content-block")
        if self.metadata_json:
            metadata_schema = {}
            if self.logical_file.metadata_schema_json:
                metadata_schema = self.logical_file.metadata_schema_json
            with metadata_json_div:
                dom_tags.legend("Schema-based Metadata")
                schema_properties_key = 'properties'
                for k, v in self.metadata_json.items():
                    if type(v) not in (int, float, bool):
                        if isinstance(v, dict):
                            if not _dict_has_value(v):
                                continue
                        elif not v:
                            # v is either a str or a list, and empty
                            continue

                        k_title = k
                        if metadata_schema:
                            root_properties_schema_node = metadata_schema[schema_properties_key]
                            if k in root_properties_schema_node:
                                k_title = root_properties_schema_node[k]['title']
                        dom_tags.legend(k_title)
                    with dom_tags.div(cls="row"):
                        def display_json_meta_field(field_name, field_value):
                            value = ''
                            if isinstance(field_value, list):
                                # check if list items are dict type
                                if isinstance(field_value[0], dict):
                                    for item in field_value:
                                        display_dict_type_value(item)
                                elif field_value:
                                    value = ", ".join(field_value)
                            elif isinstance(field_value, str):
                                value = field_value.strip()
                            else:
                                # field_value is either a bool or a number
                                value = field_value
                            if value != '':
                                with dom_tags.div(cls="col-md-6"):
                                    dom_tags.p(field_name)
                                with dom_tags.div(cls="col-md-6"):
                                    dom_tags.p(value)

                        def display_dict_type_value(value):
                            for child_k, child_v in value.items():
                                child_k_title = child_k
                                if metadata_schema:
                                    child_properties_schema_node = root_properties_schema_node[k]
                                    if 'type' in child_properties_schema_node:
                                        if child_properties_schema_node['type'] == 'array':
                                            child_properties_schema_node = child_properties_schema_node['items']
                                    child_properties_schema_node = child_properties_schema_node[
                                        schema_properties_key]
                                    if child_k in child_properties_schema_node:
                                        child_k_title = child_properties_schema_node[child_k]['title']

                                display_json_meta_field(field_name=child_k_title, field_value=child_v)

                        if isinstance(v, dict):
                            display_dict_type_value(v)
                        else:
                            display_json_meta_field(field_name=k_title, field_value=v)

        html_string += executed_by_div.render()
        html_string += metadata_json_div.render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """generates html form code to edit metadata for this aggregation"""

        form_action = "/hsapi/_internal/{}/update-modelinstance-metadata/"
        form_action = form_action.format(self.logical_file.id)
        root_div = dom_tags.div("{% load crispy_forms_tags %}")
        base_div, context = super(ModelInstanceFileMetaData, self).get_html_forms(render=False)

        def get_schema_based_form():
            json_form_action = "/hsapi/_internal/{}/update-modelinstance-metadata-json/"
            json_form_action = json_form_action.format(self.logical_file.id)
            schema_div = dom_tags.div()
            with schema_div:
                with dom_tags.form(id="id-schema-based-form", action=json_form_action,
                                   method="post", enctype="multipart/form-data"):
                    with dom_tags.fieldset():
                        dom_tags.legend("Schema-based Metadata")
                        json_schema = json.dumps(self.logical_file.metadata_schema_json)
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
            invalid_schema = False
            if self.logical_file.metadata_schema_json:
                if self.metadata_json:
                    if self.executed_by and self.executed_by.metadata_schema_json:
                        # validate metadata against the schema in the linked model program
                        try:
                            jsonschema.Draft4Validator(self.executed_by.metadata_schema_json).validate(
                                self.metadata_json)
                        except jsonschema.ValidationError:
                            invalid_schema = True

            executed_by_div = dom_tags.div()
            with executed_by_div:
                dom_tags.label('Select a Model Program', fr="id_executed_by",
                               cls="control-label")
                with dom_tags.select(cls="form-control", id="id_executed_by", name="executed_by"):
                    dom_tags.option("Select a model program", value="0")
                    this_resource = self.logical_file.resource
                    for mp_aggr in this_resource.modelprogramlogicalfile_set.all():
                        option = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                        if self.executed_by:
                            if self.executed_by.id == mp_aggr.id:
                                dom_tags.option(option, selected="selected",
                                                value=mp_aggr.id)
                            else:
                                dom_tags.option(option, value=mp_aggr.id)
                        else:
                            dom_tags.option(option, value=mp_aggr.id)
                    if self.executed_by:
                        mp_aggr = self.executed_by
                        # check if the mp aggregation is from another resource (possible only in the case of
                        # migrated mi resource)
                        if self.logical_file.resource.short_id != mp_aggr.resource.short_id:
                            option = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                            dom_tags.option(option, selected="selected", value=mp_aggr.id)

                if self.executed_by:
                    mp_aggr = self.executed_by
                    # check if the mp aggregation is from another resource (possible only in the case of
                    # migrated mi resource)
                    if self.logical_file.resource.short_id != mp_aggr.resource.short_id:
                        hs_res_url = os.path.join(current_site_url(), 'resource', mp_aggr.resource.short_id)
                        display_string = "HydroShare resource that contains the Model Program:"
                        with dom_tags.p(display_string):
                            with dom_tags.span():
                                dom_tags.a(hs_res_url, href=hs_res_url)
                        aggr_path = "Aggregation in HydroShare resource that contains the Model Program:"
                        with dom_tags.p(aggr_path):
                            dom_tags.span(mp_aggr.aggregation_name, style="font-weight: bold;")

                        external_mp_aggr_msg = "Selected model program exists in a different resource. " \
                                               "With the current release of HydroShare, you can now move your Model " \
                                               "Program into the same resource as Model Instance."
                        dom_tags.p(external_mp_aggr_msg, cls="alert alert-info")
                if invalid_schema:
                    dom_tags.div("Metadata schema in the associated model program fails to validate existing metadata. "
                                 "Updating the schema from model program will lead to loss of all schema based "
                                 "metadata in this model instance.",
                                 cls="alert alert-danger", id="div-invalid-schema-message")
                if self.executed_by and self.executed_by.metadata_schema_json:
                    if DeepDiff(self.logical_file.metadata_schema_json, self.executed_by.metadata_schema_json):
                        schema_update_url = "/hsapi/_internal/{}/update-modelinstance-meta-schema/"
                        schema_update_url = schema_update_url.format(self.logical_file.id)
                        if invalid_schema:
                            btn_cls = "btn btn-danger btn-block btn-form-submit"
                        else:
                            btn_cls = "btn btn-primary btn-block btn-form-submit"
                        dom_tags.button("Update Metadata Schema from Model Program", type="button",
                                        id="btn-mi-schema-update", data_schema_update_url=schema_update_url,
                                        cls=btn_cls)
                if self.logical_file.metadata_schema_json:
                    dom_tags.button("Show/Hide Model Instance Metadata JSON Schema", type="button",
                                    cls="btn btn-success btn-block",
                                    data_toggle="collapse", data_target="#meta-schema")
                    mi_schema_div = dom_tags.div(cls="content-block collapse", id="meta-schema",
                                                 style="margin-top:10px; padding-bottom: 20px;")
                    with mi_schema_div:
                        json_schema = json.dumps(self.logical_file.metadata_schema_json, indent=4)
                        dom_tags.textarea(json_schema, readonly=True, rows='30', style="min-width: 100%;",
                                          cls="form-control")
                if self.executed_by and not self.executed_by.metadata_schema_json and \
                        not self.logical_file.metadata_schema_json:
                    missing_schema_msg = "Selected model program is missing metadata schema. With the current " \
                                         "release of HydroShare, you can now specify specific metadata schema " \
                                         "for a Model Program."
                    dom_tags.div(missing_schema_msg, cls="alert alert-info")

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

                invalid_metadata = False
                if self.logical_file.metadata_schema_json:
                    if self.metadata_json:
                        # validate metadata against the schema in model instance (self)
                        try:
                            jsonschema.Draft4Validator(self.logical_file.metadata_schema_json).validate(
                                self.metadata_json)
                        except jsonschema.ValidationError:
                            invalid_metadata = True

                    with dom_tags.div():
                        get_schema_based_form()

        template = Template(root_div.render())
        rendered_html = template.render(context)
        return rendered_html

    def get_rdf_graph(self):
        graph = super(ModelInstanceFileMetaData, self).get_rdf_graph()
        subject = self.rdf_subject()

        graph.add((subject, HSTERMS.includesModelOutput, Literal(self.has_model_output)))

        if self.executed_by:
            if self.executed_by:
                resource = self.logical_file.resource
                if resource.short_id != self.executed_by.resource.short_id:
                    # case of model instance resource migrated to composite resource where the
                    # model program aggregation can live in another resource
                    resource = self.executed_by.resource
                hs_res_url = os.path.join(current_site_url(), 'resource', resource.file_path)
                aggr_url = os.path.join(hs_res_url, self.executed_by.map_short_file_path) + '#aggregation'
                graph.add((subject, HSTERMS.executedByModelProgram, URIRef(aggr_url)))

        if self.logical_file.metadata_schema_json:
            graph.add((subject, HSTERMS.modelProgramSchema, URIRef(self.logical_file.schema_file_url)))

        if self.metadata_json:
            graph.add((subject, HSTERMS.modelProgramSchemaValues, URIRef(self.logical_file.schema_values_file_url)))

        return graph

    def ingest_metadata(self, graph):
        from ..utils import get_logical_file_by_map_file_path

        super(ModelInstanceFileMetaData, self).ingest_metadata(graph)
        subject = self.rdf_subject_from_graph(graph)

        has_model_output = graph.value(subject=subject, predicate=HSTERMS.includesModelOutput)
        if has_model_output:
            self.has_model_output = str(has_model_output).lower() == 'true'
            self.save()

        executed_by = graph.value(subject=subject, predicate=HSTERMS.executedByModelProgram)
        if executed_by:
            aggr_map_path = executed_by.split('/resource/', 1)[1].split("#")[0]
            mp_aggr = get_logical_file_by_map_file_path(self.logical_file.resource, ModelProgramLogicalFile,
                                                        aggr_map_path)
            self.executed_by = mp_aggr
            self.save()

        schema_file = graph.value(subject=subject, predicate=HSTERMS.modelProgramSchema)
        if schema_file:
            istorage = self.logical_file.resource.get_s3_storage()
            if istorage.exists(self.logical_file.schema_file_path):
                with istorage.download(self.logical_file.schema_file_path) as f:
                    json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                metadata_schema_json = json.loads(json_str)
                self.logical_file.metadata_schema_json = metadata_schema_json
                self.logical_file.save()

        schema_values_file = graph.value(subject=subject, predicate=HSTERMS.modelProgramSchemaValues)
        if schema_values_file:
            istorage = self.logical_file.resource.get_s3_storage()
            if istorage.exists(self.logical_file.schema_values_file_path):
                with istorage.download(self.logical_file.schema_values_file_path) as f:
                    json_bytes = f.read()
                json_str = json_bytes.decode('utf-8')
                metadata_schema_json = json.loads(json_str)
                self.metadata_json = metadata_schema_json
                self.save()


class ModelInstanceLogicalFile(NestedLogicalFileMixin, AbstractModelLogicalFile):
    """ One file or more than one file in a specific folder can be part of this aggregation """

    metadata = models.OneToOneField(ModelInstanceFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "Model Instance"

    @classmethod
    def create(cls, resource):
        # this custom method MUST be used to create an instance of this class
        mi_metadata = ModelInstanceFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=mi_metadata, resource=resource)

    @staticmethod
    def get_aggregation_display_name():
        return 'Model Instance Content: One or more files with specific metadata'

    @staticmethod
    def get_aggregation_term_label():
        return "Model Instance Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    @property
    def schema_values_short_file_path(self):
        """File path of the aggregation schema values file relative to {resource_id}/data/contents/
        """

        json_file_name = self.aggregation_name
        if "/" in json_file_name:
            json_file_name = os.path.basename(json_file_name)

        json_file_name, _ = os.path.splitext(json_file_name)

        json_file_name += AggregationMetaFilePath.SCHEAMA_JSON_VALUES_FILE_ENDSWITH.value

        if self.folder:
            file_folder = self.folder
        else:
            file_folder = self.files.first().file_folder
        if file_folder:
            json_file_name = os.path.join(file_folder, json_file_name)

        return json_file_name

    @property
    def schema_values_file_path(self):
        """Full path of the aggregation schema values json file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.schema_values_short_file_path)

    @property
    def schema_values_file_url(self):
        """URL to the aggregation metadata schema values json file
        """
        from hs_core.hydroshare.utils import current_site_url
        return "{}/resource/{}".format(current_site_url(), self.schema_values_file_path)

    def set_metadata_dirty(self):
        super(ModelInstanceLogicalFile, self).set_metadata_dirty()
        for child_aggr in self.get_children():
            child_aggr.set_metadata_dirty()

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelInstanceLogicalFile, self).create_aggregation_xml_documents(create_map_xml=create_map_xml)
        for child_aggr in self.get_children():
            child_aggr.create_aggregation_xml_documents(create_map_xml=create_map_xml)
        self.create_schema_values_json_file()

    def create_schema_values_json_file(self):
        """Creates aggregation schema values json file """

        if not self.metadata.metadata_json:
            return

        # create a temp dir where the json file will be temporarily saved before copying to S3
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_s3_storage()

        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)

        # create json schema file for the aggregation
        json_from_file_name = os.path.join(tmpdir, 'schema_values.json')
        try:
            with open(json_from_file_name, 'w') as out:
                json_schema = json.dumps(self.metadata.metadata_json, indent=4)
                out.write(json_schema)
            to_file_name = self.schema_values_file_path
            istorage.saveFile(json_from_file_name, to_file_name)
        finally:
            shutil.rmtree(tmpdir)

    def can_contain_aggregation(self, aggregation):
        if aggregation.is_model_instance and self.id == aggregation.id:
            # allow moving file/folder within the same aggregation
            return True

        if aggregation.is_model_instance or aggregation.is_model_program or aggregation.is_fileset:
            return False
        return True

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return "Model Instance"

    def add_resource_files_in_folder(self, resource, folder):
        """
        A helper for creating aggregation. Makes all resource files in a given folder and its
        sub folders as part of the aggregation/logical file type
        :param  resource:  an instance of CompositeResource
        :param  folder: folder from which all files need to be made part of this aggregation
        """

        # get all resource files that in folder *folder* and all its sub folders
        res_files = ResourceFile.list_folder(resource=resource, folder=folder, sub_folders=True)

        for res_file in res_files:
            if not res_file.has_logical_file:
                self.add_resource_file(res_file, set_metadata_dirty=False)
            else:
                logical_file = res_file.logical_file
                # fileset aggregation can't be part of model instance aggregation
                if logical_file.is_fileset:
                    # remove the fileset aggregation association with the resource file
                    res_file.logical_file_content_object = None
                    self.add_resource_file(res_file, set_metadata_dirty=False)
        if res_files:
            self.set_metadata_dirty()
            resource.cleanup_aggregations()
        return res_files

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(ModelInstanceLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.metadata.has_model_output = self.metadata.has_model_output
        # Note: though copying executed_by here, it will be reset by the copy_executed_by() function
        # if the executed_by model program aggregation exists in the source resource
        copy_of_logical_file.metadata.executed_by = self.metadata.executed_by
        copy_of_logical_file.metadata.metadata_json = self.metadata.metadata_json
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.folder = self.folder
        copy_of_logical_file.metadata_schema_json = self.metadata_schema_json
        copy_of_logical_file.save()
        return copy_of_logical_file

    def copy_executed_by(self, tgt_logical_file):
        """helper function to support creating copy or new version of a resource
        :param tgt_logical_file: an instance of ModelInstanceLogicalFile which has been
        created as part of creating a copy/new version of a resource
        """

        # if the linked model program exists in the same source resource
        # then we have to reset the executed_by for the tgt logical file to the copy of the
        # same model program aggregation that is now part of the copied resource
        if self.metadata.executed_by:
            src_executed_by = self.metadata.executed_by
            src_resource = self.resource
            src_mp_logical_files = src_resource.modelprogramlogicalfile_set.all()
            if src_executed_by in src_mp_logical_files:
                tgt_resource = tgt_logical_file.resource
                tgt_mp_logical_files = tgt_resource.modelprogramlogicalfile_set.all()
                for tgt_mp_logical_file in tgt_mp_logical_files:
                    if src_executed_by.aggregation_name == tgt_mp_logical_file.aggregation_name:
                        tgt_logical_file.metadata.executed_by = tgt_mp_logical_file
                        tgt_logical_file.metadata.save()
                        break

    def logical_delete(self, user, resource=None, delete_res_files=True, delete_meta_files=True):
        # super deletes files needed to delete the values file path
        if delete_meta_files:
            if resource is None:
                resource = self.resource
            istorage = resource.get_s3_storage()
            if istorage.exists(self.schema_values_file_path):
                istorage.delete(self.schema_values_file_path)
        super(ModelInstanceLogicalFile, self).logical_delete(
            user,
            resource=resource,
            delete_res_files=delete_res_files,
            delete_meta_files=delete_meta_files
        )

    def remove_aggregation(self):
        # super deletes files needed to delete the values file path
        istorage = self.resource.get_s3_storage()

        if istorage.exists(self.schema_values_file_path):
            istorage.delete(self.schema_values_file_path)
        super(ModelInstanceLogicalFile, self).remove_aggregation()


def _dict_has_value(dct):
    """helper to check if the dict contains at least one valid value"""
    for val in dct.values():
        if isinstance(val, str):
            if val.strip() != '':
                return True
        elif isinstance(val, list):
            if val:
                return True
        elif type(val) in (int, float, bool):
            return True
        elif isinstance(val, dict):
            return _dict_has_value(val)
    return False
