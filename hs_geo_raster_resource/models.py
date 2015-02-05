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
    variableName = models.TextField(null=True)
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
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            band_info = BandInformation.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id,
                                                       content_type=metadata_type).first()
            if band_info:
                raise ValidationError('BandInformation name:%s already exists' % kwargs['name'])
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
            if 'name' in kwargs:
                if band_info.name != kwargs['name']:
                    # check to make sure this new name not already exists
                    if BandInformation.objects.filter(name_iexact=kwargs['name'], object_id=band_info.object_id,
                                                      content_type__pk=band_info.content_type.id).count()> 0:
                        raise ValidationError('BandInformation name:%s already exists.' % kwargs['name'])

                band_info.name = kwargs['name']

            for key, value in kwargs.iteritems():
                if key in ('variableName', 'variableUnit', 'method', 'comment'):
                    setattr(band_info, key, value)

            band_info.save()
        else:
            raise ObjectDoesNotExist("No BandInformation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        band_info = BandInformation.objects.get(id=element_id)
        if band_info:
            # make sure we are not deleting all bandInformation of a resource
            if BandInformation.objects.filter(object_id=band_info.object_id, content_type__pk=band_info.content_type.id).count() == 1:
                raise ValidationError("The only BandInformation of the resource can't be deleted.")
            band_info.delete()
        else:
            raise ObjectDoesNotExist("No BandInformation element can be found for id:%d." % element_id)

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
    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new BandInformation meta instance
        if 'name' in kwargs:
            # check if the variable metadata already exists
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            cell_info = CellInformation.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id,
                                                       content_type=metadata_type).first()
            if cell_info:
                raise ValidationError('CellInformation name:%s already exists' % kwargs['name'])
        else:
            raise ValidationError("name of CellInformation is missing.")

        if not 'rows' in kwargs:
            raise ValidationError("CellInformation rows is missing.")

        if not 'columns' in kwargs:
            raise ValidationError("CellInformation columns is missing.")

        if not 'cellSizeXValue' in kwargs:
            raise ValidationError("CellInformation cellSizeXValue is missing.")

        if not 'cellSizeYValue' in kwargs:
            raise ValidationError("CellInformation cellSizeYValue is missing.")

        if not 'cellSizeUnit' in kwargs:
            raise ValidationError("CellInformation cellSizeUnit is missing.")

        if not 'cellDataType' in kwargs:
            raise ValidationError("CellInformation cellDataType is missing.")

        cell_info = CellInformation.objects.create(name=kwargs['name'], rows=kwargs['rows'], columns=kwargs['columns'],
                                                   cellSizeXValue=kwargs['cellSizeXValue'], cellSizeYValue=kwargs['cellSizeYValue'],
                                                   cellSizeUnit=kwargs['cellSizeUnit'], cellDataType=kwargs['cellDataType'],
                                                   content_object=metadata_obj)

        # check for the optional fields and save them to the BandInformation metadata
        for key, value in kwargs.iteritems():
            if key in ('noDataValue'):
                setattr(cell_info, key, value)

            cell_info.save()

        return cell_info

    @classmethod
    def update(cls, element_id, **kwargs):
        cell_info = CellInformation.objects.get(id=element_id)
        if cell_info:
            if 'name' in kwargs:
                if cell_info.name != kwargs['name']:
                    # check to make sure this new name not already exists
                    if CellInformation.objects.filter(name_iexact=kwargs['name'], object_id=cell_info.object_id,
                                                      content_type__pk=cell_info.content_type.id).count()> 0:
                        raise ValidationError('CellInformation name:%s already exists.' % kwargs['name'])

                cell_info.name = kwargs['name']

            for key, value in kwargs.iteritems():
                if key in ('rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellSizeUnit', 'cellDataType', 'noDataValue'):
                    setattr(cell_info, key, value)

            cell_info.save()
        else:
            raise ObjectDoesNotExist("No CellInformation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        cell_info = CellInformation.objects.get(id=element_id)
        if cell_info:
            # make sure we are not deleting all CellInformation of a resource
            if CellInformation.objects.filter(object_id=cell_info.object_id, content_type__pk=cell_info.content_type.id).count() == 1:
                raise ValidationError("The only CellInformation of the resource can't be deleted.")
            cell_info.delete()
        else:
            raise ObjectDoesNotExist("No CellInformation element can be found for id:%d." % element_id)

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

class RasterMetaData(CoreMetaData):
    # required non-repeatable cell information metadata elements
    cellInformation = generic.GenericRelation(CellInformation)
    bandInformation = generic.GenericRelation(BandInformation)
    raster_resource = generic.GenericRelation(RasterResource)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(RasterMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('CellInformation')
        elements.append('BandInformation')
        return elements

    @property
    def resource(self):
        return self.raster_resource.all().first()

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(RasterMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject raster resource specific metadata elements to container element
        for cell_info in self.cellInformation.all():
            hsterms_cellInfo = etree.SubElement(container, '{%s}rasterCellInformation' % self.NAMESPACES['hsterms'])
            hsterms_cellInfo_rdf_Description = etree.SubElement(hsterms_cellInfo, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = cell_info.name

            hsterms_rows = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}rows' % self.NAMESPACES['hsterms'])
            hsterms_rows.text = cell_info.raster_resource.rows

            hsterms_columns = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}columns' % self.NAMESPACES['hsterms'])
            hsterms_columns.text = cell_info.raster_resource.columns

            hsterms_cellSizeXValue = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeXValue' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeXValue.text = cell_info.raster_resource.cellSizeXValue

            hsterms_cellSizeYValue = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeYValue' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeYValue.text = cell_info.raster_resource.cellSizeYValue

            hsterms_cellSizeUnit = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeUnit' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeUnit.text = cell_info.raster_resource.cellSizeUnit

            hsterms_cellSizeType = etree.SubElement(hsterms_cellInfo_rdf_Description, '{%s}cellSizeType' % self.NAMESPACES['hsterms'])
            hsterms_cellSizeType.text = cell_info.raster_resource.cellSizeType

        if cell_info.noDataValue:
            hsterms_noDataValue = etree.SubElement(hsterms_cellInfo_rdf_Description,'{%s}noDataValue' % self.NAMESPACES['hsterms'])
            hsterms_noDataValue.text = cell_info.raster_resource.noDataValue

        for band_info in self.bandInformation.all():
            hsterms_bandInfo = etree.SubElement(container, '{%s}rasterBandInformation' % self.NAMESPACES['hsterms'])
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

processor_for(RasterResource)(resource_processor)
# page processor to populate raster resource specific metadata into my-resources template page
@processor_for(RasterResource)
def main_page(request, page):
    from dublincore import models as dc
    from django import forms
    from collections import OrderedDict
    class DCTerm(forms.ModelForm):
        class Meta:
            model=dc.QualifiedDublinCoreElement
            fields = ['term', 'content']

    content_model = page.get_content_model()

    # create Coverage metadata
    md_dict = OrderedDict()

    md_dict['rows'] = content_model.rows
    md_dict['columns'] = content_model.columns
    md_dict['cellSizeXValue'] = content_model.cellSizeXValue
    md_dict['cellSizeYValue'] = content_model.cellSizeYValue
    md_dict['cellSizeUnit'] = content_model.cellSizeUnit
    md_dict['cellDataType'] = content_model.cellDataType
    md_dict['noDataValue'] = content_model.noDataValue
    md_dict['bandCount'] = content_model.bandCount

    band_dict = OrderedDict()
    i = 1
    for band in content_model.metadata.bandInformation.all():
         band_dict['name (band '+str(i)+')'] = band.name
         band_dict['variable (band '+str(i)+')'] = band.variableName
         band_dict['units (band '+str(i)+')'] = band.variableUnit
         band_dict['method (band '+str(i)+')'] = band.method
         band_dict['comment (band '+str(i)+')'] = band.comment
         i = i+1

    cvg = content_model.metadata.coverages.all()
    core_md = {}
    if cvg:
        coverage = cvg[0]
        core_md = OrderedDict()
        core_md['place/area name'] = coverage.value['name']
        core_md['projection'] = coverage.value['projection']
        core_md['units'] = coverage.value['units']
        core_md['northLimit'] = coverage.value['northlimit']
        core_md['eastLimit'] = coverage.value['eastlimit']
        core_md['southLimit'] = coverage.value['southlimit']
        core_md['westLimit'] = coverage.value['westlimit']
        core_md_dict = {'Coverage': core_md}
        return  { 'res_add_metadata': md_dict,
                  'band_metadata': band_dict,
                  'resource_type' : content_model._meta.verbose_name,
                  'dublin_core' : [t for t in content_model.dublin_metadata.all().exclude(term='AB')],
                  'core_metadata' : core_md_dict,
                  'dcterm_frm' : DCTerm()
                }
    else:
        return  { 'res_add_metadata': md_dict,
                  'band_metadata': band_dict,
                  'resource_type' : content_model._meta.verbose_name,
                  'dublin_core' : [t for t in content_model.dublin_metadata.all().exclude(term='AB')],
                  'dcterm_frm' : DCTerm()
                }
import receivers
