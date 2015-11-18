import json

from django.contrib.contenttypes import generic
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from mezzanine.pages.models import Page
from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement



# extended metadata for raster resource type to store the original box type coverage since the core metadata coverage
# stores the converted WGS84 geographic coordinate system projection coverage, see issue #210 on github for details
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

        if 'value' in kwargs:
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if not value_item in kwargs['value']:
                    raise ValidationError("For coverage of type 'box' values for one or more bounding box limits or 'units' is missing.")

            value_dict = {k: v for k, v in kwargs['value'].iteritems()
                          if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'projection')}

            value_json = json.dumps(value_dict)
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


class BandInformation(AbstractMetaDataElement):
    term = 'BandInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    name = models.CharField(max_length=500, null=True)
    variableName = models.TextField(max_length=100, null=True)
    variableUnit = models.CharField(max_length=50, null=True)
    # optional fields
    method = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("BandInformation element of the raster resource cannot be deleted.")


class CellInformation(AbstractMetaDataElement):
    term = 'CellInformation'
    # required fields
    name = models.CharField(max_length=500, null=True)
    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellDataType = models.CharField(max_length=50, null=True)

    # optional fields
    noDataValue = models.FloatField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        # CellInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CellInformation element of a raster resource cannot be removed")


#
# To create a new resource, use these two super-classes.
#
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
        return (".tif",)

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False


# this would allow us to pick up additional form elements for the template before the template is displayed via Mezzanine page processor
processor_for(RasterResource)(resource_processor)


class RasterMetaData(CoreMetaData):
    # required non-repeatable cell information metadata elements
    _cell_information = generic.GenericRelation(CellInformation)
    _band_information = generic.GenericRelation(BandInformation)
    _ori_coverage = generic.GenericRelation(OriginalCoverage)

    @property
    def cellInformation(self):
        return self._cell_information.all().first()

    @property
    def bandInformation(self):
        return self._band_information.all()

    @property
    def originalCoverage(self):
        return self._ori_coverage.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RasterMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        elements.append('OriginalCoverage')
        return elements

    def has_all_required_elements(self):
        if not super(RasterMetaData, self).has_all_required_elements():
            return False
        if not self.cellInformation:
            return False
        if not self.bandInformation:
            return False
        if not self.coverages.all().filter(type='box').first():
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(RasterMetaData, self).get_required_missing_elements()
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
        xml_string = super(RasterMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject raster resource specific metadata elements to container element
        if self.cellInformation:
            cellinfo_fields = ['name', 'rows', 'columns', 'cellSizeXValue', 'cellSizeYValue',
                           'cellDataType', 'noDataValue']
            self.add_metadata_element_to_xml(container, self.cellInformation, cellinfo_fields)

        for band_info in self.bandInformation:
            bandinfo_fields = ['name', 'variableName', 'variableUnit', 'method', 'comment']
            self.add_metadata_element_to_xml(container, band_info, bandinfo_fields)

        if self.originalCoverage:
            ori_coverage = self.originalCoverage;
            cov = etree.SubElement(container, '{%s}spatialReference' % self.NAMESPACES['hsterms'])
            cov_term = '{%s}' + 'box'
            coverage_terms = etree.SubElement(cov, cov_term % self.NAMESPACES['hsterms'])
            rdf_coverage_value = etree.SubElement(coverage_terms, '{%s}value' % self.NAMESPACES['rdf'])
            #raster original coverage is of box type
            cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                        %(ori_coverage.value['northlimit'], ori_coverage.value['eastlimit'],
                          ori_coverage.value['southlimit'], ori_coverage.value['westlimit'], ori_coverage.value['units'])

            if 'projection' in ori_coverage.value:
                cov_value = cov_value + '; projection=%s' % ori_coverage.value['projection']

            rdf_coverage_value.text = cov_value

        return etree.tostring(RDF_ROOT, pretty_print=True)

    def delete_all_elements(self):
        super(RasterMetaData, self).delete_all_elements()
        if self.cellInformation:
            self.cellInformation.delete()
        if self.originalCoverage:
            self.originalCoverage.delete()
        self.bandInformation.delete()

import receivers
