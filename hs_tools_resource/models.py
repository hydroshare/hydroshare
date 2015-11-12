from django.db import models
from django.contrib.contenttypes import generic
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor,\
                           CoreMetaData, AbstractMetaDataElement

from lxml import etree

#
# To create a new resource, use these two super-classes.
#
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
    term = 'Request Url Base'
    value = models.CharField(null=True, max_length="500") # whatever the user gives us- format is "http://www.example.com/{resource-info}"
    resShortID = models.CharField(max_length=100, default="UNKNOWN")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class SupportedResTypeChoices(models.Model):
    description = models.CharField(max_length=300)

    def __unicode__(self):
        self.description


class SupportedResTypes(AbstractMetaDataElement):
    term = 'SupportedResTypes'
    supported_res_types= models.ManyToManyField(SupportedResTypeChoices, null=True, blank=True)

    def get_supported_res_types_str(self):
        return ', '.join([parameter.description for parameter in self.supported_res_types.all()])

    @classmethod
    def create(cls, **kwargs):
        if 'supported_res_types' in kwargs:

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedResTypes.objects.create(content_object=metadata_obj,)

        for res_type_str in kwargs['supported_res_types']:
            qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type_str)
            if qs.exists():
                new_meta_instance.supported_res_types.add(qs[0])
            else:
                new_meta_instance.supported_res_types.create(description=res_type_str)

        return new_meta_instance

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedResTypes.objects.get(id=element_id)
        if meta_instance:
            if 'supported_res_types' in kwargs:
                #cls._validate_swat_model_parameters(kwargs['model_parameters'])
                meta_instance.supported_res_types.all().delete()
                for res_type_str in kwargs['supported_res_types']:
                    qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type_str)
                    if qs.exists():
                        meta_instance.supported_res_types.add(qs[0])
                    else:
                        meta_instance.supported_res_types.create(description=res_type_str)

            meta_instance.save()

            # delete model_parameters metadata element if it has no data
            if len(meta_instance.supported_res_types.all()) == 0 :
                meta_instance.delete()
        else:
            raise ObjectDoesNotExist("No supported_res_types element was found for the provided id:%s" % kwargs['id'])


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedResTypes element can't be deleted.")


class ToolVersion(AbstractMetaDataElement):
    term = 'Tool Version'
    value = models.CharField(null=True, max_length="500")

    class Meta:
        # ToolVersion element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolMetaData(CoreMetaData):
    # tool license is implemented via existing metadata element "rights" with attr. "statement" and "url"
    # should be only one Request Url Base metadata element
    url_bases = generic.GenericRelation(RequestUrlBase)

    # should be only one Version metadata element
    versions = generic.GenericRelation(ToolVersion)
    supported_res_types= generic.GenericRelation(SupportedResTypes)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ToolMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
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
            missing_required_elements.append('RequestUrlBase')
        if not self.versions.all().first():
            missing_required_elements.append('ToolVersion')
        if not self.supported_res_types.all().first():
            missing_required_elements.append('SupportedResTypes')

        return missing_required_elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(ToolMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        #inject resource specific metadata elements into container element
        for url in self.url_bases.all():
            hsterms_method = etree.SubElement(container, '{%s}RequestUrlBase' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = url.value

        for type in self.supported_res_types.all():
            hsterms_method = etree.SubElement(container, '{%s}ResourceType' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}type' % self.NAMESPACES['hsterms'])
            hsterms_name.text = type.get_supported_res_types_str()


        for v in self.versions.all():
            hsterms_method = etree.SubElement(container, '{%s}ToolVersion' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
        #     hsterms_name.text = unicode(v.value)

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers
