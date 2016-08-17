import os
import sqlite3
import csv
import shutil
import logging
import tempfile
from uuid import uuid4
from dateutil import parser

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement, Creator
from hs_core.hydroshare import utils
from hs_core.hydroshare import add_resource_files


class TimeSeriesAbstractMetaDataElement(AbstractMetaDataElement):
    series_ids = ArrayField(models.CharField(max_length=36, null=True, blank=True), default=[])
    is_dirty = models.BooleanField(default=False)

    @classmethod
    def create(cls, **kwargs):
        if 'series_ids' not in kwargs:
            raise ValidationError("Timeseries ID(s) is missing")
        elif not isinstance(kwargs['series_ids'], list):
            raise ValidationError("Timeseries ID(s) must be a list")
        elif not kwargs['series_ids']:
            raise ValidationError("Timeseries ID(s) is missing")
        else:
            # series ids must be unique
            set_series_ids = set(kwargs['series_ids'])
            if len(set_series_ids) != len(kwargs['series_ids']):
                raise ValidationError("Duplicate series IDs are found")

        return super(TimeSeriesAbstractMetaDataElement, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        if 'series_ids' in kwargs:
            raise ValidationError("Timeseries ID(s) can't be updated")
        super(TimeSeriesAbstractMetaDataElement, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        element.is_dirty = True
        element.save()
        element.metadata.is_dirty = True
        element.metadata.save()

    class Meta:
        abstract = True


# define extended metadata elements for Time Series resource type
class Site(TimeSeriesAbstractMetaDataElement):
    term = 'Site'

    site_code = models.CharField(max_length=200)
    site_name = models.CharField(max_length=255)
    elevation_m = models.IntegerField(null=True, blank=True)
    elevation_datum = models.CharField(max_length=50, null=True, blank=True)
    site_type = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.site_name

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        # check that we are not creating site elements with duplicate site_code value
        if any(kwargs['site_code'].lower() == site.site_code.lower()
                for site in metadata.sites):
            raise ValidationError("There is already a site element "
                                  "with site_code:{}".format(kwargs['site_code']))

        if len(metadata.series_names) > 0:
            # this case applies only in case of CSV upload
            selected_series_id = kwargs.pop('selected_series_id', None)
            if selected_series_id is None:
                raise ValueError("Series id is missing")
            kwargs['series_ids'] = [selected_series_id]
            element = super(Site, cls).create(**kwargs)
            # update any other site element that is associated with the selected_series_id
            update_related_elements_on_create(element=element,
                                              related_elements=element.metadata.sites,
                                              selected_series_id=selected_series_id)
        else:
            element = super(Site, cls).create(**kwargs)

        # if the user has entered a new elevation datum or site type, then
        # create a corresponding new cv term
        _create_site_related_cv_terms(element=element, data_dict=kwargs)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not updating site elements with duplicate site_code value
        if any(kwargs['site_code'].lower() == site.site_code.lower() and site.id != element.id
                for site in element.metadata.sites):
            raise ValidationError("There is already a site element "
                                  "with site_code:{}".format(kwargs['site_code']))
        # if the user has entered a new elevation datum or site type, then create a
        # corresponding new cv term
        _create_site_related_cv_terms(element=element, data_dict=kwargs)

        super(Site, cls).update(element_id, **kwargs)
        selected_series_id = kwargs.pop('selected_series_id', None)
        update_related_elements_on_update(element=element,
                                          related_elements=element.metadata.sites,
                                          selected_series_id=selected_series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Site element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


class Variable(TimeSeriesAbstractMetaDataElement):
    term = 'Variable'
    variable_code = models.CharField(max_length=20)
    variable_name = models.CharField(max_length=100)
    variable_type = models.CharField(max_length=100)
    no_data_value = models.IntegerField()
    variable_definition = models.CharField(max_length=255, null=True, blank=True)
    speciation = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.variable_name

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        # check that we are not creating variable elements with duplicate variable_code value
        if any(kwargs['variable_code'].lower() == variable.variable_code.lower()
               for variable in metadata.variables):
            raise ValidationError("There is already a variable element "
                                  "with variable_code:{}".format(kwargs['variable_code']))

        if len(metadata.series_names) > 0:
            # this case applies only in case of CSV upload
            selected_series_id = kwargs.pop('selected_series_id', None)
            if selected_series_id is None:
                raise ValueError("Series id is missing")
            kwargs['series_ids'] = [selected_series_id]
            element = super(Variable, cls).create(**kwargs)
            # update any other variable element that is associated with the selected_series_id
            update_related_elements_on_create(element=element,
                                              related_elements=element.metadata.variables,
                                              selected_series_id=selected_series_id)

        else:
            element = super(Variable, cls).create(**kwargs)

        # if the user has entered a new variable name, variable type or speciation,
        # then create a corresponding new cv term
        _create_variable_related_cv_terms(element=element, data_dict=kwargs)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating variable elements with duplicate variable_code value
        if any(kwargs['variable_code'].lower() ==
               variable.variable_code.lower() and variable.id != element.id for variable in
               element.metadata.variables):
            raise ValidationError("There is already a variable element "
                                  "with variable_code:{}".format(kwargs['variable_code']))

        # if the user has entered a new variable name, variable type or speciation,
        # then create a corresponding new cv term
        _create_variable_related_cv_terms(element=element, data_dict=kwargs)

        super(Variable, cls).update(element_id, **kwargs)
        selected_series_id = kwargs.pop('selected_series_id', None)
        update_related_elements_on_update(element=element,
                                          related_elements=element.metadata.variables,
                                          selected_series_id=selected_series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Variable element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


class Method(TimeSeriesAbstractMetaDataElement):
    term = 'Method'
    method_code = models.CharField(max_length=50)
    method_name = models.CharField(max_length=200)
    method_type = models.CharField(max_length=200)
    method_description = models.TextField(null=True, blank=True)
    method_link = models.URLField(null=True, blank=True)

    def __unicode__(self):
        return self.method_name

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        # check that we are not creating method elements with duplicate method_code value
        if any(kwargs['method_code'].lower() == method.method_code.lower()
               for method in metadata.methods):
            raise ValidationError("There is already a method element "
                                  "with method_code:{}".format(kwargs['method_code']))

        if len(metadata.series_names) > 0:
            # this case applies only in case of CSV upload
            selected_series_id = kwargs.pop('selected_series_id', None)
            if selected_series_id is None:
                raise ValueError("Series id is missing")
            kwargs['series_ids'] = [selected_series_id]
            element = super(Method, cls).create(**kwargs)
            # update any other method element that is associated with the selected_series_id
            update_related_elements_on_create(element=element,
                                              related_elements=element.metadata.methods,
                                              selected_series_id=selected_series_id)

        else:
            element = super(Method, cls).create(**kwargs)

        # if the user has entered a new method type, then create a corresponding new cv term
        _create_cv_term(element=element, cv_term_class=CVMethodType,
                        cv_term_str='method_type', element_cv_term=element.method_type,
                        element_metadata_cv_terms=element.metadata.cv_method_types.all(),
                        data_dict=kwargs)

        return element
    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating method elements with duplicate method_code value
        if any(kwargs['method_code'].lower() ==
                method.method_code.lower() and method.id != element.id for method in
                element.metadata.methods):
            raise ValidationError("There is already a method element "
                                  "with method_code:{}".format(kwargs['method_code']))

        # if the user has entered a new method type, then create a corresponding new cv term
        _create_cv_term(element=element, cv_term_class=CVMethodType,
                        cv_term_str='method_type', element_cv_term=element.method_type,
                        element_metadata_cv_terms=element.metadata.cv_method_types.all(),
                        data_dict=kwargs)

        super(Method, cls).update(element_id, **kwargs)
        selected_series_id = kwargs.pop('selected_series_id', None)
        update_related_elements_on_update(element=element,
                                          related_elements=element.metadata.methods,
                                          selected_series_id=selected_series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Method element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


class ProcessingLevel(TimeSeriesAbstractMetaDataElement):
    term = 'ProcessingLevel'
    processing_level_code = models.IntegerField()
    definition = models.CharField(max_length=200, null=True, blank=True)
    explanation = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.processing_level_code

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        # check that we are not creating processinglevel elements with duplicate
        # processing_level_code value
        if any(kwargs['processing_level_code'] == pro_level.processing_level_code
               for pro_level in metadata.processing_levels):
            err_msg = "There is already a processinglevel element with processing_level_code:{}"
            err_msg = err_msg.format(kwargs['processing_level_code'])
            raise ValidationError(err_msg)

        if len(metadata.series_names) > 0:
            # this case applies only in case of CSV upload
            selected_series_id = kwargs.pop('selected_series_id', None)
            if selected_series_id is None:
                raise ValueError("Series id is missing")
            kwargs['series_ids'] = [selected_series_id]
            element = super(ProcessingLevel, cls).create(**kwargs)
            # update any other method element that is associated with the selected_series_id
            update_related_elements_on_create(element=element,
                                              related_elements=element.metadata.processing_levels,
                                              selected_series_id=selected_series_id)
            return element

        return super(ProcessingLevel, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating processinglevel elements with duplicate
        # processing_level_code value
        if any(kwargs['processing_level_code'] ==
                pro_level.processing_level_code and
                pro_level.id != element.id for pro_level in
               element.metadata.processing_levels):
            err_msg = "There is already a processinglevel element with processing_level_code:{}"
            err_msg = err_msg.format(kwargs['processing_level_code'])
            raise ValidationError(err_msg)

        super(ProcessingLevel, cls).update(element_id, **kwargs)
        selected_series_id = kwargs.pop('selected_series_id', None)
        update_related_elements_on_update(element=element,
                                          related_elements=element.metadata.processing_levels,
                                          selected_series_id=selected_series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


class TimeSeriesResult(TimeSeriesAbstractMetaDataElement):
    term = 'TimeSeriesResult'
    units_type = models.CharField(max_length=255)
    units_name = models.CharField(max_length=255)
    units_abbreviation = models.CharField(max_length=20)
    status = models.CharField(max_length=255)
    sample_medium = models.CharField(max_length=255)
    value_count = models.IntegerField()
    aggregation_statistics = models.CharField(max_length=255)
    series_label = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.units_type

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        if len(metadata.series_names) > 0:
            # this case applies only in case of CSV upload
            selected_series_id = kwargs.pop('selected_series_id', None)
            if selected_series_id is None:
                raise ValueError("Series id is missing")
            kwargs['series_ids'] = [selected_series_id]
            element = super(TimeSeriesResult, cls).create(**kwargs)

        else:
            element = super(TimeSeriesResult, cls).create(**kwargs)

        # if the user has entered a new sample medium, units type, status, or
        # aggregation statistics then create a corresponding new cv term
        _create_timeseriesresult_related_cv_terms(element=element, data_dict=kwargs)

        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # if the user has entered a new sample medium, units type, status, or
        # aggregation statistics then create a corresponding new cv term
        _create_timeseriesresult_related_cv_terms(element=element, data_dict=kwargs)

        super(TimeSeriesResult, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


class AbstractCVLookupTable(models.Model):
    term = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_dirty = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CVVariableType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_variable_types")


class CVVariableName(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_variable_names")


class CVSpeciation(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_speciations")


class CVElevationDatum(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_elevation_datums")


class CVSiteType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_site_types")


class CVMethodType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_method_types")


class CVUnitsType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_units_types")


class CVStatus(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_statuses")


class CVMedium(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_mediums")


class CVAggregationStatistic(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesMetaData', related_name="cv_aggregation_statistics")


class TimeSeriesResource(BaseResource):
    objects = ResourceManager("TimeSeriesResource")

    class Meta:
        verbose_name = 'Time Series'
        proxy = True

    @property
    def metadata(self):
        md = TimeSeriesMetaData()
        return self._get_metadata(md)

    @property
    def has_sqlite_file(self):
        for res_file in self.files.all():
            fl_ext = utils.get_resource_file_name_and_extension(res_file)[1]
            if fl_ext == '.sqlite':
                return True
        return False

    @property
    def has_csv_file(self):
        for res_file in self.files.all():
            fl_ext = utils.get_resource_file_name_and_extension(res_file)[1]
            if fl_ext == '.csv':
                return True
        return False

    @property
    def can_add_blank_sqlite_file(self):
        # use this property as a guard to decide when to add a blank SQLIte file
        # to the resource
        if self.has_sqlite_file:
            return False
        if not self.has_csv_file:
            return False

        return self.metadata.has_all_required_elements()

    @property
    def can_update_sqlite_file(self):
        return self.has_sqlite_file and self.metadata.has_all_required_elements()

    @classmethod
    def get_supported_upload_file_types(cls):
        # either a csv or a sqlite file can be uploaded
        # the internal storage format will always be sqlite
        # if a csv file is uploaded, a sqlite file will be generated using data
        # from the uploaded csv file.
        # the original uploaded csv file will also be kept as part of the resource
        return ".sqlite", ".csv"

    @classmethod
    def can_have_multiple_files(cls):
        # can upload only 1 file
        # however, the resource can have a sqlite file and a csv file
        # if the user uploads a sqlite file, then the resource will have
        # only one file (the uploaded sqlite file).
        # if the user uploads a csv file, a sqlite file will be created and
        # both the uploaded csv file and the generated sqlite file will be part
        # of the resource.
        return False

    def add_blank_sqlite_file(self):
        # add the blank SQLite file to this resource (self)
        if not self.can_add_blank_sqlite_file:
            err_msg = """Can't add blank ODM2 SQLite file to the resource.
             Resource may already have a SQLite file or there may not be enough metadata
             for the resource."""
            raise Exception(err_msg)

        # copy the blank sqlite file to a temp directory
        temp_dir = tempfile.mkdtemp()
        odm2_sqlite_file_name = 'ODM2.sqlite'
        odm2_sqlite_file = 'hs_app_timeseries/files/{}'.format(odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(temp_dir, odm2_sqlite_file_name)
        shutil.copy(odm2_sqlite_file, target_temp_sqlite_file)

        # add the sqlite file to the resource
        files = [UploadedFile(file=open(target_temp_sqlite_file, 'rb'),
                              name=odm2_sqlite_file_name)]
        try:
            add_resource_files(self.short_id, *files)
        except Exception as ex:
            raise ex
        finally:
            # cleanup the temp sqlite file directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

# this would allow us to pick up additional form elements for the template before the template
# is displayed
processor_for(TimeSeriesResource)(resource_processor)


class TimeSeriesMetaData(CoreMetaData):
    _sites = GenericRelation(Site)
    _variables = GenericRelation(Variable)
    _methods = GenericRelation(Method)
    _processing_levels = GenericRelation(ProcessingLevel)
    _time_series_results = GenericRelation(TimeSeriesResult)
    is_dirty = models.BooleanField(default=False)
    # temporarily store the series names from the csv file
    series_names = ArrayField(models.CharField(max_length=200, null=True, blank=True), default=[])

    @property
    def resource(self):
        return TimeSeriesResource.objects.filter(object_id=self.id).first()

    @property
    def sites(self):
        return self._sites.all()

    @property
    def variables(self):
        return self._variables.all()

    @property
    def methods(self):
        return self._methods.all()

    @property
    def processing_levels(self):
        return self._processing_levels.all()

    @property
    def time_series_results(self):
        return self._time_series_results.all()

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
        if not self.sites:
            return False
        if not self.variables:
            return False
        if not self.methods:
            return False
        if not self.processing_levels:
            return False
        if not self.time_series_results:
            return False

        if len(self.series_names) > 0:
            # applies to the case of csv file upload
            # check that we have each type of metadata element for each of the series ids
            series_ids = range(0, len(self.series_names))
            series_ids = set([str(n) for n in series_ids])
        else:
            series_ids = set(TimeSeriesResult.get_series_ids(metadata_obj=self))

        if series_ids:
            if series_ids != set(Site.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(Variable.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(Method.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(ProcessingLevel.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(TimeSeriesResult.get_series_ids(metadata_obj=self)):
                return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(TimeSeriesMetaData, self).get_required_missing_elements()
        if not self.sites:
            missing_required_elements.append('Site')
        if not self.variables:
            missing_required_elements.append('Variable')
        if not self.methods:
            missing_required_elements.append('Method')
        if not self.processing_levels:
            missing_required_elements.append('Processing Level')
        if not self.time_series_results:
            missing_required_elements.append('Time Series Result')

        if len(self.series_names) > 0:
            # applies only in the case of csv file upload
            # check that we have each type of metadata element for each of the series ids
            series_ids = range(0, len(self.series_names))
            series_ids = set([str(n) for n in series_ids])
            if self.sites and series_ids != set(Site.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Site')
            if self.variables and series_ids != set(Variable.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Variable')
            if self.methods and series_ids != set(Method.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Method')
            if self.processing_levels and series_ids != \
                    set(ProcessingLevel.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Processing Level')
            if self.time_series_results and series_ids != \
                    set(TimeSeriesResult.get_series_ids(metadata_obj=self)):
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

        for time_series_result in self.time_series_results:
            # since 2nd level nesting of elements exists here, can't use the helper function
            # add_metadata_element_to_xml()
            hsterms_time_series_result = etree.SubElement(
                container, '{%s}timeSeriesResult' % self.NAMESPACES['hsterms'])
            hsterms_time_series_result_rdf_Description = etree.SubElement(
                hsterms_time_series_result, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_result_UUID = etree.SubElement(
                hsterms_time_series_result_rdf_Description, '{%s}timeSeriesResultUUID' %
                                                            self.NAMESPACES['hsterms'])
            hsterms_result_UUID.text = str(time_series_result.series_ids[0])
            hsterms_units = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                             '{%s}units' % self.NAMESPACES['hsterms'])
            hsterms_units_rdf_Description = etree.SubElement(hsterms_units, '{%s}Description' %
                                                             self.NAMESPACES['rdf'])
            hsterms_units_type = etree.SubElement(hsterms_units_rdf_Description,
                                                  '{%s}UnitsType' % self.NAMESPACES['hsterms'])
            hsterms_units_type.text = time_series_result.units_type

            hsterms_units_name = etree.SubElement(hsterms_units_rdf_Description,
                                                  '{%s}UnitsName' % self.NAMESPACES['hsterms'])
            hsterms_units_name.text = time_series_result.units_name

            hsterms_units_abbv = etree.SubElement(
                hsterms_units_rdf_Description, '{%s}UnitsAbbreviation' % self.NAMESPACES['hsterms'])
            hsterms_units_abbv.text = time_series_result.units_abbreviation

            hsterms_status = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                              '{%s}Status' % self.NAMESPACES['hsterms'])
            hsterms_status.text = time_series_result.status

            hsterms_sample_medium = etree.SubElement(
                hsterms_time_series_result_rdf_Description, '{%s}SampleMedium' %
                                                            self.NAMESPACES['hsterms'])
            hsterms_sample_medium.text = time_series_result.sample_medium

            hsterms_value_count = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                   '{%s}ValueCount' % self.NAMESPACES['hsterms'])
            hsterms_value_count.text = str(time_series_result.value_count)

            hsterms_statistics = etree.SubElement(hsterms_time_series_result_rdf_Description,
                                                  '{%s}AggregationStatistic' %
                                                  self.NAMESPACES['hsterms'])
            hsterms_statistics.text = time_series_result.aggregation_statistics

            # generate xml for 'site' element
            sites = [site for site in self.sites if time_series_result.series_ids[0] in
                     site.series_ids]
            if sites:
                site = sites[0]
                element_fields = [('site_code', 'SiteCode'), ('site_name', 'SiteName')]

                if site.elevation_m:
                    element_fields.append(('elevation_m', 'Elevation_m'))

                if site.elevation_datum:
                    element_fields.append(('elevation_datum', 'ElevationDatum'))

                if site.site_type:
                    element_fields.append(('site_type', 'SiteType'))

                self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description,
                                                 (site, 'site'), element_fields)

            # generate xml for 'variable' element
            variables = [variable for variable in self.variables if
                         time_series_result.series_ids[0] in variable.series_ids]
            if variables:
                variable = variables[0]
                element_fields = [('variable_code', 'VariableCode'),
                                  ('variable_name', 'VariableName'),
                                  ('variable_type', 'VariableType'),
                                  ('no_data_value', 'NoDataValue')
                                  ]

                if variable.variable_definition:
                    element_fields.append(('variable_definition', 'VariableDefinition'))

                if variable.speciation:
                    element_fields.append(('speciation', 'Speciation'))

                self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description,
                                                 (variable, 'variable'), element_fields)

            # generate xml for 'method' element
            methods = [method for method in self.methods if time_series_result.series_ids[0] in
                       method.series_ids]
            if methods:
                method = methods[0]
                element_fields = [('method_code', 'MethodCode'), ('method_name', 'MethodName'),
                                  ('method_type', 'MethodType')]

                if method.method_description:
                    element_fields.append(('method_description', 'MethodDescription'))

                if method.method_link:
                    element_fields.append(('method_link', 'MethodLink'))

                self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description,
                                                 (method, 'method'), element_fields)

            # generate xml for 'processing_level' element
            processing_levels = [processing_level for processing_level in self.processing_levels if
                                 time_series_result.series_ids[0] in processing_level.series_ids]

            if processing_levels:
                processing_level = processing_levels[0]
                element_fields = [('processing_level_code', 'ProcessingLevelCode')]

                if processing_level.definition:
                    element_fields.append(('definition', 'Definition'))

                if processing_level.explanation:
                    element_fields.append(('explanation', 'Explanation'))

                self.add_metadata_element_to_xml(hsterms_time_series_result_rdf_Description,
                                                 (processing_level, 'processingLevel'),
                                                 element_fields)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(TimeSeriesMetaData, self).delete_all_elements()
        # delete resource specific metadata
        self.sites.delete()
        self.variables.delete()
        self.methods.delete()
        self.processing_levels.delete()
        self.time_series_results.delete()
        # delete CV lookup django tables
        self.cv_variable_types.all().delete()
        self.cv_variable_names.all().delete()
        self.cv_speciations.all().delete()
        self.cv_elevation_datums.all().delete()
        self.cv_site_types.all().delete()
        self.cv_method_types.all().delete()
        self.cv_units_types.all().delete()
        self.cv_statuses.all().delete()
        self.cv_mediums.all().delete()
        self.cv_aggregation_statistics.all().delete()

    def update_sqlite_file(self):
        if not self.is_dirty or not self.resource.has_sqlite_file:
            return

        if self.resource.has_csv_file:
            self.populate_blank_sqlite_file()
        else:
            sqlite_file_to_update = utils.get_resource_files_by_extension(self.resource, ".sqlite")[0]
            log = logging.getLogger()

            # retrieve the sqlite file from iRODS and save it to temp directory
            temp_sqlite_file = utils.get_file_from_irods(sqlite_file_to_update)
            try:
                con = sqlite3.connect(temp_sqlite_file)
                with con:
                    # get the records in python dictionary format
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    self._update_variables_table(con, cur)
                    self._update_methods_table(con, cur)
                    self._update_processinglevels_table(con, cur)
                    self._update_sites_related_tables(con, cur)
                    self._update_results_related_tables(con, cur)
                    self._update_CV_tables(con, cur)

                    # push the updated sqlite file to iRODS
                    utils.replace_resource_file_on_irods(temp_sqlite_file, sqlite_file_to_update)
                    self.is_dirty = False
                    self.save()
            except sqlite3.Error as ex:
                sqlite_err_msg = str(ex.args[0])
                log.error("Failed to update SQLite file. Error:{}".format(sqlite_err_msg))
                raise Exception(sqlite_err_msg)
            except Exception, ex:
                log.error("Failed to update SQLite file. Error:{}".format(ex.message))
                raise ex
            finally:
                if os.path.exists(temp_sqlite_file):
                    shutil.rmtree(os.path.dirname(temp_sqlite_file))

    def populate_blank_sqlite_file(self):
        if not self.resource.has_sqlite_file or not self.resource.has_csv_file:
            return

        # update resource specific metadata element series ids with generated GUID
        self._update_metadata_element_series_ids_with_guids()
        blank_sqlite_file = utils.get_resource_files_by_extension(self.resource, ".sqlite")[0]
        csv_file = utils.get_resource_files_by_extension(self.resource, ".csv")[0]
        log = logging.getLogger()

        # retrieve the sqlite file and csv file from iRODS and save it to temp directory
        temp_sqlite_file = utils.get_file_from_irods(blank_sqlite_file)
        temp_csv_file = utils.get_file_from_irods(csv_file)
        try:
            con = sqlite3.connect(temp_sqlite_file)
            with con:
                # get the records in python dictionary format
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                # insert records to SamplingFeatures table - first delete any existing records
                cur.execute("DELETE FROM SamplingFeatures")
                con.commit()
                insert_sql = "INSERT INTO SamplingFeatures(SamplingFeatureID, " \
                             "SamplingFeatureUUID, SamplingFeatureTypeCV, " \
                             "SamplingFeatureCode, SamplingFeatureName, " \
                             "Elevation_m, ElevationDatumCV) VALUES(?,?,?,?,?,?,?)"
                for index, site in enumerate(self.sites):
                    sampling_feature_id = index + 1
                    cur.execute(insert_sql, (sampling_feature_id, uuid4().hex, site.site_type,
                                site.site_code, site.site_name, site.elevation_m,
                                site.elevation_datum),)
                # con.commit()
                # insert record to SpatialReferences table - first delete any existing records
                cur.execute("DELETE FROM SpatialReferences")
                con.commit()
                coverage = None
                insert_sql = "INSERT INTO SpatialReferences (SpatialReferenceID, " \
                             "SRSName) VALUES(?,?)"
                if self.coverages.all():
                    # NOTE: It looks like there will be always maximum of only one record created
                    # for SpatialReferences table
                    coverage = self.coverages.all().exclude(type='period').first()
                    if coverage:
                        spatial_ref_id = 1
                        srs_name = coverage.value.get("projection", '')
                        cur.execute(insert_sql, (spatial_ref_id, srs_name),)

                # insert record to Sites table - first delete any existing records
                cur.execute("DELETE FROM Sites")
                con.commit()
                insert_sql = "INSERT INTO Sites (SamplingFeatureID, SiteTypeCV, Latitude, " \
                             "Longitude, SpatialReferenceID) VALUES(?,?,?,?,?)"
                for index, site in enumerate(self.sites):
                    sampling_feature_id = index + 1
                    spatial_ref_id = 1
                    lat = ''
                    lon = ''
                    # TODO: the following code needs to change once we add 'lat' and 'lon'
                    # attribute to Site element
                    # since we have maximum of one Coverage element of spatial type
                    # we will populate the latitude and longitude columns of the Sites table for the
                    # first record
                    if coverage and index == 0:
                        if coverage.type == 'point':
                            lat = coverage.value.get('north')
                            lon = coverage.value.get('east')
                        else:
                            lat = (coverage.value.get('northlimit') +
                                   coverage.value.get('southlimit'))/2
                            lon = (coverage.value.get('eastlimit') +
                                   coverage.value.get('westlimit'))/2

                    cur.execute(insert_sql, (sampling_feature_id, site.site_type, lat, lon,
                                             spatial_ref_id), )

                # insert record to Methods table - first delete any existing records
                cur.execute("DELETE FROM Methods")
                con.commit()
                insert_sql = "INSERT INTO Methods (MethodID, MethodTypeCV, MethodCode, " \
                             "MethodName, MethodDescription, MethodLink) VALUES(?,?,?,?,?,?)"
                methods_data = []
                for index, method in enumerate(self.methods):
                    method_id = index + 1
                    cur.execute(insert_sql, (method_id, method.method_type, method.method_code,
                                             method.method_name, method.method_description,
                                             method.method_link),)
                    methods_data.append({'method_id': method_id, 'series_ids': method.series_ids})
                # insert record to Variables table - first delete any existing records
                cur.execute("DELETE FROM Variables")
                con.commit()
                insert_sql = "INSERT INTO Variables (VariableID, VariableTypeCV, " \
                             "VariableCode, VariableNameCV, VariableDefinition, " \
                             "SpeciationCV, NoDataValue) VALUES(?,?,?,?,?,?,?)"
                variable_data = []
                for index, variable in enumerate(self.variables):
                    variable_id = index + 1
                    cur.execute(insert_sql, (variable_id, variable.variable_type,
                                             variable.variable_code, variable.variable_name,
                                             variable.variable_definition, variable.speciation,
                                             variable.no_data_value),)
                    variable_data.append({'variable_id': variable_id, 'object_id': variable.id})
                # insert record to Units table - first delete any existing records
                cur.execute("DELETE FROM Units")
                con.commit()
                insert_sql = "INSERT INTO Units (UnitsID, UnitsTypeCV, UnitsAbbreviation, " \
                             "UnitsName) VALUES(?,?,?,?)"
                for index, ts_result in enumerate(self.time_series_results):
                    units_id = index + 1
                    cur.execute(insert_sql, (units_id, ts_result.units_type,
                                             ts_result.units_abbreviation, ts_result.units_name),)
                # insert record to ProcessingLevels table - first delete any existing records
                cur.execute("DELETE FROM ProcessingLevels")
                con.commit()
                insert_sql = "INSERT INTO ProcessingLevels (ProcessingLevelID, " \
                             "ProcessingLevelCode, Definition, Explanation) VALUES(?,?,?,?)"
                pro_level_data = []
                for index, pro_level in enumerate(self.processing_levels):
                    pro_level_id = index + 1
                    cur.execute(insert_sql, (pro_level_id, pro_level.processing_level_code,
                                             pro_level.definition, pro_level.explanation),)

                    pro_level_data.append({'pro_level_id': pro_level_id,
                                           'object_id': pro_level.id})

                # insert record to People table - first delete any existing records
                cur.execute("DELETE FROM People")
                con.commit()
                insert_sql = "INSERT INTO People (PersonID, PersonFirstName, " \
                             "PersonMiddleName, PersonLastName) VALUES(?,?,?,?)"
                people_data = []
                for index, person in enumerate(list(self.creators.all()) +
                                               list(self.contributors.all())):
                    person_id = index + 1
                    name_parts = person.name.split()
                    first_name = name_parts[0]
                    mid_name = ''
                    last_name = ''
                    if len(name_parts) > 2:
                        mid_name = name_parts[1]
                        last_name = name_parts[2]
                    elif len(name_parts) == 2:
                        last_name = name_parts[1]
                    cur.execute(insert_sql, (person_id, first_name, mid_name, last_name), )
                    is_creator = isinstance(person, Creator)
                    people_data.append({'person_id': person_id,
                                        'organization': person.organization,
                                        'email': person.email,
                                        'phone': person.phone,
                                        'address': person.address,
                                        'is_creator': is_creator,
                                        'object_id': person.id})
                # insert record to Organizations table - first delete any existing records
                cur.execute("DELETE FROM Organizations")
                con.commit()
                organizations = []
                org_id = 1
                insert_sql = "INSERT INTO Organizations (OrganizationID, OrganizationTypeCV, " \
                             "OrganizationCode, OrganizationName) VALUES(?,?,?,?)"
                for person in (list(self.creators.all()) + list(self.contributors.all())):
                    organization_name = person.organization if person.organization else 'Unknown'
                    if organization_name not in organizations:
                        organizations.append(organization_name)
                        cur.execute(insert_sql, (org_id, 'Unknown', str(org_id),
                                                 organization_name),)
                        org_id += 1

                # insert record to Affiliations table - first delete any existing records
                cur.execute("DELETE FROM Affiliations")
                con.commit()
                insert_sql = "INSERT INTO Affiliations (AffiliationID, PersonID, OrganizationID, " \
                             "AffiliationStartDate, PrimaryPhone, PrimaryEmail, " \
                             "PrimaryAddress) VALUES(?,?,?,?,?,?,?)"

                select_sql = "SELECT * FROM People"
                cur.execute(select_sql)
                people = cur.fetchall()
                affiliation_id = 0
                for person in people:
                    affiliation_id += 1
                    person_data = [p for p in people_data if p['person_id'] ==
                                   person['PersonID']][0]
                    org = None
                    if person_data['organization']:
                        cur.execute("SELECT * FROM Organizations WHERE OrganizationName=?",
                                    (person_data['organization'],))
                        org = cur.fetchone()
                    org_id = org['OrganizationID'] if org else None
                    cur.execute(insert_sql, (affiliation_id, person['PersonID'], org_id,
                                             now(), person_data['phone'], person_data['email'],
                                             person_data['address']), )

                # insert record to Actions table - first delete any existing records
                cur.execute("DELETE FROM Actions")
                con.commit()
                insert_sql = "INSERT INTO Actions (ActionID, ActionTypeCV, MethodID, " \
                             "BeginDateTime, BeginDateTimeUTCOffset, " \
                             "ActionDescription) VALUES(?,?,?,?,?,?)"
                for index, ts_result in enumerate(self.time_series_results.all()):
                    action_id = index + 1
                    method_id = 1
                    for method_data_item in methods_data:
                        if ts_result.series_ids[0] in method_data_item['series_ids']:
                            method_id = method_data_item['method_id']
                            break
                    cur.execute(insert_sql, (action_id, 'Observation', method_id, now(), -7,
                                             'An observation action that generated a time '
                                             'series result.'),)

                # insert record to ActionBy table - first delete any existing records
                cur.execute("DELETE FROM ActionBy")
                con.commit()
                select_sql = "SELECT * FROM People"
                cur.execute(select_sql)
                people = cur.fetchall()
                insert_sql = "INSERT INTO ActionBy (BridgeID, ActionID, AffiliationID, " \
                             "IsActionLead, RoleDescription) VALUES(?,?,?,?,?)"
                cur.execute("SELECT * FROM Actions")
                actions = cur.fetchall()
                bridge_id = 1
                found_first_author = False
                for person in people:
                    cur.execute("SELECT * FROM Affiliations WHERE PersonID=?",
                                (person['PersonID'],))
                    affiliation = cur.fetchone()
                    affiliation_id = affiliation['AffiliationID']
                    # check is this person is the first author
                    is_action_lead = False
                    role_description = 'Contributor'
                    if not found_first_author:
                        for p_item in people_data:
                            if p_item['person_id'] == person['PersonID'] and p_item['is_creator']:
                                first_author = self.creators.all().filter(order=1)[0]
                                if first_author.id == p_item['object_id']:
                                    is_action_lead = True
                                    role_description = 'Creator'
                                    found_first_author = True
                                    break

                    for action in actions:
                        cur.execute(insert_sql, (bridge_id, action['ActionID'], affiliation_id,
                                                 is_action_lead, role_description),)
                        bridge_id += 1

                # insert record to FeatureActions table - first delete any existing records
                cur.execute("DELETE FROM FeatureActions")
                con.commit()
                insert_sql = "INSERT INTO FeatureActions (FeatureActionID, SamplingFeatureID, " \
                             "ActionID) VALUES(?,?,?)"
                for action in actions:
                    cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                                (action['ActionID'],))
                    sampling_feature = cur.fetchone()
                    sampling_feature_id = sampling_feature['SamplingFeatureID'] \
                        if sampling_feature else 1
                    cur.execute(insert_sql, (action['ActionID'], sampling_feature_id,
                                             action['ActionID']),)

                # insert record to Results table - first delete any existing records
                cur.execute("DELETE FROM Results")
                con.commit()
                insert_sql = "INSERT INTO Results (ResultID, ResultUUID, FeatureActionID, " \
                             "ResultTypeCV, VariableID, UnitsID, ProcessingLevelID, " \
                             "ResultDateTime, ResultDateTimeUTCOffset, StatusCV, " \
                             "SampledMediumCV, ValueCount) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"

                results_data = []
                for index, ts_res in enumerate(self.time_series_results.all()):
                    result_id = index + 1
                    cur.execute("SELECT * FROM FeatureActions WHERE ActionID=?", (result_id,))
                    feature_act = cur.fetchone()
                    related_var = self.variables.all().filter(
                        series_ids__contains=[ts_res.series_ids[0]]).first()
                    variable_id = 1
                    for var_item in variable_data:
                        if var_item['object_id'] == related_var.id:
                            variable_id = var_item['variable_id']
                            break

                    related_pro_level = self.processing_levels.all().filter(
                        series_ids__contains=[ts_res.series_ids[0]]).first()
                    pro_level_id = 1
                    for pro_level_item in pro_level_data:
                        if pro_level_item['object_id'] == related_pro_level.id:
                            pro_level_id = pro_level_item['pro_level_id']
                            break
                    cur.execute("SELECT * FROM Units Where UnitsID=?", (result_id,))
                    unit = cur.fetchone()
                    cur.execute(insert_sql, (result_id, ts_res.series_ids[0],
                                             feature_act['FeatureActionID'], 'Time series coverage',
                                             variable_id, unit['UnitsID'], pro_level_id, now(), -7,
                                             ts_res.status, ts_res.sample_medium,
                                             ts_res.value_count),)
                    results_data.append({'result_id': result_id, 'object_id': ts_res.id})

                # insert record to TimeSeriesResults table - first delete any existing records
                cur.execute("DELETE FROM TimeSeriesResults")
                con.commit()
                insert_sql = "INSERT INTO TimeSeriesResults (ResultID, AggregationStatisticCV) " \
                             "VALUES(?,?)"
                cur.execute("SELECT * FROM Results")
                results = cur.fetchall()
                for result in results:
                    res_item = [dict_item for dict_item in results_data if
                                dict_item['result_id'] == result['ResultID']][0]
                    ts_result = [ts_item for ts_item in self.time_series_results.all() if
                                 ts_item.id == res_item['object_id']][0]
                    cur.execute(insert_sql, (result['ResultID'], ts_result.aggregation_statistics),)

                # insert record to TimeSeriesResultValues table - first delete any existing records
                cur.execute("DELETE FROM TimeSeriesResultValues")
                con.commit()
                insert_sql = "INSERT INTO TimeSeriesResultValues (ValueID, ResultID, DataValue, " \
                             "ValueDateTime, ValueDateTimeUTCOffset, CensorCodeCV, " \
                             "QualityCodeCV, TimeAggregationInterval, " \
                             "TimeAggregationIntervalUnitsID) VALUES(?,?,?,?,?,?,?,?,?)"

                # read the csv file to determine time interval (in minutes) between each reading
                # we will use the first 2 rows of data to determine this value
                time_interval = 0
                with open(temp_csv_file, 'r') as fl_obj:
                    csv_reader = csv.reader(fl_obj, delimiter=',')
                    # read the first row (header)
                    header = csv_reader.next()
                    first_row_data = csv_reader.next()
                    second_row_data = csv_reader.next()
                    time_interval = (parser.parse(second_row_data[0]) -
                                     parser.parse(first_row_data[0])).seconds/60

                # data_row_count = 0
                with open(temp_csv_file, 'r') as fl_obj:
                    csv_reader = csv.reader(fl_obj, delimiter=',')
                    # read the first row (header) and skip
                    csv_reader.next()
                    value_id = 1
                    data_header = header[1:]
                    for col, value in enumerate(data_header):
                        # get the ts_result object with matching series_label
                        ts_result = [ts_item for ts_item in self.time_series_results if
                                     ts_item.series_label == value][0]
                        # get the result id associated with ts_result object
                        result_data_item = [dict_item for dict_item in results_data if
                                            dict_item['object_id'] == ts_result.id][0]
                        result_id = result_data_item['result_id']
                        data_col_index = col + 1
                        for date_time, data_value in self._read_csv_specified_column(
                                csv_reader, data_col_index):
                            date_time = parser.parse(date_time)
                            cur.execute(insert_sql, (value_id, result_id, data_value,
                                                     date_time, -7, 'Unknown', 'Unknown',
                                                     time_interval, 102),)
                            value_id += 1

                # self._update_variables_table(con, cur)
                # self._update_methods_table(con, cur)
                # self._update_processinglevels_table(con, cur)
                # self._update_sites_related_tables(con, cur)
                # self._update_results_related_tables(con, cur)
                # self._update_CV_tables(con, cur)

                con.commit()
                # push the updated sqlite file to iRODS
                utils.replace_resource_file_on_irods(temp_sqlite_file, blank_sqlite_file)
                self.is_dirty = False
                self.save()

        except sqlite3.Error as ex:
            sqlite_err_msg = str(ex.args[0])
            log.error("Failed to update SQLite file. Error:{}".format(sqlite_err_msg))
            raise Exception(sqlite_err_msg)
        except Exception as ex:
            log.error("Failed to update SQLite file. Error:{}".format(ex.message))
            raise ex
        finally:
            con.close()
            if os.path.exists(temp_sqlite_file):
                shutil.rmtree(os.path.dirname(temp_sqlite_file))
            if os.path.exists(temp_csv_file):
                shutil.rmtree(os.path.dirname(temp_csv_file))

    def _read_csv_specified_column(self, csv_reader, data_column_index):
        for row in csv_reader:
            yield row[0], row[data_column_index]

    def _update_metadata_element_series_ids_with_guids(self):
        if len(self.series_names) > 0:
            series_ids = {}
            # generate GUID for for each of the series ids
            for ts_result in self.time_series_results:
                guid = uuid4().hex
                if ts_result.series_ids[0] not in series_ids:
                    series_ids[ts_result.series_ids[0]] = guid

            for ts_result in self.time_series_results:
                ts_result.series_ids = [series_ids[ts_result.series_ids[0]]]
                ts_result.save()

            def update_to_guids(elements):
                for element in elements:
                    guids = []
                    for series_id in element.series_ids:
                        guids.append(series_ids[series_id])
                    element.series_ids = guids
                    element.save()

            update_to_guids(self.sites)
            update_to_guids(self.variables)
            update_to_guids(self.methods)
            update_to_guids(self.processing_levels)
            # delete all series name
            self.series_names = []
            self.save()

    def _update_CV_tables(self, con, cur):
        # here 'is_dirty' true means a new term has been added
        # so a new record needs to be added to the specific CV table
        def insert_cv_record(cv_elements, cv_table_name):
            for cv_element in cv_elements:
                if cv_element.is_dirty:
                    insert_sql = "INSERT INTO {table_name}(Term, Name) VALUES(?, ?)"
                    insert_sql = insert_sql.format(table_name=cv_table_name)
                    cur.execute(insert_sql, (cv_element.term, cv_element.name))
                    con.commit()
                    cv_element.is_dirty = False
                    cv_element.save()

        insert_cv_record(self.cv_variable_names.all(), 'CV_VariableName')
        insert_cv_record(self.cv_variable_types.all(), 'CV_VariableType')
        insert_cv_record(self.cv_speciations.all(), 'CV_Speciation')
        insert_cv_record(self.cv_site_types.all(), 'CV_SiteType')
        insert_cv_record(self.cv_elevation_datums.all(), 'CV_ElevationDatum')
        insert_cv_record(self.cv_method_types.all(), 'CV_MethodType')
        insert_cv_record(self.cv_units_types.all(), 'CV_UnitsType')
        insert_cv_record(self.cv_statuses.all(), 'CV_Status')
        insert_cv_record(self.cv_mediums.all(), 'CV_Medium')
        insert_cv_record(self.cv_aggregation_statistics.all(), 'CV_AggregationStatistic')

    def _update_variables_table(self, con, cur):
        for variable in self.variables:
            if variable.is_dirty:
                # get the VariableID from Results table to update the corresponding row in
                # Variables table
                series_id = variable.series_ids[0]
                cur.execute("SELECT VariableID FROM Results WHERE ResultUUID=?", (series_id,))
                ts_result = cur.fetchone()
                update_sql = "UPDATE Variables SET VariableCode=?, VariableTypeCV=?, " \
                             "VariableNameCV=?, VariableDefinition=?, SpeciationCV=?, " \
                             "NoDataValue=?  WHERE VariableID=?"

                params = (variable.variable_code, variable.variable_type, variable.variable_name,
                          variable.variable_definition, variable.speciation, variable.no_data_value,
                          ts_result['VariableID'])
                cur.execute(update_sql, params)
                con.commit()
                variable.is_dirty = False
                variable.save()

    def _update_methods_table(self, con, cur):
        # updates the Methods table
        for method in self.methods:
            if method.is_dirty:
                # get the MethodID to update the corresponding row in Methods table
                series_id = method.series_ids[0]
                cur.execute("SELECT FeatureActionID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()
                cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()
                cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                            (feature_action["ActionID"],))
                action = cur.fetchone()

                update_sql = "UPDATE Methods SET MethodCode=?, MethodName=?, MethodTypeCV=?, " \
                             "MethodDescription=?, MethodLink=?  WHERE MethodID=?"

                params = (method.method_code, method.method_name, method.method_type,
                          method.method_description, method.method_link,
                          action['MethodID'])
                cur.execute(update_sql, params)
                con.commit()
                method.is_dirty = False
                method.save()

    def _update_processinglevels_table(self, con, cur):
        # updates the ProcessingLevels table
        for processing_level in self.processing_levels:
            if processing_level.is_dirty:
                # get the ProcessingLevelID to update the corresponding row in ProcessingLevels
                # table
                series_id = processing_level.series_ids[0]
                cur.execute("SELECT ProcessingLevelID FROM Results WHERE ResultUUID=?",
                            (series_id,))
                result = cur.fetchone()

                update_sql = "UPDATE ProcessingLevels SET ProcessingLevelCode=?, Definition=?, " \
                             "Explanation=? WHERE ProcessingLevelID=?"

                params = (processing_level.processing_level_code, processing_level.definition,
                          processing_level.explanation, result['ProcessingLevelID'])

                cur.execute(update_sql, params)
                con.commit()
                processing_level.is_dirty = False
                processing_level.save()

    def _update_sites_related_tables(self, con, cur):
        # updates 'Sites' and 'SamplingFeatures' tables
        for site in self.sites:
            if site.is_dirty:
                # get the SamplingFeatureID to update the corresponding row in Sites and
                # SamplingFeatures tables
                series_id = site.series_ids[0]
                cur.execute("SELECT FeatureActionID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()
                cur.execute("SELECT SamplingFeatureID FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()

                # first update the sites table
                update_sql = "UPDATE Sites SET SiteTypeCV=? WHERE SamplingFeatureID=?"
                params = (site.site_type, feature_action["SamplingFeatureID"])
                cur.execute(update_sql, params)

                # then update the SamplingFeatures table
                update_sql = "UPDATE SamplingFeatures SET SamplingFeatureCode=?, " \
                             "SamplingFeatureName=?, Elevation_m=?, ElevationDatumCV=? " \
                             "WHERE SamplingFeatureID=?"

                params = (site.site_code, site.site_name, site.elevation_m,
                          site.elevation_datum, feature_action["SamplingFeatureID"])
                cur.execute(update_sql, params)
                con.commit()
                site.is_dirty = False
                site.save()

    def _update_results_related_tables(self, con, cur):
        # updates 'Results', 'Units' and 'TimeSeriesResults' tables
        for ts_result in self.time_series_results:
            if ts_result.is_dirty:
                # get the UnitsID and ResultID to update the corresponding row in Results,
                # Units and TimeSeriesResults tables
                series_id = ts_result.series_ids[0]
                cur.execute("SELECT UnitsID, ResultID FROM Results WHERE ResultUUID=?",
                            (series_id,))
                result = cur.fetchone()

                # update Units table
                update_sql = "UPDATE Units SET UnitsTypeCV=?, UnitsName=?, UnitsAbbreviation=? " \
                             "WHERE UnitsID=?"
                params = (ts_result.units_type, ts_result.units_name, ts_result.units_abbreviation,
                          result['UnitsID'])
                cur.execute(update_sql, params)

                # update TimeSeriesResults table
                update_sql = "UPDATE TimeSeriesResults SET AggregationStatisticCV=? " \
                             "WHERE ResultID=?"
                params = (ts_result.aggregation_statistics, result['ResultID'])
                cur.execute(update_sql, params)

                # then update the Results table
                update_sql = "UPDATE Results SET StatusCV=?, SampledMediumCV=?, ValueCount=? " \
                             "WHERE ResultID=?"

                params = (ts_result.status, ts_result.sample_medium, ts_result.value_count,
                          result['ResultID'])
                cur.execute(update_sql, params)
                con.commit()
                ts_result.is_dirty = False
                ts_result.save()


def _create_site_related_cv_terms(element, data_dict):
    # if the user has entered a new elevation datum, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVElevationDatum,
                    cv_term_str='elevation_datum', element_cv_term=element.elevation_datum,
                    element_metadata_cv_terms=element.metadata.cv_elevation_datums.all(),
                    data_dict=data_dict)

    # if the user has entered a new site type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVSiteType,
                    cv_term_str='site_type', element_cv_term=element.site_type,
                    element_metadata_cv_terms=element.metadata.cv_site_types.all(),
                    data_dict=data_dict)


def _create_variable_related_cv_terms(element, data_dict):
    # if the user has entered a new variable name, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVVariableName,
                    cv_term_str='variable_name', element_cv_term=element.variable_name,
                    element_metadata_cv_terms=element.metadata.cv_variable_names.all(),
                    data_dict=data_dict)

    # if the user has entered a new variable type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVVariableType,
                    cv_term_str='variable_type', element_cv_term=element.variable_type,
                    element_metadata_cv_terms=element.metadata.cv_variable_types.all(),
                    data_dict=data_dict)

    # if the user has entered a new speciation, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVSpeciation,
                    cv_term_str='speciation', element_cv_term=element.speciation,
                    element_metadata_cv_terms=element.metadata.cv_speciations.all(),
                    data_dict=data_dict)


def _create_timeseriesresult_related_cv_terms(element, data_dict):
    # if the user has entered a new sample medium, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVMedium,
                    cv_term_str='sample_medium', element_cv_term=element.sample_medium,
                    element_metadata_cv_terms=element.metadata.cv_mediums.all(),
                    data_dict=data_dict)

    # if the user has entered a new units type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVUnitsType,
                    cv_term_str='units_type', element_cv_term=element.units_type,
                    element_metadata_cv_terms=element.metadata.cv_units_types.all(),
                    data_dict=data_dict)

    # if the user has entered a new status, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=CVStatus,
                    cv_term_str='status', element_cv_term=element.status,
                    element_metadata_cv_terms=element.metadata.cv_statuses.all(),
                    data_dict=data_dict)

    # if the user has entered a new aggregation statistics, then create a corresponding new
    # cv term
    _create_cv_term(element=element, cv_term_class=CVAggregationStatistic,
                    cv_term_str='aggregation_statistics',
                    element_cv_term=element.aggregation_statistics,
                    element_metadata_cv_terms=element.metadata.cv_aggregation_statistics.all(),
                    data_dict=data_dict)


def _create_cv_term(element, cv_term_class, cv_term_str, element_cv_term,
                    element_metadata_cv_terms, data_dict):
    """
    Helper function for creating a new CV term if needed
    :param element: the metadata element object being updated
    :param cv_term_class: CV term model class based on which an object to be created
    :param cv_term_str: cv term field name being updated
    :param element_cv_term: specific cv term object (an instance of cv_term_class) associated with
    the 'element' object
    :param element_metadata_cv_terms: list of all cv term objects
    (instances of cv_term_class) associated with the 'metadata' object
    :param data_dict: dict that has the data for updating the 'element'
    :return:
    """
    if cv_term_str in data_dict:
        # check if the user has entered a new name for the cv term
        if not any(data_dict[cv_term_str] == item.name
                   for item in element_metadata_cv_terms):
            # generate term for the new name
            data_dict[cv_term_str] = data_dict[cv_term_str].strip()
            term = _generate_term_from_name(data_dict[cv_term_str])
            cv_term = cv_term_class.objects.create(
                    metadata=element.metadata, term=term, name=data_dict[cv_term_str])
            cv_term.is_dirty = True
            cv_term.save()


def update_related_elements_on_create(element, related_elements, selected_series_id):
    # update any other elements of type element (on creation of element) that has
    # the selected_series_id. if an element is associated with a new series id as part
    # of updating an element, we have to update other elements of the same type
    # in terms of dis-associating any other elements with that series id.
    # If any other element is found not to be associated with a series
    # then that element needs to be deleted.

    other_elements = related_elements.filter(
        series_ids__contains=[selected_series_id]).exclude(id=element.id).all()
    for el in other_elements:
        el.series_ids.remove(selected_series_id)
        if len(el.series_ids) == 0:
            el.delete()
        else:
            el.save()


def update_related_elements_on_update(element, related_elements, selected_series_id):
    # update any other elements of type element (on update of element) that has the
    # selected_series_id. if an element is associated with a new series id as part of
    # updating an element, we have to update other elements of the same type in
    # terms of dis-associating any other elements with that series id.
    # If any other element is found to be not associated with a series
    # then that element needs to be deleted.

    if len(element.metadata.series_names) > 0:
        # this case applies only in case of CSV upload
        if selected_series_id is not None:
            if selected_series_id not in element.series_ids:
                element.series_ids = element.series_ids + [selected_series_id]
                element.save()
                other_elements = related_elements.filter(
                    series_ids__contains=[selected_series_id]).exclude(id=element.id).all()
                for el in other_elements:
                    el.series_ids.remove(selected_series_id)
                    if len(el.series_ids) == 0:
                        el.delete()
                    else:
                        el.save()

def _generate_term_from_name(name):
    name = name.strip()
    # remove any commas
    name = name.replace(',', '')
    # replace - with _
    name = name.replace('-', '_')
    # replace ( and ) with _
    name = name.replace('(', '_')
    name = name.replace(')', '_')

    name_parts = name.split()
    # first word lowercase, subsequent words start with a uppercase
    term = name_parts[0].lower() + ''.join([item.title() for item in name_parts[1:]])
    return term


def _get_series_ids(element_class, metadata_obj):
    series_ids = []
    elements = element_class.objects.filter(object_id=metadata_obj.id).all()
    for element in elements:
        series_ids += element.series_ids
    return series_ids
