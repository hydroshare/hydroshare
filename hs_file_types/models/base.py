import copy

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.models import model_to_dict

from django.contrib.postgres.fields import HStoreField, ArrayField

from dominate.tags import div, legend, table, tr, tbody, td, th, span, a, form, button, label, \
    textarea, h4, input

from lxml import etree

from hs_core.hydroshare.utils import get_resource_file_name_and_extension
from hs_core.models import AbstractMetaDataElement, Coverage, CoreMetaData


class BaseFileMetaData(models.Model):
    file_metadata_type = models.CharField(max_length=100, default="Generic")
    # key/value metadata
    extra_metadata = HStoreField(default={})
    keywords = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[])

    def delete_all_elements(self):
        self.extra_metadata = {}
        self.keywords = []
        self.save()

    @classmethod
    def get_metadata_element_classes(cls):
        return {'coverage': Coverage}

    @classmethod
    def get_supported_element_names(cls):
        return ['coverage']


class BaseMetaDataElement(models.Model):
    element_type = models.CharField(max_length=100, default="Generic")
    data = HStoreField(default={})
    metadata = models.ForeignKey(BaseFileMetaData)

    @classmethod
    def validate(cls, update_or_create='create', **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        data = kwargs.get('data', None)
        if data is None:
            raise ValidationError("Value for data attribute is missing")
        if not isinstance(data, dict):
            raise ValidationError("Value for data attribute must be a dict")
        metadata = kwargs.get('metadata', None)
        if metadata is None or not isinstance(metadata, BaseFileMetaData):
            raise ValidationError("Value for metadata attribute is missing")

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = BaseMetaDataElement.objects.get(id=element_id)
        element.data = kwargs['data']
        element.save()

# TODO: This class will not be needed once we migrate raster file metadata to HStore
class AbstractFileMetaData(models.Model):
    """ base class for HydroShare file type metadata """

    # one temporal coverage and one spatial coverage
    coverages = GenericRelation(Coverage)
    # kye/value metadata
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

    def get_metadata_elements(self):
        """returns a list of all metadata elements (instances of AbstractMetaDataElement)
         associated with this file type metadata object.
        """
        return list(self.coverages.all())

    def delete_all_elements(self):
        self.coverages.all().delete()
        self.extra_metadata = {}
        self.save()

    def get_html(self):
        """Generates html for displaying all metadata elements associated with this logical file.
        Subclass must override to include additional html for additional metadata it supports.
        """

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
        """generates html forms for all the metadata elements associated with this logical file
        type
        :param datatset_name_form If True then a form for editing dataset_name (title) attribute is
        included
        """
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
        """Generates xml+rdf representation of all the metadata elements associated with this
        logical file type instance. Subclass must override this if it has additional metadata
        elements."""

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
        """Subclass must implement this function to validate data for for the
        specified metadata element (element_name)"""
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

# TODO: This class will not be needed once we migrate the raster file metadata to HStore
class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    # files associated with this logical file group
    files = GenericRelation("hs_core.ResourceFile", content_type_field='logical_file_content_type',
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

    def get_copy(self):
        """creates a copy of this logical file object with associated metadata needed to support
        resource copy.
        Note: This copied logical file however does not have any association with resource files
        """
        copy_of_logical_file = type(self).create()
        copy_of_logical_file.dataset_name = self.dataset_name
        copy_of_logical_file.metadata.extra_metadata = copy.deepcopy(self.metadata.extra_metadata)
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


class BaseLogicalFile(models.Model):
    """ base class for HydroShare file types """

    logical_file_type = models.CharField(max_length=100, default="GenericLogicalFile")

    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)

    # this will be used for hsterms:dataType in resourcemetadata.xml
    # each specific logical type needs to rest this field
    data_type = "Generic data"

    metadata = models.OneToOneField(BaseFileMetaData, related_name="logical_file")

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        generic_metadata = BaseFileMetaData.objects.create(file_metadata_type='Generic')
        return cls.objects.create(metadata=generic_metadata)

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

        res_file.logical_file_new = self
        res_file.save()

    def get_copy(self):
        """creates a copy of this logical file object with associated metadata needed to support
        resource copy.
        Note: This copied logical file however does not have any association with resource files
        """
        copy_of_logical_file = type(self).create()
        copy_of_logical_file.dataset_name = self.dataset_name
        copy_of_logical_file.metadata.extra_metadata = copy.deepcopy(self.metadata.extra_metadata)
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
        super(BaseLogicalFile, self).delete()
        if metadata is not None:
            # this should also delete on all metadata elements that have generic relations with
            # the metadata object
            metadata.delete()


class LogicalFileTypeManager(models.Manager):
    def __init__(self, logical_file_type=None, *args, **kwargs):
        self.logical_file_type = logical_file_type
        super(LogicalFileTypeManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        if self.logical_file_type is None:
            kwargs.pop('logical_file_type', None)
        return super(LogicalFileTypeManager, self).create(*args, **kwargs)

    def get_queryset(self):
        qs = super(LogicalFileTypeManager, self).get_queryset()
        if self.logical_file_type:
            qs = qs.filter(logical_file_type=self.logical_file_type)
        return qs