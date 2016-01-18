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
    value = models.CharField(max_length=128, default="1.0")

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


class ToolMetaData(CoreMetaData):
    url_bases = generic.GenericRelation(RequestUrlBase)
    versions = generic.GenericRelation(ToolVersion)
    supported_res_types = generic.GenericRelation(SupportedResTypes)

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ToolMetaData, cls).get_supported_element_names()
        elements.append('RequestUrlBase')
        elements.append('ToolVersion')
        elements.append('SupportedResTypes')
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

    def get_xml(self):
        # get the xml string representation of the core metadata elements
        xml_string = super(ToolMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject resource specific metadata elements into container element
        if self.url_bases.all().first():
            url_bases_fields = ['value']
            self.add_metadata_element_to_xml(container,
                                             self.url_bases.all().first(),
                                             url_bases_fields)

        if self.versions.all().first():
            versions_fields = ['value']
            self.add_metadata_element_to_xml(container,
                                             self.versions.all().first(),
                                             versions_fields)

        for res_type in self.supported_res_types.all():
            hsterms_method = etree.SubElement(container, '{%s}SupportedResTypes' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}types' % self.NAMESPACES['hsterms'])
            hsterms_name.text = res_type.get_supported_res_types_str()

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers # never delete this otherwise non of the receiver function will work
