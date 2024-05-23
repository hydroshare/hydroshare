import csv
import json
import logging
import os
import shutil
import sqlite3
import tempfile
import time
from collections import OrderedDict
from uuid import uuid4

from dateutil import parser
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import models, transaction
from django.template import Context, Template
from django.utils.timezone import now
from dominate import tags as html_tags
from rdflib import BNode, Literal
from rdflib.namespace import DC, DCTERMS

from hs_core.hs_rdf import HSTERMS, rdf_terms
from hs_core.hydroshare import utils
from hs_core.models import AbstractMetaDataElement
from hs_core.signals import post_add_timeseries_aggregation
from .base import AbstractFileMetaData, AbstractLogicalFile, FileTypeContext

_SQLITE_FILE_NAME = 'ODM2.sqlite'
_ODM2_SQLITE_FILE_PATH = f'hs_file_types/files/{_SQLITE_FILE_NAME}'


class AbstractCVLookupTable(models.Model):
    term = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_dirty = models.BooleanField(default=False)

    class Meta:
        abstract = True


class CVVariableType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_variable_types")


class CVVariableName(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_variable_names")


class CVSpeciation(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_speciations")


class CVElevationDatum(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE,
                                 related_name="cv_elevation_datums")


class CVSiteType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_site_types")


class CVMethodType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_method_types")


class CVUnitsType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_units_types")


class CVStatus(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_statuses")


class CVMedium(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE, related_name="cv_mediums")


class CVAggregationStatistic(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', on_delete=models.CASCADE,
                                 related_name="cv_aggregation_statistics")


class TimeSeriesAbstractMetaDataElement(AbstractMetaDataElement):
    # for associating an metadata element with one or more time series
    series_ids = ArrayField(models.CharField(max_length=36, null=True, blank=True), default=list)
    # to track if element has been modified to trigger sqlite file update
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

        element = super(TimeSeriesAbstractMetaDataElement, cls).create(**kwargs)
        # set the 'is_dirty' field of metadata object to True
        # if we are creating the element when there is a csv file
        # note: in case of sqlite file upload we don't create any resource specific metadata
        # elements - we do only metadata element updates
        metadata = element.metadata
        ts_aggr = metadata.logical_file
        if ts_aggr.has_csv_file:
            element.is_dirty = True
            element.save()
            metadata.is_dirty = True
            metadata.save()
        return element

    def get_field_terms_and_values(self, extra_ignored_fields=[]):
        """Method that returns the field terms and field values on an object"""
        return super(TimeSeriesAbstractMetaDataElement,
                     self).get_field_terms_and_values(extra_ignored_fields=['is_dirty'])

    @classmethod
    def update(cls, element_id, **kwargs):
        super(TimeSeriesAbstractMetaDataElement, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        element.is_dirty = True
        element.save()
        element.metadata.is_dirty = True
        element.metadata.save()

    @classmethod
    def validate_series_ids(cls, metadata, element_data_dict):
        # this validation applies only in case of csv upload - until data is
        # written to the blank ODM2 sqlite file
        selected_series_id = element_data_dict.pop('selected_series_id', None)
        if selected_series_id is not None:
            element_data_dict['series_ids'] = [selected_series_id]
        if 'series_ids' in element_data_dict:
            if len(element_data_dict['series_ids']) > len(metadata.series_names):
                raise ValidationError("Not a valid series id.")
            for s_id in element_data_dict['series_ids']:
                if int(s_id) >= len(metadata.series_names):
                    raise ValidationError("Not a valid series id.")

    @classmethod
    def process_series_ids(cls, metadata, element_data_dict):
        # this class method should be called prior to updating an element
        selected_series_id = element_data_dict.get('selected_series_id', None)
        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, element_data_dict)

        if selected_series_id is not None:
            # case of additive - the selected_series_id will be added to the existing
            # series ids of the element being updated
            # so not updating series_ids as part of the element update
            # update element series_ids as part of the update_related_elements_on_update()
            series_ids = element_data_dict.pop('series_ids', [])
        else:
            # case of replacement - existing series_ids of the element will be replaced
            # by the series_ids
            series_ids = element_data_dict.get('series_ids', [])
        return series_ids

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        """Parses series_ids"""
        term = cls.get_class_term()
        if not term:
            metadata_nodes = [subject]
        else:
            metadata_nodes = graph.objects(subject=subject, predicate=term)
        for metadata_node in metadata_nodes:
            value_dict = {}
            for field in cls._meta.fields:
                if cls.ignored_fields and field.name in cls.ignored_fields:
                    continue
                field_term = cls.get_field_term(field.name)
                val = graph.value(metadata_node, field_term)
                if field_term == HSTERMS.timeSeriesResultUUID:
                    if val is not None:
                        value_dict[field.name] = [v.replace("'", "") for v in val.strip('][').split(', ')]
                elif val is not None:
                    value_dict[field.name] = str(val.toPython())
            if value_dict:
                cls.create(content_object=content_object, **value_dict)

    class Meta:
        abstract = True


@rdf_terms(HSTERMS.site, series_ids=HSTERMS.timeSeriesResultUUID, site_code=HSTERMS.SiteCode,
           site_name=HSTERMS.SiteName, elevation_m=HSTERMS.Elevation_m, elevation_datum=HSTERMS.ElevationDatum,
           site_type=HSTERMS.SiteType, latitude=HSTERMS.Latitude, longitude=HSTERMS.Longitude)
class Site(TimeSeriesAbstractMetaDataElement):
    term = 'Site'
    site_code = models.CharField(max_length=200)
    site_name = models.CharField(max_length=255, null=True, blank=True)
    elevation_m = models.FloatField(null=True, blank=True)
    elevation_datum = models.CharField(max_length=50, null=True, blank=True)
    site_type = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.site_name

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        html_table = html_tags.table(cls='custom-table')
        with html_table:
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('Code')
                        html_tags.td(self.site_code)
                    if self.site_name:
                        with html_tags.tr():
                            get_th('Name')
                            html_tags.td(self.site_name, style="word-break: normal;")
                    if self.elevation_m:
                        with html_tags.tr():
                            get_th('Elevation M')
                            html_tags.td(self.elevation_m)
                    if self.elevation_datum:
                        with html_tags.tr():
                            get_th('Elevation Datum')
                            html_tags.td(self.elevation_datum)
                    if self.site_type:
                        with html_tags.tr():
                            get_th('Site Type')
                            html_tags.td(self.site_type)
                    with html_tags.tr():
                        get_th('Latitude')
                        html_tags.td(self.latitude)
                    with html_tags.tr():
                        get_th('Longitude')
                        html_tags.td(self.longitude)

        return html_table.render(pretty=pretty)

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        # check that we are not creating site elements with duplicate site_code value
        if any(kwargs['site_code'].lower() == site.site_code.lower()
                for site in metadata.sites):
            raise ValidationError("There is already a site element "
                                  "with site_code:{}".format(kwargs['site_code']))

        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, kwargs)
            element = super(Site, cls).create(**kwargs)
            # update any other site element that is associated with the selected_series_id
            for series_id in kwargs['series_ids']:
                update_related_elements_on_create(element=element,
                                                  related_elements=element.metadata.sites,
                                                  selected_series_id=series_id)
        else:
            element = super(Site, cls).create(**kwargs)

        # if the user has entered a new elevation datum or site type, then
        # create a corresponding new cv term
        _create_site_related_cv_terms(element=element, data_dict=kwargs)

        # update resource coverage upon site element create
        _update_resource_coverage_element(site_element=element)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not updating site elements with duplicate site_code value
        if 'site_code' in kwargs:
            if any(kwargs['site_code'].lower() == site.site_code.lower() and site.id != element.id
                    for site in element.metadata.sites):
                raise ValidationError("There is already a site element "
                                      "with site_code:{}".format(kwargs['site_code']))

        series_ids = cls.process_series_ids(element.metadata, kwargs)
        super(Site, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        # if the user has entered a new elevation datum or site type, then create a
        # corresponding new cv term
        _create_site_related_cv_terms(element=element, data_dict=kwargs)

        for series_id in series_ids:
            update_related_elements_on_update(element=element,
                                              related_elements=element.metadata.sites,
                                              selected_series_id=series_id)

        # update resource coverage upon site element update
        _update_resource_coverage_element(site_element=element)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Site element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        # get the series ids associated with this element
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)


@rdf_terms(HSTERMS.variable, series_ids=HSTERMS.timeSeriesResultUUID, variable_code=HSTERMS.VariableCode,
           variable_name=HSTERMS.VariableName, variable_type=HSTERMS.VariableType, no_data_value=HSTERMS.NoDataValue,
           variable_definition=HSTERMS.VariableDefinition, speciation=HSTERMS.Speciation)
class VariableTimeseries(TimeSeriesAbstractMetaDataElement):
    term = 'Variable'
    variable_code = models.CharField(max_length=50)
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

        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, kwargs)
            element = super(VariableTimeseries, cls).create(**kwargs)
            # update any other variable element that is associated with the selected_series_id
            for series_id in kwargs['series_ids']:
                update_related_elements_on_create(element=element,
                                                  related_elements=element.metadata.variables,
                                                  selected_series_id=series_id)

        else:
            element = super(VariableTimeseries, cls).create(**kwargs)

        # if the user has entered a new variable name, variable type or speciation,
        # then create a corresponding new cv term
        _create_variable_related_cv_terms(element=element, data_dict=kwargs)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating variable elements with duplicate variable_code value
        if 'variable_code' in kwargs:
            if any(kwargs['variable_code'].lower()
                   == variable.variable_code.lower() and variable.id != element.id for variable in
                   element.metadata.variables):
                raise ValidationError("There is already a variable element "
                                      "with variable_code:{}".format(kwargs['variable_code']))

        series_ids = cls.process_series_ids(element.metadata, kwargs)
        super(VariableTimeseries, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        # if the user has entered a new variable name, variable type or speciation,
        # then create a corresponding new cv term
        _create_variable_related_cv_terms(element=element, data_dict=kwargs)
        for series_id in series_ids:
            update_related_elements_on_update(element=element,
                                              related_elements=element.metadata.variables,
                                              selected_series_id=series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Variable element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        html_table = html_tags.table(cls='custom-table')
        with html_table:
            with html_tags.tbody():
                with html_tags.tr():
                    get_th('Code')
                    html_tags.td(self.variable_code)
                with html_tags.tr():
                    get_th('Name')
                    html_tags.td(self.variable_name)
                with html_tags.tr():
                    get_th('Type')
                    html_tags.td(self.variable_type)
                with html_tags.tr():
                    get_th('No Data Value')
                    html_tags.td(self.no_data_value)
                if self.variable_definition:
                    with html_tags.tr():
                        get_th('Definition')
                        html_tags.td(self.variable_definition, style="word-break: normal;")
                if self.speciation:
                    with html_tags.tr():
                        get_th('Speciations')
                        html_tags.td(self.speciation)

        return html_table.render(pretty=pretty)


@rdf_terms(HSTERMS.method, series_ids=HSTERMS.timeSeriesResultUUID, method_code=HSTERMS.MethodCode,
           method_name=HSTERMS.MethodName, method_type=HSTERMS.MethodType, method_description=HSTERMS.MethodDescription,
           method_link=HSTERMS.MethodLink)
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

        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, kwargs)
            element = super(Method, cls).create(**kwargs)
            # update any other method element that is associated with the selected_series_id
            for series_id in kwargs['series_ids']:
                update_related_elements_on_create(element=element,
                                                  related_elements=element.metadata.methods,
                                                  selected_series_id=series_id)

        else:
            element = super(Method, cls).create(**kwargs)

        # if the user has entered a new method type, then create a corresponding new cv term
        cv_method_type_class = CVMethodType
        _create_cv_term(element=element, cv_term_class=cv_method_type_class,
                        cv_term_str='method_type',
                        element_metadata_cv_terms=element.metadata.cv_method_types.all(),
                        data_dict=kwargs)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating method elements with duplicate method_code value
        if 'method_code' in kwargs:
            if any(kwargs['method_code'].lower()
                    == method.method_code.lower() and method.id != element.id for method in
                    element.metadata.methods):
                raise ValidationError("There is already a method element "
                                      "with method_code:{}".format(kwargs['method_code']))

        series_ids = cls.process_series_ids(element.metadata, kwargs)
        super(Method, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        # if the user has entered a new method type, then create a corresponding new cv term
        cv_method_type_class = CVMethodType
        _create_cv_term(element=element, cv_term_class=cv_method_type_class,
                        cv_term_str='method_type',
                        element_metadata_cv_terms=element.metadata.cv_method_types.all(),
                        data_dict=kwargs)

        for series_id in series_ids:
            update_related_elements_on_update(element=element,
                                              related_elements=element.metadata.methods,
                                              selected_series_id=series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Method element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        # get series ids associated with this element
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        html_table = html_tags.table(cls='custom-table')
        with html_table:
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('Code')
                        html_tags.td(self.method_code)
                    with html_tags.tr():
                        get_th('Name')
                        html_tags.td(self.method_name, style="word-break: normal;")
                    with html_tags.tr():
                        get_th('Type')
                        html_tags.td(self.method_type)
                    if self.method_description:
                        with html_tags.tr():
                            get_th('Description')
                            html_tags.td(self.method_description, style="word-break: normal;")
                    if self.method_link:
                        with html_tags.tr():
                            get_th('Link')
                            with html_tags.td():
                                html_tags.a(self.method_link, target="_blank", href=self.method_link)

        return html_table.render(pretty=pretty)


@rdf_terms(HSTERMS.processingLevel, series_ids=HSTERMS.timeSeriesResultUUID,
           processing_level_code=HSTERMS.ProcessingLevelCode, definition=HSTERMS.Definition,
           explanation=HSTERMS.Explanation)
class ProcessingLevel(TimeSeriesAbstractMetaDataElement):
    term = 'ProcessingLevel'
    processing_level_code = models.CharField(max_length=50)
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

        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, kwargs)
            element = super(ProcessingLevel, cls).create(**kwargs)
            # update any other method element that is associated with the selected_series_id
            for series_id in kwargs['series_ids']:
                update_related_elements_on_create(
                    element=element,
                    related_elements=element.metadata.processing_levels,
                    selected_series_id=series_id)
            return element

        return super(ProcessingLevel, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        # check that we are not creating processinglevel elements with duplicate
        # processing_level_code value
        if 'processing_level_code' in kwargs:
            if any(kwargs['processing_level_code']
                    == pro_level.processing_level_code
                    and pro_level.id != element.id for pro_level in
                   element.metadata.processing_levels):
                err_msg = "There is already a processinglevel element with processing_level_code:{}"
                err_msg = err_msg.format(kwargs['processing_level_code'])
                raise ValidationError(err_msg)

        series_ids = cls.process_series_ids(element.metadata, kwargs)
        super(ProcessingLevel, cls).update(element_id, **kwargs)
        element = cls.objects.get(id=element_id)
        for series_id in series_ids:
            update_related_elements_on_update(
                element=element,
                related_elements=element.metadata.processing_levels,
                selected_series_id=series_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ProcessingLevel element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        html_table = html_tags.table(cls='custom-table')
        with html_table:
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('Code')
                        html_tags.td(self.processing_level_code)
                    if self.definition:
                        with html_tags.tr():
                            get_th('Definition')
                            html_tags.td(self.definition, style="word-break: normal;")
                    if self.explanation:
                        with html_tags.tr():
                            get_th('Explanation')
                            html_tags.td(self.explanation, style="word-break: normal;")

        return html_table.render(pretty=pretty)


@rdf_terms(HSTERMS.timeSeriesResult, series_ids=HSTERMS.timeSeriesResultUUID, units_type=HSTERMS.UnitsType,
           units_name=HSTERMS.UnitsName, units_abbreviation=HSTERMS.UnitsAbbreviation,
           status=HSTERMS.Status, sample_medium=HSTERMS.SampleMedium, value_count=HSTERMS.ValueCount,
           aggregation_statistics=HSTERMS.AggregationStatistic, series_label=HSTERMS.SeriesLabel)
class TimeSeriesResult(TimeSeriesAbstractMetaDataElement):
    term = 'TimeSeriesResult'
    units_type = models.CharField(max_length=255)
    units_name = models.CharField(max_length=255)
    units_abbreviation = models.CharField(max_length=20)
    status = models.CharField(max_length=255, blank=True, null=True)
    sample_medium = models.CharField(max_length=255)
    value_count = models.IntegerField()
    aggregation_statistics = models.CharField(max_length=255)
    series_label = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.units_type

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(metadata, kwargs)

        if len(kwargs['series_ids']) > 1:
            raise ValidationError("Multiple series ids can't be assigned.")

        element = super(TimeSeriesResult, cls).create(**kwargs)
        # if the user has entered a new sample medium, units type, status, or
        # aggregation statistics then create a corresponding new cv term
        _create_timeseriesresult_related_cv_terms(element=element, data_dict=kwargs)
        return element

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        if 'series_ids' in kwargs:
            if len(kwargs['series_ids']) > 1:
                raise ValidationError("Multiple series ids can't be assigned.")

        if element.metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            # this validation applies only in case of CSV upload
            cls.validate_series_ids(element.metadata, kwargs)

        super(TimeSeriesResult, cls).update(element_id, **kwargs)
        # if the user has entered a new sample medium, units type, status, or
        # aggregation statistics then create a corresponding new cv term
        _create_timeseriesresult_related_cv_terms(element=element, data_dict=kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("TimeSeriesResult element of a resource can't be deleted.")

    @classmethod
    def get_series_ids(cls, metadata_obj):
        return _get_series_ids(element_class=cls, metadata_obj=metadata_obj)

    def get_html(self, pretty=True):
        """Generates html code for displaying data for this metadata element"""

        def get_th(heading_name):
            return html_tags.th(heading_name, cls="text-muted")

        html_table = html_tags.table(cls='custom-table')
        with html_table:
            with html_tags.table(cls='custom-table'):
                with html_tags.tbody():
                    with html_tags.tr():
                        get_th('Units Type')
                        html_tags.td(self.units_type)
                    with html_tags.tr():
                        get_th('Units Name')
                        html_tags.td(self.units_name)
                    with html_tags.tr():
                        get_th('Units Abbreviation')
                        html_tags.td(self.units_abbreviation)
                    if self.status:
                        with html_tags.tr():
                            get_th('Status')
                            html_tags.td(self.status)
                    with html_tags.tr():
                        get_th('Sample Medium')
                        html_tags.td(self.sample_medium)
                    with html_tags.tr():
                        get_th('Value Count')
                        html_tags.td(self.value_count)
                    with html_tags.tr():
                        get_th('Aggregation Statistics')
                        html_tags.td(self.aggregation_statistics)
                    if self.metadata.utc_offset:
                        with html_tags.tr():
                            get_th('UTC Offset')
                            html_tags.td(self.metadata.utc_offset.value)

        return html_table.render(pretty=pretty)


@rdf_terms(HSTERMS.UTCOffSet, series_ids=HSTERMS.timeSeriesResultUUID)
class UTCOffSet(TimeSeriesAbstractMetaDataElement):
    # this element is not part of the science metadata
    term = 'UTCOffSet'
    value = models.FloatField(default=0.0)

    @classmethod
    def create(cls, **kwargs):
        metadata = kwargs['content_object']
        kwargs.pop('selected_series_id', None)
        if metadata.utc_offset:
            raise ValidationError("There is already an UTCOffSet element")

        if metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            kwargs['series_ids'] = list(range(len(metadata.series_names)))

        return super(UTCOffSet, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = cls.objects.get(id=element_id)
        kwargs.pop('selected_series_id', None)
        if element.metadata.series_names:
            # this condition is true if csv file has been uploaded but data has not been written
            # to the blank sqlite file
            kwargs['series_ids'] = list(range(len(element.metadata.series_names)))

        super(UTCOffSet, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("UTCOffSet element of a resource can't be deleted.")


class TimeSeriesMetaDataMixin(models.Model):
    """This class must be the first class in the multi-inheritance list of classes"""
    _sites = GenericRelation(Site)
    _variables = GenericRelation(VariableTimeseries)
    _methods = GenericRelation(Method)
    _processing_levels = GenericRelation(ProcessingLevel)
    _time_series_results = GenericRelation(TimeSeriesResult)
    _utc_offset = GenericRelation(UTCOffSet)

    # temporarily store the series names (data column names) from the csv file
    # for storing data column name (key) and number of data points (value) for that column
    # this field is set to an empty dict once metadata changes are written to the blank sqlite
    # file as part of the sync operation
    value_counts = HStoreField(default=dict)

    class Meta:
        abstract = True

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

    @property
    def utc_offset(self):
        return self._utc_offset.all().first()

    @property
    def series_names(self):
        # This is used only in case of csv file upload
        # this property holds a list of data column names read from the
        # uploaded csv file. This list becomes an empty list
        # once metadata changes are written to the blank sqlite file as
        # part of the sync operation.
        self.refresh_from_db()
        return list(self.value_counts.keys())

    @property
    def series_ids(self):
        return TimeSeriesResult.get_series_ids(metadata_obj=self)

    @property
    def series_ids_with_labels(self):
        """Returns a dict with series id as the key and an associated label as value"""
        series_ids = {}
        tgt_obj = self.logical_file
        if tgt_obj.has_csv_file and tgt_obj.metadata.series_names:
            # this condition is true if the user has uploaded a csv file and the blank
            # sqlite file (added by the system) has never been synced before with metadata changes
            for index, series_name in enumerate(tgt_obj.metadata.series_names):
                series_ids[str(index)] = series_name
        else:
            for result in tgt_obj.metadata.time_series_results:
                series_id = result.series_ids[0]
                series_ids[series_id] = self._get_series_label(series_id, tgt_obj)

        # sort the dict on series names - item[1]
        series_ids = OrderedDict(sorted(list(series_ids.items()), key=lambda item: item[1].lower()))
        return series_ids

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(TimeSeriesMetaDataMixin, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Site')
        elements.append('VariableTimeseries')
        elements.append('Method')
        elements.append('ProcessingLevel')
        elements.append('TimeSeriesResult')
        elements.append('UTCOffSet')
        return elements

    def has_all_required_elements(self):
        if not super(TimeSeriesMetaDataMixin, self).has_all_required_elements():
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

        tg_obj = self.logical_file
        if tg_obj.has_csv_file:
            # applies to the case of csv file upload
            if not self.utc_offset:
                return False

        if self.series_names:
            # applies to the case of csv file upload
            # check that we have each type of metadata element for each of the series ids
            series_ids = list(range(0, len(self.series_names)))
            series_ids = set([str(n) for n in series_ids])
        else:
            series_ids = set(TimeSeriesResult.get_series_ids(metadata_obj=self))

        if series_ids:
            if series_ids != set(Site.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(VariableTimeseries.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(Method.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(ProcessingLevel.get_series_ids(metadata_obj=self)):
                return False
            if series_ids != set(TimeSeriesResult.get_series_ids(metadata_obj=self)):
                return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(TimeSeriesMetaDataMixin,
                                          self).get_required_missing_elements()
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

        if self.series_names:
            # applies only in the case of csv file upload
            # check that we have each type of metadata element for each of the series ids
            series_ids = list(range(0, len(self.series_names)))
            series_ids = set([str(n) for n in series_ids])
            if self.sites and series_ids != set(Site.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Site')
            if self.variables and series_ids != set(VariableTimeseries.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Variable')
            if self.methods and series_ids != set(Method.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Method')
            if self.processing_levels and series_ids != \
                    set(ProcessingLevel.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Processing Level')
            if self.time_series_results and series_ids != \
                    set(TimeSeriesResult.get_series_ids(metadata_obj=self)):
                missing_required_elements.append('Time Series Result')
            if not self.utc_offset:
                missing_required_elements.append('UTC Offset')

        return missing_required_elements

    def delete_all_elements(self):
        super(TimeSeriesMetaDataMixin, self).delete_all_elements()
        # delete resource specific metadata
        self.sites.delete()
        self.variables.delete()
        self.methods.delete()
        self.processing_levels.delete()
        self.time_series_results.delete()
        if self.utc_offset:
            self.utc_offset.delete()

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

    def create_cv_lookup_models(self, sql_cur):
        cv_variable_type = CVVariableType
        cv_variable_name = CVVariableName
        cv_speciation = CVSpeciation
        cv_site_type = CVSiteType
        cv_elevation_datum = CVElevationDatum
        cv_method_type = CVMethodType
        cv_units_type = CVUnitsType
        cv_status = CVStatus
        cv_medium = CVMedium
        cv_agg_statistic = CVAggregationStatistic

        table_name_class_mappings = {'CV_VariableType': cv_variable_type,
                                     'CV_VariableName': cv_variable_name,
                                     'CV_Speciation': cv_speciation,
                                     'CV_SiteType': cv_site_type,
                                     'CV_ElevationDatum': cv_elevation_datum,
                                     'CV_MethodType': cv_method_type,
                                     'CV_UnitsType': cv_units_type,
                                     'CV_Status': cv_status,
                                     'CV_Medium': cv_medium,
                                     'CV_AggregationStatistic': cv_agg_statistic}
        for table_name in table_name_class_mappings:
            sql_cur.execute("SELECT Term, Name FROM {}".format(table_name))
            table_rows = sql_cur.fetchall()
            for row in table_rows:
                table_name_class_mappings[table_name].objects.create(metadata=self,
                                                                     term=row['Term'],
                                                                     name=row['Name'])

    def get_element_by_series_id(self, series_id, elements):
        for element in elements:
            if series_id in element.series_ids:
                return element
        return None

    def _read_csv_specified_column(self, csv_reader, data_column_index):
        # generator function to read (one row) the datetime column and the specified data column
        for row in csv_reader:
            yield row[0], row[data_column_index]

    def _get_series_label(self, series_id, source):
        """Generate a label given a series id
        :param  series_id: id of the time series
        :param  source: either an instance of BaseResource or an instance of a Logical file type
        """
        label = "{site_code}:{site_name}, {variable_code}:{variable_name}, {units_name}, " \
                "{pro_level_code}, {method_name}"
        site = [site for site in source.metadata.sites if series_id in site.series_ids][0]
        variable = [variable for variable in source.metadata.variables if
                    series_id in variable.series_ids][0]
        method = [method for method in source.metadata.methods if series_id in method.series_ids][
            0]
        pro_level = [pro_level for pro_level in source.metadata.processing_levels if
                     series_id in pro_level.series_ids][0]
        ts_result = [ts_result for ts_result in source.metadata.time_series_results if
                     series_id in ts_result.series_ids][0]
        label = label.format(site_code=site.site_code, site_name=site.site_name,
                             variable_code=variable.variable_code,
                             variable_name=variable.variable_name, units_name=ts_result.units_name,
                             pro_level_code=pro_level.processing_level_code,
                             method_name=method.method_name)
        return label

    def update_CV_tables(self, con, cur):
        # here 'is_dirty' true means a new term has been added
        # so a new record needs to be added to the specific CV table
        # used both for writing to blank sqlite file and non-blank sqlite file
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

    def update_datasets_table(self, con, cur):
        # updates the Datasets table
        # used for updating the sqlite file that is not blank
        update_sql = "UPDATE Datasets SET DatasetTitle=?, DatasetAbstract=? " \
                     "WHERE DatasetID=1"

        ds_title = self.logical_file.dataset_name
        ds_abstract = self.abstract if self.abstract is not None else ''

        cur.execute(update_sql, (ds_title, ds_abstract), )
        con.commit()

    def update_datasets_table_insert(self, con, cur):
        # insert record to Datasets table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM Datasets")
        con.commit()
        insert_sql = "INSERT INTO Datasets (DatasetID, DatasetUUID, DatasetTypeCV, " \
                     "DatasetCode, DatasetTitle, DatasetAbstract) VALUES(?,?,?,?,?,?)"

        ds_title = self.logical_file.dataset_name
        ds_abstract = self.abstract if self.abstract is not None else ''
        ds_code = self.logical_file.resource.short_id

        cur.execute(insert_sql, (1, uuid4().hex, 'Multi-time series', ds_code, ds_title,
                                 ds_abstract), )

    def update_datatsetsresults_table_insert(self, con, cur):
        # insert record to DatasetsResults table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM DatasetsResults")
        con.commit()
        insert_sql = "INSERT INTO DatasetsResults (BridgeID, DatasetID, " \
                     "ResultID) VALUES(?,?,?)"

        cur.execute("SELECT ResultID FROM Results")
        results = cur.fetchall()
        cur.execute("SELECT DatasetID FROM DataSets")
        dataset = cur.fetchone()
        for index, result in enumerate(results):
            bridge_id = index + 1
            cur.execute(insert_sql, (bridge_id, dataset['DatasetID'], result['ResultID']), )

    def update_utcoffset_related_tables(self, con, cur):
        # updates Actions, Results, TimeSeriesResultValues tables
        # used for updating a sqlite file that is not blank and a csv file exists

        target_obj = self.logical_file
        if target_obj.has_csv_file and self.utc_offset.is_dirty:
            update_sql = "UPDATE Actions SET BeginDateTimeUTCOffset=?, EndDateTimeUTCOffset=?"
            utc_offset = self.utc_offset.value
            param_values = (utc_offset, utc_offset)
            cur.execute(update_sql, param_values)

            update_sql = "UPDATE Results SET ResultDateTimeUTCOffset=?"
            param_values = (utc_offset,)
            cur.execute(update_sql, param_values)

            update_sql = "UPDATE TimeSeriesResultValues SET ValueDateTimeUTCOffset=?"
            param_values = (utc_offset,)
            cur.execute(update_sql, param_values)

            con.commit()
            self.utc_offset.is_dirty = False
            self.utc_offset.save()

    def update_variables_table(self, con, cur):
        # updates Variables table
        # used for updating a sqlite file that is not blank
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

    def update_variables_table_insert(self, con, cur):
        # insert record to Variables table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM Variables")
        con.commit()
        insert_sql = "INSERT INTO Variables (VariableID, VariableTypeCV, " \
                     "VariableCode, VariableNameCV, VariableDefinition, " \
                     "SpeciationCV, NoDataValue) VALUES(?,?,?,?,?,?,?)"
        variables_data = []
        for index, variable in enumerate(self.variables):
            variable_id = index + 1
            cur.execute(insert_sql, (variable_id, variable.variable_type,
                                     variable.variable_code, variable.variable_name,
                                     variable.variable_definition, variable.speciation,
                                     variable.no_data_value), )
            variables_data.append({'variable_id': variable_id, 'object_id': variable.id})
        return variables_data

    def update_methods_table(self, con, cur):
        # updates the Methods table
        # used for updating a sqlite file that is not blank
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

    def update_methods_table_insert(self, con, cur):
        # insert record to Methods table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM Methods")
        con.commit()
        insert_sql = "INSERT INTO Methods (MethodID, MethodTypeCV, MethodCode, " \
                     "MethodName, MethodDescription, MethodLink) VALUES(?,?,?,?,?,?)"
        methods_data = []
        for index, method in enumerate(self.methods):
            method_id = index + 1
            cur.execute(insert_sql, (method_id, method.method_type, method.method_code,
                                     method.method_name, method.method_description,
                                     method.method_link), )
            methods_data.append({'method_id': method_id, 'series_ids': method.series_ids})

        return methods_data

    def update_processinglevels_table(self, con, cur):
        # updates the ProcessingLevels table
        # used for updating a sqlite file that is not blank
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

    def update_processinglevels_table_insert(self, con, cur):
        # insert record to ProcessingLevels table - first delete any existing records
        # this function used only in case of writing data to a blank database (case of CSV upload)

        cur.execute("DELETE FROM ProcessingLevels")
        con.commit()
        insert_sql = "INSERT INTO ProcessingLevels (ProcessingLevelID, " \
                     "ProcessingLevelCode, Definition, Explanation) VALUES(?,?,?,?)"
        pro_levels_data = []
        for index, pro_level in enumerate(self.processing_levels):
            pro_level_id = index + 1
            cur.execute(insert_sql, (pro_level_id, pro_level.processing_level_code,
                                     pro_level.definition, pro_level.explanation), )

            pro_levels_data.append({'pro_level_id': pro_level_id,
                                    'object_id': pro_level.id})

        return pro_levels_data

    def update_sites_related_tables(self, con, cur):
        # updates 'Sites' and 'SamplingFeatures' tables
        # used for updating a sqlite file that is not blank
        for site in self.sites:
            if site.is_dirty:
                # get the SamplingFeatureID to update the corresponding row in Sites and
                # SamplingFeatures tables
                # No need to process each series id associated with a site element. This
                # is due to the fact that for each site there can be only one value for
                # SamplingFeatureID. If we take into account all the series ids associated
                # with a site we will end up updating the same record in site table multiple
                # times with the same data.
                series_id = site.series_ids[0]
                cur.execute("SELECT FeatureActionID FROM Results WHERE ResultUUID=?", (series_id,))
                result = cur.fetchone()
                cur.execute("SELECT SamplingFeatureID FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()

                # first update the sites table
                update_sql = "UPDATE Sites SET SiteTypeCV=?, Latitude=?, Longitude=? " \
                             "WHERE SamplingFeatureID=?"
                params = (site.site_type, site.latitude, site.longitude,
                          feature_action["SamplingFeatureID"])
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

    def update_sites_table_insert(self, con, cur):
        # insert record to Sites table - first delete any existing records
        # this function used only in case of writing data to a blank database (case of CSV upload)

        cur.execute("DELETE FROM Sites")
        con.commit()
        insert_sql = "INSERT INTO Sites (SamplingFeatureID, SiteTypeCV, Latitude, " \
                     "Longitude, SpatialReferenceID) VALUES(?,?,?,?,?)"
        for index, site in enumerate(self.sites):
            sampling_feature_id = index + 1
            spatial_ref_id = 1
            cur.execute(insert_sql, (sampling_feature_id, site.site_type, site.latitude,
                                     site.longitude, spatial_ref_id), )

    def update_results_related_tables(self, con, cur):
        # updates 'Results', 'Units' and 'TimeSeriesResults' tables
        # this function is used for writing data to a sqlite file that is not blank
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

    def update_results_table_insert(self, con, cur, variables_data, pro_levels_data):
        # insert record to Results table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM Results")
        con.commit()
        insert_sql = "INSERT INTO Results (ResultID, ResultUUID, FeatureActionID, " \
                     "ResultTypeCV, VariableID, UnitsID, ProcessingLevelID, " \
                     "ResultDateTime, ResultDateTimeUTCOffset, StatusCV, " \
                     "SampledMediumCV, ValueCount) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"

        results_data = []
        utc_offset = self.utc_offset.value
        for index, ts_res in enumerate(self.time_series_results.all()):
            result_id = index + 1
            cur.execute("SELECT * FROM FeatureActions WHERE ActionID=?", (result_id,))
            feature_act = cur.fetchone()
            related_var = self.variables.all().filter(
                series_ids__contains=[ts_res.series_ids[0]]).first()
            variable_id = 1
            for var_item in variables_data:
                if var_item['object_id'] == related_var.id:
                    variable_id = var_item['variable_id']
                    break

            related_pro_level = self.processing_levels.all().filter(
                series_ids__contains=[ts_res.series_ids[0]]).first()
            pro_level_id = 1
            for pro_level_item in pro_levels_data:
                if pro_level_item['object_id'] == related_pro_level.id:
                    pro_level_id = pro_level_item['pro_level_id']
                    break
            cur.execute("SELECT * FROM Units Where UnitsID=?", (result_id,))
            unit = cur.fetchone()
            cur.execute(insert_sql, (result_id, ts_res.series_ids[0],
                                     feature_act['FeatureActionID'], 'Time series coverage',
                                     variable_id, unit['UnitsID'], pro_level_id, now(), utc_offset,
                                     ts_res.status, ts_res.sample_medium,
                                     ts_res.value_count), )
            results_data.append({'result_id': result_id, 'object_id': ts_res.id})
        return results_data

    def update_units_table_insert(self, con, cur):
        # insert record to Units table - first delete any existing records
        # this function used only in case of writing data to a blank database (case of CSV upload)

        cur.execute("DELETE FROM Units")
        con.commit()
        insert_sql = "INSERT INTO Units (UnitsID, UnitsTypeCV, UnitsAbbreviation, " \
                     "UnitsName) VALUES(?,?,?,?)"
        for index, ts_result in enumerate(self.time_series_results):
            units_id = index + 1
            cur.execute(insert_sql, (units_id, ts_result.units_type,
                                     ts_result.units_abbreviation, ts_result.units_name), )

    def update_metadata_element_series_ids_with_guids(self):
        # replace sequential series ids (0, 1, 2 ...) with GUID
        # only needs to be done in case of csv file upload before
        # writing metadata to the blank sqlite file
        if self.series_names:
            series_ids = {}
            # generate GUID for each of the series ids
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
            # delete all value_counts
            self.value_counts = {}
            self.save()

    def update_samplingfeatures_table_insert(self, con, cur):
        # insert records to SamplingFeatures table - first delete any existing records
        cur.execute("DELETE FROM SamplingFeatures")
        con.commit()
        insert_sql = "INSERT INTO SamplingFeatures(SamplingFeatureID, " \
                     "SamplingFeatureUUID, SamplingFeatureTypeCV, " \
                     "SamplingFeatureCode, SamplingFeatureName, " \
                     "SamplingFeatureGeotypeCV, Elevation_m, ElevationDatumCV) " \
                     "VALUES(?,?,?,?,?,?,?,?)"
        for index, site in enumerate(self.sites):
            sampling_feature_id = index + 1
            cur.execute(insert_sql, (sampling_feature_id, uuid4().hex, site.site_type,
                                     site.site_code, site.site_name, 'Point', site.elevation_m,
                                     site.elevation_datum), )

    def update_spatialreferences_table_insert(self, con, cur):
        # insert record to SpatialReferences table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM SpatialReferences")
        con.commit()
        insert_sql = "INSERT INTO SpatialReferences (SpatialReferenceID, " \
                     "SRSCode, SRSName) VALUES(?,?,?)"
        if self.coverages.all():
            # NOTE: It looks like there will be always maximum of only one record created
            # for SpatialReferences table
            coverage = self.coverages.all().exclude(type='period').first()
            if coverage:
                spatial_ref_id = 1
                # this is the default projection system for coverage in HydroShare
                srs_name = 'World Geodetic System 1984 (WGS84)'
                srs_code = 'EPSG:4326'
                cur.execute(insert_sql, (spatial_ref_id, srs_code, srs_name), )

    def update_featureactions_table_insert(self, con, cur):
        # insert record to FeatureActions table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM FeatureActions")
        con.commit()
        insert_sql = "INSERT INTO FeatureActions (FeatureActionID, SamplingFeatureID, " \
                     "ActionID) VALUES(?,?,?)"
        cur.execute("SELECT * FROM Actions")
        actions = cur.fetchall()
        for action in actions:
            cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                        (action['ActionID'],))
            sampling_feature = cur.fetchone()
            sampling_feature_id = sampling_feature['SamplingFeatureID'] \
                if sampling_feature else 1
            cur.execute(insert_sql, (action['ActionID'], sampling_feature_id,
                                     action['ActionID']), )

    def update_actions_table_insert(self, con, cur, methods_data):
        # insert record to Actions table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM Actions")
        con.commit()
        insert_sql = "INSERT INTO Actions (ActionID, ActionTypeCV, MethodID, " \
                     "BeginDateTime, BeginDateTimeUTCOffset, " \
                     "EndDateTime, EndDateTimeUTCOffset, " \
                     "ActionDescription) VALUES(?,?,?,?,?,?,?,?)"
        # get the begin and end date of timeseries data from the temporal coverage
        temp_coverage = self.coverages.filter(type='period').first()
        start_date = parser.parse(temp_coverage.value['start'])
        end_date = parser.parse(temp_coverage.value['end'])

        utc_offset = self.utc_offset.value
        for index, ts_result in enumerate(self.time_series_results.all()):
            action_id = index + 1
            method_id = 1
            for method_data_item in methods_data:
                if ts_result.series_ids[0] in method_data_item['series_ids']:
                    method_id = method_data_item['method_id']
                    break
            cur.execute(insert_sql, (action_id, 'Observation', method_id, start_date, utc_offset,
                                     end_date, utc_offset,
                                     'An observation action that generated a time '
                                     'series result.'), )

    def update_timeseriesresults_table_insert(self, con, cur, results_data):
        # insert record to TimeSeriesResults table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

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
            cur.execute(insert_sql, (result['ResultID'], ts_result.aggregation_statistics), )

    def update_timeseriesresultvalues_table_insert(self, con, cur, temp_csv_file, results_data):
        # insert record to TimeSeriesResultValues table - first delete any existing records
        # used for updating a sqlite file that is blank (case of CSV upload)

        cur.execute("DELETE FROM TimeSeriesResultValues")
        con.commit()
        insert_sql = "INSERT INTO TimeSeriesResultValues (ValueID, ResultID, DataValue, " \
                     "ValueDateTime, ValueDateTimeUTCOffset, CensorCodeCV, " \
                     "QualityCodeCV, TimeAggregationInterval, " \
                     "TimeAggregationIntervalUnitsID) VALUES(?,?,?,?,?,?,?,?,?)"

        # read the csv file to determine time interval (in minutes) between each reading
        # we will use the first 2 rows of data to determine this value
        utc_offset = self.utc_offset.value
        with open(temp_csv_file, 'r') as fl_obj:
            csv_reader = csv.reader(fl_obj, delimiter=',')
            # read the first row (header)
            header = next(csv_reader)
            first_row_data = next(csv_reader)
            second_row_data = next(csv_reader)
            time_interval = (parser.parse(second_row_data[0])
                             - parser.parse(first_row_data[0])).seconds / 60

        with open(temp_csv_file, 'r') as fl_obj:
            csv_reader = csv.reader(fl_obj, delimiter=',')
            # read the first row (header) and skip
            next(csv_reader)
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
                # start at the beginning of data row
                fl_obj.seek(0)
                next(csv_reader)
                for date_time, data_value in self._read_csv_specified_column(
                        csv_reader, data_col_index):
                    date_time = parser.parse(date_time)
                    cur.execute(insert_sql, (value_id, result_id, data_value,
                                             date_time, utc_offset, 'Unknown', 'Unknown',
                                             time_interval, 102), )
                    value_id += 1

    def populate_blank_sqlite_file(self, temp_sqlite_file, user):
        """
        writes data to a blank sqlite file. This function is executed only in case
        of CSV file upload and executed only once when updating the sqlite file for the first time.
        :param temp_sqlite_file: this is the sqlite file copied from irods to a temp location on
         Django.
        :param user: current user (must have edit permission on resource) who is updating the
        sqlite file to sync metadata changes in django database.
        :return:
        """
        log = logging.getLogger()

        if not self.logical_file.has_csv_file:
            msg = "Logical file needs to have a CSV file before a blank SQLite file " \
                  "can be updated"
            log.exception(msg)
            raise Exception(msg)

        # update resource specific metadata element series ids with generated GUID
        self.update_metadata_element_series_ids_with_guids()
        logical_file = self.logical_file
        for f in logical_file.files.all():
            if f.extension == '.sqlite':
                blank_sqlite_file = f
            elif f.extension == '.csv':
                csv_file = f

        # retrieve the csv file from iRODS and save it to temp directory
        temp_csv_file = utils.get_file_from_irods(resource=self.resource, file_path=csv_file.storage_path)
        try:
            con = sqlite3.connect(temp_sqlite_file)
            with con:
                # get the records in python dictionary format
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                # insert records to SamplingFeatures table
                self.update_samplingfeatures_table_insert(con, cur)

                # insert record to SpatialReferences table
                self.update_spatialreferences_table_insert(con, cur)

                # insert record to Sites table
                self.update_sites_table_insert(con, cur)

                # insert record to Methods table
                methods_data = self.update_methods_table_insert(con, cur)

                # insert record to Variables table
                variables_data = self.update_variables_table_insert(con, cur)

                # insert record to Units table
                self.update_units_table_insert(con, cur)

                # insert record to ProcessingLevels table
                pro_levels_data = self.update_processinglevels_table_insert(con, cur)

                # insert record to Actions table
                self.update_actions_table_insert(con, cur, methods_data)

                # insert record to FeatureActions table
                self.update_featureactions_table_insert(con, cur)

                # insert record to Results table
                results_data = self.update_results_table_insert(con, cur, variables_data,
                                                                pro_levels_data)

                # insert record to TimeSeriesResults table
                self.update_timeseriesresults_table_insert(con, cur, results_data)

                # insert record to TimeSeriesResultValues table
                self.update_timeseriesresultvalues_table_insert(con, cur, temp_csv_file,
                                                                results_data)

                # insert record to Datasets table
                self.update_datasets_table_insert(con, cur)

                # insert record to DatasetsResults table
                self.update_datatsetsresults_table_insert(con, cur)

                self.update_CV_tables(con, cur)
                con.commit()
                # push the updated sqlite file to iRODS
                utils.replace_resource_file_on_irods(temp_sqlite_file, blank_sqlite_file, user)
                self.is_dirty = False
                self.save()
                log.info("Blank SQLite file was updated successfully.")
        except sqlite3.Error as ex:
            sqlite_err_msg = str(ex.args[0])
            log.error("Failed to update blank SQLite file. Error:{}".format(sqlite_err_msg))
            raise Exception(sqlite_err_msg)
        except Exception as ex:
            log.exception("Failed to update blank SQLite file. Error:{}".format(str(ex)))
            raise ex
        finally:
            if os.path.exists(temp_sqlite_file):
                shutil.rmtree(os.path.dirname(temp_sqlite_file))
            if os.path.exists(temp_csv_file):
                shutil.rmtree(os.path.dirname(temp_csv_file))


class TimeSeriesFileMetaData(TimeSeriesMetaDataMixin, AbstractFileMetaData):
    model_app_label = 'hs_file_types'
    # this is to store abstract
    abstract = models.TextField(null=True, blank=True)

    # flag to track when the .sqlite file of the aggregation needs to be updated
    is_update_file = models.BooleanField(default=False)

    def get_metadata_elements(self):
        elements = super(TimeSeriesFileMetaData, self).get_metadata_elements()
        elements += list(self.sites)
        elements += list(self.variables)
        elements += list(self.methods)
        elements += list(self.processing_levels)
        elements += list(self.time_series_results)
        if self.utc_offset is not None:
            elements += [self.utc_offset]
        return elements

    def _get_metadata_element_model_type(self, element_model_name):
        if element_model_name.lower() == 'variable':
            element_model_name = 'variabletimeseries'
        return super()._get_metadata_element_model_type(element_model_name)

    def get_html(self, **kwargs):
        """overrides the base class function"""

        series_id = kwargs.get('series_id', None)
        if series_id is None:
            series_id = list(self.series_ids_with_labels.keys())[0]
        elif series_id not in list(self.series_ids_with_labels.keys()):
            raise ValidationError("Series id:{} is not a valid series id".format(series_id))

        html_string = super(TimeSeriesFileMetaData, self).get_html()
        if self.abstract:
            abstract_div = html_tags.div(cls="content-block")
            with abstract_div:
                html_tags.legend("Abstract")
                html_tags.p(self.abstract)
            html_string += abstract_div.render()
        spatial_coverage = self.spatial_coverage
        if spatial_coverage:
            html_string += spatial_coverage.get_html()

        temporal_coverage = self.temporal_coverage
        if temporal_coverage:
            html_string += temporal_coverage.get_html()

        series_selection_div = self.get_series_selection_html(selected_series_id=series_id)
        html_tags.legend("Corresponding Metadata")
        with series_selection_div:
            div_meta_row = html_tags.div(cls='custom-well')
            with div_meta_row:
                # create 1st column of the row
                with html_tags.div(cls="content-block"):
                    # generate html for display of site element
                    site = self.get_element_by_series_id(series_id=series_id, elements=self.sites)
                    if site:
                        html_tags.legend("Site", cls='space-top')
                        site.get_html()

                    # generate html for variable element
                    variable = self.get_element_by_series_id(series_id=series_id,
                                                             elements=self.variables)
                    if variable:
                        html_tags.legend("Variable", cls='space-top')
                        variable.get_html()

                    # generate html for method element
                    method = self.get_element_by_series_id(series_id=series_id,
                                                           elements=self.methods)
                    if method:
                        html_tags.legend("Method", cls='space-top')
                        method.get_html()

                # create 2nd column of the row
                with html_tags.div(cls="content-block"):
                    # generate html for processing_level element
                    processing_levels = self.processing_levels
                    if processing_levels:
                        html_tags.legend("Processing Level")
                        pro_level = self.get_element_by_series_id(series_id=series_id,
                                                                  elements=processing_levels)
                        if pro_level:
                            pro_level.get_html()

                    # generate html for timeseries_result element
                    time_series_results = self.time_series_results
                    if time_series_results:
                        html_tags.legend("Time Series Result", cls='space-top')
                        ts_result = self.get_element_by_series_id(series_id=series_id,
                                                                  elements=time_series_results)
                        if ts_result:
                            ts_result.get_html()

        html_string += series_selection_div.render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """overrides the base class function"""

        series_id = kwargs.get('series_id', None)
        if series_id is None:
            series_id = list(self.series_ids_with_labels.keys())[0]
        elif series_id not in list(self.series_ids_with_labels.keys()):
            raise ValidationError("Series id:{} is not a valid series id".format(series_id))

        root_div = html_tags.div("{% load crispy_forms_tags %}")
        with root_div:
            self.get_update_sqlite_file_html_form()
            super(TimeSeriesFileMetaData, self).get_html_forms(temporal_coverage=False)
            self.get_abstract_form()
            spatial_coverage = self.spatial_coverage
            if spatial_coverage:
                spatial_coverage.get_html()

            temporal_coverage = self.temporal_coverage
            if temporal_coverage:
                temporal_coverage.get_html()

            series_selection_div = self.get_series_selection_html(selected_series_id=series_id)
            with series_selection_div:
                with html_tags.div(cls='custom-well'):
                    with html_tags.div(cls="content-block time-series-forms hs-coordinates-picker",
                                       id="site-filetype", data_coordinates_type="point"):
                        with html_tags.form(id="id-site-file-type", data_coordinates_type='point',
                                            action="{{ site_form.action }}",
                                            method="post", enctype="multipart/form-data"):
                            html_tags.div("{% crispy site_form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                       "col-md-2 col-xs-6"):
                                    html_tags.button("Save changes", type="button",
                                                     cls="btn btn-primary pull-right",
                                                     style="display: none;")

                    with html_tags.div(cls="content-block time-series-forms",
                                       id="processinglevel-filetype"):
                        with html_tags.form(id="id-processinglevel-file-type",
                                            action="{{ processinglevel_form.action }}",
                                            method="post", enctype="multipart/form-data"):
                            html_tags.div("{% crispy processinglevel_form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                       "col-md-2 col-xs-6"):
                                    html_tags.button("Save changes", type="button",
                                                     cls="btn btn-primary pull-right",
                                                     style="display: none;")

                    with html_tags.div(cls="content-block time-series-forms", id="variable-filetype"):
                        with html_tags.form(id="id-variable-file-type",
                                            action="{{ variable_form.action }}",
                                            method="post", enctype="multipart/form-data"):
                            html_tags.div("{% crispy variable_form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                       "col-md-2 col-xs-6"):
                                    html_tags.button("Save changes", type="button",
                                                     cls="btn btn-primary pull-right",
                                                     style="display: none;")

                    with html_tags.div(cls="content-block time-series-forms",
                                       id="timeseriesresult-filetype"):
                        with html_tags.form(id="id-timeseriesresult-file-type",
                                            action="{{ timeseriesresult_form.action }}",
                                            method="post", enctype="multipart/form-data"):
                            html_tags.div("{% crispy timeseriesresult_form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                       "col-md-2 col-xs-6"):
                                    html_tags.button("Save changes", type="button",
                                                     cls="btn btn-primary pull-right",
                                                     style="display: none;")

                    with html_tags.div(cls="content-block time-series-forms", id="method-filetype"):
                        with html_tags.form(id="id-method-file-type",
                                            action="{{ method_form.action }}",
                                            method="post", enctype="multipart/form-data"):
                            html_tags.div("{% crispy method_form %}")
                            with html_tags.div(cls="row", style="margin-top:10px;"):
                                with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                       "col-md-2 col-xs-6"):
                                    html_tags.button("Save changes", type="button",
                                                     cls="btn btn-primary pull-right",
                                                     style="display: none;")
                    if self.logical_file.has_csv_file:
                        with html_tags.div(cls="content-block time-series-forms",
                                           id="utcoffset-filetype"):
                            with html_tags.form(id="id-utcoffset-file-type",
                                                action="{{ utcoffset_form.action }}",
                                                method="post", enctype="multipart/form-data"):
                                html_tags.div("{% crispy utcoffset_form %}")
                                with html_tags.div(cls="row", style="margin-top:10px;"):
                                    with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 "
                                                           "col-md-2 col-xs-6"):
                                        html_tags.button("Save changes", type="button",
                                                         cls="btn btn-primary pull-right",
                                                         style="display: none;")

        template = Template(root_div.render(pretty=True))
        context_dict = dict()
        context_dict["site_form"] = create_site_form(self.logical_file, series_id)
        context_dict["variable_form"] = create_variable_form(self.logical_file, series_id)
        context_dict["method_form"] = create_method_form(self.logical_file, series_id)
        context_dict["processinglevel_form"] = create_processing_level_form(self.logical_file,
                                                                            series_id)
        context_dict["timeseriesresult_form"] = create_timeseries_result_form(self.logical_file,
                                                                              series_id)
        if self.logical_file.has_csv_file:
            context_dict['utcoffset_form'] = create_utcoffset_form(self.logical_file, series_id)
        context = Context(context_dict)
        return template.render(context)

    def get_series_selection_html(self, selected_series_id, pretty=True):
        """Generates html needed to display series selection dropdown box and the
        associated form"""

        root_div = html_tags.div(id="div-series-selection-file_type", cls="content-block")
        heading = "Select a timeseries to see corresponding metadata (Number of time series:{})"
        series_names = self.series_names
        if series_names:
            time_series_count = len(series_names)
        else:
            time_series_count = self.time_series_results.count()
        heading = heading.format(str(time_series_count))
        with root_div:
            html_tags.legend("Corresponding Metadata")
            html_tags.span(heading)
            action_url = "/hsapi/_internal/{logical_file_id}/series_id/resource_mode/"
            action_url += "get-timeseries-file-metadata/"
            action_url = action_url.format(logical_file_id=self.logical_file.id)
            with html_tags.form(id="series-selection-form-file_type", action=action_url, method="get",
                                enctype="multipart/form-data"):
                with html_tags.select(cls="form-control", id="series_id_file_type"):
                    for series_id, label in list(self.series_ids_with_labels.items()):
                        display_text = label[:120] + "..."
                        if series_id == selected_series_id:
                            html_tags.option(display_text, value=series_id, selected="selected", title=label)
                        else:
                            html_tags.option(display_text, value=series_id, title=label)
        return root_div

    def get_update_sqlite_file_html_form(self):
        form_action = "/hsapi/_internal/{}/update-sqlite-file/".format(self.logical_file.id)
        style = "display:none;"
        is_dirty = 'False'
        can_update_sqlite_file = 'False'
        if self.logical_file.can_update_sqlite_file:
            can_update_sqlite_file = 'True'
        if self.is_update_file:
            style = "margin-bottom:10px"
            is_dirty = 'True'
        root_div = html_tags.div(id="div-sqlite-file-update", cls="row", style=style)

        with root_div:
            with html_tags.div(cls="col-sm-12"):
                with html_tags.div(cls="alert alert-warning alert-dismissible", role="alert"):
                    html_tags.strong("SQLite file needs to be synced with metadata changes.")
                    if self.series_names:
                        # this is the case of CSV file based time series file type
                        with html_tags.div():
                            with html_tags.strong():
                                html_tags.span("NOTE:", style="color:red;")
                                html_tags.span("New resource specific metadata elements can't be created "
                                               "after you update the SQLite file.")
                    html_tags._input(id="metadata-dirty", type="hidden", value=is_dirty)
                    html_tags._input(id="can-update-sqlite-file", type="hidden",
                                     value=can_update_sqlite_file)
                    with html_tags.form(action=form_action, method="post", id="update-sqlite-file"):
                        html_tags.button("Update SQLite File", type="button", cls="btn btn-primary",
                                         id="id-update-sqlite-file")

        return root_div

    def get_abstract_form(self):
        form_action = "/hsapi/_internal/{}/update-timeseries-abstract/"
        form_action = form_action.format(self.logical_file.id)
        root_div = html_tags.div(cls="content-block")
        if self.abstract:
            abstract = self.abstract
        else:
            abstract = ''
        with root_div:
            with html_tags.form(action=form_action, id="filetype-abstract",
                                method="post", enctype="multipart/form-data"):
                html_tags.div("{% csrf_token %}")
                with html_tags.div(cls="form-group"):
                    with html_tags.div(cls="control-group"):
                        html_tags.legend('Abstract')
                        with html_tags.div(cls="controls"):
                            html_tags.textarea(abstract,
                                               cls="form-control input-sm textinput textInput",
                                               id="file_abstract", cols=40, rows=5,
                                               name="abstract")
                with html_tags.div(cls="row", style="margin-top:10px;"):
                    with html_tags.div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        html_tags.button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                                         style="display: none;", type="button")
        return root_div

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        from ..forms import SiteValidationForm, VariableTimeseriesValidationForm, MethodValidationForm, \
            ProcessingLevelValidationForm, TimeSeriesResultValidationForm, UTCOffSetValidationForm

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Time Series file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}

        validation_forms_mapping = {'site': SiteValidationForm,
                                    'variabletimeseries': VariableTimeseriesValidationForm,
                                    'method': MethodValidationForm,
                                    'processinglevel': ProcessingLevelValidationForm,
                                    'timeseriesresult': TimeSeriesResultValidationForm,
                                    'utcoffset': UTCOffSetValidationForm}
        element_name = element_name.lower()
        if element_name not in validation_forms_mapping:
            raise ValidationError("Invalid metadata element name:{}".format(element_name))

        element_validation_form = validation_forms_mapping[element_name](request.POST)

        if element_validation_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_validation_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None,
                    "errors": element_validation_form.errors}

    def ingest_metadata(self, graph):
        subject = self.rdf_subject_from_graph(graph)

        def copy_out_of_result(term):
            class HashableDict(dict):
                def __hash__(self):
                    s = sorted(self.items())
                    t = tuple(s)
                    h = hash(t)
                    return h
            # extract all term_entries
            terms_by_id = {}
            for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
                term_entry = HashableDict()
                term_node = graph.value(subject=result_node, predicate=term)
                result_uuid = graph.value(subject=result_node, predicate=HSTERMS.timeSeriesResultUUID)
                result_uuid = str(result_uuid)
                if term_node:
                    for _, terms_term, term_value in graph.triples((term_node, None, None)):
                        term_entry[terms_term] = term_value
                    terms_by_id[result_uuid] = term_entry

            # group common term_entries
            flipped = {}
            for key, value in terms_by_id.items():
                if value not in flipped:
                    flipped[value] = [key]
                else:
                    flipped[value].append(key)

            # update the graph
            for term_entry, result_uuids in flipped.items():
                term_node = BNode()
                graph.add((subject, term, term_node))
                graph.add((term_node, HSTERMS.timeSeriesResultUUID, Literal(result_uuids)))
                for key, value in term_entry.items():
                    graph.add((term_node, key, value))

            # remove nested entry of term
            for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
                for _, _, term_node in graph.triples((result_node, term, None)):
                    for _, pred, obj in graph.triples((term_node, None, None)):
                        graph.remove((term_node, pred, obj))
                    graph.remove((result_node, term, term_node))

        copy_out_of_result(HSTERMS.site)
        copy_out_of_result(HSTERMS.variable)
        copy_out_of_result(HSTERMS.method)
        copy_out_of_result(HSTERMS.processingLevel)
        copy_out_of_result(HSTERMS.UTCOffSet)

        # pull units from unit section
        for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
            unit = graph.value(subject=result_node, predicate=HSTERMS.unit)
            if unit:
                for _, unit_term, unit_value in graph.triples((unit, None, None)):
                    graph.add((result_node, unit_term, unit_value))
                    graph.remove((unit, unit_term, unit_value))
                graph.remove((result_node, HSTERMS.unit, unit))

        for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
            series_id = graph.value(subject=result_node, predicate=HSTERMS.timeSeriesResultUUID)
            graph.remove((result_node, HSTERMS.timeSeriesResultUUID, series_id))
            graph.add((result_node, HSTERMS.timeSeriesResultUUID, Literal([str(series_id)])))

        # abstract is all by itself on this model, won't get picked up by ingestion automatically
        description_node = graph.value(subject=subject, predicate=DC.description, default=None)
        if description_node:
            self.abstract = graph.value(subject=description_node, predicate=DCTERMS.abstract, default="").toPython()
            self.save()

        super(TimeSeriesFileMetaData, self).ingest_metadata(graph)

    def get_rdf_graph(self):
        graph = super(TimeSeriesFileMetaData, self).get_rdf_graph()

        subject = self.rdf_subject()

        def copy_into_result(term, result_id):
            for _, _, term_node in graph.triples((subject, term, None)):
                for _, _, term_series_ids in graph.triples((term_node, HSTERMS.timeSeriesResultUUID, None)):
                    if term_series_ids:
                        term_series_ids = term_series_ids.strip('][').split(', ')
                        if result_id in term_series_ids:
                            result_term_node = BNode()
                            graph.add((result_node, term, result_term_node))
                            for _, term_pred, term_obj in graph.triples((term_node, None, None)):
                                if term_pred != HSTERMS.timeSeriesResultUUID:
                                    graph.add((result_term_node, term_pred, term_obj))

        def remove_term(term):
            for _, _, term_node in graph.triples((subject, term, None)):
                for _, pred, obj in graph.triples((term_node, None, None)):
                    graph.remove((term_node, pred, obj))
                graph.remove((subject, term, term_node))

        for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
            result_series_id = graph.value(subject=result_node, predicate=HSTERMS.timeSeriesResultUUID)
            if result_series_id:
                result_series_id = result_series_id.strip('][').split(', ')[0]
                copy_into_result(HSTERMS.site, result_series_id)
                copy_into_result(HSTERMS.variable, result_series_id)
                copy_into_result(HSTERMS.method, result_series_id)
                copy_into_result(HSTERMS.processingLevel, result_series_id)
                copy_into_result(HSTERMS.UTCOffSet, result_series_id)
                graph.remove((result_node, HSTERMS.timeSeriesResultUUID, None))
                result_series_id = result_series_id.replace("'", "")
                graph.add((result_node, HSTERMS.timeSeriesResultUUID, Literal(result_series_id)))

        remove_term(HSTERMS.site)
        remove_term(HSTERMS.variable)
        remove_term(HSTERMS.method)
        remove_term(HSTERMS.processingLevel)
        remove_term(HSTERMS.UTCOffSet)

        # correct series_id entry from list cast to string
        for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
            series_id = graph.value(subject=result_node, predicate=HSTERMS.timeSeriesResultUUID)
            graph.remove((result_node, HSTERMS.timeSeriesResultUUID, series_id))
            series_id = series_id.replace("['", "").replace("']", "")
            graph.add((result_node, HSTERMS.timeSeriesResultUUID, Literal(series_id)))

        # push unit values into units section
        for _, _, result_node in graph.triples((subject, HSTERMS.timeSeriesResult, None)):
            units_type = graph.value(subject=result_node, predicate=HSTERMS.UnitsType)
            units_name = graph.value(subject=result_node, predicate=HSTERMS.UnitsName)
            units_abbreviation = graph.value(subject=result_node, predicate=HSTERMS.UnitsAbbreviation)
            if units_type or units_name or units_abbreviation:
                unit_node = BNode()
                graph.add((result_node, HSTERMS.unit, unit_node))
                if units_type:
                    graph.add((unit_node, HSTERMS.UnitsType, units_type))
                    graph.remove((result_node, HSTERMS.UnitsType, units_type))
                if units_name:
                    graph.add((unit_node, HSTERMS.UnitsName, units_name))
                    graph.remove((result_node, HSTERMS.UnitsName, units_name))
                if units_abbreviation:
                    graph.add((unit_node, HSTERMS.UnitsAbbreviation, units_abbreviation))
                    graph.remove((result_node, HSTERMS.UnitsAbbreviation, units_abbreviation))

        if self.abstract:
            # abstract is all by itself on this model, won't get picked up by rdf/xml creation automatically
            description_node = BNode()
            graph.add((subject, DC.description, description_node))
            graph.add((description_node, DCTERMS.abstract, Literal(self.abstract)))

        return graph


class TimeSeriesLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(TimeSeriesFileMetaData, on_delete=models.CASCADE, related_name="logical_file")
    data_type = "TimeSeries"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .csv and .sqlite file can be set to this logical file group"""
        return [".csv", ".sqlite"]

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".sqlite"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .csv and .sqlite"""
        return [".csv", ".sqlite"]

    @staticmethod
    def get_aggregation_display_name():
        return 'Time Series Content: One or more time series held in an ODM2 format SQLite ' \
               'file and optional source comma separated (.csv) files'

    @staticmethod
    def get_aggregation_term_label():
        return "Time Series Aggregation"

    @staticmethod
    def get_aggregation_type_name():
        return "TimeSeriesAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "Time Series"

    @classmethod
    def create(cls, resource):
        """this custom method MUST be used to create an instance of this class"""
        ts_metadata = TimeSeriesFileMetaData.objects.create(keywords=[], extra_metadata={})
        # Note we are not creating the logical file record in DB at this point
        # the caller must save this to DB
        return cls(metadata=ts_metadata, resource=resource)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_add(self):
        """doesn't allow a resource file to be added"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False

    @property
    def has_sqlite_file(self):
        for res_file in self.files.all():
            if res_file.extension.lower() == '.sqlite':
                return True
        return False

    @property
    def has_csv_file(self):
        for res_file in self.files.all():
            if res_file.extension.lower() == '.csv':
                return True
        return False

    @property
    def can_add_blank_sqlite_file(self):
        """use this property as a guard to decide when to add a blank SQLIte file
        to the resource
        """
        if self.has_sqlite_file:
            return False
        if not self.has_csv_file:
            return False

        return True

    @property
    def can_update_sqlite_file(self):
        """guard property to determine when the sqlite file can be updated as result of
        metadata changes
        """
        return self.has_sqlite_file and self.metadata.has_all_required_elements()

    def update_sqlite_file(self, user):
        # get sqlite resource file
        sqlite_file_to_update = None
        for res_file in self.files.all():
            if res_file.extension.lower() == '.sqlite':
                sqlite_file_to_update = res_file
                break
        if sqlite_file_to_update is None:
            raise Exception("Logical file has no SQLite file. Invalid operation.")
        sqlite_file_update(self, sqlite_file_to_update, user)

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) != 1:
            # no files or more than 1 file
            return ""

        if files[0].extension.lower() not in cls.get_allowed_uploaded_file_types():
            return ""

        return cls.__name__

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=''):
        """ Creates a TimeSeriesLogicalFile (aggregation) from a sqlite or a csv resource file, or
        a folder
        """

        log = logging.getLogger()
        with FileTypeContext(aggr_cls=cls, user=user, resource=resource, file_id=file_id,
                             folder_path=folder_path,
                             post_aggr_signal=post_add_timeseries_aggregation,
                             is_temp_file=True) as ft_ctx:

            res_file = ft_ctx.res_file
            temp_res_file = ft_ctx.temp_file

            if res_file.extension.lower() == '.sqlite':
                validate_err_message = validate_odm2_db_file(temp_res_file)
            else:
                # file must be a csv file
                validate_err_message = validate_csv_file(temp_res_file)

            if validate_err_message is not None:
                log.error(validate_err_message)
                raise ValidationError(validate_err_message)

            file_name = res_file.file_name
            # file name without the extension - used for new aggregation dataset_name attribute
            base_file_name = file_name[:-len(res_file.extension)]
            file_folder = res_file.file_folder
            upload_folder = file_folder
            res_files_for_aggr = [res_file]
            msg = "TimeSeries aggregation type. Error when creating. Error:{}"
            with transaction.atomic():
                try:
                    if res_file.extension.lower() == '.csv':
                        new_sqlite_file = add_blank_sqlite_file(resource, upload_folder)
                        res_files_for_aggr.append(new_sqlite_file)

                    # create a TimeSeriesLogicalFile object
                    logical_file = cls.create_aggregation(dataset_name=base_file_name,
                                                          resource=resource,
                                                          res_files=res_files_for_aggr,
                                                          new_files_to_upload=[],
                                                          folder_path=upload_folder)

                    info_msg = "TimeSeries aggregation type - {} file was added to the aggregation."
                    info_msg = info_msg.format(res_file.extension[1:])
                    log.info(info_msg)
                    # extract metadata if we are creating aggregation form a sqlite file
                    if res_file.extension.lower() == ".sqlite":
                        extract_err_message = extract_metadata(resource, temp_res_file,
                                                               logical_file)
                        if extract_err_message:
                            raise ValidationError(extract_err_message)
                        log.info("Metadata was extracted from sqlite file.")
                    else:
                        # populate CV metadata django models from the blank sqlite file
                        extract_cv_metadata_from_blank_sqlite_file(logical_file)
                    ft_ctx.logical_file = logical_file
                except Exception as ex:
                    logical_file.remove_aggregation()
                    msg = msg.format(str(ex))
                    log.exception(msg)
                    raise ValidationError(msg)

            return logical_file

    def remove_aggregation(self):
        """Deletes the aggregation object (logical file) *self* and the associated metadata
        object. If the aggregation contains a system generated sqlite file that resource file also will be
        deleted."""

        # need to delete the system generated sqlite file
        sqlite_file = None
        if self.has_csv_file:
            # the sqlite file is a system generated file
            for res_file in self.files.all():
                if res_file.file_name.lower().endswith(".sqlite"):
                    sqlite_file = res_file
                    break

        super(TimeSeriesLogicalFile, self).remove_aggregation()

        if sqlite_file is not None:
            sqlite_file.delete()

    def get_copy(self, copied_resource):
        """Overrides the base class method"""

        copy_of_logical_file = super(TimeSeriesLogicalFile, self).get_copy(copied_resource)
        copy_of_logical_file.metadata.abstract = self.metadata.abstract
        copy_of_logical_file.metadata.value_counts = self.metadata.value_counts
        copy_of_logical_file.metadata.is_dirty = self.metadata.is_dirty
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.save()

        copy_cv_terms(src_metadata=self.metadata, tgt_metadata=copy_of_logical_file.metadata)
        return copy_of_logical_file

    @classmethod
    def get_primary_resource_file(cls, resource_files):
        """Gets a resource file that has extension .sqlite or .csv from the list of files
        *resource_files*
        """

        res_files = [f for f in resource_files if f.extension.lower() == '.sqlite'
                     or f.extension.lower() == '.csv']
        return res_files[0] if res_files else None

    @classmethod
    def _validate_set_file_type_inputs(cls, resource, file_id=None, folder_path=''):
        res_file, folder_path = super(TimeSeriesLogicalFile, cls)._validate_set_file_type_inputs(
            resource, file_id, folder_path)
        if not folder_path and res_file.extension.lower() not in ('.sqlite', '.csv'):
            # when a file is specified by the user for creating this file type it must be a
            # sqlite or csv file
            raise ValidationError("Not a valid timeseries file.")
        return res_file, folder_path


def copy_cv_terms(src_metadata, tgt_metadata):
    """copy CV related metadata items from the source metadata *src_metadata*
    to the target metadata *tgt_metadata*
    This is a helper function to support resource copy or version creation
    :param  src_metadata: an instance of TimeSeriesMetaData or TimeSeriesFileMetaData from which
    cv related metadata items to copy from
    :param  tgt_metadata: an instance of TimeSeriesFileMetaData to which
    cv related metadata items to copy to
    Note: src_metadata and tgt_metadata must be of the same type
    """

    # create CV terms
    def copy_cv_terms(cv_class, cv_terms_to_copy):
        for cv_term in cv_terms_to_copy:
            cv_class.objects.create(metadata=tgt_metadata, name=cv_term.name,
                                    term=cv_term.term,
                                    is_dirty=cv_term.is_dirty)

    if type(src_metadata) is not type(tgt_metadata):
        raise ValidationError("Source metadata and target metadata objects must be of the "
                              "same type")

    cv_variable_type = CVVariableType
    cv_variable_name = CVVariableName
    cv_speciation = CVSpeciation
    cv_elevation_datum = CVElevationDatum
    cv_site_type = CVSiteType
    cv_method_type = CVMethodType
    cv_units_type = CVUnitsType
    cv_status = CVStatus
    cv_medium = CVMedium
    cv_aggr_statistics = CVAggregationStatistic

    copy_cv_terms(cv_variable_type, src_metadata.cv_variable_types.all())
    copy_cv_terms(cv_variable_name, src_metadata.cv_variable_names.all())
    copy_cv_terms(cv_speciation, src_metadata.cv_speciations.all())
    copy_cv_terms(cv_elevation_datum, src_metadata.cv_elevation_datums.all())
    copy_cv_terms(cv_site_type, src_metadata.cv_site_types.all())
    copy_cv_terms(cv_method_type, src_metadata.cv_method_types.all())
    copy_cv_terms(cv_units_type, src_metadata.cv_units_types.all())
    copy_cv_terms(cv_status, src_metadata.cv_statuses.all())
    copy_cv_terms(cv_medium, src_metadata.cv_mediums.all())
    copy_cv_terms(cv_aggr_statistics, src_metadata.cv_aggregation_statistics.all())

    # set all cv terms is_dirty to false
    cv_terms = list(tgt_metadata.cv_variable_names.all()) + \
        list(tgt_metadata.cv_variable_types.all()) + \
        list(tgt_metadata.cv_speciations.all()) + \
        list(tgt_metadata.cv_site_types.all()) + \
        list(tgt_metadata.cv_elevation_datums.all()) + \
        list(tgt_metadata.cv_method_types.all()) + \
        list(tgt_metadata.cv_units_types.all()) + \
        list(tgt_metadata.cv_statuses.all()) + \
        list(tgt_metadata.cv_mediums.all()) + \
        list(tgt_metadata.cv_aggregation_statistics.all())
    for cv_term in cv_terms:
        cv_term.is_dirty = False
        cv_term.save(update_fields=["is_dirty"])


def validate_odm2_db_file(sqlite_file_path):
    """
    Validates if the sqlite file *sqlite_file_path* is a valid ODM2 sqlite file
    :param sqlite_file_path: path of the sqlite file to be validated
    :return: If validation fails then an error message string is returned otherwise None is
    returned
    """
    err_message = "Uploaded file is not a valid ODM2 SQLite file."
    log = logging.getLogger()
    try:
        con = sqlite3.connect(sqlite_file_path)
        with con:

            # TODO: check that each of the core tables has the necessary columns

            # check that the uploaded file has all the tables from ODM2Core and the CV tables
            cur = con.cursor()
            odm2_core_table_names = ['People', 'Affiliations', 'SamplingFeatures', 'ActionBy',
                                     'Organizations', 'Methods', 'FeatureActions', 'Actions',
                                     'RelatedActions', 'Results', 'Variables', 'Units', 'Datasets',
                                     'DatasetsResults', 'ProcessingLevels', 'TaxonomicClassifiers',
                                     'CV_VariableType', 'CV_VariableName', 'CV_Speciation',
                                     'CV_SiteType', 'CV_ElevationDatum', 'CV_MethodType',
                                     'CV_UnitsType', 'CV_Status', 'CV_Medium',
                                     'CV_AggregationStatistic']
            # check the tables exist
            for table_name in odm2_core_table_names:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                            ("table", table_name))
                result = cur.fetchone()
                if result[0] <= 0:
                    err_message += " Table '{}' is missing.".format(table_name)
                    log.info(err_message)
                    return err_message

            # check that the tables have at least one record
            for table_name in odm2_core_table_names:
                if table_name == 'RelatedActions' or table_name == 'TaxonomicClassifiers':
                    continue
                cur.execute("SELECT COUNT(*) FROM " + table_name)
                result = cur.fetchone()
                if result[0] <= 0:
                    err_message += " Table '{}' has no records.".format(table_name)
                    log.info(err_message)
                    return err_message
        return None
    except sqlite3.Error as e:
        sqlite_err_msg = str(e.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception as e:
        log.error(str(e))
        return str(e)


def validate_csv_file(csv_file_path):
    err_message = "Uploaded file is not a valid timeseries csv file."
    log = logging.getLogger()
    with open(csv_file_path, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row
        header = next(csv_reader)
        header = [el.strip() for el in header]
        if any(len(h) == 0 for h in header):
            err_message += " Column heading is missing."
            log.error(err_message)
            return err_message

        # check that there are at least 2 headings
        if len(header) < 2:
            err_message += " There needs to be at least 2 columns of data."
            log.error(err_message)
            return err_message

        # check the header has only string values
        for hdr in header:
            try:
                float(hdr)
                err_message += " Column heading must be a string."
                log.error(err_message)
                return err_message
            except ValueError:
                pass

        # check that there are no duplicate column headings
        if len(header) != len(set(header)):
            err_message += " There are duplicate column headings."
            log.error(err_message)
            return err_message

        # process data rows
        date_data_error = False
        data_row_count = 0
        for row in csv_reader:
            # check that data row has the same number of columns as the header
            if len(row) != len(header):
                err_message += " Number of columns in the header is not same as the data columns."
                log.error(err_message)
                return err_message
            # check that the first column data is of type datetime
            try:
                # some numeric values (e.g., 20080101, 1.602652223413681) are recognized by the
                # the parser as valid date value - we don't allow any such value as valid date
                float(row[0])
                date_data_error = True
            except ValueError:
                try:
                    parser.parse(row[0])
                except ValueError:
                    date_data_error = True

            if date_data_error:
                err_message += " Data for the first column must be a date value."
                log.error(err_message)
                return err_message

            # check that the data values (2nd column onwards) are of numeric
            for data_value in row[1:]:
                try:
                    float(data_value)
                except ValueError:
                    err_message += " Data values must be numeric."
                    log.error(err_message)
                    return err_message
            data_row_count += 1

        if data_row_count < 2:
            err_message += " There needs to be at least two rows of data."
            log.error(err_message)
            return err_message

    return None


def add_blank_sqlite_file(resource, upload_folder):
    """Adds the blank SQLite file to the resource to the specified folder **upload_folder**
    :param  upload_folder: folder to which the blank sqlite file needs to be uploaded
    :return the uploaded resource file object - an instance of ResourceFile
    """

    log = logging.getLogger()

    # add the sqlite file to the resource
    odm2_sqlite_file_name = _get_timestamped_file_name(_SQLITE_FILE_NAME)

    try:
        uploaded_file = UploadedFile(file=open(_ODM2_SQLITE_FILE_PATH, 'rb'), name=odm2_sqlite_file_name)
        new_res_file = utils.add_file_to_resource(
            resource, uploaded_file, folder=upload_folder, save_file_system_metadata=True
        )

        log.info("Blank SQLite file was added.")
        return new_res_file
    except Exception as ex:
        log.exception("Error when adding the blank SQLite file. Error:{}".format(str(ex)))
        raise ex


def extract_metadata(resource, sqlite_file_name, logical_file=None):
    """
    Extracts metadata from the sqlite file *sqlite_file_name" and adds metadata at the resource
    and/or file level
    :param resource: an instance of BaseResource
    :param sqlite_file_name: path of the sqlite file
    :param logical_file: an instance of TimeSeriesLogicalFile if metadata needs to be part of the
    logical file
    :return:
    """
    err_message = "Not a valid ODM2 SQLite file"
    log = logging.getLogger()
    target_obj = logical_file if logical_file is not None else resource
    try:
        con = sqlite3.connect(sqlite_file_name)
        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            # populate the lookup CV tables that are needed later for metadata editing
            target_obj.metadata.create_cv_lookup_models(cur)

            # read data from necessary tables and create metadata elements
            # extract core metadata

            # extract abstract and title
            cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
            dataset = cur.fetchone()
            # update title element
            if dataset["DataSetTitle"]:
                if logical_file is None \
                        or resource.metadata.title.value.lower() == 'untitled resource':
                    resource.metadata.update_element('title', element_id=resource.metadata.title.id,
                                                     value=dataset["DataSetTitle"])
                if logical_file is not None:
                    logical_file.dataset_name = dataset["DataSetTitle"].strip()
                    logical_file.save()

            # create abstract/description element
            if dataset["DataSetAbstract"]:
                if logical_file is None or resource.metadata.description is None:
                    resource.metadata.create_element('description',
                                                     abstract=dataset["DataSetAbstract"])
                if logical_file is not None:
                    logical_file.metadata.abstract = dataset["DataSetAbstract"].strip()
                    logical_file.metadata.save()

            # extract keywords/subjects
            # these are the comma separated values in the VariableNameCV column of the Variables
            # table
            cur.execute("SELECT VariableID, VariableNameCV FROM Variables")
            variables = cur.fetchall()
            keyword_list = []
            for variable in variables:
                keywords = variable["VariableNameCV"].split(",")
                keyword_list = keyword_list + keywords

            if logical_file is None:
                # use set() to remove any duplicate keywords
                for kw in set(keyword_list):
                    resource.metadata.create_element("subject", value=kw)
            else:
                # file type
                logical_file.metadata.keywords = list(set(keyword_list))
                logical_file.metadata.save()
                # update resource level keywords
                resource_keywords = [subject.value.lower() for subject in
                                     resource.metadata.subjects.all()]
                for kw in logical_file.metadata.keywords:
                    if kw.lower() not in resource_keywords:
                        resource.metadata.create_element('subject', value=kw)

            # find the contributors for metadata
            _extract_creators_contributors(resource, cur)

            # extract coverage data
            _extract_coverage_metadata(resource, cur, logical_file)

            # extract additional metadata
            cur.execute("SELECT * FROM Sites")
            sites = cur.fetchall()
            is_create_multiple_site_elements = len(sites) > 1

            cur.execute("SELECT * FROM Variables")
            variables = cur.fetchall()
            is_create_multiple_variable_elements = len(variables) > 1

            cur.execute("SELECT * FROM Methods")
            methods = cur.fetchall()
            is_create_multiple_method_elements = len(methods) > 1

            cur.execute("SELECT * FROM ProcessingLevels")
            processing_levels = cur.fetchall()
            is_create_multiple_processinglevel_elements = len(processing_levels) > 1

            cur.execute("SELECT * FROM TimeSeriesResults")
            timeseries_results = cur.fetchall()
            is_create_multiple_timeseriesresult_elements = len(timeseries_results) > 1

            cur.execute("SELECT * FROM Results")
            results = cur.fetchall()
            for result in results:
                # extract site element data
                # Start with Results table to -> FeatureActions table -> SamplingFeatures table
                # check if we need to create multiple site elements
                cur.execute("SELECT * FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()
                if is_create_multiple_site_elements or len(target_obj.metadata.sites) == 0:
                    cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    sampling_feature = cur.fetchone()

                    cur.execute("SELECT * FROM Sites WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    site = cur.fetchone()
                    if not any(sampling_feature["SamplingFeatureCode"] == s.site_code for s
                               in target_obj.metadata.sites):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['site_code'] = sampling_feature["SamplingFeatureCode"]
                        data_dict['site_name'] = sampling_feature["SamplingFeatureName"]
                        if sampling_feature["Elevation_m"]:
                            data_dict["elevation_m"] = sampling_feature["Elevation_m"]

                        if sampling_feature["ElevationDatumCV"]:
                            data_dict["elevation_datum"] = sampling_feature["ElevationDatumCV"]

                        if site["SiteTypeCV"]:
                            data_dict["site_type"] = site["SiteTypeCV"]

                        data_dict["latitude"] = site["Latitude"]
                        data_dict["longitude"] = site["Longitude"]

                        # create site element
                        target_obj.metadata.create_element('site', **data_dict)
                    else:
                        matching_site = [s for s in target_obj.metadata.sites if
                                         s.site_code == sampling_feature["SamplingFeatureCode"]][0]
                        _update_element_series_ids(matching_site, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.sites[0], result["ResultUUID"])

                # extract variable element data
                # Start with Results table to -> Variables table
                if is_create_multiple_variable_elements or len(target_obj.metadata.variables) == 0:
                    cur.execute("SELECT * FROM Variables WHERE VariableID=?",
                                (result["VariableID"],))
                    variable = cur.fetchone()
                    if not any(variable["VariableCode"] == v.variable_code for v
                               in target_obj.metadata.variables):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['variable_code'] = variable["VariableCode"]
                        data_dict["variable_name"] = variable["VariableNameCV"]
                        data_dict['variable_type'] = variable["VariableTypeCV"]
                        data_dict["no_data_value"] = variable["NoDataValue"]
                        if variable["VariableDefinition"]:
                            data_dict["variable_definition"] = variable["VariableDefinition"]

                        if variable["SpeciationCV"]:
                            data_dict["speciation"] = variable["SpeciationCV"]

                        # create variable element
                        target_obj.metadata.create_element('variabletimeseries', **data_dict)
                    else:
                        matching_variable = [v for v in target_obj.metadata.variables if
                                             v.variable_code == variable["VariableCode"]][0]
                        _update_element_series_ids(matching_variable, result["ResultUUID"])

                else:
                    _update_element_series_ids(target_obj.metadata.variables[0],
                                               result["ResultUUID"])

                # extract method element data
                # Start with Results table -> FeatureActions table to -> Actions table to ->
                # Method table
                if is_create_multiple_method_elements or len(target_obj.metadata.methods) == 0:
                    cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                                (feature_action["ActionID"],))
                    action = cur.fetchone()
                    cur.execute("SELECT * FROM Methods WHERE MethodID=?", (action["MethodID"],))
                    method = cur.fetchone()
                    if not any(method["MethodCode"] == m.method_code for m
                               in target_obj.metadata.methods):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['method_code'] = method["MethodCode"]
                        data_dict["method_name"] = method["MethodName"]
                        data_dict['method_type'] = method["MethodTypeCV"]

                        if method["MethodDescription"]:
                            data_dict["method_description"] = method["MethodDescription"]

                        if method["MethodLink"]:
                            data_dict["method_link"] = method["MethodLink"]

                        # create method element
                        target_obj.metadata.create_element('method', **data_dict)
                    else:
                        matching_method = [m for m in target_obj.metadata.methods if
                                           m.method_code == method["MethodCode"]][0]
                        _update_element_series_ids(matching_method, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.methods[0], result["ResultUUID"])

                # extract processinglevel element data
                # Start with Results table to -> ProcessingLevels table
                if is_create_multiple_processinglevel_elements \
                        or len(target_obj.metadata.processing_levels) == 0:
                    cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?",
                                (result["ProcessingLevelID"],))
                    pro_level = cur.fetchone()
                    if not any(pro_level["ProcessingLevelCode"] == p.processing_level_code for p
                               in target_obj.metadata.processing_levels):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
                        if pro_level["Definition"]:
                            data_dict["definition"] = pro_level["Definition"]

                        if pro_level["Explanation"]:
                            data_dict["explanation"] = pro_level["Explanation"]

                        # create processinglevel element
                        target_obj.metadata.create_element('processinglevel', **data_dict)
                    else:
                        matching_pro_level = [p for p in target_obj.metadata.processing_levels if
                                              p.processing_level_code == pro_level[
                                                  "ProcessingLevelCode"]][0]
                        _update_element_series_ids(matching_pro_level, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.processing_levels[0],
                                               result["ResultUUID"])

                # extract data for TimeSeriesResult element
                # Start with Results table
                if is_create_multiple_timeseriesresult_elements \
                        or len(target_obj.metadata.time_series_results) == 0:
                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    if result["StatusCV"] is not None:
                        data_dict["status"] = result["StatusCV"]
                    else:
                        data_dict["status"] = ""
                    data_dict["sample_medium"] = result["SampledMediumCV"]
                    data_dict["value_count"] = result["ValueCount"]

                    cur.execute("SELECT * FROM Units WHERE UnitsID=?", (result["UnitsID"],))
                    unit = cur.fetchone()
                    data_dict['units_type'] = unit["UnitsTypeCV"]
                    data_dict['units_name'] = unit["UnitsName"]
                    data_dict['units_abbreviation'] = unit["UnitsAbbreviation"]

                    cur.execute("SELECT AggregationStatisticCV FROM TimeSeriesResults WHERE "
                                "ResultID=?", (result["ResultID"],))
                    ts_result = cur.fetchone()
                    data_dict["aggregation_statistics"] = ts_result["AggregationStatisticCV"]

                    # create the TimeSeriesResult element
                    target_obj.metadata.create_element('timeseriesresult', **data_dict)
                else:
                    _update_element_series_ids(target_obj.metadata.time_series_results[0],
                                               result["ResultUUID"])

            return None

    except sqlite3.Error as ex:
        sqlite_err_msg = str(ex.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception as ex:
        log.error(str(ex))
        return err_message


def extract_cv_metadata_from_blank_sqlite_file(target):
    """Extracts CV metadata from the blank sqlite file and populates the django metadata
    models - this function is applicable only in the case of a CSV file being used as the
    source of time series data
    :param  target: an instance of TimeSeriesLogicalFile
    """

    # find the csv file
    csv_res_file = None
    for f in target.files.all():
        if f.extension.lower() == ".csv":
            csv_res_file = f
            break
    if csv_res_file is None:
        raise Exception("No CSV file was found")

    # copy the blank sqlite file to a temp directory
    temp_dir = tempfile.mkdtemp()
    odm2_sqlite_file_name = _get_timestamped_file_name(_SQLITE_FILE_NAME)

    target_temp_sqlite_file = os.path.join(temp_dir, odm2_sqlite_file_name)
    shutil.copy(_ODM2_SQLITE_FILE_PATH, target_temp_sqlite_file)

    con = sqlite3.connect(target_temp_sqlite_file)
    with con:
        # get the records in python dictionary format
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # populate the lookup CV tables that are needed later for metadata editing
        target.metadata.create_cv_lookup_models(cur)

    # save some data from the csv file
    # get the csv file from iRODS to a temp directory
    resource = csv_res_file.resource
    temp_csv_file = utils.get_file_from_irods(resource=resource, file_path=csv_res_file.storage_path)
    with open(temp_csv_file, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row - header
        header = next(csv_reader)
        # read the 1st data row
        start_date_str = next(csv_reader)[0]
        last_row = None
        data_row_count = 1
        for row in csv_reader:
            last_row = row
            data_row_count += 1
        end_date_str = last_row[0]

        # save the series names along with number of data points for each series
        # columns starting with the 2nd column are data series names
        value_counts = {}
        for data_col_name in header[1:]:
            value_counts[data_col_name] = str(data_row_count)

        metadata_obj = target.metadata
        metadata_obj.value_counts = value_counts
        metadata_obj.save()

        # create the temporal coverage element
        target.metadata.create_element('coverage', type='period',
                                       value={'start': start_date_str, 'end': end_date_str})

    # cleanup the temp sqlite file directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # cleanup the temp csv file
    if os.path.exists(temp_csv_file):
        shutil.rmtree(os.path.dirname(temp_csv_file))


def _get_timestamped_file_name(file_name):
    name, ext = os.path.splitext(file_name)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    return "{}_{}{}".format(name, timestr, ext)


def _extract_creators_contributors(resource, cur):
    # check if the AuthorList table exists
    authorlists_table_exists = False
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                ("table", "AuthorLists"))
    qry_result = cur.fetchone()
    if qry_result[0] > 0:
        authorlists_table_exists = True

    # contributors are People associated with the Actions that created the Result
    cur.execute("SELECT * FROM People")
    people = cur.fetchall()
    is_create_multiple_author_elements = len(people) > 1

    cur.execute("SELECT FeatureActionID FROM Results")
    results = cur.fetchall()
    authors_data_dict = {}
    author_ids_already_used = []
    for result in results:
        if is_create_multiple_author_elements or (len(resource.metadata.creators.all()) == 1
                                                  and len(resource.metadata.contributors.all()) == 0):
            cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                        (result["FeatureActionID"],))
            feature_actions = cur.fetchall()
            for feature_action in feature_actions:
                cur.execute("SELECT ActionID FROM Actions WHERE ActionID=?",
                            (feature_action["ActionID"],))

                actions = cur.fetchall()
                for action in actions:
                    # get the AffiliationID from the ActionsBy table for the matching ActionID
                    cur.execute("SELECT AffiliationID FROM ActionBy WHERE ActionID=?",
                                (action["ActionID"],))
                    actionby_rows = cur.fetchall()

                    for actionby in actionby_rows:
                        # get the matching Affiliations records
                        cur.execute("SELECT * FROM Affiliations WHERE AffiliationID=?",
                                    (actionby["AffiliationID"],))
                        affiliation_rows = cur.fetchall()
                        for affiliation in affiliation_rows:
                            # get records from the People table
                            if affiliation['PersonID'] not in author_ids_already_used:
                                author_ids_already_used.append(affiliation['PersonID'])
                                cur.execute("SELECT * FROM People WHERE PersonID=?",
                                            (affiliation['PersonID'],))
                                person = cur.fetchone()

                                # get person organization name - get only one organization name
                                organization = None
                                if affiliation['OrganizationID']:
                                    cur.execute("SELECT OrganizationName FROM Organizations WHERE "
                                                "OrganizationID=?",
                                                (affiliation["OrganizationID"],))
                                    organization = cur.fetchone()

                                # create contributor metadata elements
                                person_name = person["PersonFirstName"]
                                if person['PersonMiddleName']:
                                    person_name = person_name + " " + person['PersonMiddleName']

                                person_name = person_name + " " + person['PersonLastName']
                                data_dict = {}
                                data_dict['name'] = person_name
                                if affiliation['PrimaryPhone']:
                                    data_dict["phone"] = affiliation["PrimaryPhone"]
                                if affiliation["PrimaryEmail"]:
                                    data_dict["email"] = affiliation["PrimaryEmail"]
                                if affiliation["PrimaryAddress"]:
                                    data_dict["address"] = affiliation["PrimaryAddress"]
                                if organization:
                                    data_dict["organization"] = organization[0]

                                # check if this person is an author (creator)
                                author = None
                                if authorlists_table_exists:
                                    cur.execute("SELECT * FROM AuthorLists WHERE PersonID=?",
                                                (person['PersonID'],))
                                    author = cur.fetchone()

                                if author:
                                    # save the extracted creator data in the dictionary
                                    # so that we can later sort it based on author order
                                    # and then create the creator metadata elements
                                    authors_data_dict[author["AuthorOrder"]] = data_dict
                                else:
                                    # create contributor metadata element
                                    if not resource.metadata.contributors.filter(
                                            name=data_dict['name']).exists():
                                        resource.metadata.create_element('contributor', **data_dict)

    # TODO: extraction of creator data has not been tested as the sample database does not have
    #  any records in the AuthorLists table
    authors_data_dict_sorted_list = sorted(authors_data_dict,
                                           key=lambda key: authors_data_dict[key])
    for data_dict in authors_data_dict_sorted_list:
        # create creator metadata element
        if not resource.metadata.creators.filter(name=data_dict['name']).exists():
            resource.metadata.create_element('creator', **data_dict)


def _extract_coverage_metadata(resource, cur, logical_file=None):
    # get point or box coverage
    target_obj = logical_file if logical_file is not None else resource
    cur.execute("SELECT * FROM Sites")
    sites = cur.fetchall()
    if len(sites) == 1:
        site = sites[0]
        if site["Latitude"] and site["Longitude"]:
            value_dict = {'east': site["Longitude"], 'north': site["Latitude"],
                          'units': "Decimal degrees"}
            # get spatial reference
            if site["SpatialReferenceID"]:
                cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                            (site["SpatialReferenceID"],))
                spatialref = cur.fetchone()
                if spatialref:
                    if spatialref["SRSName"]:
                        value_dict["projection"] = spatialref["SRSName"]

            target_obj.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        # in case of multiple sites we will create one coverage element of type 'box'
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for site in sites:
            if site["Latitude"]:
                if bbox['northlimit'] < site["Latitude"]:
                    bbox['northlimit'] = site["Latitude"]
                if bbox['southlimit'] > site["Latitude"]:
                    bbox['southlimit'] = site["Latitude"]

            if site["Longitude"]:
                if bbox['eastlimit'] < site['Longitude']:
                    bbox['eastlimit'] = site['Longitude']

                if bbox['westlimit'] > site['Longitude']:
                    bbox['westlimit'] = site['Longitude']

            if bbox['projection'] == 'Unknown':
                if site["SpatialReferenceID"]:
                    cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                                (site["SpatialReferenceID"],))
                    spatialref = cur.fetchone()
                    if spatialref:
                        if spatialref["SRSName"]:
                            bbox['projection'] = spatialref["SRSName"]

            if bbox['projection'] == 'Unknown':
                bbox['projection'] = 'WGS 84 EPSG:4326'

        target_obj.metadata.create_element('coverage', type='box', value=bbox)

    # extract temporal coverage
    cur.execute("SELECT MAX(ValueDateTime) AS 'EndDate', MIN(ValueDateTime) AS 'BeginDate' "
                "FROM TimeSeriesResultValues")

    dates = cur.fetchone()
    begin_date = dates['BeginDate']
    end_date = dates['EndDate']

    # create coverage element
    value_dict = {"start": begin_date, "end": end_date}
    target_obj.metadata.create_element('coverage', type='period', value=value_dict)


def _update_element_series_ids(element, series_id):
    element.series_ids = element.series_ids + [series_id]
    element.save()


def create_utcoffset_form(target, selected_series_id):
    """
    Creates an instance of UTCOffSetForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of UTCOffSetForm
    """
    from ..forms import UTCOffSetForm

    res_short_id = None
    file_type = True
    target_id = target.id

    utc_offset = target.metadata.utc_offset
    utcoffset_form = UTCOffSetForm(instance=utc_offset,
                                   res_short_id=res_short_id,
                                   element_id=utc_offset.id if utc_offset else None,
                                   selected_series_id=selected_series_id,
                                   file_type=file_type)
    if utc_offset is not None:
        utcoffset_form.action = _get_element_update_form_action('utcoffset', target_id, utc_offset.id)
    else:
        utcoffset_form.action = _get_element_create_form_action('utcoffset', target_id)
    return utcoffset_form


def create_site_form(target, selected_series_id):
    """
    Creates an instance of SiteForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of SiteForm
    """
    from ..forms import SiteForm

    res_short_id = None
    file_type = True
    target_id = target.id

    if target.metadata.sites:
        site = target.metadata.sites.filter(
            series_ids__contains=[selected_series_id]).first()
        site_form = SiteForm(instance=site, res_short_id=res_short_id,
                             element_id=site.id if site else None,
                             cv_site_types=target.metadata.cv_site_types.all(),
                             cv_elevation_datums=target.metadata.cv_elevation_datums.all(),
                             show_site_code_selection=len(target.metadata.series_names) > 0,
                             available_sites=target.metadata.sites,
                             selected_series_id=selected_series_id,
                             file_type=file_type)

        if site is not None:
            site_form.action = _get_element_update_form_action('site', target_id, site.id)
            site_form.number = site.id

            site_form.set_dropdown_widgets(site_form.initial['site_type'],
                                           site_form.initial['elevation_datum'])
        else:
            site_form.action = _get_element_create_form_action('site', target_id)
            site_form.set_dropdown_widgets()

    else:
        # this case can happen only in case of CSV upload
        site_form = SiteForm(instance=None, res_short_id=res_short_id,
                             element_id=None,
                             cv_site_types=target.metadata.cv_site_types.all(),
                             cv_elevation_datums=target.metadata.cv_elevation_datums.all(),
                             selected_series_id=selected_series_id,
                             file_type=file_type)

        site_form.action = _get_element_create_form_action('site', target_id)
        site_form.set_dropdown_widgets()
    return site_form


def create_variable_form(target, selected_series_id):
    """
    Creates an instance of VariableTimeseriesForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of VariableTimeseriesForm
    """
    from ..forms import VariableTimeseriesForm

    res_short_id = None
    file_type = True
    target_id = target.id

    if target.metadata.variables:
        variable = target.metadata.variables.filter(
            series_ids__contains=[selected_series_id]).first()
        variable_form = VariableTimeseriesForm(
            instance=variable, res_short_id=res_short_id,
            element_id=variable.id if variable else None,
            cv_variable_types=target.metadata.cv_variable_types.all(),
            cv_variable_names=target.metadata.cv_variable_names.all(),
            cv_speciations=target.metadata.cv_speciations.all(),
            show_variable_code_selection=len(target.metadata.series_names) > 0,
            available_variables=target.metadata.variables,
            selected_series_id=selected_series_id,
            file_type=file_type)

        if variable is not None:
            variable_form.action = _get_element_update_form_action('variabletimeseries', target_id, variable.id)
            variable_form.number = variable.id

            variable_form.set_dropdown_widgets(variable_form.initial['variable_type'],
                                               variable_form.initial['variable_name'],
                                               variable_form.initial['speciation'])
        else:
            # this case can only happen in case of csv upload
            variable_form.action = _get_element_create_form_action('variabletimeseries', target_id)
            variable_form.set_dropdown_widgets()
    else:
        # this case can happen only in case of CSV upload
        variable_form = VariableTimeseriesForm(instance=None, res_short_id=res_short_id,
                                               element_id=None,
                                               cv_variable_types=target.metadata.cv_variable_types.all(),
                                               cv_variable_names=target.metadata.cv_variable_names.all(),
                                               cv_speciations=target.metadata.cv_speciations.all(),
                                               available_variables=target.metadata.variables,
                                               selected_series_id=selected_series_id,
                                               file_type=file_type)

        variable_form.action = _get_element_create_form_action('variabletimeseries', target_id)
        variable_form.set_dropdown_widgets()

    return variable_form


def create_method_form(target, selected_series_id):
    """
    Creates an instance of MethodForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of MethodForm
    """

    from ..forms import MethodForm

    res_short_id = None
    file_type = True
    target_id = target.id

    if target.metadata.methods:
        method = target.metadata.methods.filter(
            series_ids__contains=[selected_series_id]).first()
        method_form = MethodForm(instance=method, res_short_id=res_short_id,
                                 element_id=method.id if method else None,
                                 cv_method_types=target.metadata.cv_method_types.all(),
                                 show_method_code_selection=len(target.metadata.series_names) > 0,
                                 available_methods=target.metadata.methods,
                                 selected_series_id=selected_series_id,
                                 file_type=file_type)

        if method is not None:
            method_form.action = _get_element_update_form_action('method', target_id, method.id)
            method_form.number = method.id
            method_form.set_dropdown_widgets(method_form.initial['method_type'])
        else:
            # this case can only happen in case of csv upload
            method_form.action = _get_element_create_form_action('method', target_id)
            method_form.set_dropdown_widgets()
    else:
        # this case can happen only in case of CSV upload
        method_form = MethodForm(instance=None, res_short_id=res_short_id,
                                 element_id=None,
                                 cv_method_types=target.metadata.cv_method_types.all(),
                                 selected_series_id=selected_series_id, file_type=file_type)

        method_form.action = _get_element_create_form_action('method', target_id)
        method_form.set_dropdown_widgets()
    return method_form


def create_processing_level_form(target, selected_series_id):
    """
    Creates an instance of ProcessingLevelForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of ProcessingLevelForm
    """
    from ..forms import ProcessingLevelForm

    res_short_id = None
    file_type = True
    target_id = target.id

    if target.metadata.processing_levels:
        pro_level = target.metadata.processing_levels.filter(
            series_ids__contains=[selected_series_id]).first()
        processing_level_form = ProcessingLevelForm(
            instance=pro_level,
            res_short_id=res_short_id,
            element_id=pro_level.id if pro_level else None,
            show_processing_level_code_selection=len(target.metadata.series_names) > 0,
            available_processinglevels=target.metadata.processing_levels,
            selected_series_id=selected_series_id,
            file_type=file_type)

        if pro_level is not None:
            processing_level_form.action = _get_element_update_form_action('processinglevel', target_id, pro_level.id)
            processing_level_form.number = pro_level.id
        else:
            processing_level_form.action = _get_element_create_form_action('processinglevel', target_id)
    else:
        # this case can happen only in case of CSV upload
        processing_level_form = ProcessingLevelForm(instance=None, res_short_id=res_short_id,
                                                    element_id=None,
                                                    selected_series_id=selected_series_id,
                                                    file_type=file_type)
        processing_level_form.action = _get_element_create_form_action('processinglevel', target_id)

    return processing_level_form


def create_timeseries_result_form(target, selected_series_id):
    """
    Creates an instance of ProcessingLevelForm
    :param target: an instance of TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of ProcessingLevelForm
    """
    from ..forms import TimeSeriesResultForm

    res_short_id = None
    file_type = True
    target_id = target.id

    time_series_result = target.metadata.time_series_results.filter(
        series_ids__contains=[selected_series_id]).first()
    timeseries_result_form = TimeSeriesResultForm(
        instance=time_series_result,
        res_short_id=res_short_id,
        element_id=time_series_result.id if time_series_result else None,
        cv_sample_mediums=target.metadata.cv_mediums.all(),
        cv_units_types=target.metadata.cv_units_types.all(),
        cv_aggregation_statistics=target.metadata.cv_aggregation_statistics.all(),
        cv_statuses=target.metadata.cv_statuses.all(),
        selected_series_id=selected_series_id,
        file_type=file_type)

    if time_series_result is not None:
        timeseries_result_form.action = _get_element_update_form_action('timeseriesresult', target_id,
                                                                        time_series_result.id)
        timeseries_result_form.number = time_series_result.id
        timeseries_result_form.set_dropdown_widgets(timeseries_result_form.initial['sample_medium'],
                                                    timeseries_result_form.initial['units_type'],
                                                    timeseries_result_form.initial[
                                                        'aggregation_statistics'],
                                                    timeseries_result_form.initial['status'])
    else:
        series_ids = target.metadata.series_ids_with_labels
        if series_ids and selected_series_id is not None:
            selected_series_label = series_ids[selected_series_id]
        else:
            selected_series_label = ''
        ts_result_value_count = None
        if target.metadata.series_names and selected_series_id is not None:
            sorted_series_names = sorted(target.metadata.series_names)
            selected_series_name = sorted_series_names[int(selected_series_id)]
            ts_result_value_count = int(target.metadata.value_counts[selected_series_name])
        timeseries_result_form.set_dropdown_widgets()
        timeseries_result_form.set_series_label(selected_series_label)
        timeseries_result_form.set_value_count(ts_result_value_count)
        timeseries_result_form.action = _get_element_create_form_action('timeseriesresult', target_id)
    return timeseries_result_form


def sqlite_file_update(instance, sqlite_res_file, user):
    """updates the sqlite file on metadata changes
    :param  instance: an instance of TimeSeriesLogicalFile
    :param  sqlite_res_file: SQLite file as a resource file
    :param  user: user requesting update of SQLite file
    """

    instance.metadata.refresh_from_db()
    if not instance.metadata.is_dirty or not instance.metadata.is_update_file:
        return

    log = logging.getLogger()

    sqlite_file_to_update = sqlite_res_file
    resource = sqlite_res_file.resource
    # retrieve the sqlite file from iRODS and save it to temp directory
    temp_sqlite_file = utils.get_file_from_irods(resource=resource, file_path=sqlite_file_to_update.storage_path)

    if instance.has_csv_file and instance.metadata.series_names:
        instance.metadata.populate_blank_sqlite_file(temp_sqlite_file, user)
    else:
        try:
            con = sqlite3.connect(temp_sqlite_file)
            with con:
                # get the records in python dictionary format
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                # update dataset table for changes in title and abstract
                instance.metadata.update_datasets_table(con, cur)

                # since we are allowing user to set the UTC offset in case of CSV file
                # upload we have to update the actions table
                if instance.metadata.utc_offset is not None:
                    instance.metadata.update_utcoffset_related_tables(con, cur)

                # update resource/file specific metadata
                instance.metadata.update_variables_table(con, cur)
                instance.metadata.update_methods_table(con, cur)
                instance.metadata.update_processinglevels_table(con, cur)
                instance.metadata.update_sites_related_tables(con, cur)
                instance.metadata.update_results_related_tables(con, cur)

                # update CV terms related tables
                instance.metadata.update_CV_tables(con, cur)

                # push the updated sqlite file to iRODS
                utils.replace_resource_file_on_irods(temp_sqlite_file, sqlite_file_to_update,
                                                     user)
                metadata = instance.metadata
                metadata.is_update_file = False
                metadata.save()
                log.info("SQLite file update was successful.")
        except sqlite3.Error as ex:
            sqlite_err_msg = str(ex.args[0])
            log.error("Failed to update SQLite file. Error:{}".format(sqlite_err_msg))
            raise Exception(sqlite_err_msg)
        except Exception as ex:
            log.exception("Failed to update SQLite file. Error:{}".format(str(ex)))
            raise ex
        finally:
            if os.path.exists(temp_sqlite_file):
                shutil.rmtree(os.path.dirname(temp_sqlite_file))


def _get_element_update_form_action(element_name, target_id, element_id):
    # target_id is logical file object id
    action = "/hsapi/_internal/TimeSeriesLogicalFile/{logical_file_id}/{element_name}/" \
             "{element_id}/update-file-metadata/"
    return action.format(logical_file_id=target_id, element_name=element_name,
                         element_id=element_id)


def _get_element_create_form_action(element_name, target_id):
    # target_id is logical file object id
    action = "/hsapi/_internal/TimeSeriesLogicalFile/{logical_file_id}/{element_name}/" \
             "add-file-metadata/"
    return action.format(logical_file_id=target_id, element_name=element_name)


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


def _create_cv_term(element, cv_term_class, cv_term_str, element_metadata_cv_terms, data_dict):
    """
    Helper function for creating a new CV term if needed
    :param element: the metadata element object being updated
    :param cv_term_class: CV term model class based on which an object to be created
    :param cv_term_str: cv term field name being updated
    :param element_metadata_cv_terms: list of all cv term objects
    (instances of cv_term_class) associated with the 'metadata' object
    :param data_dict: dict that has the data for updating the 'element'
    :return:
    """
    if cv_term_str in data_dict:
        # check if the user has entered a new name for the cv term
        if len(data_dict[cv_term_str]) > 0:
            if not any(data_dict[cv_term_str].lower() == item.name.lower()
                       for item in element_metadata_cv_terms):
                # generate term for the new name
                data_dict[cv_term_str] = data_dict[cv_term_str].strip()
                term = _generate_term_from_name(data_dict[cv_term_str])
                cv_term = cv_term_class.objects.create(
                    metadata=element.metadata, term=term, name=data_dict[cv_term_str])
                cv_term.is_dirty = True
                cv_term.save()


def _create_site_related_cv_terms(element, data_dict):
    # if the user has entered a new elevation datum, then create a corresponding new cv term

    cv_elevation_datum_class = CVElevationDatum
    cv_site_type_class = CVSiteType
    _create_cv_term(element=element, cv_term_class=cv_elevation_datum_class,
                    cv_term_str='elevation_datum',
                    element_metadata_cv_terms=element.metadata.cv_elevation_datums.all(),
                    data_dict=data_dict)

    # if the user has entered a new site type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=cv_site_type_class,
                    cv_term_str='site_type',
                    element_metadata_cv_terms=element.metadata.cv_site_types.all(),
                    data_dict=data_dict)


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


def _update_resource_coverage_element(site_element):
    """A helper to create/update the coverage element for TimeSeriesLogicalFile based on changes to the Site element"""

    point_value = {'east': site_element.longitude, 'north': site_element.latitude,
                   'units': "Decimal degrees"}

    def compute_bounding_box(site_elements):
        bbox_value = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                      'projection': 'Unknown', 'units': "Decimal degrees"}
        for site in site_elements:
            if site.latitude:
                if bbox_value['northlimit'] < site.latitude:
                    bbox_value['northlimit'] = site.latitude
                if bbox_value['southlimit'] > site.latitude:
                    bbox_value['southlimit'] = site.latitude

            if site.longitude:
                if bbox_value['eastlimit'] < site.longitude:
                    bbox_value['eastlimit'] = site.longitude

                if bbox_value['westlimit'] > site.longitude:
                    bbox_value['westlimit'] = site.longitude
        return bbox_value

    cov_type = "point"
    if len(site_element.metadata.sites) > 1:
        cov_type = 'box'
        bbox_value = compute_bounding_box(site_element.metadata.sites.all())

    # Need to do the coverage update for timeseries aggregation
    logical_metadata = site_element.metadata
    if logical_metadata.sites.count() > 1:
        cov_type = 'box'
        bbox_value = compute_bounding_box(logical_metadata.sites.all())

    spatial_cov = logical_metadata.coverages.all().exclude(type='period').first()
    if spatial_cov:
        # need to update aggregation level coverage
        spatial_cov.type = cov_type
        if cov_type == 'point':
            point_value['projection'] = spatial_cov.value['projection']
            spatial_cov._value = json.dumps(point_value)
        else:
            bbox_value['projection'] = spatial_cov.value['projection']
            spatial_cov._value = json.dumps(bbox_value)
        spatial_cov.save()
    else:
        # need to create aggregation level coverage
        if cov_type == 'point':
            value_dict = point_value
        else:
            value_dict = bbox_value
        logical_metadata.create_element("coverage", type=cov_type, value=value_dict)


def _create_variable_related_cv_terms(element, data_dict):
    """Creates a new CV term if the user has added a new variable name."""

    cv_variable_name_class = CVVariableName
    cv_variable_type_class = CVVariableType
    cv_speciation_class = CVSpeciation

    _create_cv_term(element=element, cv_term_class=cv_variable_name_class,
                    cv_term_str='variable_name',
                    element_metadata_cv_terms=element.metadata.cv_variable_names.all(),
                    data_dict=data_dict)

    # if the user has entered a new variable type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=cv_variable_type_class,
                    cv_term_str='variable_type',
                    element_metadata_cv_terms=element.metadata.cv_variable_types.all(),
                    data_dict=data_dict)

    # if the user has entered a new speciation, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=cv_speciation_class,
                    cv_term_str='speciation',
                    element_metadata_cv_terms=element.metadata.cv_speciations.all(),
                    data_dict=data_dict)


def _create_timeseriesresult_related_cv_terms(element, data_dict):
    """Creates a new CV term if the user has added a new sample medium."""

    cv_medium = CVMedium
    cv_units_type = CVUnitsType
    cv_status = CVStatus
    cv_agg_statistic = CVAggregationStatistic

    _create_cv_term(element=element, cv_term_class=cv_medium,
                    cv_term_str='sample_medium',
                    element_metadata_cv_terms=element.metadata.cv_mediums.all(),
                    data_dict=data_dict)

    # if the user has entered a new units type, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=cv_units_type,
                    cv_term_str='units_type',
                    element_metadata_cv_terms=element.metadata.cv_units_types.all(),
                    data_dict=data_dict)

    # if the user has entered a new status, then create a corresponding new cv term
    _create_cv_term(element=element, cv_term_class=cv_status,
                    cv_term_str='status',
                    element_metadata_cv_terms=element.metadata.cv_statuses.all(),
                    data_dict=data_dict)

    # if the user has entered a new aggregation statistics, then create a corresponding new
    # cv term
    _create_cv_term(element=element, cv_term_class=cv_agg_statistic,
                    cv_term_str='aggregation_statistics',
                    element_metadata_cv_terms=element.metadata.cv_aggregation_statistics.all(),
                    data_dict=data_dict)


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
