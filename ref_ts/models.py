from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor,\
                           CoreMetaData, AbstractMetaDataElement

from lxml import etree


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
    referenceURLs = GenericRelation(ReferenceURL)
    sites = GenericRelation(Site)
    variables = GenericRelation(Variable)
    methods = GenericRelation(Method)
    quality_levels = GenericRelation(QualityControlLevel)
    datasources = GenericRelation(DataSource)

    @property
    def resource(self):
        return RefTimeSeriesResource.objects.filter(object_id=self.id).first()

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

    def delete_all_elements(self):
        super(RefTSMetadata, self).delete_all_elements()
        self.referenceURLs.all().delete()
        self.sites.all().delete()
        self.variables.all().delete()
        self.methods.all().delete()
        self.quality_levels.all().delete()
        self.datasources.all().delete()

from . import receivers
