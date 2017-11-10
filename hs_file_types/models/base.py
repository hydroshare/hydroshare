import os
import copy

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.models import model_to_dict

from django.contrib.postgres.fields import HStoreField, ArrayField

from dominate.tags import div, legend, table, tr, tbody, thead, td, th, \
    span, a, form, button, label, textarea, h4, input, ul, li, p

from lxml import etree

from hs_core.hydroshare.utils import get_resource_file_name_and_extension, current_site_url
from hs_core.models import ResourceFile, AbstractMetaDataElement, Coverage, CoreMetaData


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

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of all the metadata elements associated with this
        logical file type instance. Subclass must override this if it has additional metadata
        elements."""

        NAMESPACES = CoreMetaData.NAMESPACES
        dataset_container = etree.SubElement(
            container, '{%s}Dataset' % NAMESPACES['hsterms'])
        rdf_Description = etree.SubElement(dataset_container, '{%s}Description' % NAMESPACES['rdf'])
        dc_datatype = etree.SubElement(rdf_Description, '{%s}type' % NAMESPACES['dc'])
        data_type = current_site_url() + "/terms/" + self.logical_file.data_type
        dc_datatype.set('{%s}resource' % NAMESPACES['rdf'], data_type)

        if self.logical_file.dataset_name:
            dc_datatitle = etree.SubElement(rdf_Description, '{%s}title' % NAMESPACES['dc'])
            dc_datatitle.text = self.logical_file.dataset_name

        # add fileType node
        for res_file in self.logical_file.files.all():
            hsterms_datafile = etree.SubElement(rdf_Description,
                                                '{%s}dataFile' % NAMESPACES['hsterms'])
            rdf_dataFile_Description = etree.SubElement(hsterms_datafile,
                                                        '{%s}Description' % NAMESPACES['rdf'])
            file_uri = u'{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
                hs_url=current_site_url(),
                res_id=self.logical_file.resource.short_id,
                file_name=res_file.short_path)
            rdf_dataFile_Description.set('{%s}about' % NAMESPACES['rdf'], file_uri)
            dc_title = etree.SubElement(rdf_dataFile_Description,
                                        '{%s}title' % NAMESPACES['dc'])

            file_name = get_resource_file_name_and_extension(res_file)[1]
            dc_title.text = file_name

            dc_format = etree.SubElement(rdf_dataFile_Description, '{%s}format' % NAMESPACES['dc'])
            dc_format.text = res_file.mime_type

        self.add_keywords_to_xml_container(rdf_Description)
        self.add_extra_metadata_to_xml_container(rdf_Description)
        for coverage in self.coverages.all():
            coverage.add_to_xml_container(rdf_Description)
        return rdf_Description

    def add_extra_metadata_to_xml_container(self, container):
        """Generates xml+rdf representation of the all the key/value metadata associated
        with an instance of the logical file type"""

        for key, value in self.extra_metadata.iteritems():
            hsterms_key_value = etree.SubElement(
                container, '{%s}extendedMetadata' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_key_value_rdf_Description = etree.SubElement(
                hsterms_key_value, '{%s}Description' % CoreMetaData.NAMESPACES['rdf'])
            hsterms_key = etree.SubElement(hsterms_key_value_rdf_Description,
                                           '{%s}key' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_key.text = key
            hsterms_value = etree.SubElement(hsterms_key_value_rdf_Description,
                                             '{%s}value' % CoreMetaData.NAMESPACES['hsterms'])
            hsterms_value.text = value

    def add_keywords_to_xml_container(self, container):
        """Generates xml+rdf representation of the all the keywords associated
        with an instance of the logical file type"""

        for kw in self.keywords:
            dc_subject = etree.SubElement(container, '{%s}subject' % CoreMetaData.NAMESPACES['dc'])
            dc_subject.text = kw

    def create_element(self, element_model_name, **kwargs):
        # had to import here to avoid circular import
        from hs_file_types.utils import update_resource_coverage_element
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        if element_model_name.lower() == "coverage":
            resource = element.metadata.logical_file.resource
            # resource will be None in case of coverage element being
            # created as part of copying a resource that supports logical file
            # types
            if resource is not None:
                update_resource_coverage_element(resource)
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        # had to import here to avoid circular import
        from hs_file_types.utils import update_resource_coverage_element
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)
        self.is_dirty = True
        self.save()
        if element_model_name.lower() == "coverage":
            element = model_type.model_class().objects.get(id=element_id)
            resource = element.metadata.logical_file.resource
            update_resource_coverage_element(resource)

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

    class Meta:
        abstract = True

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # any file can be part of this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # can store any file types in this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def type_name(cls):
        return cls.__name__

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
        """allows a folder containing resource file(s) that are part of this logical file type
        to be zipped"""
        return True

    @property
    def supports_delete_folder_on_zip(self):
        """allows the original folder to be deleted upon zipping of that folder"""
        return True

    @property
    def supports_unzip(self):
        """allows a zip file that is part of this logical file type to get unzipped"""
        return True

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

    # TODO: unit test this
    def reset_to_generic(self, user):
        """
        This sets all files in this logical file group to GenericLogicalFile type

        :param  user: user who is re-setting to generic file type
        :return:
        """
        from .generic import GenericLogicalFile

        for res_file in self.files.all():
            if res_file.has_logical_file:
                res_file.logical_file.logical_delete(user=user, delete_res_files=False)
            logical_file = GenericLogicalFile.create()
            res_file.logical_file_content_object = logical_file
            res_file.save()

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
