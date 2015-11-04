from django.db import models
from django.contrib.contenttypes import generic

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor,\
                           CoreMetaData, AbstractMetaDataElement

from lxml import etree

class RefTimeSeriesResource(BaseResource):
    objects = ResourceManager("RefTimeSeriesResource")

    class Meta:
        verbose_name = "HIS Referenced Time Series"
        proxy = True

    @property
    def metadata(self):
        md = RefTSMetadata()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False


processor_for(RefTimeSeriesResource)(resource_processor)

class ReferenceURL(AbstractMetaDataElement):
    term = 'Reference URL'
    value = models.CharField(max_length=500)
    type = models.CharField(max_length=4)

class Method(AbstractMetaDataElement):
    term = 'Method'
    value = models.CharField(max_length=200)

class QualityControlLevel(AbstractMetaDataElement):
    term = 'QualityControlLevel'
    value = models.CharField(max_length=200)

class Variable(AbstractMetaDataElement):
    term = 'Variable'
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    data_type = models.CharField(max_length=50, null=True)
    sample_medium = models.CharField(max_length=50, null=True)

class Site(AbstractMetaDataElement):
    term = 'Site'
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

class RefTSMetadata(CoreMetaData):
    methods = generic.GenericRelation(Method)
    quality_levels = generic.GenericRelation(QualityControlLevel)
    variables = generic.GenericRelation(Variable)
    sites = generic.GenericRelation(Site)
    referenceURLs = generic.GenericRelation(ReferenceURL)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RefTSMetadata, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Method')
        elements.append('QualityControlLevel')
        elements.append('Variable')
        elements.append('Site')
        elements.append('ReferenceURL')
        return elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(RefTSMetadata, self).get_xml(pretty_print=True)
        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject resource specific metadata elements to container element
        for refURL in self.referenceURLs.all():
            hsterms_refURL = etree.SubElement(container, '{%s}ReferenceURL' % self.NAMESPACES['hsterms'])
            hsterms_refURL_rdf_Description = etree.SubElement(hsterms_refURL, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_refURL_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = refURL.value
            hsterms_name = etree.SubElement(hsterms_refURL_rdf_Description, '{%s}type' % self.NAMESPACES['hsterms'])
            hsterms_name.text = refURL.type

        for method in self.methods.all():
            hsterms_method = etree.SubElement(container, '{%s}method' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = method.value

        for q_l in self.quality_levels.all():
            hsterms_q_l = etree.SubElement(container, '{%s}qualitycontrollevel' % self.NAMESPACES['hsterms'])
            hsterms_q_l_rdf_Description = etree.SubElement(hsterms_q_l, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_q_l_rdf_Description, '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_name.text = q_l.value

        for variable in self.variables.all():
            hsterms_variable = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_variable_rdf_Description = etree.SubElement(hsterms_variable, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_variable_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = variable.name
            hsterms_code = etree.SubElement(hsterms_variable_rdf_Description, '{%s}code' % self.NAMESPACES['hsterms'])
            hsterms_code.text = variable.code
            hsterms_data_type = etree.SubElement(hsterms_variable_rdf_Description, '{%s}dataType' % self.NAMESPACES['hsterms'])
            hsterms_data_type.text = variable.data_type
            hsterms_sample_medium = etree.SubElement(hsterms_variable_rdf_Description, '{%s}sampleMedium' % self.NAMESPACES['hsterms'])
            hsterms_sample_medium.text = variable.sample_medium

        for site in self.sites.all():
            hsterms_site = etree.SubElement(container, '{%s}site' % self.NAMESPACES['hsterms'])
            hsterms_site_rdf_Description = etree.SubElement(hsterms_site, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_site_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = site.name
            hsterms_code = etree.SubElement(hsterms_site_rdf_Description, '{%s}code' % self.NAMESPACES['hsterms'])
            hsterms_code.text = site.code
            hsterms_latitude = etree.SubElement(hsterms_site_rdf_Description, '{%s}latitude' % self.NAMESPACES['hsterms'])
            hsterms_latitude.text = unicode(site.latitude) or ''
            hsterms_longitude = etree.SubElement(hsterms_site_rdf_Description, '{%s}longitude' % self.NAMESPACES['hsterms'])
            hsterms_longitude.text = unicode(site.longitude) or ''

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers
