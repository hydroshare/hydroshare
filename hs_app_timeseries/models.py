from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models

from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement


# define extended metadata elements for Time Series resource type
class Site(AbstractMetaDataElement):
    term = 'Site'
    site_code = models.CharField(max_length=200)
    site_name = models.CharField(max_length=255)
    elevation_m = models.IntegerField(null=True, blank=True)
    elevation_datum = models.CharField(max_length=50, null=True, blank=True)
    site_type = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.site_name

    class Meta:
        # site element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Site element of a resource can't be deleted.")


class Variable(AbstractMetaDataElement):
    term = 'Variable'
    variable_code = models.CharField(max_length=20)
    variable_name = models.CharField(max_length=100)
    variable_type = models.CharField(max_length=100)
    no_data_value = models.IntegerField()
    variable_definition = models.CharField(max_length=255, null=True, blank=True)
    speciation = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.variable_name

    class Meta:
        # variable element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Variable element of a resource can't be deleted.")


class Method(AbstractMetaDataElement):
    term = 'Method'
    method_code = models.IntegerField()
    method_name = models.CharField(max_length=200)
    method_type = models.CharField(max_length=200)
    method_description = models.TextField(null=True, blank=True)
    method_link = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.method_name

    class Meta:
        # method element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Method element of a resource can't be deleted.")


