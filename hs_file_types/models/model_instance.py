import json
import os

import jsonschema
from deepdiff import DeepDiff
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.template import Template, Context
from dominate import tags as dom_tags
from rdflib import BNode, Literal, URIRef, RDF
from rdflib.namespace import Namespace, DC

from hs_core.hs_rdf import NAMESPACE_MANAGER, HSTERMS
from hs_core.hydroshare.utils import current_site_url
from hs_core.models import ResourceFile
from .base import NestedLogicalFileMixin
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
                dom_tags.legend("Schema Based Metadata")
                schema_properties_key = 'properties'
                for k, v in self.metadata_json.items():
                    if v:
                        if isinstance(v, dict):
                            if not _dict_has_value(v):
                                continue
                        k_title = k
                        if metadata_schema:
                            root_properties_schema_node = metadata_schema[schema_properties_key]
                            if k in root_properties_schema_node:
                                k_title = root_properties_schema_node[k]['title']
                        dom_tags.legend(k_title)
                    with dom_tags.div(cls="row"):
                        def add_obj_field(field_name, field_value):
                            value = ''
                            if isinstance(field_value, list):
                                if field_value:
                                    value = ", ".join(field_value)
                            elif isinstance(field_value, str):
                                value = field_value.strip()
                            else:
                                value = field_value
                            if value != '':
                                with dom_tags.div(cls="col-md-6"):
                                    dom_tags.p(field_name)
                                with dom_tags.div(cls="col-md-6"):
                                    dom_tags.p(value)
                        if v:
                            if isinstance(v, dict):
                                if not _dict_has_value(v):
                                    continue
                                for child_k, child_v in v.items():
                                    child_k_title = child_k
                                    if metadata_schema:
                                        child_properties_schema_node = root_properties_schema_node[k]
                                        child_properties_schema_node = child_properties_schema_node[
                                            schema_properties_key]
                                        if child_k in child_properties_schema_node:
                                            child_k_title = child_properties_schema_node[child_k]['title']

                                    add_obj_field(field_name=child_k_title, field_value=child_v)
                            else:
                                add_obj_field(field_name=k_title, field_value=v)

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
                        dom_tags.legend("Schema Based Metadata")
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
                    for mp_aggr in this_resource.get_model_program_aggregations():
                        option = "{} ({})".format(mp_aggr.aggregation_name, mp_aggr.dataset_name)
                        if self.executed_by:
                            if self.executed_by.id == mp_aggr.id:
                                dom_tags.option(option, selected="selected",
                                                value=mp_aggr.id)
                            else:
                                dom_tags.option(option, value=mp_aggr.id)
                        else:
                            dom_tags.option(option, value=mp_aggr.id)
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
                    dom_tags.button("Show Model Instance Metadata JSON Schema", type="button",
                                    cls="btn btn-success btn-block",
                                    data_toggle="collapse", data_target="#meta-schema")
                    mi_schema_div = dom_tags.div(cls="content-block collapse", id="meta-schema",
                                                 style="margin-top:10px; padding-bottom: 20px;")
                    with mi_schema_div:
                        json_schema = json.dumps(self.logical_file.metadata_schema_json, indent=4)
                        dom_tags.textarea(json_schema, readonly=True, rows='30', style="min-width: 100%;",
                                          cls="form-control")
                if self.executed_by and not self.executed_by.metadata_schema_json:
                    dom_tags.div("Selected model program is missing metadata schema", cls="alert alert-danger")

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

        def find_schema_field_value(field_path, schema_dict):
            keys = field_path.split(".")
            element_value = schema_dict
            for key in keys:
                try:
                    element_value = element_value[key]
                except KeyError:
                    if key != 'description':
                        raise KeyError
                    return None
            return element_value

        def add_sub_element(sub_element_node, sub_element_value):
            """adds the element node only if the element has a value"""
            sub_value = ''
            if isinstance(sub_element_value, str):
                if len(sub_element_value.strip()) > 0:
                    sub_value = sub_element_value
            elif isinstance(sub_element_value, list):
                if sub_element_value:
                    sub_value = ", ".join(sub_element_value)
            else:
                sub_value = sub_element_value
            if sub_value != '':
                graph.add((sub_element_node, RDF.value, Literal(sub_value)))
                return True
            return False

        valid_schema = False
        resource = self.logical_file.resource
        if self.metadata_json:
            try:
                jsonschema.Draft4Validator(self.logical_file.metadata_schema_json).validate(
                    self.metadata_json)
                valid_schema = True
            except jsonschema.ValidationError:
                valid_schema = False

        # need to add this additional namespace for encoding the schema based metadata
        # xmlns="http://hydroshare.org/resource/<resourceID>/"
        res_xmlns = os.path.join(current_site_url(), 'resource', resource.short_id) + "/"
        ns_prefix = None
        NS_META_SCHEMA = Namespace(res_xmlns)
        NAMESPACE_MANAGER.bind(prefix=ns_prefix, namespace=NS_META_SCHEMA, override=False)
        graph.namespace_manager = NAMESPACE_MANAGER

        model_meta_node = BNode()
        graph.add((subject, NS_META_SCHEMA.modelSpecificMetadata, model_meta_node))
        model_title = ""
        if self.logical_file.metadata_schema_json:
            model_title = self.logical_file.metadata_schema_json.get('title', "")
        graph.add((model_meta_node, DC.title, Literal(model_title)))
        if self.has_model_output:
            includes_output = 'true'
        else:
            includes_output = 'false'
        graph.add((model_meta_node, HSTERMS.includesModelOutput, Literal(includes_output)))

        if self.executed_by:
            if self.executed_by:
                resource = self.logical_file.resource
                hs_res_url = os.path.join(current_site_url(), 'resource', resource.file_path)
                aggr_url = os.path.join(hs_res_url, self.executed_by.map_short_file_path) + '#aggregation'
                graph.add((model_meta_node, HSTERMS.executedByModelProgram, URIRef(aggr_url)))

        if valid_schema:
            metadata_dict = self.metadata_json
            model_prop_node = BNode()
            graph.add((model_meta_node, NS_META_SCHEMA.modelProperties, model_prop_node))
            meta_schema_dict = self.logical_file.metadata_schema_json
            meta_schema_dict_properties = meta_schema_dict.get("properties")
            for k, v in metadata_dict.items():
                # skip key (element) that is missing a valid value
                if v:
                    if isinstance(v, dict):
                        if not _dict_has_value(v):
                            continue
                    elif isinstance(v, str):
                        if str(v).strip() == '':
                            continue
                elif not isinstance(v, bool):
                    continue

                k_element_node = BNode()
                k_predicate = NS_META_SCHEMA.term('{}'.format(k))
                graph.add((model_prop_node, k_predicate, k_element_node))
                element_path_root = "{}".format(k)
                element_path_title = "{}.{}".format(element_path_root, 'title')
                element_title_value = find_schema_field_value(field_path=element_path_title,
                                                              schema_dict=meta_schema_dict_properties)
                graph.add((k_element_node, DC.title, Literal(element_title_value)))
                element_path_desc = "{}.{}".format(element_path_root, 'description')
                element_desc_value = find_schema_field_value(field_path=element_path_desc,
                                                             schema_dict=meta_schema_dict_properties)
                if element_desc_value is not None:
                    graph.add((k_element_node, DC.description, Literal(element_desc_value)))

                if isinstance(v, dict) and v:
                    k_element_prop_node = BNode()
                    predicate = NS_META_SCHEMA.term('{}Properties'.format(k))
                    graph.add((k_element_node, predicate, k_element_prop_node))
                    sub_element_path_root = "{}.properties".format(element_path_root)
                    for k_sub, v_sub in v.items():
                        k_sub_element_node = BNode()
                        k_sub_predicate = NS_META_SCHEMA.term('{}'.format(k_sub))
                        graph.add((k_element_prop_node, k_sub_predicate, k_sub_element_node))
                        k_sub_path_title = "{}.{}.{}".format(sub_element_path_root, k_sub, 'title')
                        k_sub_title_value = find_schema_field_value(field_path=k_sub_path_title,
                                                                    schema_dict=meta_schema_dict_properties)
                        graph.add((k_sub_element_node, DC.title, Literal(k_sub_title_value)))
                        k_sub_path_desc = "{}.{}.{}".format(sub_element_path_root, k_sub, 'description')
                        k_sub_desc_value = find_schema_field_value(field_path=k_sub_path_desc,
                                                                   schema_dict=meta_schema_dict_properties)
                        if k_sub_desc_value is not None:
                            graph.add((k_sub_element_node, DC.description, Literal(k_sub_desc_value)))

                        added = add_sub_element(k_sub_element_node, v_sub)
                        if not added:
                            # remove the sub element node from the graph
                            for _, pred, obj in graph.triples((k_sub_element_node, None, None)):
                                graph.remove((k_sub_element_node, pred, obj))
                            graph.remove((k_element_prop_node, None, k_sub_element_node))
                else:
                    added = add_sub_element(k_element_node, v)
                    if not added:
                        graph.remove((model_prop_node, None, k_element_node))

        return graph


class ModelInstanceLogicalFile(NestedLogicalFileMixin, AbstractModelLogicalFile):
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
    def get_aggregation_term_label():
        return "Model Instance Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "ModelInstanceAggregation"

    # used in discovery faceting to aggregate native and composite content types
    def get_discovery_content_type(self):
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types).
        """
        return self.model_instance_type

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
                self.add_resource_file(res_file)
            else:
                logical_file = res_file.logical_file
                if logical_file.is_fileset:
                    res_file.logical_file_content_object = None
                    self.add_resource_file(res_file)
        return res_files

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(ModelInstanceLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()

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


def _dict_has_value(dct):
    """helper to check if the dict contains at least one valid value"""
    for val in dct.values():
        if isinstance(val, str):
            if val.strip() != '':
                return True
        elif isinstance(val, list):
            if val:
                return True
        elif isinstance(val, dict):
            return _dict_has_value(val)
    return False
