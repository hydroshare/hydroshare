from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement


# define extended metadata elements for Time Series resource type
class Site(AbstractMetaDataElement):
    term = 'Site'
    site_code = models.CharField(max_length=200)
    site_name = models.CharField(max_length=255)
    elevation_m = models.IntegerField(null=True, blank=True)
    elevation_datum = models.CharField(max_length=50, null=True, blank=True)
    site_type = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        self.site_name

    class Meta:
        # site element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return Site.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        site = Site.objects.get(id=element_id)
        if site:
            for key, value in kwargs.iteritems():
                setattr(site, key, value)

            site.save()
        else:
            raise ObjectDoesNotExist("No Site element was found for the provided id:%s" % kwargs['id'])

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
        self.variable_name

    class Meta:
        # variable element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return Variable.objects.create(**kwargs)


    @classmethod
    def update(cls, element_id, **kwargs):
        variable = Variable.objects.get(id=element_id)
        if variable:
            for key, value in kwargs.iteritems():
                setattr(variable, key, value)

            variable.save()
        else:
            raise ObjectDoesNotExist("No Variable element was found for the provided id:%s" % kwargs['id'])

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
        self.method_name

    class Meta:
        # method element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return Method.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        method = Method.objects.get(id=element_id)
        if method:
            for key, value in kwargs.iteritems():
                setattr(method, key, value)

            method.save()
        else:
            raise ObjectDoesNotExist("No Method element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Method element of a resource can't be deleted.")