class ProcessingLevel(AbstractMetaDataElement):
    term = 'ProcessingLevel'
    processing_level_code = models.IntegerField()
    definition = models.CharField(max_length=200, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.processing_level_code

    class Meta:
        # processinglevel element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")


class TimeSeriesResult(AbstractMetaDataElement):
    term = 'TimeSeriesResult'
    units_type = models.CharField(max_length=255)
    units_name = models.CharField(max_length=255)
    units_abbreviation = models.CharField(max_length=20)
    status = models.CharField(max_length=255)
    sample_medium = models.CharField(max_length=255)
    value_count = models.IntegerField()
    aggregation_statistics = models.CharField(max_length=255)

    def __unicode__(self):
        return self.units_type

    class Meta:
        # processinglevel element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")

# To create a new resource, use these three super-classes.
#


class TimeSeriesResource(BaseResource):
    objects = ResourceManager("TimeSeriesResource")

    class Meta:
        verbose_name = 'Time Series'
        proxy = True

    @property
    def metadata(self):
        md = TimeSeriesMetaData()
        return self._get_metadata(md)

    # not sure why we have to implement all the can_ type methods that we are inheriting from AbstractResource

    @classmethod
    def get_supported_upload_file_types(cls):
        # final phase of this resource type implementation will support 3 file types
        #return (".csv", ".xml", ".sqlite")
        # phase-1 of implementation supports only sqlite file
        return (".sqlite",)


    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False


# this would allow us to pick up additional form elements for the template before the template is displayed
processor_for(TimeSeriesResource)(resource_processor)


class TimeSeriesMetaData(CoreMetaData):
    _site = generic.GenericRelation(Site)
    _variable = generic.GenericRelation(Variable)
    _method = generic.GenericRelation(Method)
    _processing_level = generic.GenericRelation(ProcessingLevel)
    _time_series_result = generic.GenericRelation(TimeSeriesResult)

    @property
    def site(self):
        return self._site.all().first()

    @property
    def variable(self):
        return self._variable.all().first()

    @property
    def method(self):
        return self._method.all().first()

    @property
    def processing_level(self):
        return self._processing_level.all().first()

    @property
    def time_series_result(self):
        return self._time_series_result.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(TimeSeriesMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Site')
        elements.append('Variable')
        elements.append('Method')
        elements.append('ProcessingLevel')
        elements.append('TimeSeriesResult')
        return elements

    def has_all_required_elements(self):
        if not super(TimeSeriesMetaData, self).has_all_required_elements():
            return False
        if not self.site:
            return False
        if not self.variable:
            return False
        if not self.method:
            return False
        if not self.processing_level:
            return False
        if not self.time_series_result:
            return False

        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(TimeSeriesMetaData, self).get_required_missing_elements()
        if not self.site:
            missing_required_elements.append('Site')
        if not self.variable:
            missing_required_elements.append('Variable')
        if not self.method:
            missing_required_elements.append('Method')
        if not self.processing_level:
            missing_required_elements.append('Processing Level')
        if not self.time_series_result:
            missing_required_elements.append('Time Series Result')
        return missing_required_elements

    def get_xml(self, pretty_print=True):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(TimeSeriesMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.site:
            element_fields = [('site_code', 'SiteCode'), ('site_name', 'SiteName')]

            if self.site.elevation_m:
                element_fields.append(('elevation_m', 'Elevation_m'))

            if self.site.elevation_datum:
                element_fields.append(('elevation_datum', 'ElevationDatum'))

            if self.site.site_type:
                element_fields.append(('site_type', 'SiteType'))

            self.add_metadata_element_to_xml(container, (self.site, 'site'), element_fields)

        if self.variable:
            element_fields = [('variable_code', 'VariableCode'), ('variable_name', 'VariableName'),
                              ('variable_type', 'VariableType'), ('no_data_value', 'NoDataValue')]

            if self.variable.variable_definition:
                element_fields.append(('variable_definition', 'VariableDefinition'))

            if self.variable.speciation:
                element_fields.append(('speciation', 'Speciation'))

            self.add_metadata_element_to_xml(container, (self.variable, 'variable'), element_fields)

        if self.method:
            element_fields = [('method_code', 'MethodCode'), ('method_name', 'MethodName'),
                              ('method_type', 'MethodType')]

            if self.method.method_description:
                element_fields.append(('method_description', 'MethodDescription'))

            if self.method.method_link:
                element_fields.append(('method_link', 'MethodLink'))

            self.add_metadata_element_to_xml(container, (self.method, 'method'), element_fields)

        if self.processing_level:
            element_fields = [('processing_level_code', 'ProcessingLevelCode')]

            if self.processing_level.definition:
                element_fields.append(('definition', 'Definition'))

            if self.processing_level.explanation:
                element_fields.append(('explanation', 'Explanation'))

            self.add_metadata_element_to_xml(container, (self.processing_level, 'processingLevel'), element_fields)

        if self.time_series_result:
            # since 2nd level nesting of elements exists here, can't use the helper function add_metadata_element_to_xml()
            hsterms_time_series_result = etree.SubElement(container, '{%s}timeSeriesResult' % self.NAMESPACES['hsterms'])
            hsterms_time_series_result_rdf_Description = etree.SubElement(hsterms_time_series_result, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_units = etree.SubElement(hsterms_time_series_result_rdf_Description, '{%s}units' % self.NAMESPACES['hsterms'])
            hsterms_units_rdf_Description = etree.SubElement(hsterms_units, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_units_type = etree.SubElement(hsterms_units_rdf_Description, '{%s}UnitsType' % self.NAMESPACES['hsterms'])
            hsterms_units_type.text = self.time_series_result.units_type

            hsterms_units_name = etree.SubElement(hsterms_units_rdf_Description, '{%s}UnitsName' % self.NAMESPACES['hsterms'])
            hsterms_units_name.text = self.time_series_result.units_name

            hsterms_units_abbv = etree.SubElement(hsterms_units_rdf_Description, '{%s}UnitsAbbreviation' % self.NAMESPACES['hsterms'])
            hsterms_units_abbv.text = self.time_series_result.units_abbreviation

            hsterms_status = etree.SubElement(hsterms_time_series_result_rdf_Description, '{%s}Status' % self.NAMESPACES['hsterms'])
            hsterms_status.text = self.time_series_result.status

            hsterms_sample_medium = etree.SubElement(hsterms_time_series_result_rdf_Description, '{%s}SampleMedium' % self.NAMESPACES['hsterms'])
            hsterms_sample_medium.text = self.time_series_result.sample_medium

            hsterms_value_count = etree.SubElement(hsterms_time_series_result_rdf_Description, '{%s}ValueCount' % self.NAMESPACES['hsterms'])
            hsterms_value_count.text = str(self.time_series_result.value_count)

            hsterms_statistics = etree.SubElement(hsterms_time_series_result_rdf_Description, '{%s}AggregationStatistic' % self.NAMESPACES['hsterms'])
            hsterms_statistics.text = self.time_series_result.aggregation_statistics

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(TimeSeriesMetaData, self).delete_all_elements()
        if self.site:
            self.site.delete()
        if self.variable:
            self.variable.delete()
        if self.method:
            self.method.delete()
        if self.processing_level:
            self.processing_level.delete()
        if self.time_series_result:
            self.time_series_result.delete()


import receivers
