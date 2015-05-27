from django.db import models
from django.contrib.contenttypes import generic
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core import hydroshare
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType
from mezzanine.pages.models import Page
from mezzanine.pages.page_processors import processor_for

# def get_resource_names():
#     names = []
#     for res in hydroshare.get_resource_types():
#         names.append(res.__name__)
#
#         
        
#
# To create a new resource, use these two super-classes.
#
class ToolResource(Page, AbstractResource):

    class Meta:
        verbose_name = 'Tool Resource'

    def extra_capabilities(self):
        return None

    @property
    def metadata(self):
        md = ToolMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False



processor_for(ToolResource)(resource_processor)


class RequestUrlBase(AbstractMetaDataElement):
    term = 'Request Url Base'
    value = models.CharField(null=True, max_length="500") # whatever the user gives us- format is "http://www.example.com/{resource-info}"


    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if 'content_object' in kwargs:
                content_object = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(content_object)
                url_base = RequestUrlBase.objects.filter(value__iexact=kwargs['value'], object_id=content_object.id, content_type=metadata_type).first()
                if url_base:
                    raise ValidationError('There can only be one Request Url Base')
                url_base = RequestUrlBase.objects.create(value=kwargs['value'], content_object=content_object)
                return url_base
            else:
                raise ValidationError('Metadata instance for which Request Url Base element to be created is missing.')
        else:
            raise ValidationError("Value of Request Url Base is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        url_base = RequestUrlBase.objects.get(id=element_id)
        if url_base:
            if 'value' in kwargs:
                url_base.value = kwargs['value']
                url_base.save()
            else:
                raise ValidationError('Value of Request Url Base is missing')
        else:
            raise ObjectDoesNotExist("No Request Url Base element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        url_base = RequestUrlBase.objects.get(id=element_id)
        if url_base:
            url_base.delete()
        else:
            raise ObjectDoesNotExist("No Request Url Base element was found for id:%d." % element_id)

#the resource types that can be used by this tool- one class instance per type
class ToolResourceType(AbstractMetaDataElement):
    term = 'Tool Resource Type'
    tool_res_type = models.CharField(null=True, max_length="500")  #a string of the resource type class, lowered. like res.content_model

    @classmethod
    def create(cls, **kwargs):
        if 'tool_res_type' in kwargs:
            if 'content_object' in kwargs:
                content_object = kwargs['content_object']
                tool_res_type_res = ToolResourceType.objects.create(tool_res_type=kwargs['tool_res_type'], content_object=content_object)
                return tool_res_type_res
            else:
                raise ValidationError('Metadata instance for which Resource Type element to be created is missing.')
        else:
            raise ValidationError("string 'tool_res_type' is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        tool_res_type_res = ToolResourceType.objects.get(id=element_id)
        if tool_res_type_res:
            if 'tool_res_type' in kwargs:
                tool_res_type_res.tool_res_type = kwargs['tool_res_type']
                tool_res_type_res.save()
            else:
                raise ValidationError("String 'tool_res_type' is missing.")
        else:
            raise ObjectDoesNotExist("No Resource Type element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        tool_res_type_res = ToolResourceType.objects.get(id=element_id)
        if tool_res_type_res:
            tool_res_type_res.delete()
        else:
            raise ObjectDoesNotExist("No Resource Type element was found for id:%d." % element_id)

class Fee(AbstractMetaDataElement):
    term = 'Fee'
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def create(cls, **kwargs):
        if 'content_object' in kwargs:
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            fee = Fee.objects.create(value=kwargs.get('value'),
                                     description=kwargs.get('description'),
                                     content_object=metadata_obj)
            return fee
        else:
            raise ValidationError('metadata object is missing from inputs')

    @classmethod
    def update(cls, element_id, **kwargs):
        fee = Fee.objects.get(id=element_id)
        if fee:
            if 'value' in kwargs:
                fee.value = kwargs['value']
            if 'description' in kwargs:
                fee.description = kwargs['description']
            fee.save()
        else:
            raise ObjectDoesNotExist("No Fee element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        fee = Fee.objects.get(id=element_id)
        if fee:
            fee.delete()
        else:
            raise ObjectDoesNotExist("No Fee element was found for id:%d." % element_id)


class ToolVersion(AbstractMetaDataElement):
    term = 'Tool Version'
    value = models.CharField(null=True, max_length="500")

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if 'content_object' in kwargs:
                content_object = kwargs['content_object']
                metadata_type = ContentType.objects.get_for_model(content_object)
                version = ToolVersion.objects.filter(value__iexact=kwargs['value'], object_id=content_object.id, content_type=metadata_type).first()
                if version:
                    raise ValidationError('There can only be one Tool Version')
                version = ToolVersion.objects.create(value=kwargs['value'], content_object=content_object)
                return version
            else:
                raise ValidationError('Metadata instance for which Tool Version element to be created is missing.')
        else:
            raise ValidationError("Value of Tool Version is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        version = ToolVersion.objects.get(id=element_id)
        if version:
            if 'value' in kwargs:
                version.value = kwargs['value']
                version.save()
            else:
                raise ValidationError('Value of Tool Version is missing')
        else:
            raise ObjectDoesNotExist("No Tool Version element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        version = ToolVersion.objects.get(id=element_id)
        if version:
            version.delete()
        else:
            raise ObjectDoesNotExist("No Tool Version element was found for id:%d." % element_id)

class ToolMetaData(CoreMetaData):
    # tool license is implemented via existing metadata element "rights" with attr. "statement" and "url"
    # should be only one Request Url Base metadata element
    url_bases = generic.GenericRelation(RequestUrlBase)
    res_types = generic.GenericRelation(ToolResourceType)
    fees = generic.GenericRelation(Fee)
    # should be only one Version metadata element
    versions = generic.GenericRelation(ToolVersion)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(ToolMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('RequestUrlBase')   # needs to match the class name
        elements.append('ToolResourceType')
        elements.append('Fee')
        elements.append('ToolVersion')
        return elements

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

        for type in self.res_types.all():
            hsterms_method = etree.SubElement(container, '{%s}ResourceType' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}type' % self.NAMESPACES['hsterms'])
            hsterms_name.text = type.tool_res_type

        for fee in self.fees.all():
            hsterms_method = etree.SubElement(container, '{%s}Fee' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = unicode(fee.value)
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}description' % self.NAMESPACES['hsterms'])
            hsterms_name.text = fee.description

        for v in self.versions.all():
            hsterms_method = etree.SubElement(container, '{%s}ToolVersion' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = unicode(v.value)

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers