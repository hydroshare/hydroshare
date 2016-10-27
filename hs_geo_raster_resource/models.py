import json

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from mezzanine.pages.models import Page
from mezzanine.pages.page_processors import processor_for

from dominate.tags import *

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, \
    AbstractMetaDataElement


# extended metadata for raster resource type to store the original box type coverage since
# the core metadata coverage
# stores the converted WGS84 geographic coordinate system projection coverage,
# see issue #210 on github for details

class OriginalCoverage(AbstractMetaDataElement):
    term = 'OriginalCoverage'

    """
    _value field stores a json string as shown below for box coverage type
     _value = "{'northlimit':northenmost coordinate value,
                'eastlimit':easternmost coordinate value,
                'southlimit':southernmost coordinate value,
                'westlimit':westernmost coordinate value,
                'units:units applying to 4 limits (north, east, south & east),
                'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024, null=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def value(self):
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        """
        The '_value' subelement needs special processing. (Check if the 'value' includes the required info and convert
        'value' dict as Json string to be the '_value' subelement value.) The base class create() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary

        """

        value_arg_dict = None
        if 'value' in kwargs:
            value_arg_dict = kwargs['value']
        elif '_value' in kwargs:
            value_arg_dict = json.loads(kwargs['_value'])

        if value_arg_dict:
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if not value_item in value_arg_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more bounding box limits or 'units' is missing.")

            value_dict = {k: v for k, v in value_arg_dict.iteritems()
                          if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'projection')}

            value_json = json.dumps(value_dict)
            if 'value' in kwargs:
                del kwargs['value']
            kwargs['_value'] = value_json
            return super(OriginalCoverage, cls).create(**kwargs)
        else:
            raise ValidationError('Coverage value is missing.')

    @classmethod
    def update(cls, element_id, **kwargs):
        """
        The '_value' subelement needs special processing. (Convert the 'value' dict as Json string to be the "_value"
        subelement value.) The base class update() can't do it.

        :param kwargs: the 'value' in kwargs should be a dictionary
        """

        cov = OriginalCoverage.objects.get(id=element_id)

        if 'value' in kwargs:
            value_dict = cov.value

            for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'projection'):
                if item_name in kwargs['value']:
                    value_dict[item_name] = kwargs['value'][item_name]

            value_json = json.dumps(value_dict)
            del kwargs['value']
            kwargs['_value'] = value_json
            super(OriginalCoverage, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Coverage element can't be deleted.")

    def get_html_form(self, resource):
        from .forms import OriginalCoverageSpatialForm

        ori_coverage_data_dict = dict()
        ori_coverage_data_dict['units'] = self.value['units']
        ori_coverage_data_dict['projection'] = self.value.get('projection', None)
        ori_coverage_data_dict['northlimit'] = self.value['northlimit']
        ori_coverage_data_dict['eastlimit'] = self.value['eastlimit']
        ori_coverage_data_dict['southlimit'] = self.value['southlimit']
        ori_coverage_data_dict['westlimit'] = self.value['westlimit']

        originalcov_form = OriginalCoverageSpatialForm(initial=ori_coverage_data_dict,
                                     res_short_id=resource.short_id if resource else None,
                                     element_id=self.id if self else None)
        
        return originalcov_form

    def get_html(self, pretty=True):
        # Using the dominate module to generate the
        # html to display data for this element (resource view mode)
        root_div = div(cls="col-xs-6 col-sm-6", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Spatial Reference')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('Coordinate Reference System')
                        td(self.value['projection'])
                    with tr():
                        get_th('Coordinate Reference System Unit')
                        td(self.value['units'])

            h4('Extent')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('North')
                        td(self.value['northlimit'])
                    with tr():
                        get_th('West')
                        td(self.value['westlimit'])
                    with tr():
                        get_th('South')
                        td(self.value['southlimit'])
                    with tr():
                        get_th('East')
                        td(self.value['eastlimit'])

        return root_div.render(pretty=pretty)


class BandInformation(AbstractMetaDataElement):
    term = 'BandInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by
    # the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    name = models.CharField(max_length=500, null=True)
    variableName = models.TextField(max_length=100, null=True)
    variableUnit = models.CharField(max_length=50, null=True)

    # optional fields
    method = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    noDataValue = models.TextField(null=True, blank=True)
    maximumValue = models.TextField(null=True, blank=True)
    minimumValue = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("BandInformation element of the raster resource cannot be deleted.")

    def get_html(self, pretty=True):
        # Using the dominate module to generate the
        # html to display data for this element (resource view mode)
        root_div = div(cls="col-xs-12 pull-left", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Variable Name')
                            td(self.variableName)
                        with tr():
                            get_th('Variable Unit')
                            td(self.variableUnit)
                        if self.noDataValue:
                            with tr():
                                get_th('No Data Value')
                                td(self.noDataValue)
                        if self.maximumValue:
                            with tr():
                                get_th('Maximum Value')
                                td(self.maximumValue)
                        if self.minimumValue:
                            with tr():
                                get_th('Minimum Value')
                                td(self.minimumValue)
                        if self.method:
                            with tr():
                                get_th('Method')
                                td(self.method)
                        if self.comment:
                            with tr():
                                get_th('Comment')
                                td(self.comment)

        return root_div.render(pretty=pretty)


class CellInformation(AbstractMetaDataElement):
    term = 'CellInformation'
    # required fields
    name = models.CharField(max_length=500, null=True)
    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellDataType = models.CharField(max_length=50, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        # CellInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CellInformation element of a raster resource cannot be removed")

    def add_to_xml(self, container):
        cellinfo_fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue',
                           'cellDataType']
        self.add_metadata_element_to_xml(container, self, cellinfo_fields)

    def get_html_form(self, resource):
        from .forms import CellInfoForm
        cellinfo_form = CellInfoForm(instance=self,
                                     res_short_id=resource.short_id if resource else None,
                                     element_id=self.id if self else None)
        return cellinfo_form

    def get_html(self, pretty=True):
        # Using the dominate module to generate the
        # html to display data for this element (resource view mode)
        root_div = div(cls="col-xs-6 col-sm-6", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            legend('Cell Information')
            with table(cls='custom-table'):
                with tbody():
                    with tr():
                        get_th('Rows')
                        td(self.rows)
                    with tr():
                        get_th('Columns')
                        td(self.columns)
                    with tr():
                        get_th('Cell Size X Value')
                        td(self.cellSizeXValue)
                    with tr():
                        get_th('Cell Size Y Value')
                        td(self.cellSizeYValue)
                    with tr():
                        get_th('Cell Data Type')
                        td(self.cellDataType)

        return root_div.render(pretty=pretty)

# To create a new resource, use these two super-classes.
class RasterResource(BaseResource):
    objects = ResourceManager("RasterResource")

    class Meta:
        verbose_name = 'Geographic Raster'
        proxy = True

    @property
    def metadata(self):
        md = RasterMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # only tif file type is supported
        return (".tif",".zip")

    @classmethod
    def allow_multiple_file_upload(cls):
        # can upload only 1 file
        return False

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False


# this would allow us to pick up additional form elements for the template before the template
# is displayed via Mezzanine page processor
processor_for(RasterResource)(resource_processor)


# This mixin should not generate any new migration for this resource type
class GeoRasterMetaDataMixin(models.Model):

    class Meta:
        abstract = True

    @property
    def cellInformation(self):
        return self._cell_information.all().first()

    @property
    def bandInformations(self):
        return self._band_information.all()

    @property
    def originalCoverage(self):
        return self._ori_coverage.all().first()

    def has_all_required_elements(self):
        # this works because the superclass we want is listed first
        if not super(type(self), self).has_all_required_elements():
            return False
        if not self.cellInformation:
            return False
        if not self.bandInformation:
            return False
        if not self.coverages.all().filter(type='box').first():
            return False
        return True

    def get_required_missing_elements(self):
        # this works because the superclass we want is listed first
        missing_required_elements = super(type(self), self).get_required_missing_elements()
        if not self.coverages.all().filter(type='box').first():
            missing_required_elements.append('Spatial Coverage: Box')
        if not self.cellInformation:
            missing_required_elements.append('Cell Information')
        if not self.bandInformation:
            missing_required_elements.append('Band Information')

        return missing_required_elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        # this works because the superclass we want is listed first
        xml_string = super(type(self), self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject raster resource specific metadata elements to container element
        if self.cellInformation:
            cellinfo_fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue',
                               'cellDataType']
            self.add_metadata_element_to_xml(container, self.cellInformation, cellinfo_fields)

        for band_info in self.bandInformation:
            bandinfo_fields = ['name', 'variableName', 'variableUnit', 'noDataValue',
                               'maximumValue', 'minimumValue',
                               'method', 'comment']
            self.add_metadata_element_to_xml(container, band_info, bandinfo_fields)

        if self.originalCoverage:
            ori_coverage = self.originalCoverage
            cov = etree.SubElement(container, '{%s}spatialReference' % self.NAMESPACES['hsterms'])
            cov_term = '{%s}' + 'box'
            coverage_terms = etree.SubElement(cov, cov_term % self.NAMESPACES['hsterms'])
            rdf_coverage_value = etree.SubElement(coverage_terms,
                                                  '{%s}value' % self.NAMESPACES['rdf'])
            # raster original coverage is of box type
            cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                        % (ori_coverage.value['northlimit'], ori_coverage.value['eastlimit'],
                           ori_coverage.value['southlimit'], ori_coverage.value['westlimit'],
                           ori_coverage.value['units'])

            if 'projection' in ori_coverage.value:
                cov_value = cov_value + '; projection=%s' % ori_coverage.value['projection']

            rdf_coverage_value.text = cov_value

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        # this works because the superclass we want is listed first
        super(type(self), self).delete_all_elements()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()
        self.bandInformation.delete()


# this additional inheritance from GeoRasterMetaDataMixin should not generate new migration
class RasterMetaData(CoreMetaData, GeoRasterMetaDataMixin):
    # required non-repeatable cell information metadata elements
    _cell_information = GenericRelation(CellInformation)
    _band_information = GenericRelation(BandInformation)
    _ori_coverage = GenericRelation(OriginalCoverage)

    @property
    def resource(self):
        return RasterResource.objects.filter(object_id=self.id).first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RasterMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        return elements


import receivers
