import os
import copy
from uuid import uuid4
import shutil
import random
import logging

from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
from rdflib import Namespace, URIRef

from django.db import models
from django.core.files.uploadedfile import UploadedFile
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.models import model_to_dict
from django.contrib.postgres.fields import HStoreField, ArrayField

from mezzanine.conf import settings

from dominate.tags import div, legend, table, tr, tbody, thead, td, th, \
    span, a, form, button, label, textarea, h4, input, ul, li, p

from lxml import etree

from hs_core.hydroshare.utils import current_site_url, get_resource_file_by_id, \
    set_dirty_bag_flag, add_file_to_resource, resource_modified, get_resource_by_shortkey
from hs_core.models import ResourceFile, AbstractMetaDataElement, Coverage, CoreMetaData
from hs_core.hydroshare.resource import delete_resource_file


class AbstractFileMetaData(models.Model):
    """ base class for HydroShare file type metadata """

    # one temporal coverage and one spatial coverage
    coverages = GenericRelation(Coverage)
    # key/value metadata
    extra_metadata = HStoreField(default={})
    # keywords
    keywords = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[])
    # to track if any metadata element has been modified to trigger file update
    is_dirty = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @classmethod
    def get_metadata_model_classes(cls):
        return {'coverage': Coverage}

    def get_metadata_elements(self):
        """returns a list of all metadata elements (instances of AbstractMetaDataElement)
         associated with this file type metadata object.
        """
        return list(self.coverages.all())

    def delete_all_elements(self):
        self.coverages.all().delete()
        self.extra_metadata = {}
        self.keywords = []
        self.save()

    def get_html(self, include_extra_metadata=True, **kwargs):
        """Generates html for displaying all metadata elements associated with this logical file.
        Subclass must override to include additional html for additional metadata it supports.
        :param include_extra_metadata: a flag to control if necessary html for displaying key/value
        metadata will be included
        """

        root_div = div()
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
            dataset_name_div = div(cls="col-xs-12 content-block")
            with dataset_name_div:
                legend("Title")
                p(self.logical_file.dataset_name)
            return dataset_name_div

    def get_keywords_html(self):
        """generates html for viewing keywords"""
        keywords_div = div()
        if self.keywords:
            keywords_div = div(cls="col-sm-12 content-block")
            with keywords_div:
                legend('Keywords')
                with div(cls="tags"):
                    with ul(id="list-keywords-file-type", cls="tag-list custom-well"):
                        for kw in self.keywords:
                            with li():
                                a(kw, cls="tag")
        return keywords_div

    def get_key_value_metadata_html(self):
        """generates html for viewing key/vale extra metadata"""
        extra_metadata_div = div()
        if self.extra_metadata:
            extra_metadata_div = div(cls="col-sm-12 content-block")
            with extra_metadata_div:
                legend('Extended Metadata')
                with table(cls="hs-table table dataTable no-footer", style="width: 100%"):
                    with thead():
                        with tr(cls="header-row"):
                            th("Key")
                            th("Value")
                    with tbody():
                        for k, v in self.extra_metadata.iteritems():
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
        root_div = div()

        with root_div:
            if dataset_name_form:
                self.get_dataset_name_form()

            self.get_keywords_html_form()

            self.get_extra_metadata_html_form()
            if temporal_coverage:
                self.get_temporal_coverage_html_form()
        return root_div

    def get_keywords_html_form(self):
        keywords_div = div(cls="col-sm-12 content-block", id="filetype-keywords")
        action = "/hsapi/_internal/{0}/{1}/add-file-keyword-metadata/"
        action = action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        delete_action = "/hsapi/_internal/{0}/{1}/delete-file-keyword-metadata/"
        delete_action = delete_action.format(self.logical_file.__class__.__name__,
                                             self.logical_file.id)
        with keywords_div:
            legend("Keywords")
            with form(id="id-keywords-filetype", action=action, method="post",
                      enctype="multipart/form-data"):
                input(id="id-delete-keyword-filetype-action", type="hidden",
                      value=delete_action)
                with div(cls="tags"):
                    with div(id="add-keyword-wrapper", cls="input-group"):
                        input(id="txt-keyword-filetype", cls="form-control",
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
            root_div_extra = div(cls="col-xs-12", id="filetype-extra-metadata")
            with root_div_extra:
                legend('Extended Metadata')
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
                        for k, v in self.extra_metadata.iteritems():
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
            root_div_extra = div(id="filetype-extra-metadata", cls="col-xs-12 content-block")
            with root_div_extra:
                legend('Extended Metadata')
                get_add_keyvalue_button()
                self._get_add_key_value_modal_form()
            return root_div_extra

    def get_temporal_coverage_html_form(self):
        # Note: When using this form layout the context variable 'temp_form' must be
        # set prior to calling the template.render(context)
        root_div = div(cls="col-lg-6 col-xs-12", id="temporal-coverage-filetype")
        with root_div:
            with form(id="id-coverage_temporal-file-type", action="{{ temp_form.action }}",
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
        return True

    @classmethod
    def get_supported_element_names(cls):
        return ['Coverage']

    def get_required_missing_elements(self):
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

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        RDF_ROOT = etree.Element('{%s}RDF' % CoreMetaData.NAMESPACES['rdf'],
                                 nsmap=CoreMetaData.NAMESPACES)
        # create the Description element
        rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' %
                                           CoreMetaData.NAMESPACES['rdf'])

        resource = self.logical_file.resource

        aggregation_map_file_path = os.path.join(resource.file_path,
                                                 self.logical_file.map_file_path)
        aggregation_map_file_path += "#aggregation"
        aggregation_map_uri = current_site_url() + "/{}".format(aggregation_map_file_path)
        rdf_Description.set('{%s}about' % CoreMetaData.NAMESPACES['rdf'], aggregation_map_uri)

        # add aggregation title
        if self.logical_file.dataset_name:
            dc_datatitle = etree.SubElement(rdf_Description, '{%s}title' %
                                            CoreMetaData.NAMESPACES['dc'])
            dc_datatitle.text = self.logical_file.dataset_name

        # add aggregation type
        aggregation_term_uri = current_site_url() + "/terms/{}"
        aggregation_term_uri = aggregation_term_uri.format(
            self.logical_file.get_aggregation_type_name())

        dc_type = etree.SubElement(rdf_Description, '{%s}type' % CoreMetaData.NAMESPACES['dc'])
        dc_type.set('{%s}resource' % CoreMetaData.NAMESPACES['rdf'], aggregation_term_uri)

        # add lang element
        dc_lang = etree.SubElement(rdf_Description, '{%s}language' % CoreMetaData.NAMESPACES['dc'])
        dc_lang.text = resource.metadata.language.code

        # add rights element
        dc_rights = etree.SubElement(rdf_Description, '{%s}rights' % CoreMetaData.NAMESPACES['dc'])
        dc_rights_rdf_Description = etree.SubElement(dc_rights,
                                                     '{%s}Description' %
                                                     CoreMetaData.NAMESPACES['rdf'])
        hsterms_statement = etree.SubElement(dc_rights_rdf_Description,
                                             '{%s}rightsStatement' %
                                             CoreMetaData.NAMESPACES['hsterms'])
        hsterms_statement.text = resource.metadata.rights.statement
        if resource.metadata.rights.url:
            hsterms_url = etree.SubElement(dc_rights_rdf_Description,
                                           '{%s}URL' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_url.set('{%s}resource' % CoreMetaData.NAMESPACES['rdf'],
                            resource.metadata.rights.url)

        # add keywords
        for kw in self.keywords:
            dc_subject = etree.SubElement(rdf_Description, '{%s}subject' %
                                          CoreMetaData.NAMESPACES['dc'])
            dc_subject.text = kw

        # add any key/value metadata items
        for key, value in self.extra_metadata.iteritems():
            hsterms_key_value = etree.SubElement(
                rdf_Description, '{%s}extendedMetadata' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_key_value_rdf_Description = etree.SubElement(
                hsterms_key_value, '{%s}Description' % CoreMetaData.NAMESPACES['rdf'])
            hsterms_key = etree.SubElement(hsterms_key_value_rdf_Description,
                                           '{%s}key' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_key.text = key
            hsterms_value = etree.SubElement(hsterms_key_value_rdf_Description,
                                             '{%s}value' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_value.text = value

        # add coverages
        for coverage in self.coverages.all():
            coverage.add_to_xml_container(rdf_Description)

        # create the Description element for aggregation type
        rdf_Description_aggr_type = etree.SubElement(RDF_ROOT, '{%s}Description' %
                                                     CoreMetaData.NAMESPACES['rdf'])

        rdf_Description_aggr_type.set('{%s}about' % CoreMetaData.NAMESPACES['rdf'],
                                      aggregation_term_uri)
        rdfs_label = etree.SubElement(rdf_Description_aggr_type, '{%s}label' %
                                      CoreMetaData.NAMESPACES['rdfs1'])
        rdfs_label.text = self.logical_file.get_aggregation_display_name()

        rdfs_isDefinedBy = etree.SubElement(rdf_Description_aggr_type, '{%s}isDefinedBy' %
                                            CoreMetaData.NAMESPACES['rdfs1'])
        rdfs_isDefinedBy.text = current_site_url() + "/terms"

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def _get_xml_containers(self):
        """Helper for the subclasses to get the xml containers element to which the sub classes
        can then add any additional elements for metadata xml generation"""

        xml_string = super(type(self), self).get_xml(pretty_print=False)
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container_to_add_to = RDF_ROOT.find('rdf:Description', namespaces=CoreMetaData.NAMESPACES)
        return RDF_ROOT, container_to_add_to

    def create_element(self, element_model_name, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        if element_model_name.lower() == "coverage":
            resource = element.metadata.logical_file.resource
            # resource will be None in case of coverage element being
            # created as part of copying a resource that supports logical file
            # types
            if resource is not None:
                # get the typed resource - CompositeResource
                resource = get_resource_by_shortkey(resource.short_id)
                resource.update_coverage()
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)
        self.is_dirty = True
        self.save()
        if element_model_name.lower() == "coverage":
            element = model_type.model_class().objects.get(id=element_id)
            resource = element.metadata.logical_file.resource
            # get the typed resource - CompositeResource
            resource = get_resource_by_shortkey(resource.short_id)
            resource.update_coverage()

    def delete_element(self, element_model_name, element_id):
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)
        self.is_dirty = True
        self.save()

    def _get_metadata_element_model_type(self, element_model_name):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported metadata elements for %s."
                                  % element_model_name, type(self))

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
        root_div = div(cls="col-xs-12")
        dataset_name = self.logical_file.dataset_name if self.logical_file.dataset_name else ""
        with root_div:
            with form(action=form_action, id="filetype-dataset-name",
                      method="post", enctype="multipart/form-data"):
                div("{% csrf_token %}")
                with div(cls="form-group"):
                    with div(cls="control-group"):
                        legend('Title')
                        with div(cls="controls"):
                            input(value=dataset_name,
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
                                        input(cls="form-control input-sm textinput textInput",
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
            for k, v in self.extra_metadata.iteritems():
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
                                                input(value=k, readonly="readonly",
                                                      cls="form-control input-sm textinput "
                                                          "textInput",
                                                      id="file_extra_meta_key_original",
                                                      maxlength="100",
                                                      name="key_original", type="text")
                                        with div(cls="control-group"):
                                            label("Key", cls="control-label requiredField",
                                                  fr="file_extra_meta_key")
                                            with div(cls="controls"):
                                                input(value=k,
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
            for k, v in self.extra_metadata.iteritems():
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
                                                input(cls="form-control input-sm textinput "
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


class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    # files associated with this logical file group
    files = GenericRelation(ResourceFile, content_type_field='logical_file_content_type',
                            object_id_field='logical_file_object_id')
    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)
    # this will be used for dc:type in resourcemetadata.xml
    # each specific logical type needs to reset this field
    # also this data type needs to be defined in in terms.html page
    data_type = "Generic"

    # display name for content type: used in discovery faceting
    verbose_content_type = "Generic"

    class Meta:
        abstract = True

    @classmethod
    def initialize(cls, dataset_name):
        """
        A helper for creating aggregation. Creates a new aggregation/logical_file type
        instance and sets it's dataset field
        :param  dataset_name: a name/title for the aggregation/logical file
        """
        logical_file = cls.create()
        logical_file.dataset_name = dataset_name
        logical_file.save()
        return logical_file

    def _finalize(self, user, resource, folder_created, res_files_to_delete, reset_title=False):
        """
        A helper for creating aggregation. As a final step in creation of aggregation/logical file,
        sets resource access control and generates aggregation xml files and if necessary delete
        original resource files
        :param  user: user who is creating a new aggregation
        :param  resource: an instance of CompositeResource
        :param  folder_created: True/False to indicate if a new folder has been created represent
        this aggregation
        :param  res_files_to_delete: a list of resource files to delete
        :param  reset_title: True/False to indicate if aggregation dataset_name attribute needs
        to be modified
        """

        # for multi-file aggregation set the aggregation dataset_name field to the containing
        # folder name
        if not self.is_single_file_aggregation and reset_title:
            if '/' in self.aggregation_name:
                folder = os.path.basename(self.aggregation_name)
            else:
                folder = self.aggregation_name
            self.dataset_name = folder
            self.save()
        # set resource to private if logical file is missing required metadata
        resource.update_public_and_discoverable()
        self.create_aggregation_xml_documents()
        # check if we need to delete any files
        if len(res_files_to_delete) == 1:
            res_file = res_files_to_delete[0]
            if res_file.extension.lower() == '.zip' or folder_created:
                delete_resource_file(resource.short_id, res_file.id, user)
        elif folder_created:
            for res_file in res_files_to_delete:
                delete_resource_file(resource.short_id, res_file.id, user)

        resource_modified(resource, user, overwrite_bag=False)

    @classmethod
    def _create_aggregation_folder(cls, resource, file_folder, base_file_name):
        """
        A helper for creating aggregation. Creates a folder for a new multi-file aggregation
        :param  resource: an instance of CompositeResource for which aggregation being created
        :param  file_folder: folder path of the file from which aggregation being created
        :param  base_file_name: name of file without the extension - the file used for crating
        aggregation
        """
        from hs_core.views.utils import create_folder

        new_folder_path = cls.compute_file_type_folder(resource, file_folder, base_file_name)
        create_folder(resource.short_id, new_folder_path)
        relative_aggregation_path = new_folder_path[len('data/contents/'):]
        return relative_aggregation_path

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # any file can be part of this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def get_main_file_type(cls):
        # a singel file extension in the group which is considered the main file
        # - subclass needs to override this
        return None

    @property
    def get_main_file(self):
        file_extension = self.get_main_file_type()
        if file_extension:
            for f in self.files.all():
                if f.extension == file_extension:
                    return f
        return None

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
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
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
    def _validate_set_file_type_inputs(cls, resource, file_id=None, folder_path=None):
        """Validation of *file_id* and *folder_path* for creating file type (aggregation)

        :param resource: an instance of resource type CompositeResource
        :param file_id: (optional) id of the resource file to be set as an aggregation type -
        if this is missing then folder_path must be specified
        :param folder_path: (optional) path of the folder which needs to be set to an aggregation
        type - if this is missing then file_id must be specified. If specified a path relative
        to the resource.file_path will be returned
        :raise  ValidationError if validation fails
        :return an instance of ResourceFile if validation is successful and the folder_path
        """

        if file_id is None and folder_path is None:
            raise ValueError("Must specify id of the file or path of the folder to set as an "
                             "aggregation type")
        if file_id is not None:
            # user selected a file to set aggregation
            res_file = get_resource_file_by_id(resource, file_id)
        else:
            # user selected a folder to set aggregation - check if the specified folder exists
            storage = resource.get_irods_storage()
            if folder_path.startswith("data/contents/"):
                folder_path = folder_path[len("data/contents/"):]
            path_to_check = os.path.join(resource.file_path, folder_path)
            if not storage.exists(path_to_check):
                msg = "Specified folder {} path does not exist in irods."
                msg = msg.format(path_to_check)
                raise ValidationError(msg)

            # check if an aggregation can be created from the specified folder
            aggregation_to_set = resource.get_folder_aggregation_type_to_set(path_to_check)
            if aggregation_to_set is None:
                msg = "Aggregation can't be created from the specified folder:{}"
                msg = msg.format(path_to_check)
                raise ValidationError(msg)

            # get the files from the specified folder location
            res_files = ResourceFile.list_folder(resource=resource, folder=folder_path,
                                                 sub_folders=False)
            if not res_files:
                msg = "The specified folder {} does not contain any file."
                msg = msg.format(path_to_check)
                raise ValidationError(msg)
            else:
                # check if the specified folder is suitable for aggregation
                if cls.check_files_for_aggregation_type(res_files):
                    # get the primary file suitable for creating a specific aggregation type
                    res_file = cls.get_primary_resouce_file(res_files)
                else:
                    res_file = None

        if res_file is None or not res_file.exists:
            raise ValidationError("File not found.")

        if res_file.has_logical_file:
            msg = "Selected {} {} is already part of an aggregation."
            if folder_path is None:
                msg = msg.format('file', res_file.file_name)
            else:
                msg = msg.format('folder', folder_path)
            raise ValidationError(msg)

        return res_file, folder_path

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
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
    def _cleanup_on_fail_to_create_aggregation(user, resource, folder_to_delete, original_folder,
                                               aggregation_from_folder):
        """Deletes folder if a new aggregation folder *folder_to_delete*  was created
        :param  user: user hwo was trying to create the aggregation
        :param  resource: an instance of CompositeResource for which the aggregation was created
        :param  folder_to_delete: the aggregation folder to delete
        :param  original_folder: folder path for the files originally located before moving to the
        new aggregation folder
        :param  aggregation_from_folder: (bool) a flag to indicate if the aggregation was being
        created from a folder or not
        """
        # had to import it here to avoid import loop
        from hs_core.views.utils import remove_folder, move_or_rename_file_or_folder

        new_folder_created = folder_to_delete and not aggregation_from_folder
        if new_folder_created:

            # delete if a new folder was created for the aggregation
            folder_to_remove = os.path.join('data', 'contents', folder_to_delete)
            res_files = ResourceFile.list_folder(resource=resource, folder=folder_to_delete,
                                                 sub_folders=False)
            # move the files from the folder to delete to the original folder
            if original_folder is None:
                original_folder = ''
            original_folder_path = os.path.join('data', 'contents', original_folder)
            for f in res_files:
                tgt_file_path = os.path.join(original_folder_path, f.file_name)
                src_file_path = os.path.join('data', 'contents', f.short_path)
                move_or_rename_file_or_folder(user, resource.short_id, src_file_path,
                                              tgt_file_path, validate_move_rename=False)
            remove_folder(user, resource.short_id, folder_to_remove)

    def get_aggregation_class_name(self):
        """Return the class name of the logical type (aggregation type)"""
        return self.__class__.__name__

    @staticmethod
    def get_aggregation_type_name():
        """Return the appropriate aggregation name needed for aggregation xml metadata and
        map document. Subclasses must implement this method.
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
    def resource(self):
        res_file = self.files.all().first()
        if res_file is not None:
            return res_file.resource
        else:
            return None

    @property
    def can_contain_folders(self):
        """By default an aggregation can't have folders"""
        return False

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
        is not allowed to be zipped"""
        return False

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
        if self.is_single_file_aggregation:
            # self is a single file aggregation type
            return self.files.first().short_path
        else:
            # self is a multi- file aggregation type
            return self.files.first().file_folder

    @property
    def metadata_short_file_path(self):
        """File path of the aggregation metadata xml file relative to {resource_id}/data/contents/
        """

        xml_file_name = self.aggregation_name
        if "/" in xml_file_name:
            xml_file_name = os.path.basename(xml_file_name)
        xml_file_name += "_meta.xml"
        file_folder = self.files.first().file_folder
        if file_folder is not None:
            xml_file_name = os.path.join(file_folder, xml_file_name)
        return xml_file_name

    @property
    def metadata_file_path(self):
        """Full file path of the aggregation metadata xml file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.metadata_short_file_path)

    @property
    def map_short_file_path(self):
        """File path of the aggregation map xml file relative to {resource_id}/data/contents/
        """
        xml_file_name = self.aggregation_name
        if "/" in xml_file_name:
            xml_file_name = os.path.basename(xml_file_name)
        xml_file_name += "_resmap.xml"
        file_folder = self.files.first().file_folder
        if file_folder is not None:
            xml_file_name = os.path.join(file_folder, xml_file_name)
        return xml_file_name

    @property
    def map_file_path(self):
        """Full file path of the aggregation map xml file starting with {resource_id}/data/contents/
        """
        return os.path.join(self.resource.file_path, self.map_short_file_path)

    @property
    def is_single_file_aggregation(self):
        """
        Returns True if the aggregation consists of only one file, otherwise, False.
        Subclasses that support only single file must override this property

        :return: True or False
        """
        return False

    def add_resource_file(self, res_file):
        """Makes a ResourceFile (res_file) object part of this logical file object. If res_file
        is already associated with any other logical file object, this function does not do
        anything to that logical object. The caller needs to take necessary action for the
        previously associated logical file object. If res_file is already part of this
        logical file, it raise ValidationError.

        :param res_file an instance of ResourceFile
        """

        if res_file in self.files.all():
            raise ValidationError("Resource file is already part of this logical file.")

        res_file.logical_file_content_object = self
        res_file.save()

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
                resource, uploaded_file, folder=upload_folder
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
            self.add_resource_file(res_file)

        return res_files

    def copy_resource_files(self, resource, files_to_copy, tgt_folder):
        """
        A helper for creating aggregation. Copies the given list of resource files to the the
        specified folder path and then makes those copied files as part of the aggregation
        :param  resource: an instance of CompositeResource for which aggregation being created
        :param  files_to_copy: a list of resource file paths in irods that need to be copied
        to a specified directory *tgt_folder* and made part of this aggregation
        """

        for res_file in files_to_copy:
            source_path = res_file.storage_path
            copied_res_file = ResourceFile.create(resource=resource,
                                                  file=None,
                                                  folder=tgt_folder,
                                                  source=source_path)

            # make the copied file as part of the aggregation/file type
            self.add_resource_file(copied_res_file)

    def get_copy(self):
        """creates a copy of this logical file object with associated metadata needed to support
        resource copy.
        Note: This copied logical file however does not have any association with resource files
        """
        copy_of_logical_file = type(self).create()
        copy_of_logical_file.dataset_name = self.dataset_name
        copy_of_logical_file.metadata.extra_metadata = copy.deepcopy(self.metadata.extra_metadata)
        copy_of_logical_file.metadata.keywords = self.metadata.keywords
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.save()
        # copy the metadata elements
        elements_to_copy = self.metadata.get_metadata_elements()
        for element in elements_to_copy:
            element_args = model_to_dict(element)
            element_args.pop('content_type')
            element_args.pop('id')
            element_args.pop('object_id')
            copy_of_logical_file.metadata.create_element(element.term, **element_args)

        return copy_of_logical_file

    @classmethod
    def compute_file_type_folder(cls, resource, file_folder, file_name):
        """
        Computes the new folder path where the file type files will be stored
        :param resource: an instance of BaseResource
        :param file_folder: current file folder of the file which is being set to a specific file
        type
        :param file_name: name of the file (without extension) which is being set to a specific
        file type
        :return: computed new folder path
        """
        current_folder_path = 'data/contents'
        if file_folder is not None:
            current_folder_path = os.path.join(current_folder_path, file_folder)

        new_folder_path = os.path.join(current_folder_path, file_name)

        # To avoid folder creation failure when there is already matching
        # directory path, first check that the folder does not exist
        # If folder path exists then change the folder name by adding a number
        # to the end
        istorage = resource.get_irods_storage()
        counter = 0
        while istorage.exists(os.path.join(resource.short_id, new_folder_path)):
            new_file_name = file_name + "_{}".format(counter)
            new_folder_path = os.path.join(current_folder_path, new_file_name)
            counter += 1
        return new_folder_path

    def logical_delete(self, user, delete_res_files=True):
        """
        Deletes the logical file as well as all resource files associated with this logical file.
        This function is primarily used by the system to delete logical file object and associated
        metadata as part of deleting a resource file object. Any time a request is made to
        deleted a specific resource file object, if the the requested file is part of a
        logical file then all files in the same logical file group will be deleted. if custom logic
        requires deleting logical file object (LFO) then instead of using LFO.delete(), you must
        use LFO.logical_delete()
        :param delete_res_files If True all resource files that are part of this logical file will
        be deleted
        """

        from hs_core.hydroshare.resource import delete_resource_file

        # delete associated metadata and map xml documents
        istorage = self.resource.get_irods_storage()
        if istorage.exists(self.metadata_file_path):
            istorage.delete(self.metadata_file_path)
        if istorage.exists(self.map_file_path):
            istorage.delete(self.map_file_path)

        # delete all resource files associated with this instance of logical file
        if delete_res_files:
            for f in self.files.all():
                delete_resource_file(f.resource.short_id, f.id, user,
                                     delete_logical_file=False)

        # delete logical file first then delete the associated metadata file object
        # deleting the logical file object will not automatically delete the associated
        # metadata file object
        metadata = self.metadata if self.has_metadata else None
        super(AbstractLogicalFile, self).delete()
        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. However, it doesn't delete any resource files that are part of the aggregation."""

        # delete associated metadata and map xml document
        istorage = self.resource.get_irods_storage()
        if istorage.exists(self.metadata_file_path):
            istorage.delete(self.metadata_file_path)
        if istorage.exists(self.map_file_path):
            istorage.delete(self.map_file_path)

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
        super(AbstractLogicalFile, self).delete()
        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()

    def create_aggregation_xml_documents(self, create_map_xml=True):
        """Creates aggregation map xml and aggregation metadata xml files
        :param  create_map_xml: if true, aggregation map xml file will be created
        """

        log = logging.getLogger()

        # create a temp dir where the xml files will be temporarily saved before copying to iRODS
        tmpdir = os.path.join(settings.TEMP_FILE_DIR, str(random.getrandbits(32)), uuid4().hex)
        istorage = self.resource.get_irods_storage()

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
            istorage.saveFile(meta_from_file_name, to_file_name, True)
            log.debug("Aggregation metadata xml file:{} created".format(to_file_name))

            if create_map_xml:
                with open(map_from_file_name, 'w') as out:
                    out.write(self._generate_map_xml())
                to_file_name = self.map_file_path
                istorage.saveFile(map_from_file_name, to_file_name, True)
                log.debug("Aggregation map xml file:{} created".format(to_file_name))
            # setting bag flag to dirty - as resource map document needs to be re-generated as
            # resource map xml file has references to aggregation map xml file paths
            set_dirty_bag_flag(self.resource)
        except Exception as ex:
            log.error("Failed to create aggregation metadata xml file. Error:{}".format(ex.message))
            raise ex
        finally:
            shutil.rmtree(tmpdir)

    @staticmethod
    def _check_create_aggregation_folder(selected_res_file, selected_folder,
                                         aggregation_file_count):
        """
        A helper that checks if a new folder needs to be created for the aggregation
        :param: selected_res_file: the file that has been selected by the user to set aggregation
        :param: aggregation_file_count: number of files that are going to be part of the
        aggregation to be created
        """
        create_new_folder = False
        file_folder = selected_res_file.file_folder
        if file_folder and not selected_folder:
            resource = selected_res_file.resource
            istorage = resource.get_irods_storage()
            store = istorage.listdir(selected_res_file.dir_path)

            folders = store[0]
            files = store[1]
            if folders:
                # since there are folders under dir_path - need to create a new folder for
                # the new aggregation
                create_new_folder = True

            elif len(files) > aggregation_file_count:
                # there are additional files at selected_res_file.dir_path - need to create a new
                # folder new aggregation
                create_new_folder = True
        else:
            create_new_folder = True

        return create_new_folder

    def _generate_map_xml(self):
        """Generates the xml needed to write to the aggregation map xml document"""

        from hs_core.hydroshare.utils import current_site_url, get_file_mime_type

        current_site_url = current_site_url()
        # This is the qualified resource url.
        hs_res_url = os.path.join(current_site_url, 'resource', self.resource.file_path)
        # this is the path to the resourcemedata file for download
        aggr_metadata_file_path = self.metadata_short_file_path
        metadata_url = os.path.join(hs_res_url, aggr_metadata_file_path)
        # this is the path to the aggregation resourcemap file for download
        aggr_map_file_path = self.map_short_file_path
        res_map_url = os.path.join(hs_res_url, aggr_map_file_path)

        # make the resource map:
        utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
        utils.namespaceSearchOrder.append('citoterms')

        ag_url = res_map_url + '#aggregation'
        a = Aggregation(ag_url)

        # Set properties of the aggregation
        a._dc.title = self.dataset_name
        agg_type_url = "{site}/terms/{aggr_type}".format(site=current_site_url,
                                                         aggr_type=self.get_aggregation_type_name())
        a._dcterms.type = URIRef(agg_type_url)
        a._citoterms.isDocumentedBy = metadata_url
        a._ore.isDescribedBy = res_map_url

        res_type_aggregation = AggregatedResource(agg_type_url)
        res_type_aggregation._rdfs.label = self.get_aggregation_display_name()
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
            res_uri = u'{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url,
                res_id=self.resource.short_id,
                file_name=f.short_path)
            resFiles.append(AggregatedResource(res_uri))
            resFiles[n]._ore.isAggregatedBy = ag_url
            resFiles[n]._dc.format = get_file_mime_type(os.path.basename(f.short_path))

        # Add the resource files to the aggregation
        a.add_resource(resMetaFile)
        for f in resFiles:
            a.add_resource(f)

        # Register a serializer with the aggregation, which creates a new ResourceMap that
        # needs a URI
        serializer = RdfLibSerializer('xml')
        # resMap = a.register_serialization(serializer, res_map_url)
        a.register_serialization(serializer, res_map_url)

        # Fetch the serialization
        remdoc = a.get_serialization()
        # remove this additional xml element - not sure why it gets added
        # <ore:aggregates rdf:resource="http://hydroshare.org/terms/[aggregation name]"/>
        xml_element_to_replace = '<ore:aggregates rdf:resource="{}"/>\n'.format(agg_type_url)
        xml_string = remdoc.data.replace(xml_element_to_replace, '')
        return xml_string
