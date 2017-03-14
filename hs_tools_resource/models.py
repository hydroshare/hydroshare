import requests
import base64
import imghdr

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement
from .utils import get_SupportedResTypes_choices


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
    supported_res_types = models.ManyToManyField(SupportedResTypeChoices, blank=True)

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


class SupportedSharingStatusChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedSharingStatus(AbstractMetaDataElement):
    term = 'SupportedSharingStatus'
    sharing_status = models.ManyToManyField(SupportedSharingStatusChoices, blank=True)

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


class ToolIcon(AbstractMetaDataElement):
    term = 'ToolIcon'
    value = models.CharField(max_length=1024, blank=True, default="")
    data_url = models.TextField(blank=True, default="")

    @classmethod
    def _validate_tool_icon(cls, url):
        try:
            response = requests.get(url, verify=False)
        except:
            raise ValidationError("Failed to read data from given url.")
        if response.status_code != 200:
            raise ValidationError("Failed to read data from given url.")
        image_size_mb = float(response.headers["content-length"])/1024.0/1024.0
        if image_size_mb > 1:
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
        if 'value' in kwargs:
            url = kwargs["value"]
            data_url = cls._validate_tool_icon(url)

            metadata_obj = kwargs['content_object']
            new_meta_instance = ToolIcon.objects.create(content_object=metadata_obj)
            new_meta_instance.value = url
            new_meta_instance.data_url = data_url
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
    url_bases = GenericRelation(RequestUrlBase)
    versions = GenericRelation(ToolVersion)
    supported_res_types = GenericRelation(SupportedResTypes)
    tool_icon = GenericRelation(ToolIcon)
    supported_sharing_status = GenericRelation(SupportedSharingStatus)
    homepage_url = GenericRelation(AppHomePageUrl)

    @property
    def resource(self):
        return ToolResource.objects.filter(object_id=self.id).first()

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ToolMetaData, cls).get_supported_element_names()
        elements.append('RequestUrlBase')
        elements.append('ToolVersion')
        elements.append('SupportedResTypes')
        elements.append('ToolIcon')
        elements.append('SupportedSharingStatus')
        elements.append('AppHomePageUrl')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(ToolMetaData, self).get_required_missing_elements()

        # At least one of the two metadata must exist: Home Page URL or App-launching URL Pattern
        if (not self.url_bases.all().first() or not self.url_bases.all().first().value) \
           and (not self.homepage_url.all().first() or not self.homepage_url.all().first().value):
                missing_required_elements.append('App Home Page URL or App-launching URL Pattern')
        else:
            # If one between App-launching URL Pattern and Supported Res Type presents,
            # the other must present as well
            if self.url_bases.all().first() and self.url_bases.all().first().value:
                if not self.supported_res_types.all().first() \
                   or not self.supported_res_types.all().first().supported_res_types.count() > 0:
                    missing_required_elements.append('Supported Resource Types')

            if self.supported_res_types.all().first() \
               and self.supported_res_types.all().first().supported_res_types.count() > 0:
                if not self.url_bases.all().first() or not self.url_bases.all().first().value:
                    missing_required_elements.append('App-launching URL Pattern')

            # if Supported Res Type presents, Supported Sharing Status must present, not vice versa
            if self.supported_res_types.all().first() \
               and self.supported_res_types.all().first().supported_res_types.count() > 0:
                if not self.supported_sharing_status.all().first() \
                   or not self.supported_sharing_status.all().first().sharing_status.count() > 0:
                    missing_required_elements.append('Supported Sharing Status')

        return missing_required_elements

    def delete_all_elements(self):
        super(ToolMetaData, self).delete_all_elements()
        self.url_bases.all().delete()
        self.versions.all().delete()
        self.supported_res_types.all().delete()
        self.tool_icon.all().delete()
        self.supported_sharing_status.all().delete()
        self.homepage_url.all().delete()
