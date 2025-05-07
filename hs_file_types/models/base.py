import copy
import logging
import os
import random
import shutil
from uuid import uuid4

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField, ArrayField
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.forms.models import model_to_dict
from dominate.tags import div, legend, table, tr, tbody, thead, td, th, \
    span, a, form, button, label, textarea, h4, h3, _input, ul, li, p
from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from mezzanine.conf import settings
from rdflib import Literal, Namespace, BNode, URIRef, Graph
from rdflib.namespace import DC

from hs_core.hs_rdf import RDFS1, HSTERMS, RDF_MetaData_Mixin
from hs_core.hydroshare.resource import delete_resource_file
from hs_core.hydroshare.utils import current_site_url, get_resource_file_by_id, \
    set_dirty_bag_flag, add_file_to_resource, resource_modified, get_file_from_s3
from hs_core.models import ResourceFile, AbstractMetaDataElement, Coverage
from hs_core.signals import post_remove_file_aggregation
from ..enums import AggregationMetaFilePath


class NestedLogicalFileMixin(object):
    """a mixin for any logical file class that needs to contain other aggregations"""

    def get_children(self):
        """Return a list of aggregation that this (self) aggregation contains"""
        child_aggregations = []
        for aggr in self.resource.logical_files:
            if aggr != self:
                parent_aggr = aggr.get_parent()
                if parent_aggr is not None and parent_aggr == self:
                    child_aggregations.append(aggr)

        return child_aggregations

    def update_temporal_coverage(self):
        """Updates temporal coverage of this aggregation based on the contained temporal
        coverages of aggregations (file type). Note: This action will overwrite any existing
        fileset temporal coverage data.
        """

        from ..utils import update_target_temporal_coverage

        update_target_temporal_coverage(self)

    def update_spatial_coverage(self):
        """Updates spatial coverage of this aggregation based on the contained spatial
        coverages of aggregations (file type). Note: This action will overwrite any existing
        fileset spatial coverage data.
        """
        from ..utils import update_target_spatial_coverage

        update_target_spatial_coverage(self)

    def update_coverage(self):
        """Update this aggregation's  spatial and temporal coverage based on the corresponding coverages
        from all the contained aggregations (logical file) only if this aggregation's coverage is not
        already set"""

        # update spatial coverage only if there is no spatial coverage already
        if self.metadata.spatial_coverage is None:
            self.update_spatial_coverage()

        # update temporal coverage only if there is no temporal coverage already
        if self.metadata.temporal_coverage is None:
            self.update_temporal_coverage()

    def save_metadata_json_file(self):
        """Creates aggregation metadata json file and saves it to S3 """
        for child_aggr in self.get_children():
            child_aggr.save_metadata_json_file()


class AbstractFileMetaData(models.Model, RDF_MetaData_Mixin):
    """ base class for HydroShare file type metadata """

    # one temporal coverage and one spatial coverage
    coverages = GenericRelation(Coverage)
    # key/value metadata (additional metadata)
    extra_metadata = HStoreField(default=dict)

    # keywords
    keywords = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=list)
    # to track if any metadata element has been modified to trigger file update
    is_dirty = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Overriding the django model delete() here so that subclasses can do further
        override if needed"""
        super(AbstractFileMetaData, self).delete()

    @classmethod
    def get_metadata_model_classes(cls):
        return {'coverage': Coverage}

    def get_metadata_elements(self):
        """returns a list of all metadata elements (instances of AbstractMetaDataElement)
         associated with this file type metadata object.
        """
        return list(self.coverages.all())

    def dict(self):
        dict = {}
        metadata = self.get_metadata_elements()
        for element in metadata:
            dict.update(element.dict)
        return dict

    def delete_all_elements(self):
        self.coverages.all().delete()
        self.extra_metadata = {}
        self.keywords = []
        self.save()

    def to_json(self):
        """Return the metadata in JSON format - uses schema.org terms where possible and the rest
        terms are based on hsterms."""

        json_dict = {
            "context": [
                "https://schema.org/",
                {
                    "hsterms": "https://hydroshare.org/terms/"
                }
            ],
            "type": "Dataset"
        }
        for coverage in self.coverages.all():
            json_dict.update(coverage.to_json())
        if self.keywords:
            json_dict.update({"keywords": self.keywords})
        additional_metadata = {"hsterms:additionalMetadata": []}
        for key, value in self.extra_metadata.items():
            as_property_value = {
                "type": "PropertyValue",
                "name": key,
                "value": value
            }
            additional_metadata["hsterms:additionalMetadata"].append(as_property_value)
        if additional_metadata["hsterms:additionalMetadata"]:
            json_dict.update(additional_metadata)

        associated_media = {"associatedMedia": []}
        for res_file in self.logical_file.files.all():
            media_object = {
                "type": "MediaObject",
                "name": res_file.file_name,
                "contentUrl": os.path.join(current_site_url(), 'resource', res_file.storage_path),
                "contentSize": res_file.size,
                "sha256": res_file.checksum,
                "encodingFormat": res_file.mime_type,
            }
            associated_media["associatedMedia"].append(media_object)
        if associated_media["associatedMedia"]:
            json_dict.update(associated_media)

        child_aggr_has_parts = []
        for child_aggr in self.logical_file.get_children():
            child_aggr_has_parts.append(child_aggr.metadata_json_file_url_path)
        if child_aggr_has_parts:
            if 'hasPart' not in json_dict:
                json_dict['hasPart'] = [child_aggr_has_parts]
            else:
                json_dict['hasPart'].extend(child_aggr_has_parts)

        parent_aggr = self.logical_file.get_parent()
        if parent_aggr is not None:
            json_dict['isPartOf'] = [parent_aggr.metadata_json_file_url_path]
        else:
            json_dict['isPartOf'] = [self.logical_file.resource.metadata_json_file_url_path]

        return json_dict

    def get_html(self, include_extra_metadata=True, **kwargs):
        """Generates html for displaying all metadata elements associated with this logical file.
        Subclass must override to include additional html for additional metadata it supports.
        :param include_extra_metadata: a flag to control if necessary html for displaying key/value
        metadata will be included
        """

        root_div = div()
        with root_div:
            h3("{} Content Metadata".format(self.logical_file.data_type), style="margin-bottom: 20px;")
            if self.logical_file.data_type == "CSV":
                csv_metadata = self.logical_file.metadata
                csv_metadata.get_preview_data_html()

        if self.logical_file.dataset_name:
            root_div.add(self.get_dataset_name_html())
        if self.keywords:
            root_div.add(self.get_keywords_html())
        if self.extra_metadata and include_extra_metadata:
            root_div.add(self.get_key_value_metadata_html())

        return root_div.render()

    def get_dataset_name_html(self):
        """generates html for viewing dataset name (title)"""
        if self.logical_file.dataset_name:
            dataset_name_div = div(cls="content-block")
            with dataset_name_div:
                legend("Title")
                p(self.logical_file.dataset_name)
            return dataset_name_div

    def get_keywords_html(self):
        """generates html for viewing keywords"""
        keywords_div = div(cls='content-block')
        if self.keywords:
            with keywords_div:
                legend('Keywords')
                with div(cls="tags"):
                    with ul(id="list-keywords-file-type", cls="tag-list custom-well"):
                        for kw in self.keywords:
                            with li():
                                a(kw, cls="tag",
                                  href="/search/?q=&selected_facets=subject_exact:" + kw)
        return keywords_div

    def get_key_value_metadata_html(self):
        """generates html for viewing key/vale extra metadata"""
        extra_metadata_div = div()
        if self.extra_metadata:
            extra_metadata_div = div(cls="content-block")
            with extra_metadata_div:
                legend('Additional Metadata')
                with table(cls="hs-table table dataTable no-footer", style="width: 100%"):
                    with thead():
                        with tr(cls="header-row"):
                            th("Key")
                            th("Value")
                    with tbody():
                        for k, v in list(self.extra_metadata.items()):
                            with tr(data_key=k):
                                td(k)
                                td(v)
        return extra_metadata_div

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """generates html forms for all the metadata elements associated with this logical file
        type
        :param dataset_name_form: If True then a form for editing dataset_name (title) attribute is
        included
        :param  temporal_coverage: if True then form elements for editing temporal coverage are
        included
        """

        skip_coverage = kwargs.get('skip_coverage', False)
        root_div = div()
        with root_div:
            h3("{} Content Metadata".format(self.logical_file.data_type), style="margin-bottom: 20px;")
            if self.logical_file.data_type == "CSV":
                csv_metadata = self.logical_file.metadata
                csv_metadata.get_preview_data_html()
            if dataset_name_form:
                self.get_dataset_name_form()

            self.get_keywords_html_form()

            self.get_extra_metadata_html_form()
            if not skip_coverage:
                if temporal_coverage:
                    # for aggregation that contains other aggregations with temporal data,
                    # show option to update temporal coverage from contained aggregations
                    if self.logical_file.has_children_temporal_data:
                        with self.get_temporal_coverage_html_form():
                            with div():
                                button("Set temporal coverage from folder contents",
                                       type="button",
                                       cls="btn btn-primary",
                                       id="btn-update-aggregation-temporal-coverage")
                    else:
                        self.get_temporal_coverage_html_form()
        return root_div

    def get_keywords_html_form(self):
        keywords_div = div(cls="content-block", id="filetype-keywords")
        action = "/hsapi/_internal/{0}/{1}/add-file-keyword-metadata/"
        action = action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        delete_action = "/hsapi/_internal/{0}/{1}/delete-file-keyword-metadata/"
        delete_action = delete_action.format(self.logical_file.__class__.__name__,
                                             self.logical_file.id)
        with keywords_div:
            legend("Keywords")
            with form(id="id-keywords-filetype", action=action, method="post",
                      enctype="multipart/form-data"):
                _input(id="id-delete-keyword-filetype-action", type="hidden",
                       value=delete_action)
                with div(cls="tags"):
                    with div(id="add-keyword-wrapper", cls="input-group"):
                        _input(id="txt-keyword-filetype", cls="form-control",
                               placeholder="keyword",
                               type="text", name="keywords")
                        with span(cls="input-group-btn"):
                            a("Add", id="btn-add-keyword-filetype", cls="btn btn-success",
                              type="button")
                with ul(id="lst-tags-filetype", cls="custom-well tag-list"):
                    for kw in self.keywords:
                        with li(cls="tag"):
                            span(kw)
                            with a():
                                span(cls="glyphicon glyphicon-remove-circle icon-remove")
            p("Duplicate. Keywords not added.", id="id-keywords-filetype-msg",
              cls="text-danger small", style="display: none;")

    def get_spatial_coverage_form(self, allow_edit=False):
        return Coverage.get_spatial_html_form(resource=None, element=self.spatial_coverage,
                                              allow_edit=allow_edit, file_type=True)

    def get_temporal_coverage_form(self, allow_edit=True):
        return Coverage.get_temporal_html_form(resource=None, element=self.temporal_coverage,
                                               file_type=True, allow_edit=allow_edit)

    def get_extra_metadata_html_form(self):
        def get_add_keyvalue_button():
            add_key_value_btn = a(cls="btn btn-success", type="button", data_toggle="modal",
                                  data_target="#add-keyvalue-filetype-modal",
                                  style="margin-bottom:20px;")
            with add_key_value_btn:
                with span(cls="glyphicon glyphicon-plus"):
                    span("Add Key/Value", cls="button-label")
            return add_key_value_btn

        if self.extra_metadata:
            root_div_extra = div(id="filetype-extra-metadata")
            with root_div_extra:
                legend('Additional Metadata')
                get_add_keyvalue_button()
                with table(cls="hs-table table dataTable no-footer",
                           style="width: 100%"):
                    with thead():
                        with tr(cls="header-row"):
                            th("Key")
                            th("Value")
                            th("Edit/Remove")
                    with tbody():
                        counter = 0
                        for k, v in list(self.extra_metadata.items()):
                            counter += 1
                            with tr(data_key=k):
                                td(k)
                                td(v)
                                with td():
                                    span(data_toggle="modal", data_placement="auto", title="Edit",
                                         cls="btn-edit-icon glyphicon glyphicon-pencil "
                                             "icon-blue table-icon",
                                         data_target="#edit-keyvalue-filetype-modal"
                                                     "-{}".format(counter))
                                    span(data_toggle="modal", data_placement="auto",
                                         title="Remove",
                                         cls="btn-remove-icon glyphicon glyphicon-trash "
                                             "btn-remove table-icon",
                                         data_target="#delete-keyvalue-filetype-modal"
                                                     "-{}".format(counter))

                self._get_add_key_value_modal_form()
                self._get_edit_key_value_modal_forms()
                self._get_delete_key_value_modal_forms()
            return root_div_extra
        else:
            root_div_extra = div(id="filetype-extra-metadata", cls="content-block")
            with root_div_extra:
                legend('Additional Metadata')
                get_add_keyvalue_button()
                self._get_add_key_value_modal_form()
            return root_div_extra

    def get_temporal_coverage_html_form(self):
        # Note: When using this form layout the context variable 'temp_form' must be
        # set prior to calling the template.render(context)
        root_div = div(id="temporal-coverage-filetype", cls='content-block')
        with root_div:
            with form(id="id-coverage-temporal-file-type", action="{{ temp_form.action }}",
                      method="post", enctype="multipart/form-data"):
                div("{% crispy temp_form %}")
                with div(cls="row", style="margin-top:10px;"):
                    with div(cls="col-md-offset-10 col-xs-offset-6 "
                                 "col-md-2 col-xs-6"):
                        button("Save changes", type="button",
                               cls="btn btn-primary pull-right",
                               style="display: none;")
        return root_div

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            # required metadata is missing
            return False
        return True

    @classmethod
    def get_supported_element_names(cls):
        return ['Coverage']

    def get_required_missing_elements(self, *args):
        return []

    @property
    def has_metadata(self):
        if not self.coverages.all() and not self.extra_metadata \
                and not self.logical_file.dataset_name:
            return False
        return True

    @property
    def spatial_coverage(self):
        return self.coverages.exclude(type='period').first()

    @property
    def temporal_coverage(self):
        return self.coverages.filter(type='period').first()

    def rdf_subject(self):
        return Namespace("{}/resource/{}#".format(current_site_url(), self.logical_file.map_file_path)).aggregation

    def rdf_metadata_subject(self):
        return URIRef("{}/resource/{}#".format(current_site_url(), self.logical_file.metadata_file_path))

    def rdf_type(self):
        return getattr(HSTERMS, self.logical_file.get_aggregation_type_name())

    def ingest_metadata(self, graph):
        super(AbstractFileMetaData, self).ingest_metadata(graph)
        subject = self.rdf_subject_from_graph(graph)

        title = graph.value(subject=subject, predicate=DC.title)
        if title:
            self.logical_file.dataset_name = title
            self.logical_file.save()
        for object in graph.objects(subject=subject, predicate=DC.subject):
            self.keywords.append(object.value)
        extra_metadata = {}
        for o in graph.objects(subject=subject, predicate=HSTERMS.extendedMetadata):
            key = graph.value(subject=o, predicate=HSTERMS.key).value
            value = graph.value(subject=o, predicate=HSTERMS.value).value
            extra_metadata[key] = value
        self.extra_metadata = copy.deepcopy(extra_metadata)

        self.save()

    def get_rdf_graph(self):
        graph = super(AbstractFileMetaData, self).get_rdf_graph()

        resource = self.logical_file.resource
        subject = self.rdf_subject()
        # add aggregation title
        if self.logical_file.dataset_name:
            graph.add((subject, DC.title, Literal(self.logical_file.dataset_name)))

        # add aggregation type
        aggregation_type = self.logical_file.get_aggregation_type_name()
        hsterms_aggregation_type = getattr(HSTERMS, aggregation_type)
        graph.add((subject, DC.type, hsterms_aggregation_type))

        # add lang element
        resource.metadata.language.rdf_triples(subject, graph)

        # add rights element
        resource.metadata.rights.rdf_triples(subject, graph)

        # add keywords
        for kw in self.keywords:
            graph.add((subject, DC.subject, Literal(kw)))

        # add any key/value metadata items
        if len(self.extra_metadata) > 0:
            for key, value in list(self.extra_metadata.items()):
                extendedMetadata = BNode()
                graph.add((subject, HSTERMS.extendedMetadata, extendedMetadata))
                graph.add((extendedMetadata, HSTERMS.key, Literal(key)))
                graph.add((extendedMetadata, HSTERMS.value, Literal(value)))

        TYPE_SUBJECT = getattr(Namespace("{}/terms/".format(current_site_url())), aggregation_type)
        graph.add((TYPE_SUBJECT, RDFS1.label, Literal(self.logical_file.get_aggregation_display_name())))
        graph.add((TYPE_SUBJECT, RDFS1.isDefinedBy, URIRef(HSTERMS)))
        return graph

    def create_element(self, element_model_name, **kwargs):
        resource = self.logical_file.resource
        if resource.raccess.published:
            raise ValidationError("Aggregation metadata editing is not allowed for a published resource")

        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        self.is_dirty = True

        if element_model_name.lower() == "coverage":
            aggr = element.metadata.logical_file
            # aggregation won't have resource files in case of coverage element being
            # created as part of copying a resource that supports logical file
            # types - in that case no need for updating resource level coverage
            if aggr.files.all().count() > 0:
                resource = aggr.resource
                resource.update_coverage()

            # if the aggregation (logical file) for which coverage data is created
            # has a parent aggregation then coverage needs to be updated for that
            # parent aggregation except in the case of metadata element being created as
            # part of copying a resource.
            # aggregation won't have resource files when copying a resource
            if aggr.files.all().count() > 0:
                parent_aggr = aggr.get_parent()
                if parent_aggr is not None:
                    parent_aggr.update_coverage()
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        resource = self.logical_file.resource
        if resource.raccess.published:
            raise ValidationError("Aggregation metadata editing is not allowed for a published resource")
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)
        self.is_dirty = True
        self.save()
        if element_model_name.lower() == "coverage":
            element = model_type.model_class().objects.get(id=element_id)
            resource.update_coverage()

            # if the aggregation (logical file) for which coverage data is updated
            # has a parent aggregation then coverage needs to be updated for that
            # parent aggregation
            aggr = element.metadata.logical_file
            parent_aggr = aggr.get_parent()
            if parent_aggr is not None:
                parent_aggr.update_coverage()

    def delete_element(self, element_model_name, element_id):
        resource = self.logical_file.resource
        if resource.raccess.published:
            raise ValidationError("Aggregation metadata editing is not allowed for a published resource")
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)
        self.is_dirty = True
        self.save()

    def get_element(self, element_model_name, element_id):
        """Gets a metadata element record based on name of the metadata element and id."""

        model_type = self._get_metadata_element_model_type(element_model_name)
        return model_type.model_class().objects.get(id=element_id)

    def _get_metadata_element_model_type(self, element_model_name):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported metadata elements for %s."
                                  % (element_model_name, type(self)))

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label=self.model_app_label,
                                                 model=element_model_name)
        except ObjectDoesNotExist:
            try:
                model_type = ContentType.objects.get(app_label='hs_core',
                                                     model=element_model_name)
            except ObjectDoesNotExist:
                raise ValidationError(unsupported_element_error)

        if not issubclass(model_type.model_class(), AbstractMetaDataElement):
            raise ValidationError(unsupported_element_error)

        return model_type

    def _is_valid_element(self, element_name):
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements

    @classmethod
    def validate_element_data(cls, request, element_name):
        """Subclass must implement this function to validate data for for the
        specified metadata element (element_name)"""
        raise NotImplementedError

    def get_dataset_name_form(self):
        form_action = "/hsapi/_internal/{0}/{1}/update-filetype-dataset-name/"
        form_action = form_action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        root_div = div()
        dataset_name = self.logical_file.dataset_name if self.logical_file.dataset_name else ""
        with root_div:
            with form(action=form_action, id="filetype-dataset-name",
                      method="post", enctype="multipart/form-data"):
                div("{% csrf_token %}")
                with div(cls="form-group"):
                    with div(cls="control-group"):
                        legend('Title')
                        with div(cls="controls"):
                            _input(value=dataset_name,
                                   cls="form-control input-sm textinput textInput",
                                   id="file_dataset_name", maxlength="250",
                                   name="dataset_name", type="text")
                with div(cls="row", style="margin-top:10px;"):
                    with div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                               style="display: none;", type="button")
        return root_div

    def _get_add_key_value_modal_form(self):
        form_action = "/hsapi/_internal/{0}/{1}/update-file-keyvalue-metadata/"
        form_action = form_action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        modal_div = div(cls="modal fade", id="add-keyvalue-filetype-modal", tabindex="-1",
                        role="dialog", aria_labelledby="add-key-value-metadata",
                        aria_hidden="true")
        with modal_div:
            with div(cls="modal-dialog", role="document"):
                with div(cls="modal-content"):
                    with form(action=form_action, id="add-keyvalue-filetype-metadata",
                              method="post", enctype="multipart/form-data"):
                        div("{% csrf_token %}")
                        with div(cls="modal-header"):
                            button("x", type="button", cls="close", data_dismiss="modal",
                                   aria_hidden="true")
                            h4("Add Key/Value Metadata", cls="modal-title",
                               id="add-key-value-metadata")
                        with div(cls="modal-body"):
                            with div(cls="form-group"):
                                with div(cls="control-group"):
                                    label("Key", cls="control-label requiredField",
                                          fr="file_extra_meta_name")
                                    with div(cls="controls"):
                                        _input(cls="form-control input-sm textinput textInput",
                                                   id="file_extra_meta_name", maxlength="100",
                                                   name="name", type="text")
                                with div(cls="control-group"):
                                    label("Value", cls="control-label requiredField",
                                          fr="file_extra_meta_value")
                                    with div(cls="controls"):
                                        textarea(cls="form-control input-sm textarea",
                                                 cols="40", rows="10",
                                                 id="file_extra_meta_value",
                                                 style="resize: vertical;",
                                                 name="value", type="text")
                        with div(cls="modal-footer"):
                            button("Cancel", type="button", cls="btn btn-default",
                                   data_dismiss="modal")
                            button("OK", type="button", cls="btn btn-primary",
                                   id="btn-confirm-add-metadata")  # TODO: TESTING
        return modal_div

    def _get_edit_key_value_modal_forms(self):
        # TODO: See if can use one modal dialog to edit any pair of key/value
        form_action = "/hsapi/_internal/{0}/{1}/update-file-keyvalue-metadata/"
        form_action = form_action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        counter = 0
        root_div = div(id="edit-keyvalue-filetype-modals")
        with root_div:
            for k, v in list(self.extra_metadata.items()):
                counter += 1
                modal_div = div(cls="modal fade",
                                id="edit-keyvalue-filetype-modal-{}".format(counter),
                                tabindex="-1",
                                role="dialog", aria_labelledby="edit-key-value-metadata",
                                aria_hidden="true")
                with modal_div:
                    with div(cls="modal-dialog", role="document"):
                        with div(cls="modal-content"):
                            form_id = "edit-keyvalue-filetype-metadata-{}".format(counter)
                            with form(action=form_action,
                                      id=form_id, data_counter="{}".format(counter),
                                      method="post", enctype="multipart/form-data"):
                                div("{% csrf_token %}")
                                with div(cls="modal-header"):
                                    button("x", type="button", cls="close", data_dismiss="modal",
                                           aria_hidden="true")
                                    h4("Update Key/Value Metadata", cls="modal-title",
                                       id="edit-key-value-metadata")
                                with div(cls="modal-body"):
                                    with div(cls="form-group"):
                                        with div(cls="control-group"):
                                            label("Key(Original)",
                                                  cls="control-label requiredField",
                                                  fr="file_extra_meta_key_original")
                                            with div(cls="controls"):
                                                _input(value=k, readonly="readonly",
                                                       cls="form-control input-sm textinput "
                                                       "textInput",
                                                       id="file_extra_meta_key_original",
                                                       maxlength="100",
                                                       name="key_original", type="text")
                                        with div(cls="control-group"):
                                            label("Key", cls="control-label requiredField",
                                                  fr="file_extra_meta_key")
                                            with div(cls="controls"):
                                                _input(value=k,
                                                       cls="form-control input-sm textinput "
                                                       "textInput",
                                                       id="file_extra_meta_key", maxlength="100",
                                                       name="key", type="text")
                                        with div(cls="control-group"):
                                            label("Value", cls="control-label requiredField",
                                                  fr="file_extra_meta_value")
                                            with div(cls="controls"):
                                                textarea(v,
                                                         cls="form-control input-sm textarea",
                                                         cols="40", rows="10",
                                                         id="file_extra_meta_value",
                                                         style="resize: vertical;",
                                                         name="value", type="text")
                                with div(cls="modal-footer"):
                                    button("Cancel", type="button", cls="btn btn-default",
                                           data_dismiss="modal")
                                    button("OK", id="btn-confirm-edit-key-value",
                                           type="button", cls="btn btn-primary")
            return root_div

    def _get_delete_key_value_modal_forms(self):
        form_action = "/hsapi/_internal/{0}/{1}/delete-file-keyvalue-metadata/"
        form_action = form_action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        counter = 0
        root_div = div(id="delete-keyvalue-filetype-modals")
        with root_div:
            for k, v in list(self.extra_metadata.items()):
                counter += 1
                modal_div = div(cls="modal fade",
                                id="delete-keyvalue-filetype-modal-{}".format(counter),
                                tabindex="-1",
                                role="dialog", aria_labelledby="delete-key-value-metadata",
                                aria_hidden="true")
                with modal_div:
                    with div(cls="modal-dialog", role="document"):
                        with div(cls="modal-content"):
                            form_id = "delete-keyvalue-filetype-metadata-{}".format(counter)
                            with form(action=form_action,
                                      id=form_id,
                                      method="post", enctype="multipart/form-data"):
                                div("{% csrf_token %}")
                                with div(cls="modal-header"):
                                    button("x", type="button", cls="close", data_dismiss="modal",
                                           aria_hidden="true")
                                    h4("Confirm to Delete Key/Value Metadata", cls="modal-title",
                                       id="delete-key-value-metadata")
                                with div(cls="modal-body"):
                                    with div(cls="form-group"):
                                        with div(cls="control-group"):
                                            label("Key", cls="control-label requiredField",
                                                  fr="file_extra_meta_name")
                                            with div(cls="controls"):
                                                _input(cls="form-control input-sm textinput "
                                                       "textInput", value=k,
                                                           id="file_extra_meta_key", maxlength="100",
                                                           name="key", type="text", readonly="readonly")
                                        with div(cls="control-group"):
                                            label("Value", cls="control-label requiredField",
                                                  fr="file_extra_meta_value")
                                            with div(cls="controls"):
                                                textarea(v, cls="form-control input-sm textarea",
                                                         cols="40", rows="10",
                                                         id="file_extra_meta_value",
                                                         style="resize: vertical;",
                                                         name="value", type="text",
                                                         readonly="readonly")
                                with div(cls="modal-footer"):
                                    button("Cancel", type="button", cls="btn btn-default",
                                           data_dismiss="modal")
                                    button("Delete", type="button", cls="btn btn-danger",
                                           id="btn-delete-key-value")  # TODO: TESTING
        return root_div

    @classmethod
    def get_preview_data_url(self, resource, folder_path):
        # A data preview url pointing to an external data service.
        # - subclass needs to override this
        return None


class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    resource = models.ForeignKey('hs_composite_resource.CompositeResource', on_delete=models.CASCADE)
    # files associated with this logical file group
    files = GenericRelation(ResourceFile, content_type_field='logical_file_content_type',
                            object_id_field='logical_file_object_id')
    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)
    # this will be used for dc:type in resourcemetadata.xml
    # each specific logical type needs to reset this field
    # also this data type needs to be defined in terms.html page
    data_type = "Generic"

    # this field is for logical file to store extra key:value pairs, e.g., currently for .url
    # file to store url value for easy redirection when opening the file
    # for internal use only - won't get recorded in bag and shouldn't be used for storing metadata
    extra_data = HStoreField(default=dict)

    class Meta:
        abstract = True

    @classmethod
    def initialize(cls, dataset_name, resource):
        """
        A helper for creating aggregation. Creates a new aggregation/logical_file type
        instance and sets it's dataset field
        :param  dataset_name: a name/title for the aggregation/logical file
        :param  resource: an instance of composite resource for which this aggregation being
        created
        """
        logical_file = cls.create(resource)
        logical_file.dataset_name = dataset_name
        # at this point the logical file is not created in DB - caller needs to save it to DB
        return logical_file

    @classmethod
    def create_aggregation(cls, dataset_name, resource, res_files=None, new_files_to_upload=None,
                           folder_path=''):
        """Creates an aggregation
        :param  dataset_name  a value for setting the dataset_name attribute of the new aggregation
        :param  resource  an instance of CompositeResource in which the aggregation to be created
        :param  res_files  a list of resource files that need to be part of the new aggregation
        :param  new_files_to_upload  a list of files that needs to be uploaded to the resource as
        part of creating the new aggregation
        :param  folder_path  path of the folder to which files need to be uploaded

        :returns a new aggregation
        """
        logical_file = cls.initialize(dataset_name, resource)
        logical_file.save()
        if res_files is None:
            res_files = []

        # make all existing resource files part of the aggregation
        for res_file in res_files:
            logical_file.add_resource_file(res_file)

        if new_files_to_upload is None:
            new_files_to_upload = []
        # add all new files to the resource
        for f in new_files_to_upload:
            uploaded_file = UploadedFile(file=open(f, 'rb'), name=os.path.basename(f))

            new_res_file = add_file_to_resource(
                resource, uploaded_file, folder=folder_path, add_to_aggregation=False, save_file_system_metadata=True
            )
            logical_file.add_resource_file(new_res_file)

        return logical_file

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # any file can be part of this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def get_main_file_type(cls):
        # a single file extension in the group which is considered the main file
        # - subclass needs to override this
        return None

    @classmethod
    def can_set_folder_to_aggregation(cls, resource, dir_path, aggregations=None):
        """helper to check if the specified folder *dir_path* can be set to this aggregation type

        :param  resource: an instance of composite resource in which the folder to be checked
        :param dir_path: Resource file directory path (full folder path starting with resource id)
        for which this aggregation type to be set
        :param  aggregations: a list of aggregations in *resource*
        :return True or False
        """
        return False

    def can_be_deleted_on_file_delete(self):
        """Checks if this logical file (self) can be deleted on delete of any resource file
        that is part of this aggregation"""
        return True

    def can_contain_aggregation(self, aggregation):
        """Checks if the specified *aggregation* can be part of this (self) aggregation
        :param aggregation: an aggregation that can be part of this aggregation (aggregation nesting)
        """
        return False

    @property
    def get_main_file(self):
        file_extension = self.get_main_file_type()
        if file_extension:
            if file_extension == ".*":
                # any file can serve as main file
                return self.files.all().first()
            else:
                for f in self.files.all():
                    if f.extension == file_extension:
                        return f
        return None

    @property
    def url(self):
        return os.path.join("/", "resource", self.resource.file_path, self.aggregation_name)

    @classmethod
    def get_allowed_storage_file_types(cls):
        # can store any file types in this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def type_name(cls):
        return cls.__name__

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type. Sub classes that
        support aggregation creation from a folder must override this.
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        return ""

    @classmethod
    def supports_folder_based_aggregation(cls):
        """If an aggregation of this type can be created from a folder"""
        return False

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """Sub classes must implement this method to create specific logical file (aggregation) type
        :param resource: an instance of resource type CompositeResource
        :param file_id: (optional) id of the resource file to be set as an aggregation type -
        if this is missing then folder_path must be specified
        :param folder_path: (optional) path of the folder which needs to be set to an aggregation
        type - if this is missing then file_id must be specified
        :param user: user who is setting the file type
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def _validate_set_file_type_inputs(cls, resource, file_id=None, folder_path=''):
        """Validation of *file_id* and *folder_path* for creating file type (aggregation)

        :param resource: an instance of resource type CompositeResource
        :param file_id: (optional) id of the resource file to be set as an aggregation type -
        if this is missing then folder_path must be specified
        :param folder_path: (optional) path of the folder which needs to be set to a FileSet
        aggregation type - if this is missing then file_id must be specified. If specified a
        path relative to the resource.file_path will be returned
        :raise  ValidationError if validation fails
        :return an instance of ResourceFile if validation is successful and the folder_path
        """

        if file_id is None and not folder_path:
            raise ValueError("Must specify id of the file or path of the folder to set as an "
                             "aggregation type")

        if file_id is not None and folder_path:
            raise ValueError("Must specify either id of the file or path of the folder to set as an "
                             "aggregation type, but not both.")

        if cls.__name__ == 'FileSetLogicalFile' and not folder_path:
            raise ValueError("Must specify path of the folder to set as a "
                             "fileset aggregation type")

        if cls.__name__ not in ['FileSetLogicalFile', 'ModelProgramLogicalFile', 'ModelInstanceLogicalFile'] \
                and file_id is None:
            raise ValueError("Must specify id of the file to set as an "
                             "aggregation type")

        res_file = None
        if file_id is not None:
            # user selected a file to set aggregation
            res_file = get_resource_file_by_id(resource, file_id)
            if res_file is None or not res_file.exists:
                raise ValidationError("File not found.")

            logical_file = None
            if res_file.has_logical_file:
                logical_file = res_file.logical_file

            if logical_file is not None:
                if not logical_file.is_fileset and not logical_file.is_model_instance:
                    msg = "Selected file {} is already part of an aggregation.".format(res_file.file_name)
                    raise ValidationError(msg)
                elif cls.__name__ == 'ModelProgramLogicalFile':
                    if logical_file.is_model_instance:
                        msg = "Model program aggregation is not allowed within a model instance aggregation"
                        raise ValidationError(msg)
        else:
            # user selected a folder to set aggregation - check if the specified folder exists
            storage = resource.get_s3_storage()
            if folder_path.startswith("data/contents/"):
                folder_path = folder_path[len("data/contents/"):]
            path_to_check = os.path.join(resource.file_path, folder_path)
            if not storage.exists(path_to_check):
                msg = "Specified folder {} path does not exist in S3."
                msg = msg.format(path_to_check)
                raise ValidationError(msg)

            if cls.__name__ in ("FileSetLogicalFile", "ModelInstanceLogicalFile", "ModelProgramLogicalFile"):
                if not cls.can_set_folder_to_aggregation(resource=resource, dir_path=path_to_check):
                    msg = "{} aggregation can't be created from the specified folder:{}"
                    if cls.__name__ == "FileSetLogicalFile":
                        msg = msg.format("Fileset", path_to_check)
                    elif cls.__name__ == "ModelProgramLogicalFile":
                        msg = msg.format("Model program", path_to_check)
                    else:
                        msg = msg.format("Model instance", path_to_check)
                    raise ValidationError(msg)

        return res_file, folder_path

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Returns one specific file as the primary file from the list of resource
        files *resource_files*. A file is a primary file which can be used for creating a
        file type (aggregation). Subclasses must implement this.

        :param  resource_files: a list of resource files - instances of ResourceFile
        :return a resource file (instance of ResourceFile) if found, otherwise, None
        """

        raise NotImplementedError

    @staticmethod
    def get_aggregation_display_name():
        """Sub classes must implement this method to return a name for this
        logical (aggregation) type used in UI"""
        raise NotImplementedError()

    @staticmethod
    def get_aggregation_term_label():
        """Sub classes must implement this method to return the label for this
        logical (aggregation) term used in aggregation xml metadata and resource map files"""
        raise NotImplementedError()

    def get_aggregation_class_name(self):
        """Return the class name of the logical type (aggregation type)"""
        return self.__class__.__name__

    @property
    def is_fileset(self):
        """Return True if this aggregation is a fileset aggregation, otherwise False"""
        return self.get_aggregation_class_name() == 'FileSetLogicalFile'

    @property
    def is_model_program(self):
        """Return True if this aggregation is a model program aggregation, otherwise False"""
        return self.get_aggregation_class_name() == 'ModelProgramLogicalFile'

    @property
    def is_model_instance(self):
        """Return True if this aggregation is a model instance aggregation, otherwise False"""
        return self.get_aggregation_class_name() == 'ModelInstanceLogicalFile'

    @property
    def is_dangling(self):
        """Checks if this aggregation is a dangling aggregation or not"""

        resource = self.resource
        istorage = resource.get_s3_storage()
        if self.files.count() == 0:
            if any([self.is_fileset, self.is_model_instance, self.is_model_program]):
                # check folder exist in S3
                if self.folder:
                    path = os.path.join(resource.file_path, self.folder)
                    if not istorage.exists(path):
                        return True
                else:
                    return True
            else:
                return True
        return False

    @staticmethod
    def get_aggregation_type_name():
        """Return the appropriate aggregation name needed for aggregation xml metadata and
        map document. Subclasses must implement this method.
        """
        raise NotImplementedError

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        Subclasses must implement this method.
        """
        raise NotImplementedError

    @property
    def has_metadata(self):
        return hasattr(self, 'metadata')

    @property
    def size(self):
        # get total size (in bytes) of all files in this file type
        return sum([f.size for f in self.files.all()])

    @property
    def supports_resource_file_move(self):
        """allows a resource file that is part of this logical file type to be moved"""
        return True

    @property
    def supports_resource_file_add(self):
        """allows a resource file to be added"""
        return True

    @property
    def supports_resource_file_rename(self):
        """allows a resource file that is part of this logical file type to be renamed"""
        return True

    @property
    def supports_zip(self):
        """a folder containing resource file(s) that are part of this logical file type
        is allowed to be zipped"""
        return True

    @property
    def supports_delete_folder_on_zip(self):
        """allows the original folder to be deleted upon zipping of that folder"""
        return True

    @property
    def supports_unzip(self):
        """allows a zip file that is part of this logical file type to get unzipped"""
        return True

    @property
    def aggregation_name(self):
        """Returns aggregation name as per the aggregation naming rule defined in issue#2568"""

        primary_file = self.get_primary_resource_file(self.files.all())
        if not primary_file:
            return ""
        return primary_file.short_path

    @property
    def aggregation_path(self):
        """Returns the full path of the aggregation (self) that starts with resource id
        example: 0e917683abae48988bf3fc1f9df5803f/data/contents/netcdf-aggr
        """
        aggr_path = os.path.join(self.resource.file_path, self.aggregation_name)
        return aggr_path

    @property
    def metadata_short_file_path(self):
        """File path of the aggregation metadata xml file relative to {resource_id}/data/contents/
        """
        return self.xml_file_short_path(resmap=False)

    @property
    def metadata_file_path(self):
        """Full path of the aggregation metadata xml file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.metadata_short_file_path)

    @property
    def map_short_file_path(self):
        """File path of the aggregation map xml file relative to {resource_id}/data/contents/
        """
        return self.xml_file_short_path()

    @property
    def map_file_path(self):
        """Full file path of the aggregation map xml file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.map_short_file_path)

    @property
    def metadata_json_file_path(self):
        """Returns the path of the aggregation metadata json file starting with {resource_id}/data/contents/
        """
        raise NotImplementedError

    @property
    def metadata_json_file_url_path(self):
        """Returns the url path of the aggregation metadata json file"""

        from hs_core.hydroshare.utils import current_site_url

        meta_file_path = self.metadata_json_file_path
        meta_file_url_path = os.path.join(current_site_url(), 'resource', meta_file_path)
        return meta_file_url_path

    @property
    def is_single_file_aggregation(self):
        """
        Returns True if the aggregation consists of only one file, otherwise, False.
        Subclasses that support only single file must override this property

        :return: True or False
        """
        return False

    def add_resource_file(self, res_file, set_metadata_dirty=True):
        """Makes a ResourceFile (res_file) object part of this logical file object. If res_file
        is already associated with any other logical file object, this function does not do
        anything to that logical object. The caller needs to take necessary action for the
        previously associated logical file object. If res_file is already part of this
        logical file, it raises ValidationError.

        :param res_file an instance of ResourceFile
        :param set_metadata_dirty: a boolean to indicate if metadata needs to be set dirty
        """
        res_file.logical_file_content_object = self
        res_file.save()
        if set_metadata_dirty:
            self.set_metadata_dirty()

    def add_files_to_resource(self, resource, files_to_add, upload_folder):
        """A helper for adding any new files to resource as part of creating an aggregation
        :param  resource: an instance of CompositeResource
        :param  files_to_add: a list of file paths for files that need to be added to the resource
        and made part of this aggregation
        """
        for fl in files_to_add:
            uploaded_file = UploadedFile(file=open(fl, 'rb'),
                                         name=os.path.basename(fl))
            new_res_file = add_file_to_resource(
                resource, uploaded_file, folder=upload_folder, add_to_aggregation=False, save_file_system_metadata=True
            )

            # make each resource file we added part of the logical file
            self.add_resource_file(new_res_file)

    def add_resource_files_in_folder(self, resource, folder):
        """
        A helper for creating aggregation. Makes all resource files in a given folder as part of
        the aggregation/logical file type
        :param  resource:  an instance of CompositeResource
        :param  folder: folder from which all files need to be made part of this aggregation
        """

        res_files = ResourceFile.list_folder(resource=resource, folder=folder,
                                             sub_folders=False)

        for res_file in res_files:
            self.add_resource_file(res_file, set_metadata_dirty=False)
        self.set_metadata_dirty()
        return res_files

    def copy_resource_files(self, resource, files_to_copy, tgt_folder):
        """
        A helper for creating aggregation. Copies the given list of resource files to the
        specified folder path and then makes those copied files as part of the aggregation
        :param  resource: an instance of CompositeResource for which aggregation being created
        :param  files_to_copy: a list of resource file paths in S3 that need to be copied
        to a specified directory *tgt_folder* and made part of this aggregation
        :param  tgt_folder: folder to which files need to be copied to
        """

        for res_file in files_to_copy:
            source_path = res_file.storage_path
            copied_res_file = ResourceFile.create(resource=resource,
                                                  file=None,
                                                  folder=tgt_folder,
                                                  source=source_path)

            # make the copied file as part of the aggregation/file type
            self.add_resource_file(copied_res_file)

    def get_copy(self, copied_resource):
        """creates a copy of this logical file object with associated metadata needed to support
        resource copy.
        :param  copied_resource: a copy of the resource for which a copy of aggregation needs to be
        created
        Note: This copied logical file however does not have any association with resource files
        """
        copy_of_logical_file = type(self).create(copied_resource)
        copy_of_logical_file.dataset_name = self.dataset_name
        copy_of_logical_file.metadata.extra_metadata = copy.deepcopy(self.metadata.extra_metadata)
        copy_of_logical_file.metadata.keywords = self.metadata.keywords
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.extra_data = copy.deepcopy(self.extra_data)
        copy_of_logical_file.save()
        # copy the metadata elements
        elements_to_copy = self.metadata.get_metadata_elements()
        for element in elements_to_copy:
            element_args = model_to_dict(element)
            element_args.pop('content_type')
            element_args.pop('id')
            element_args.pop('object_id')
            copy_of_logical_file.metadata.create_element(element.__class__.__name__, **element_args)

        return copy_of_logical_file

    def delete(self, using=None, keep_parents=False):
        """Overriding the django model delete() here so that subclasses can do further
        override if needed"""
        super(AbstractLogicalFile, self).delete()

    def logical_delete(self, user, resource=None, delete_res_files=True, delete_meta_files=True):
        """
        Deletes the logical file as well as all resource files associated with this logical file.
        This function is primarily used by the system to delete logical file object and associated
        metadata as part of deleting a resource file object. Any time a request is made to
        delete a specific resource file object, if the requested file is part of a
        logical file then all files in the same logical file group will be deleted. if custom logic
        requires deleting logical file object (LFO) then instead of using LFO.delete(), you must
        use LFO.logical_delete()
        :param  user:  user who is deleting file type/aggregation
        :param  resource: an instance of CompositeResource to which this logical file belongs to
        :param delete_res_files: If True all resource files that are part of this logical file will
        be deleted
        :param delete_meta_files: If True the resource map and metadata files that are part of this logical file
        will be deleted. The only time this should be set to False is when deleting a folder as the folder
        gets deleted from S3 which deletes the associated metadata and resource map files.
        """

        from hs_core.hydroshare.resource import delete_resource_file

        parent_aggr = self.get_parent()
        if resource is None:
            # this generates a db query
            resource = self.resource

        if delete_meta_files:
            # delete associated metadata and map xml documents
            istorage = resource.get_s3_storage()
            if istorage.exists(self.metadata_file_path):
                istorage.delete(self.metadata_file_path)
            if istorage.exists(self.map_file_path):
                istorage.delete(self.map_file_path)

        # delete all resource files associated with this instance of logical file
        if delete_res_files:
            for f in self.files.all():
                delete_resource_file(resource.short_id, f.id, user, delete_logical_file=False)
        else:
            # first need to set the aggregation for each of the associated resource files to None
            # so that deleting the aggregation (logical file) does not cascade to deleting of
            # resource files associated with the aggregation
            self.files.update(logical_file_object_id=None, logical_file_content_type=None)

        # delete logical file first then delete the associated metadata file object
        # deleting the logical file object will not automatically delete the associated
        # metadata file object
        metadata = self.metadata if self.has_metadata else None
        self.delete()

        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

        # if this deleted aggregation has a parent aggregation - xml files for the parent
        # aggregation needs to be generated so that the references to the deleted aggregation can be removed
        # setting parent aggregation metadata dirty will regenerate xml files for parent aggregation at the time
        # of download
        if parent_aggr is not None:
            parent_aggr.set_metadata_dirty()
        resource.cleanup_aggregations()

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. However, it doesn't delete any resource files that are part of the aggregation."""

        # delete associated metadata and map xml document
        istorage = self.resource.get_s3_storage()
        if istorage.exists(self.metadata_file_path):
            istorage.delete(self.metadata_file_path)
        if istorage.exists(self.map_file_path):
            istorage.delete(self.map_file_path)

        # find if there is a parent aggregation - files in this (self) aggregation
        # need to be added to parent if exists
        parent_aggr = self.get_parent()

        res_files = []
        res_files.extend(self.files.all())

        # first need to set the aggregation for each of the associated resource files to None
        # so that deleting the aggregation (logical file) does not cascade to deleting of
        # resource files associated with the aggregation
        for res_file in self.files.all():
            res_file.logical_file_content_object = None
            res_file.save()

        # delete logical file (aggregation) first then delete the associated metadata file object
        # deleting the logical file object will not automatically delete the associated
        # metadata file object
        metadata = self.metadata if self.has_metadata else None
        self.delete()

        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

        # make all the resource files of this (self) aggregation part of the parent aggregation
        if parent_aggr is not None:
            for res_file in res_files:
                parent_aggr.add_resource_file(res_file)

            # need to regenerate the xml files for the parent so that the references to this deleted aggregation
            # can be removed from the parent xml files - so need to set the parent aggregation metadata to dirty
            parent_aggr.set_metadata_dirty()

        post_remove_file_aggregation.send(
            sender=self.__class__,
            resource=self.resource,
            res_files=self.files.all()
        )

        self.resource.setAVU("bag_modified", True)
        self.resource.setAVU('metadata_dirty', 'true')

    def get_parent(self):
        """Find the parent model instance or fileset aggregation of this aggregation
        :return a model instance or fileset aggregation if found, otherwise None
        """
        parent_aggr = None
        aggr_path = self.aggregation_name
        if aggr_path and "/" in aggr_path:
            parent_aggr_path = os.path.dirname(aggr_path)
            # first check for a model instance aggregation in the path
            parent_aggr = self.resource.get_model_aggregation_in_path(parent_aggr_path)
            if parent_aggr is None:
                parent_aggr = self.resource.get_fileset_aggregation_in_path(parent_aggr_path)

        return parent_aggr

    @property
    def has_parent(self):
        """Checks if this aggregation has a parent aggregation
        :return True if there is a parent aggregation otherwise False
        """
        return self.get_parent() is not None

    def get_children(self):
        """Returns a list of all aggregations that are directly under the folder that represents
        this (self) aggregation
        :return a list of aggregations

        Note: Aggregation types that support nested aggregation must override this method
        """

        return []

    @property
    def has_children(self):
        """Returns True if this aggregation contains any other aggregations, otherwise False"""
        return len(self.get_children()) > 0

    @property
    def has_children_spatial_data(self):
        """Returns True if any of the contained aggregation has spatial data, otherwise False"""
        return any(child_aggr.metadata.spatial_coverage is not None for child_aggr in
                   self.get_children())

    @property
    def has_children_temporal_data(self):
        """Returns True if any of the contained aggregation has temporal data, otherwise False"""
        return any(child_aggr.metadata.temporal_coverage is not None for child_aggr in
                   self.get_children())

    def set_metadata_dirty(self):
        self.metadata.is_dirty = True
        self.metadata.save(update_fields=["is_dirty"])

    def create_aggregation_xml_documents(self, create_map_xml=True):
        """Creates aggregation map xml and aggregation metadata xml files
        :param  create_map_xml: if true, aggregation map xml file will be created
        """

        log = logging.getLogger()

        # create a temp dir where the xml files will be temporarily saved before copying to S3
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_s3_storage()

        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.makedirs(tmpdir)

        # create and copy the map and metadata xml documents for the aggregation
        meta_from_file_name = os.path.join(tmpdir, 'metadata.xml')
        map_from_file_name = os.path.join(tmpdir, 'map.xml')
        try:
            with open(meta_from_file_name, 'w') as out:
                out.write(self.metadata.get_xml())
            to_file_name = self.metadata_file_path
            istorage.saveFile(meta_from_file_name, to_file_name)
            log.debug("Aggregation metadata xml file:{} created".format(to_file_name))

            if create_map_xml:
                with open(map_from_file_name, 'w') as out:
                    out.write(self.generate_map_xml())
                to_file_name = self.map_file_path
                istorage.saveFile(map_from_file_name, to_file_name)
                log.debug("Aggregation map xml file:{} created".format(to_file_name))
            # setting bag flag to dirty - as resource map document needs to be re-generated as
            # resource map xml file has references to aggregation map xml file paths
            set_dirty_bag_flag(self.resource)
        except Exception as ex:
            log.error("Failed to create aggregation metadata xml file. Error:{}".format(str(ex)))
            raise ex
        finally:
            shutil.rmtree(tmpdir)

    def generate_map_xml(self):
        """Generates the xml needed to write to the aggregation map xml document"""
        from hs_core.hydroshare import encode_resource_url
        from hs_core.hydroshare.utils import current_site_url, get_file_mime_type

        current_site_url = current_site_url()
        # This is the qualified resource url.
        hs_res_url = os.path.join(current_site_url, 'resource', self.resource.file_path)
        # this is the path to the resource metadata file for download
        aggr_metadata_file_path = self.metadata_short_file_path
        metadata_url = os.path.join(hs_res_url, aggr_metadata_file_path)
        metadata_url = encode_resource_url(metadata_url)
        # this is the path to the aggregation resourcemap file for download
        aggr_map_file_path = self.map_short_file_path
        res_map_url = os.path.join(hs_res_url, aggr_map_file_path)
        res_map_url = encode_resource_url(res_map_url)

        # make the resource map:
        utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
        utils.namespaceSearchOrder.append('citoterms')

        ag_url = res_map_url + '#aggregation'
        a = Aggregation(ag_url)

        # Set properties of the aggregation
        a._dc.title = self.dataset_name
        agg_type_url = "{site}/terms/{aggr_type}"\
            .format(site=current_site_url, aggr_type=self.get_aggregation_type_name())
        a._dcterms.type = URIRef(agg_type_url)
        a._citoterms.isDocumentedBy = metadata_url
        a._ore.isDescribedBy = res_map_url

        res_type_aggregation = AggregatedResource(agg_type_url)
        res_type_aggregation._rdfs.label = self.get_aggregation_term_label()
        res_type_aggregation._rdfs.isDefinedBy = current_site_url + "/terms"

        a.add_resource(res_type_aggregation)

        # Create a description of the metadata document that describes the whole resource and add it
        # to the aggregation
        resMetaFile = AggregatedResource(metadata_url)
        resMetaFile._citoterms.documents = ag_url
        resMetaFile._ore.isAggregatedBy = ag_url
        resMetaFile._dc.format = "application/rdf+xml"

        # Create a description of the content file and add it to the aggregation
        files = self.files.all()
        resFiles = []
        for n, f in enumerate(files):
            res_uri = '{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=self.resource.short_id,
                file_name=f.short_path)
            res_uri = encode_resource_url(res_uri)
            resFiles.append(AggregatedResource(res_uri))
            resFiles[n]._ore.isAggregatedBy = ag_url
            resFiles[n]._dc.format = get_file_mime_type(os.path.basename(f.short_path))

        # Add the resource files to the aggregation
        a.add_resource(resMetaFile)
        for f in resFiles:
            a.add_resource(f)

        # Create a description of the contained aggregations and add it to the aggregation
        child_ore_aggregations = []
        for n, child_aggr in enumerate(self.get_children()):
            res_uri = '{hs_url}/resource/{res_id}/data/contents/{aggr_name}'.format(
                hs_url=current_site_url,
                res_id=self.resource.short_id,
                aggr_name=child_aggr.map_short_file_path + '#aggregation')
            res_uri = encode_resource_url(res_uri)
            child_ore_aggr = Aggregation(res_uri)
            child_ore_aggregations.append(child_ore_aggr)
            child_ore_aggregations[n]._ore.isAggregatedBy = ag_url
            child_agg_type_url = "{site}/terms/{aggr_type}"
            child_agg_type_url = child_agg_type_url.format(
                site=current_site_url, aggr_type=child_aggr.get_aggregation_type_name())
            child_ore_aggregations[n]._dcterms.type = URIRef(child_agg_type_url)

        # Add contained aggregations to the aggregation
        for aggr in child_ore_aggregations:
            a.add_resource(aggr)

        # Register a serializer with the aggregation, which creates a new ResourceMap that
        # needs a URI
        serializer = RdfLibSerializer('xml')
        # resMap = a.register_serialization(serializer, res_map_url)
        a.register_serialization(serializer, res_map_url)

        # Fetch the serialization
        remdoc = a.get_serialization()
        # remove this additional xml element - not sure why it gets added
        # <ore:aggregates rdf:resource="https://www.hydroshare.org/terms/[aggregation name]"/>
        xml_element_to_replace = '<ore:aggregates rdf:resource="{}"/>\n'.format(agg_type_url)
        xml_string = remdoc.data.replace(xml_element_to_replace, '')
        return xml_string

    def get_xml_file_name(self, resmap=True):
        xml_file_name = self.aggregation_name
        if "/" in xml_file_name:
            xml_file_name = os.path.basename(xml_file_name)

        xml_file_name, _ = os.path.splitext(xml_file_name)

        if resmap:
            xml_file_name += AggregationMetaFilePath.RESMAP_FILE_ENDSWITH
        else:
            xml_file_name += AggregationMetaFilePath.METADATA_FILE_ENDSWITH
        return xml_file_name

    def xml_file_short_path(self, resmap=True):
        """File path of the aggregation metadata or map xml file relative
        to {resource_id}/data/contents/
        :param  resmap  If true file path for aggregation resmap xml file, otherwise file path for
        aggregation metadata file is returned
        """

        xml_file_name = self.get_xml_file_name(resmap=resmap)
        aggr_file = self.files.first()
        file_folder = aggr_file.file_folder if aggr_file else ""
        if file_folder:
            xml_file_name = os.path.join(file_folder, xml_file_name)
        return xml_file_name

    def read_metadata_file(self):
        istorage = self.resource.get_s3_storage()
        return istorage.download(self.metadata_file_path).read()

    def read_metadata_as_rdf(self):
        g = Graph()
        return g.parse(data=self.read_metadata_file())


class FileTypeContext(object):
    """A ContextManager for creating file type/aggregation
    :param  aggr_cls  aggregation class using this context manager
    :param  user  an instance of User  (user creating the aggregation)
    :param  resource  an instance of CompositeResource for which aggregation is created
    :param  file_id  (optional) id of the resource file from which aggregation to be created -
    required for creating any aggregation other than FileSet aggregation
    :param  folder_path (optional) path of the folder from which aggregation to be created -
    required for creating FileSet aggregation
    :param post_aggr_signal (optional) post aggregation creation signal to send signal
    :param  is_temp_file if True resource file specified by file_id will be retrieved from
    S3 to temp directory
    """

    def __init__(self, aggr_cls, user, resource, file_id=None, folder_path='',
                 post_aggr_signal=None, is_temp_file=True):

        self.aggr_cls = aggr_cls
        self.user = user
        self.resource = resource
        self.file_id = file_id
        self.folder_path = folder_path
        self.post_aggr_signal = post_aggr_signal
        self.is_temp_file = is_temp_file
        # caller must set the logical_file attribute of the context manager
        # before existing context manager
        self.logical_file = None
        # if any resource files need to be deleter as part of creating aggregation, caller needs
        # to set the res_files_to_delete attribute of the context manager
        self.res_files_to_delete = []

    def __enter__(self):
        # run this code at the start of the context manager before control returns to the caller
        self.temp_dir = None
        self.temp_file = None

        self.res_file, self.folder_path = self.aggr_cls._validate_set_file_type_inputs(
            self.resource, self.file_id, self.folder_path)

        if self.is_temp_file:
            # need to get the file from S3 to temp dir
            self.temp_file = get_file_from_s3(resource=self.resource, file_path=self.res_file.storage_path)
            self.temp_dir = os.path.dirname(self.temp_file)
        return self  # control returned to the caller

    def __exit__(self, exc_type, exc_val, exc_tb):
        # run this code when caller is done with the context manager
        if self.logical_file is not None:
            # set resource to private if logical file is missing required metadata
            self.resource.update_public_and_discoverable()

            # set this new logical file metadata to dirty so that meta xml files will be generated as part of download
            self.logical_file.set_metadata_dirty()

            # if this new logical file has a parent logical file that too needs to be set to metadata dirty
            parent_aggr = self.logical_file.get_parent()
            if parent_aggr is not None:
                parent_aggr.set_metadata_dirty()
            if self.post_aggr_signal is not None:
                self.post_aggr_signal.send(
                    sender=AbstractLogicalFile,
                    resource=self.resource,
                    file=self.logical_file
                )

        # delete res files
        for res_file in self.res_files_to_delete:
            delete_resource_file(self.resource.short_id, res_file.id, self.user)

        self.resource.cleanup_aggregations()
        resource_modified(self.resource, self.user, overwrite_bag=False)

        # delete temp dir
        if self.temp_dir is not None:
            if os.path.isdir(self.temp_dir):
                shutil.rmtree(self.temp_dir)
