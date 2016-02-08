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
    term = 'ReferenceURL'
    value = models.CharField(max_length=500)
    type = models.CharField(max_length=4)

class Method(AbstractMetaDataElement):
    term = 'Method'
    code = models.CharField(max_length=500, default="", blank=True)
    description = models.TextField(default="", blank=True)

class QualityControlLevel(AbstractMetaDataElement):
    term = 'QualityControlLevel'
    code = models.CharField(max_length=500, default="", blank=True)
    definition = models.CharField(max_length=500, default="", blank=True)

class Variable(AbstractMetaDataElement):
    term = 'Variable'
    name = models.CharField(max_length=500, default="", blank=True)
    code = models.CharField(max_length=500, default="", blank=True)
    data_type = models.CharField(max_length=500, default="", blank=True)
    sample_medium = models.CharField(max_length=500, default="", blank=True)

class Site(AbstractMetaDataElement):
    term = 'Site'
    name = models.CharField(max_length=500, default="", blank=True)
    code = models.CharField(max_length=500, default="", blank=True)
    net_work = models.CharField(max_length=500, default="", blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

# source code
class DataSource(AbstractMetaDataElement):
    term = 'DataSource'
    code = models.CharField(max_length=500, default="", blank=True)

class RefTSMetadata(CoreMetaData):
    referenceURLs = generic.GenericRelation(ReferenceURL)
    sites = generic.GenericRelation(Site)
    variables = generic.GenericRelation(Variable)
    methods = generic.GenericRelation(Method)
    quality_levels = generic.GenericRelation(QualityControlLevel)
    datasources = generic.GenericRelation(DataSource)

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
        elements.append('DataSource')
        return elements

    def get_xml(self):
        # get the xml string representation of the core metadata elements
        xml_string = super(RefTSMetadata, self).get_xml(pretty_print=False)
        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject resource specific metadata elements to container element
        if self.referenceURLs.all().first():
            referenceURLs_fields = ['value', 'type']
            self.add_metadata_element_to_xml(container,
                                             self.referenceURLs.all().first(),
                                             referenceURLs_fields)

        if self.sites.all().first():
            sites_fields = ['name', 'code', 'latitude', 'longitude']
            self.add_metadata_element_to_xml(container,
                                             self.sites.all().first(),
                                             sites_fields)

        if self.variables.all().first():
            variables_fields = ['name', 'code', 'data_type', 'sample_medium']
            self.add_metadata_element_to_xml(container,
                                             self.variables.all().first(),
                                             variables_fields)

        if self.methods.all().first():
            methods_fields = ['code', 'description']
            self.add_metadata_element_to_xml(container,
                                             self.methods.all().first(),
                                             methods_fields)
        if self.quality_levels.all().first():
            quality_levels_fields = ['code', 'definition']
            self.add_metadata_element_to_xml(container,
                                             self.quality_levels.all().first(),
                                             quality_levels_fields)

        if self.datasources.all().first():
            datasources_fields = ['code']
            self.add_metadata_element_to_xml(container,
                                             self.datasources.all().first(),
                                             datasources_fields)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(RefTSMetadata, self).delete_all_elements()
        self.referenceURLs.all().delete()
        self.sites.all().delete()
        self.variables.all().delete()
        self.methods.all().delete()
        self.quality_levels.all().delete()
        self.datasources.all().delete()

import receivers