class ProcessingLevel(AbstractMetaDataElement):
    term = 'ProcessingLevel'
    processing_level_code = models.IntegerField()
    definition = models.CharField(max_length=200, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        self.processing_level_code

    class Meta:
        # processinglevel element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return ProcessingLevel.objects.create(**kwargs)


    @classmethod
    def update(cls, element_id, **kwargs):
        processing_level = ProcessingLevel.objects.get(id=element_id)
        if processing_level:
            for key, value in kwargs.iteritems():
                setattr(processing_level, key, value)

            processing_level.save()
        else:
            raise ObjectDoesNotExist("No ProcessingLevel element was found for the provided id:%s" % kwargs['id'])

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
        self.processing_level_code

    class Meta:
        # processinglevel element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        return TimeSeriesResult.objects.create(**kwargs)


    @classmethod
    def update(cls, element_id, **kwargs):
        time_series_result = TimeSeriesResult.objects.get(id=element_id)
        if time_series_result:
            for key, value in kwargs.iteritems():
                setattr(time_series_result, key, value)

            time_series_result.save()
        else:
            raise ObjectDoesNotExist("No TimeSeriesResult element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")

# To create a new resource, use these three super-classes.
#

class TimeSeriesResource(Page, AbstractResource):
    class Meta:
        verbose_name = 'Time Series'

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
    _time_series_resource = generic.GenericRelation(TimeSeriesResource)


    @property
    def resource(self):
        return self._time_series_resource.all().first()

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
            hsterms_site = etree.SubElement(container, '{%s}site' % self.NAMESPACES['hsterms'])
            hsterms_site_rdf_Description = etree.SubElement(hsterms_site, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_site_code = etree.SubElement(hsterms_site_rdf_Description, '{%s}SiteCode' % self.NAMESPACES['hsterms'])
            hsterms_site_code.text = self.site.site_code

            hsterms_site_name = etree.SubElement(hsterms_site_rdf_Description, '{%s}SiteName' % self.NAMESPACES['hsterms'])
            hsterms_site_name.text = self.site.site_name

            if self.site.elevation_m:
                hsterms_site_elevation_m = etree.SubElement(hsterms_site_rdf_Description, '{%s}Elevation_m' % self.NAMESPACES['hsterms'])
                hsterms_site_elevation_m.text = str(self.site.elevation_m)

            if self.site.elevation_datum:
                hsterms_site_elevation_datum = etree.SubElement(hsterms_site_rdf_Description, '{%s}ElevationDatum' % self.NAMESPACES['hsterms'])
                hsterms_site_elevation_datum.text = self.site.elevation_datum

            if self.site.site_type:
                hsterms_site_type = etree.SubElement(hsterms_site_rdf_Description, '{%s}SiteType' % self.NAMESPACES['hsterms'])
                hsterms_site_type.text = self.site.site_type

        if self.variable:
            hsterms_variable = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_variable_rdf_Description = etree.SubElement(hsterms_variable, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_variable_code = etree.SubElement(hsterms_variable_rdf_Description, '{%s}VariableCode' % self.NAMESPACES['hsterms'])
            hsterms_variable_code.text = self.variable.variable_code

            hsterms_variable_name = etree.SubElement(hsterms_variable_rdf_Description, '{%s}VariableName' % self.NAMESPACES['hsterms'])
            hsterms_variable_name.text = self.variable.variable_name

            hsterms_variable_type = etree.SubElement(hsterms_variable_rdf_Description, '{%s}VariableType' % self.NAMESPACES['hsterms'])
            hsterms_variable_type.text = self.variable.variable_type

            hsterms_no_data_value = etree.SubElement(hsterms_variable_rdf_Description, '{%s}NoDataValue' % self.NAMESPACES['hsterms'])
            hsterms_no_data_value.text = str(self.variable.no_data_value)

            if self.variable.variable_definition:
                hsterms_variable_def = etree.SubElement(hsterms_variable_rdf_Description, '{%s}VariableDefinition' % self.NAMESPACES['hsterms'])
                hsterms_variable_def.text = self.variable.variable_definition

            if self.variable.speciation:
                hsterms_speciation = etree.SubElement(hsterms_variable_rdf_Description, '{%s}Speciation' % self.NAMESPACES['hsterms'])
                hsterms_speciation.text = self.variable.speciation

        if self.method:
            hsterms_method = etree.SubElement(container, '{%s}method' % self.NAMESPACES['hsterms'])
            hsterms_method_rdf_Description = etree.SubElement(hsterms_method, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_method_code = etree.SubElement(hsterms_method_rdf_Description, '{%s}MethodCode' % self.NAMESPACES['hsterms'])
            hsterms_method_code.text = str(self.method.method_code)

            hsterms_method_name = etree.SubElement(hsterms_method_rdf_Description, '{%s}MethodName' % self.NAMESPACES['hsterms'])
            hsterms_method_name.text = self.method.method_name

            hsterms_method_type = etree.SubElement(hsterms_method_rdf_Description, '{%s}MethodType' % self.NAMESPACES['hsterms'])
            hsterms_method_type.text = self.method.method_type

            if self.method.method_description:
                hsterms_method_description = etree.SubElement(hsterms_method_rdf_Description, '{%s}MethodDescription' % self.NAMESPACES['hsterms'])
                hsterms_method_description.text = self.method.method_description

            if self.method.method_link:
                hsterms_method_link = etree.SubElement(hsterms_method_rdf_Description, '{%s}MethodLink' % self.NAMESPACES['hsterms'])
                hsterms_method_link.text = self.method.method_link

        if self.processing_level:
            hsterms_processing_level = etree.SubElement(container, '{%s}processingLevel' % self.NAMESPACES['hsterms'])
            hsterms_processing_level_rdf_Description = etree.SubElement(hsterms_processing_level, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_processing_level_code = etree.SubElement(hsterms_processing_level_rdf_Description, '{%s}ProcessingLevelCode' % self.NAMESPACES['hsterms'])
            hsterms_processing_level_code.text = str(self.processing_level.processing_level_code)

            if self.processing_level.definition:
                hsterms_definition = etree.SubElement(hsterms_processing_level_rdf_Description, '{%s}Definition' % self.NAMESPACES['hsterms'])
                hsterms_definition.text = str(self.processing_level.definition)

            if self.processing_level.explanation:
                hsterms_explanation = etree.SubElement(hsterms_processing_level_rdf_Description, '{%s}Explanation' % self.NAMESPACES['hsterms'])
                hsterms_explanation.text = str(self.processing_level.explanation)

        if self.time_series_result:
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

import receivers