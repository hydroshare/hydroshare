import requests
import base64
import imghdr

from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement
from .utils import get_SupportedResTypes_choices, get_SupportedFileTypes_choices


class ToolResource(BaseResource):
    objects = ResourceManager('ToolResource')

    class Meta:
        proxy = True
        verbose_name = 'Web App Resource'

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def allow_multiple_file_upload(cls):
        # no file can be uploaded
        return False

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False

    @property
    def metadata(self):
        md = ToolMetaData()
        return self._get_metadata(md)

    @property
    def can_be_published(self):
        return False


processor_for(ToolResource)(resource_processor)

SupportedResourcePermission_choices = (
        ('2', 'Edit Resource Metadata and Files'),
        ('1', 'Read Resource Metadata and Files'),
        ('0', 'Read Resource Metadata'),
    )


class SupportedResourcePermission(AbstractMetaDataElement):
    term = "SupportedResourcePermission"
    value = models.CharField(max_length=1024, default="1",
                             choices=SupportedResourcePermission_choices)

    class Meta:
        # UserPermissionOverAssociatedResource element is not repeatable
        unique_together = ("content_type", "object_id")


class AppHomePageUrl(AbstractMetaDataElement):
    term = 'AppHomePageUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # AppHomePageUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class RequestUrlBase(AbstractMetaDataElement):
    term = 'RequestUrlBase'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolVersion(AbstractMetaDataElement):
    term = 'AppVersion'
    value = models.CharField(max_length=128, blank=True)

    class Meta:
        # ToolVersion element is not repeatable
        unique_together = ("content_type", "object_id")


class SupportedResTypeChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedResTypes(AbstractMetaDataElement):
    term = 'SupportedResTypes'
    supported_res_types = models.ManyToManyField(SupportedResTypeChoices,
                                                 blank=True,
                                                 related_name="associated_with")

    class Meta:
        # SupportedResTypes element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_supported_res_types_str(self):
        return ','.join([parameter.description for parameter in self.supported_res_types.all()])

    @classmethod
    def _add_supported_res_type(cls, meta_instance, supported_res_types):

        for res_type in supported_res_types:
            # there are two possibilities for res_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the resource)
            if isinstance(res_type, int):
                # "copy res" or "create a new version"
                qs = SupportedResTypeChoices.objects.filter(id=res_type)
                if not qs.exists():
                    raise
                meta_instance.supported_res_types.add(qs[0])

            elif isinstance(res_type, basestring):
                # create or update res
                qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type)
                if qs.exists():
                    meta_instance.supported_res_types.add(qs[0])
                else:
                    meta_instance.supported_res_types.create(description=res_type)
            else:
                raise ValidationError("No supported_res_types parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_supported_res_types(cls, supported_res_types):
        for res_type in supported_res_types:
            if isinstance(res_type, basestring) \
                    and res_type not in [res_type_choice[0]
                                         for res_type_choice in get_SupportedResTypes_choices()]:
                raise ValidationError('Invalid supported_res_types:%s' % res_type)

    @classmethod
    def create(cls, **kwargs):
        if 'supported_res_types' in kwargs:
            cls._validate_supported_res_types(kwargs['supported_res_types'])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedResTypes.objects.create(content_object=metadata_obj)

            cls._add_supported_res_type(new_meta_instance, kwargs['supported_res_types'])
            return new_meta_instance
        else:
            raise ValidationError("No supported_res_types parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedResTypes.objects.get(id=element_id)

        if 'supported_res_types' in kwargs:
            cls._validate_supported_res_types(kwargs['supported_res_types'])

            meta_instance.supported_res_types.clear()
            cls._add_supported_res_type(meta_instance, kwargs['supported_res_types'])
            meta_instance.save()
        else:
            raise ValidationError("No supported_res_types parameter was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedResTypes element can't be deleted.")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class SupportedSharingStatusChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedSharingStatus(AbstractMetaDataElement):
    term = 'SupportedSharingStatus'
    sharing_status = models.ManyToManyField(SupportedSharingStatusChoices,
                                            blank=True,
                                            related_name="associated_with")

    class Meta:
        # SupportedSharingStatus element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_sharing_status_str(self):
        return ', '.join([parameter.description for parameter in self.sharing_status.all()])

    @classmethod
    def _add_sharing_status(cls, meta_instance, sharing_status_list):
        for sharing_status in sharing_status_list:
            # there are two possibilities for res_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the resource)
            if isinstance(sharing_status, int):
                # "copy res" or "create a new version"
                qs = SupportedSharingStatusChoices.objects.filter(id=sharing_status)
                if not qs.exists():
                    raise
                meta_instance.sharing_status.add(qs[0])
            elif isinstance(sharing_status, basestring):
                # create or update res
                qs = SupportedSharingStatusChoices.objects.\
                    filter(description__iexact=sharing_status)
                if qs.exists():
                    meta_instance.sharing_status.add(qs[0])
                else:
                    meta_instance.sharing_status.create(description=sharing_status)
            else:
                raise ValidationError("No sharing_status parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_sharing_status(cls, sharing_status_list):
        for sharing_status in sharing_status_list:
            if isinstance(sharing_status, basestring) and \
                            sharing_status not in \
                            ["Published", "Public", "Discoverable", "Private"]:
                raise ValidationError('Invalid sharing_status:%s' % sharing_status)

    @classmethod
    def create(cls, **kwargs):
        if 'sharing_status' in kwargs:
            cls._validate_sharing_status(kwargs["sharing_status"])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedSharingStatus.objects.create(content_object=metadata_obj)

            cls._add_sharing_status(new_meta_instance, kwargs['sharing_status'])
            return new_meta_instance
        else:
            raise ValidationError("No sharing_status parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedSharingStatus.objects.get(id=element_id)
        if 'sharing_status' in kwargs:
            cls._validate_sharing_status(kwargs["sharing_status"])

            meta_instance.sharing_status.clear()

            cls._add_sharing_status(meta_instance, kwargs['sharing_status'])
            meta_instance.save()
        else:
            raise ValidationError("No sharing_status parameter "
                                  "was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedSharingStatus element can't be deleted.")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class SupportedFileTypeChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedFileTypes(AbstractMetaDataElement):
    term = 'SupportedFileTypes'
    supported_file_types = models.ManyToManyField(SupportedFileTypeChoices,
                                                  blank=True,
                                                  related_name="associated_with")

    def get_supported_file_types_str(self):
        return ','.join([parameter.description for parameter in self.supported_file_types.all()])

    @classmethod
    def _add_supported_file_type(cls, meta_instance, supported_file_types):

        for file_type in supported_file_types:
            # there are two possibilities for file_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the resource)
            if isinstance(file_type, int):
                # "copy res" or "create a new version"
                qs = SupportedFileTypeChoices.objects.filter(id=file_type)
                if not qs.exists():
                    raise
                meta_instance.supported_file_types.add(qs[0])

            elif isinstance(file_type, basestring):
                # create or update res
                qs = SupportedFileTypeChoices.objects.filter(description__iexact=file_type)
                if qs.exists():
                    meta_instance.supported_file_types.add(qs[0])
                else:
                    meta_instance.supported_file_types.create(description=file_type)
            else:
                raise ValidationError("No supported_file_types parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_supported_file_types(cls, supported_file_types):
        for file_type in supported_file_types:
            if isinstance(file_type, basestring) \
                    and file_type not in [supported_file_type[0]
                                          for supported_file_type in
                                          get_SupportedFileTypes_choices()]:
                raise ValidationError('Invalid supported_file_types:%s' % file_type)

    @classmethod
    def create(cls, **kwargs):
        if 'supported_file_types' in kwargs:
            cls._validate_supported_file_types(kwargs['supported_file_types'])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedFileTypes.objects.create(content_object=metadata_obj)

            cls._add_supported_file_type(new_meta_instance, kwargs['supported_file_types'])
            return new_meta_instance
        else:
            raise ValidationError("No supported_file_types parameter was "
                                  "found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedFileTypes.objects.get(id=element_id)

        if 'supported_file_types' in kwargs:
            cls._validate_supported_file_types(kwargs['supported_file_types'])

            meta_instance.supported_file_types.clear()
            cls._add_supported_file_type(meta_instance, kwargs['supported_file_types'])
            meta_instance.save()
        else:
            raise ValidationError("No supported_file_types parameter "
                                  "was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedFileTypes element can't be deleted.")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class URLTemplateFileType(AbstractMetaDataElement):
    term = 'URLTemplateFileType'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # URLTemplateFileType element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolIcon(AbstractMetaDataElement):
    term = 'ToolIcon'
    value = models.CharField(max_length=1024, blank=True, default="")
    data_url = models.TextField(blank=True, default="")

    @classmethod
    def _validate_tool_icon(cls, url):
        try:
            response = requests.get(url, verify=False)
        except Exception as ex:
            raise ValidationError("Failed to read data from given url: {0}".format(ex.message))
        if response.status_code != 200:
            raise HttpResponse("Failed to read data from given url. HTTP_code {0}".
                               format(response.status_code))
        image_size_mb = float(response.headers["content-length"])
        if image_size_mb > 1000000:  # 1mb
            raise ValidationError("Icon image size should be less than 1MB.")
        image_type = imghdr.what(None, h=response.content)
        if image_type not in ["png", "gif", "jpeg"]:
            raise ValidationError("Supported icon image types are png, gif and jpeg")
        base64_string = base64.b64encode(response.content)
        data_url = "data:image/{image_type};base64,{base64_string}".\
                   format(image_type=image_type, base64_string=base64_string)
        return data_url

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs and "data_url" not in kwargs:
            url = kwargs["value"]
            data_url = cls._validate_tool_icon(url)

            metadata_obj = kwargs['content_object']
            new_meta_instance = ToolIcon.objects.create(content_object=metadata_obj)
            new_meta_instance.value = url
            new_meta_instance.data_url = data_url
            new_meta_instance.save()
            return new_meta_instance
        elif "data_url" in kwargs:
            metadata_obj = kwargs['content_object']
            new_meta_instance = ToolIcon.objects.create(content_object=metadata_obj)
            new_meta_instance.value = kwargs["value"] if "value" in kwargs else ""
            new_meta_instance.data_url = kwargs["data_url"]
            new_meta_instance.save()
            return new_meta_instance
        else:
            raise ValidationError("No value parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = ToolIcon.objects.get(id=element_id)
        if 'value' in kwargs:
            url = kwargs["value"]
            data_url = cls._validate_tool_icon(url)
            meta_instance.value = url
            meta_instance.data_url = data_url
            meta_instance.save()
        else:
            raise ValidationError("No value parameter was found in the **kwargs list")

    class Meta:
        # ToolIcon element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolMetaData(CoreMetaData):
    _url_base = GenericRelation(RequestUrlBase)
    _url_template_file_type = GenericRelation(URLTemplateFileType)
    _version = GenericRelation(ToolVersion)
    _supported_res_types = GenericRelation(SupportedResTypes)
    _supported_file_types = GenericRelation(SupportedFileTypes)
    _tool_icon = GenericRelation(ToolIcon)
    _supported_sharing_status = GenericRelation(SupportedSharingStatus)
    _homepage_url = GenericRelation(AppHomePageUrl)
    _supported_resource_permission = GenericRelation(SupportedResourcePermission)

    @property
    def supported_resource_permission(self):
        return self._supported_resource_permission.all().first()

    @property
    def resource(self):
        return ToolResource.objects.filter(object_id=self.id).first()

    @property
    def url_base(self):
        return self._url_base.all().first()

    @property
    def url_template_file_type(self):
        return self._url_template_file_type.first()

    @property
    def version(self):
        return self._version.all().first()

    @property
    def supported_res_types(self):
        return self._supported_res_types.all().first()

    @property
    def supported_file_types(self):
        return self._supported_file_types.all().first()

    @property
    def supported_sharing_status(self):
        return self._supported_sharing_status.all().first()

    @property
    def app_home_page_url(self):
        return self._homepage_url.all().first()

    @property
    def app_icon(self):
        return self._tool_icon.all().first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import ToolMetaDataSerializer
        return ToolMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'requesturlbase' in keys_to_update:
            parsed_metadata.append({"requesturlbase": metadata.pop('requesturlbase')})

        if 'urltemplatefiletype' in keys_to_update:
            parsed_metadata.append({"urltemplatefiletype": metadata.pop('urltemplatefiletype')})

        if 'toolversion' in keys_to_update:
            parsed_metadata.append({"toolversion": metadata.pop('toolversion')})

        if 'toolicon' in keys_to_update:
            parsed_metadata.append({"toolicon": metadata.pop('toolicon')})

        if 'apphomepageurl' in keys_to_update:
            parsed_metadata.append({"apphomepageurl": metadata.pop('apphomepageurl')})

        if 'supportedrestypes' in keys_to_update:
            parsed_metadata.append({"supportedrestypes": metadata.pop('supportedrestypes')})

        if 'supportedfiletypes' in keys_to_update:
            parsed_metadata.append({"supportedfiletypes": metadata.pop('supportedfiletypes')})

        if 'supportedsharingstatus' in keys_to_update:
            parsed_metadata.append({"supportedsharingstatus":
                                    metadata.pop('supportedsharingstatus')})

        if 'supportedresourcepermission' in keys_to_update:
            parsed_metadata.append({"supportedresourcepermission":
                                    metadata.pop('supportedresourcepermission')})

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ToolMetaData, cls).get_supported_element_names()
        elements.append('RequestUrlBase')
        elements.append('URLTemplateFileType')
        elements.append('ToolVersion')
        elements.append('SupportedResTypes')
        elements.append('SupportedFileTypes')
        elements.append('ToolIcon')
        elements.append('SupportedSharingStatus')
        elements.append('AppHomePageUrl')
        elements.append('SupportedResourcePermission')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(ToolMetaData, self).get_required_missing_elements()

        # At least one of the two metadata must exist: Home Page URL or App-launching URL Pattern
        if (not self.url_base or not self.url_base.value) \
           and (not self.app_home_page_url or not self.app_home_page_url.value):
                missing_required_elements.append('App Home Page URL or App-launching URL Pattern')
        else:
            # If one between App-launching URL Pattern and Supported Res Type presents,
            # the other must present as well
            if self.url_base and self.url_base.value:
                if not self.supported_res_types \
                   or not self.supported_res_types.supported_res_types.count() > 0:
                    missing_required_elements.append('Supported Resource Types')

            if self.supported_res_types \
               and self.supported_res_types.supported_res_types.count() > 0:
                if not self.url_base or not self.url_base.value:
                    missing_required_elements.append('App-launching URL Pattern')

            # if Supported Res Type presents, Supported Sharing Status must present, not vice versa
            if self.supported_res_types \
               and self.supported_res_types.supported_res_types.count() > 0:
                if not self.supported_sharing_status \
                   or not self.supported_sharing_status.sharing_status.count() > 0:
                    missing_required_elements.append('Supported Sharing Status')

        return missing_required_elements

    def delete_all_elements(self):
        super(ToolMetaData, self).delete_all_elements()
        self._url_base.all().delete()
        self._url_template_file_type.all().delete()
        self._version.all().delete()
        self._supported_res_types.all().delete()
        self._supported_file_types.all().delete()
        self._tool_icon.all().delete()
        self._supported_sharing_status.all().delete()
        self._homepage_url.all().delete()
        self._supported_resource_permission.all().delete()

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata

        from forms import SupportedResTypesValidationForm, SupportedSharingStatusValidationForm, \
            UrlValidationForm, VersionValidationForm, ToolIconValidationForm, \
            SupportedResourcePermissionValidationForm

        # update any core metadata
        super(ToolMetaData, self).update(metadata, user)

        # update resource specific metadata

        def validate_form(form):
            if not form.is_valid():
                err_string = self.get_form_errors_as_string(form)
                raise ValidationError(err_string)

        with transaction.atomic():
            for dict_item in metadata:
                if 'supportedrestypes' in dict_item:
                    validation_form = SupportedResTypesValidationForm(
                        dict_item['supportedrestypes'])
                    validate_form(validation_form)
                    self.create_element('supportedrestypes', **dict_item['supportedrestypes'])
                elif 'supportedsharingstatus' in dict_item:
                    validation_form = SupportedSharingStatusValidationForm(
                        dict_item['supportedsharingstatus'])
                    validate_form(validation_form)
                    self.create_element('supportedsharingstatus',
                                        **dict_item['supportedsharingstatus'])
                elif 'requesturlbase' in dict_item:
                    validation_form = UrlValidationForm(dict_item['requesturlbase'])
                    validate_form(validation_form)
                    request_url = self.url_base
                    if request_url is not None:
                        self.update_element('requesturlbase', request_url.id,
                                            value=dict_item['requesturlbase'])
                    else:
                        self.create_element('requesturlbase', value=dict_item['requesturlbase'])
                elif 'toolversion' in dict_item:
                    validation_form = VersionValidationForm(dict_item['toolversion'])
                    validate_form(validation_form)
                    tool_version = self.version
                    if tool_version is not None:
                        self.update_element('toolversion', tool_version.id,
                                            **dict_item['toolversion'])
                    else:
                        self.create_element('toolversion', **dict_item['toolversion'])
                elif 'toolicon' in dict_item:
                    validation_form = ToolIconValidationForm(dict_item['toolicon'])
                    validate_form(validation_form)
                    tool_icon = self.app_icon
                    if tool_icon is not None:
                        self.update_element('toolicon', tool_icon.id, **dict_item['toolicon'])
                    else:
                        self.create_element('toolicon', **dict_item['toolicon'])
                elif 'apphomepageurl' in dict_item:
                    validation_form = UrlValidationForm(dict_item['apphomepageurl'])
                    validate_form(validation_form)
                    app_url = self.app_home_page_url
                    if app_url is not None:
                        self.update_element('apphomepageurl', app_url.id,
                                            **dict_item['apphomepageurl'])
                    else:
                        self.create_element('apphomepageurl', **dict_item['apphomepageurl'])
                elif 'urltemplatefiletype' in dict_item:
                    validation_form = UrlValidationForm(dict_item['urltemplatefiletype'])
                    validate_form(validation_form)
                    url_template_file_type = self.url_template_file_type
                    if url_template_file_type is not None:
                        self.update_element('urltemplatefiletype', url_template_file_type.id,
                                            value=dict_item['urltemplatefiletype'])
                    else:
                        self.create_element('urltemplatefiletype',
                                            value=dict_item['urltemplatefiletype'])
                elif 'supportedresourcepermission' in dict_item:
                    validation_form = SupportedResourcePermissionValidationForm(dict_item['supportedresourcepermission'])
                    validate_form(validation_form)
                    supported_resource_permission = self.supported_resource_permission
                    if supported_resource_permission is not None:
                        self.update_element('supportedresourcepermission', supported_resource_permission.id,
                                            value=dict_item['supportedresourcepermission'])
                    else:
                        self.create_element('supportedresourcepermission',
                                            value=dict_item['supportedresourcepermission'])
