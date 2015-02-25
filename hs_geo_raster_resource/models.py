from django.contrib.contenttypes import generic
from django.db import models
from mezzanine.pages.models import Page
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement
from mezzanine.pages.page_processors import processor_for
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError

class BandInformation(AbstractMetaDataElement):
    term = 'BandInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    name = models.CharField(max_length=50, null=True)
    variableName = models.TextField(max_length=100, null=True)
    variableUnit = models.CharField(max_length=50, null=True)
    # optional fields
    method = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    def __unicode__(self):
        self.name
    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new BandInformation meta instance
        if 'name' in kwargs:
            # check if the variable metadata already exists
            metadata_obj = kwargs['content_object']
            # metadata_type = ContentType.objects.get_for_model(metadata_obj)
            # band_info = BandInformation.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id,
            #                                            content_type=metadata_type).first()
            # if band_info:
            #     raise ValidationError('BandInformation name:%s already exists' % kwargs['name'])
        else:
            raise ValidationError("name of BandInformation is missing.")

        if not 'variableName' in kwargs:
            raise ValidationError("BandInformation variableName is missing.")

        if not 'variableUnit' in kwargs:
            raise ValidationError("BandInformation variableUnit is missing.")

        band_info = BandInformation.objects.create(name=kwargs['name'], variableName=kwargs['variableName'],
                                                   variableUnit=kwargs['variableUnit'], content_object=metadata_obj)

        # check for the optional fields and save them to the BandInformation metadata
        for key, value in kwargs.iteritems():
            if key in ('method', 'comment'):
                setattr(band_info, key, value)

        band_info.save()

        return band_info

    @classmethod
    def update(cls, element_id, **kwargs):
        band_info = BandInformation.objects.get(id=element_id)
        if band_info:
            # if 'name' in kwargs:
            #     if band_info.name != kwargs['name']:
            #         # check to make sure this new name not already exists
            #         if BandInformation.objects.filter(name_iexact=kwargs['name'], object_id=band_info.object_id,
            #                                           content_type__pk=band_info.content_type.id).count()> 0:
            #             raise ValidationError('BandInformation name:%s already exists.' % kwargs['name'])
            #
            #     band_info.name = kwargs['name']

            for key, value in kwargs.iteritems():
                if key in ('name', 'variableName', 'variableUnit', 'method', 'comment'):
                    setattr(band_info, key, value)

            band_info.save()
        else:
            raise ObjectDoesNotExist("No BandInformation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("BandInformation element of the raster resource cannot be deleted.")

class CellInformation(AbstractMetaDataElement):
    term = 'CellInformation'
    # required fields
    name = models.CharField(max_length=50, null=True)

    rows = models.IntegerField(null=True)
    columns = models.IntegerField(null=True)
    cellSizeXValue = models.FloatField(null=True)
    cellSizeYValue = models.FloatField(null=True)
    cellSizeUnit = models.CharField(max_length=50, null=True)
    cellDataType = models.CharField(max_length=50, null=True)

    # optional fields
    noDataValue = models.FloatField(null=True)

    def __unicode__(self):
        self.name

    class Meta:
        # CellInformation element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new CellInformation meta instance
        # if not 'name' in kwargs:
        #     raise ValidationError("name of CellInformation is missing.")
        #
        # if not 'rows' in kwargs:
        #     raise ValidationError("CellInformation rows is missing.")
        #
        # if not 'columns' in kwargs:
        #     raise ValidationError("CellInformation columns is missing.")
        #
        # if not 'cellSizeXValue' in kwargs:
        #     raise ValidationError("CellInformation cellSizeXValue is missing.")
        #
        # if not 'cellSizeYValue' in kwargs:
        #     raise ValidationError("CellInformation cellSizeYValue is missing.")
        #
        # if not 'cellSizeUnit' in kwargs:
        #     raise ValidationError("CellInformation cellSizeUnit is missing.")
        #
        # if not 'cellDataType' in kwargs:
        #     raise ValidationError("CellInformation cellDataType is missing.")

        cell_info = CellInformation.objects.create(name=kwargs['name'], rows=kwargs['rows'], columns=kwargs['columns'],
                                                   cellSizeXValue=kwargs['cellSizeXValue'], cellSizeYValue=kwargs['cellSizeYValue'],
                                                   cellSizeUnit=kwargs['cellSizeUnit'], cellDataType=kwargs['cellDataType'],
                                                   content_object=kwargs['content_object'])

        # check for the optional fields and save them to the CellInformation metadata
        if 'noDataValue' in kwargs:
            setattr(cell_info, 'noDataValue', kwargs['noDataValue'])

        cell_info.save()

        return cell_info

    @classmethod
    def update(cls, element_id, **kwargs):
        cell_info = CellInformation.objects.get(id=element_id)
        if cell_info:
            for key, value in kwargs.iteritems():
                #if key in ('rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellSizeUnit', 'cellDataType', 'noDataValue'):
                setattr(cell_info, key, value)

            cell_info.save()
        else:
            raise ObjectDoesNotExist("No CellInformation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("CellInformation element of a raster resource cannot be removed")

#
# To create a new resource, use these two super-classes.
#
class RasterResource(Page, AbstractResource):
    class Meta:
        verbose_name = 'Geographic Raster Resource'

    @property
    def metadata(self):
        md = RasterMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

# this would allow us to pick up additional form elements for the template before the template is displayed via Mezzanine page processor
processor_for(RasterResource)(resource_processor)

class RasterMetaData(CoreMetaData):
    # required non-repeatable cell information metadata elements
    _cell_information = generic.GenericRelation(CellInformation)
    _band_information = generic.GenericRelation(BandInformation)
    _raster_resource = generic.GenericRelation(RasterResource)

    @property
    def resource(self):
        return self._raster_resource.all().first()
    @property
    def cellInformation(self):
        return self._cell_information.all().first()

    @property
    def bandInformation(self):
        return self._band_information.all()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RasterMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        return elements

    def has_all_required_elements(self):
        if not super(RasterMetaData, self).has_all_required_elements():
            return False
        if not self.cellInformation:
            return False
        if not self.bandInformation:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(RasterMetaData, self).get_required_missing_elements()
        if not self.cellInformation:
            missing_required_elements.append('CellInformation')
        if not self.bandInformation:
            missing_required_elements.append('BandInformation')
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
            hsterms_cellInfo = etree.SubElement(container, '{%s}cellInformation' % self.NAMESPACES['hsterms'])
            hsterms_cellInfo_rdf_Description = etree.SubElement(hsterms_cellInfo, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = self.cellInformation.name

            hsterms_rows = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}rows' % self.NAMESPACES['hsterms'])
            hsterms_rows.text = str(self.cellInformation.rows)

            hsterms_columns = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}columns' % self.NAMESPACES['hsterms'])
            hsterms_columns.text = str(self.cellInformation.columns)

            hsterms_cellSizeXValue = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeXValue' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeXValue.text = str(self.cellInformation.cellSizeXValue)

            hsterms_cellSizeYValue = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeYValue' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeYValue.text = str(self.cellInformation.cellSizeYValue)

            hsterms_cellSizeUnit = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeUnit' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeUnit.text = self.cellInformation.cellSizeUnit

            hsterms_cellDataType = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellDataType' % self.NAMESPACES['hsterms'])
            hsterms_cellDataType.text = self.cellInformation.cellDataType

        if self.cellInformation.noDataValue:
            hsterms_noDataValue = etree.SubElement(hsterms_cellInfo_rdf_Description,'{%s}noDataValue' % self.NAMESPACES['hsterms'])
            hsterms_noDataValue.text = str(self.cellInformation.noDataValue)

        for band_info in self.bandInformation:
            hsterms_bandInfo = etree.SubElement(container, '{%s}BandInformation' % self.NAMESPACES['hsterms'])
            hsterms_bandInfo_rdf_Description = etree.SubElement(hsterms_bandInfo, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_bandInfo_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = band_info.name

            hsterms_variableName = etree.SubElement(hsterms_bandInfo_rdf_Description, '{%s}variableName' % self.NAMESPACES['hsterms'])
            hsterms_variableName.text = band_info.variableName

            hsterms_variableUnit = etree.SubElement(hsterms_bandInfo_rdf_Description, '{%s}variableUnit' % self.NAMESPACES['hsterms'])
            hsterms_variableUnit.text = band_info.variableUnit

            if band_info.method:
                hsterms_method = etree.SubElement(hsterms_bandInfo_rdf_Description,'{%s}method' % self.NAMESPACES['hsterms'])
                hsterms_method.text = band_info.method

            if band_info.comment:
                hsterms_comment = etree.SubElement(hsterms_bandInfo_rdf_Description, '{%s}comment' % self.NAMESPACES['hsterms'])
                hsterms_comment.text = band_info.comment

        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers
