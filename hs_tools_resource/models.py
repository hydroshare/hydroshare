from django.db import models
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement

from lxml import etree


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
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False

    @property
    def metadata(self):
        md = ToolMetaData()
        return self._get_metadata(md)

processor_for(ToolResource)(resource_processor)


class RequestUrlBase(AbstractMetaDataElement):
    term = 'RequestUrlBase'
    value = models.CharField(max_length=1024, null=True)

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
    supported_res_types = models.ManyToManyField(SupportedResTypeChoices, null=True, blank=True)

    def get_supported_res_types_str(self):
        return ','.join([parameter.description for parameter in self.supported_res_types.all()])

    @classmethod
    def create(cls, **kwargs):
        if 'supported_res_types' in kwargs:
            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedResTypes.objects.create(content_object=metadata_obj)
            for res_type_str in kwargs['supported_res_types']:
                qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type_str)
                if qs.exists():
                    new_meta_instance.supported_res_types.add(qs[0])
                else:
                    new_meta_instance.supported_res_types.create(description=res_type_str)
            return new_meta_instance
        else:
            raise ObjectDoesNotExist("No supported_res_types parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedResTypes.objects.get(id=element_id)
        if meta_instance:
            if 'supported_res_types' in kwargs:
                meta_instance.supported_res_types.clear()
                for res_type_str in kwargs['supported_res_types']:
                    qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type_str)
                    if qs.exists():
                        meta_instance.supported_res_types.add(qs[0])
                    else:
                        meta_instance.supported_res_types.create(description=res_type_str)
                meta_instance.save()
                if meta_instance.supported_res_types.all().count() == 0:
                    meta_instance.delete()
            else:
                raise ObjectDoesNotExist("No supported_res_types parameter was found in the **kwargs list")
        else:
            raise ObjectDoesNotExist("No SupportedResTypes object was found with the provided id: %s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedResTypes element can't be deleted.")


class ToolIcon(AbstractMetaDataElement):
    term = 'ToolIcon'
    url = models.CharField(max_length=1024, null=True, blank=True)

    class Meta:
        # ToolVersion element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolMetaData(CoreMetaData):
    url_bases = generic.GenericRelation(RequestUrlBase)
    versions = generic.GenericRelation(ToolVersion)
    supported_res_types = generic.GenericRelation(SupportedResTypes)
    tool_icon = generic.GenericRelation(ToolIcon)

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ToolMetaData, cls).get_supported_element_names()
        elements.append('RequestUrlBase')
        elements.append('ToolVersion')
        elements.append('SupportedResTypes')
        elements.append('ToolIcon')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(ToolMetaData, self).get_required_missing_elements()
        if not self.url_bases.all().first():
            missing_required_elements.append('App Url')
        elif not self.url_bases.all().first().value:
            missing_required_elements.append('App Url')
        if not self.supported_res_types.all().first():
            missing_required_elements.append('Supported Resource Types')

        return missing_required_elements

import receivers # never delete this otherwise non of the receiver function will work
