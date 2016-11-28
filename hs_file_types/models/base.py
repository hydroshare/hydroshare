from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from django.contrib.postgres.fields import HStoreField

from dominate.tags import *
from lxml import etree

from hs_core.hydroshare.utils import get_resource_file_name_and_extension
from hs_core.models import ResourceFile, AbstractMetaDataElement, Coverage, CoreMetaData


class AbstractFileMetaData(models.Model):
    """ base class for HydroShare file type metadata """

    # one temporal coverage and one spatial coverage
    coverages = GenericRelation(Coverage)
    # kye/value metadata
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

    def delete_all_elements(self):
        self.coverages.all().delete()

    def get_html(self):
        # subclass must override
        # returns a string representing html code for display of metadata in view mode
        dataset_name_div = div()
        if self.logical_file.dataset_name:
            with dataset_name_div:
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            th("Title", cls="text-muted")
                            td(self.logical_file.dataset_name)

        if self.extra_metadata:
            root_div = div(cls="col-sm-12 content-block")
            root_div.add(dataset_name_div)
            with root_div:
                legend('Extended Metadata')
                with table(cls="table table-striped funding-agencies-table"):
                    with tbody():
                        with tr(cls="header-row"):
                            th("Key")
                            th("Value")
                        for k, v in self.extra_metadata.iteritems():
                            with tr(data_key=k):
                                td(k)
                                td(v)

            return root_div.render()
        else:
            return dataset_name_div.render()

    def get_html_forms(self, datatset_name_form=True):
        root_div = div()

        def get_add_keyvalue_button():
            add_key_value_btn = a(cls="btn btn-success", type="button", data_toggle="modal",
                                  data_target="#add-keyvalue-filetype-modal",
                                  style="margin-bottom:20px;")
            with add_key_value_btn:
                with span(cls="glyphicon glyphicon-plus"):
                    span("Add Key/Value", cls="button-label")
            return add_key_value_btn

        with root_div:
            if datatset_name_form:
                self._get_dataset_name_form()
            # root_div_extra = div(cls="col-sm-12 content-block", id="filetype-extra-metadata")
            if self.extra_metadata:
                root_div_extra = div(cls="col-sm-12 content-block", id="filetype-extra-metadata")
                with root_div_extra:
                    legend('Extended Metadata')
                    get_add_keyvalue_button()
                    with table(cls="table table-striped funding-agencies-table"):
                        with tbody():
                            with tr(cls="header-row"):
                                th("Key")
                                th("Value")
                                th("Edit/Remove")
                            counter = 0
                            for k, v in self.extra_metadata.iteritems():
                                counter += 1
                                with tr(data_key=k):
                                    td(k)
                                    td(v)
                                    with td():
                                        a(data_toggle="modal", data_placement="auto", title="Edit",
                                          cls="glyphicon glyphicon-pencil icon-button icon-blue",
                                          data_target="#edit-keyvalue-filetype-modal"
                                                      "-{}".format(counter))
                                        a(data_toggle="modal", data_placement="auto",
                                          title="Remove",
                                          cls="glyphicon glyphicon-trash icon-button btn-remove",
                                          data_target="#delete-keyvalue-filetype-modal"
                                                      "-{}".format(counter))

                    self._get_add_key_value_modal_form()
                    self._get_edit_key_value_modal_forms()
                    self._get_delete_key_value_modal_forms()
                return root_div
            else:
                root_div_extra = div(cls="col-sm-12 content-block", id="filetype-extra-metadata")
                with root_div_extra:
                    legend('Extended Metadata')
                    get_add_keyvalue_button()
                    self._get_add_key_value_modal_form()
                return root_div

    def has_all_required_elements(self):
        return True

    @classmethod
    def get_supported_element_names(cls):
        return ['Coverage']

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
        NAMESPACES = CoreMetaData.NAMESPACES
        dataset_container = etree.SubElement(
            container, '{%s}Dataset' % NAMESPACES['hsterms'])
        rdf_Description = etree.SubElement(dataset_container, '{%s}Description' % NAMESPACES['rdf'])
        hsterms_datatype = etree.SubElement(rdf_Description, '{%s}dataType' % NAMESPACES['hsterms'])
        hsterms_datatype.text = self.logical_file.data_type
        if self.logical_file.dataset_name:
            hsterms_datatitle = etree.SubElement(rdf_Description,
                                                 '{%s}dataTitle' % NAMESPACES['hsterms'])
            hsterms_datatitle.text = self.logical_file.dataset_name

        # add fileType node
        for res_file in self.logical_file.files.all():
            hsterms_datafile = etree.SubElement(rdf_Description,
                                                '{%s}dataFile' % NAMESPACES['hsterms'])
            rdf_dataFile_Description = etree.SubElement(hsterms_datafile,
                                                        '{%s}Description' % NAMESPACES['rdf'])
            dc_title = etree.SubElement(rdf_dataFile_Description,
                                        '{%s}title' % NAMESPACES['dc'])

            file_name = get_resource_file_name_and_extension(res_file)[1]
            dc_title.text = file_name

            dc_format = etree.SubElement(rdf_dataFile_Description, '{%s}format' % NAMESPACES['dc'])
            dc_format.text = res_file.mime_type

            # TODO: check if we should include the file size here

        self.add_extra_metadata_to_xml_container(rdf_Description)
        for coverage in self.coverages.all():
            coverage.add_to_xml_container(rdf_Description)
        return rdf_Description

    def add_extra_metadata_to_xml_container(self, container):
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

    def create_element(self, element_model_name, **kwargs):
        # had to import here to avoid circular import
        from hs_file_types.utils import update_resource_coverage_element
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        if element_model_name.lower() == "coverage":
            resource = element.metadata.logical_file.resource
            update_resource_coverage_element(resource)
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        # had to import here to avoid circular import
        from hs_file_types.utils import update_resource_coverage_element
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)
        if element_model_name.lower() == "coverage":
            element = model_type.model_class().objects.get(id=element_id)
            resource = element.metadata.logical_file.resource
            update_resource_coverage_element(resource)

    def delete_element(self, element_model_name, element_id):
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)

    def _get_metadata_element_model_type(self, element_model_name):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported metadata elements."
                                  % element_model_name)

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label='hs_geo_raster_resource',
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
        raise NotImplementedError

    def _get_dataset_name_form(self):
        form_action = "/hsapi/_internal/{0}/{1}/update-filetype-dataset-name/"
        form_action = form_action.format(self.logical_file.__class__.__name__, self.logical_file.id)
        root_div = div(cls="col-sm-12 col-xs-12")
        dataset_name = self.logical_file.dataset_name if self.logical_file.dataset_name else ""
        with root_div:
            with form(action=form_action, id="filetype-dataset-name",
                      method="post", enctype="multipart/form-data"):
                div("{% csrf_token %}")
                with div(cls="form-group"):
                    with div(cls="control-group"):
                        legend('Title')
                        # label("Title", cls="control-label requiredField",
                        #       fr="file_dataset_name")
                        with div(cls="controls"):
                            input(value=dataset_name,
                                  cls="form-control input-sm textinput textInput",
                                  id="file_dataset_name", maxlength="250",
                                  name="dataset_name", type="text")
                with div(cls="row", style="margin-top:10px;"):
                    with div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        button("Save changes", cls="btn btn-primary pull-right",
                               onclick="metadata_update_ajax_submit('filetype-dataset-name'); "
                                       "return false;", style="display: none;", type="button")
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
                                                 name="value", type="text")
                        with div(cls="modal-footer"):
                            button("Cancel", type="button", cls="btn btn-default",
                                   data_dismiss="modal")
                            button("OK", type="button", cls="btn btn-primary",
                                   onclick="addFileTypeExtraMetadata(); return true;")
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
                                                         name="value", type="text")
                                with div(cls="modal-footer"):
                                    button("Cancel", type="button", cls="btn btn-default",
                                           data_dismiss="modal")
                                    button("OK", type="button", cls="btn btn-primary",
                                           onclick="updateFileTypeExtraMetadata('{}'); "
                                                   "return true;".format(form_id))
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
                                                         name="value", type="text",
                                                         readonly="readonly")
                                with div(cls="modal-footer"):
                                    button("Cancel", type="button", cls="btn btn-default",
                                           data_dismiss="modal")
                                    button("Delete", type="button", cls="btn btn-danger",
                                           onclick="deleteFileTypeExtraMetadata('{}'); "
                                                   "return true;".format(form_id))
        return root_div


class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    # files associated with this logical file group
    files = GenericRelation(ResourceFile, content_type_field='logical_file_content_type',
                            object_id_field='logical_file_object_id')
    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)
    # this will be used for hsterms:dataType in resourcemetadata.xml
    # each specific logical type needs to rest this field
    data_type = "Generic data"

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
        return self.files.all().first().resource

    @property
    def allow_resource_file_move(self):
        return True

    @property
    def allow_resource_file_rename(self):
        return True

    def logical_delete(self, user, delete_res_files=True):
        # deletes the logical file as well as all resource files associated with this logical file
        # mostly this will be used by the system to delete logical file object and associated
        # metadata as part of deleting a resource file object. However, if custom logic requires
        # deleting logical file object (lfo) then instead of using lfo.delete(), you must use
        # lfo.logical_delete()
        from hs_core.hydroshare.resource import delete_resource_file
        self.delete_metadata()
        # delete all resource files associated with this instance of logical file
        if delete_res_files:
            for f in self.files.all():
                delete_resource_file(f.resource.short_id, f.id, user,
                                     delete_logical_file=False)

        # delete logical file first then delete the associated metadata file object
        metadata = self.metadata
        super(AbstractLogicalFile, self).delete()
        metadata.delete()

    def delete_metadata(self):
        # delete all metadata associated with this file type
        if self.has_metadata:
            self.metadata.delete_all_elements()
