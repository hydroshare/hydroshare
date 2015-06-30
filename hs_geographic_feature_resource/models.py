from django.db import models
from mezzanine.pages.page_processors import processor_for
from hs_core.models import AbstractResource
from hs_core.models import resource_processor, CoreMetaData, AbstractMetaDataElement
from mezzanine.pages.models import Page
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import json
from django.contrib.contenttypes import generic

# Create your models here.

#
# Define original spatial coverage metadata info
class OriginalCoverage(AbstractMetaDataElement):

    term = 'OriginalCoverage'
    """
    _value field stores a json string. The content of the json as box coverage info
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                   }"
    """
    _extent = models.CharField(max_length=1024)
    projection_string = models.TextField(max_length=1024, null=True, blank=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def extent(self):
        print self._extent
        return json.loads(self._extent)

    @classmethod
    def create(cls, **kwargs):
        if 'extent' in kwargs:
            if isinstance(kwargs['extent'], dict):
                # check that all the required sub-elements exist and create new original coverage meta
                for value_item in ['northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                    if not value_item in kwargs['extent']:
                        raise ValidationError("For original coverage meta, one or more bounding box limits or 'units' is missing.")

                extent_dict = {k: v for k, v in kwargs['extent'].iteritems()
                              if k in ('northlimit', 'eastlimit', 'southlimit', 'westlimit')}

                extent_json = json.dumps(extent_dict)
                metadata_obj = kwargs['content_object']
                ori_cov = OriginalCoverage.objects.create(_extent=extent_json, content_object=metadata_obj,)

                # # update projection string info
                for key, value in kwargs.iteritems():
                    if key in ('projection_string'):
                        setattr(ori_cov, key, value)
                        ori_cov.save()

                return ori_cov
            else:
                raise ValidationError('Invalid coverage value format.')
        else:
            raise ValidationError('Coverage value is missing.')

    @classmethod
    def update(cls, element_id, **kwargs):
        ori_cov = OriginalCoverage.objects.get(id=element_id)
        if ori_cov:
            # update bounding box info
            if 'extent' in kwargs:
                if not isinstance(kwargs['extent'], dict):
                    raise ValidationError('Invalid coverage value format.')

                extent_dict = ori_cov.extent

                for item_name in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
                    if item_name in kwargs['extent']:
                        extent_dict[item_name] = kwargs['extent'][item_name]

                extent_json = json.dumps(extent_dict)
                ori_cov._extent = extent_json
                ori_cov.save()

            # # update projection string info
            for key, value in kwargs.iteritems():
                if key in ('projection_string'):
                    setattr(ori_cov, key, value)
                    ori_cov.save()
        else:
            raise ObjectDoesNotExist("No coverage element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        ori_cov = OriginalCoverage.objects.get(id=element_id)
        if ori_cov:
            ori_cov.delete()
        else:
            raise ObjectDoesNotExist("No original coverage element exists for id:%d."%element_id)


class FieldInfomation(AbstractMetaDataElement):
    term = 'FieldInfomation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    fieldName = models.CharField(max_length=50)
    fieldTypeCode = models.CharField(max_length=50)
    fieldType = models.CharField(max_length=50)
    fieldWidth = models.IntegerField()
    fileldPrecision = models.IntegerField()

    def __unicode__(self):
        self.fieldName
    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new BandInformation meta instance
        if 'fieldName' in kwargs:
            # check if the variable metadata already exists
            metadata_obj = kwargs['content_object']
            # metadata_type = ContentType.objects.get_for_model(metadata_obj)
            # band_info = BandInformation.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id,
            #                                            content_type=metadata_type).first()
            # if band_info:
            #     raise ValidationError('BandInformation name:%s already exists' % kwargs['name'])
        else:
            raise ValidationError("fieldName of FieldInfomation is missing.")

        if not 'variableName' in kwargs:
            raise ValidationError("BandInformation variableName is missing.")

        if not 'variableUnit' in kwargs:
            raise ValidationError("BandInformation variableUnit is missing.")

        filed_info = FieldInfomation.objects.create(fieldName=kwargs['fieldName'], fieldTypeCode=kwargs['fieldTypeCode'],
                                                   fieldType=kwargs['fieldType'], fieldWidth=kwargs['fieldWidth'],
                                                   fileldPrecision=kwargs['fieldPrecision'],
                                                    content_object=metadata_obj)

        filed_info.save()
        return filed_info

    @classmethod
    def update(cls, element_id, **kwargs):
        field_info = FieldInfomation.objects.get(id=element_id)
        if field_info:
            # if 'name' in kwargs:
            #     if band_info.name != kwargs['name']:
            #         # check to make sure this new name not already exists
            #         if BandInformation.objects.filter(name_iexact=kwargs['name'], object_id=band_info.object_id,
            #                                           content_type__pk=band_info.content_type.id).count()> 0:
            #             raise ValidationError('BandInformation name:%s already exists.' % kwargs['name'])
            #
            #     band_info.name = kwargs['name']

            for key, value in kwargs.iteritems():
                if key in ('fieldName', 'fieldTypeCode', 'fieldType', 'fieldWidth', 'fieldPrecision'):
                    setattr(field_info, key, value)

            field_info.save()
        else:
            raise ObjectDoesNotExist("No FieldInfomation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("FieldInfomation element of the geographic feature resource cannot be deleted.")




# Define the netCDF resource
class GeographicFeatureResource(Page, AbstractResource):

    @property
    def metadata(self):
        md = GeographicFeatureMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # 3 file types are supported
        return (".shp", ".shx", ".dbf", ".prj")

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return True

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

    class Meta:
            verbose_name = 'Geographic Feature (Vector)'

processor_for(GeographicFeatureResource)(resource_processor)

# define the GeographicFeatureMetaData metadata
class GeographicFeatureMetaData(CoreMetaData):
    field_info = generic.GenericRelation(FieldInfomation)
    originalcoverage = generic.GenericRelation(OriginalCoverage)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeographicFeatureMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('FieldInfomation')
        elements.append('OriginalCoverage')
        return elements

    def has_all_required_elements(self):
        if not super(GeographicFeatureMetaData, self).has_all_required_elements():  # check required meta
            return False
        if not self.field_info.all():
            return False
        if not self.originalcoverage.all().first():
            return False
        if not (self.coverages.all().filter(type='box').first() or self.coverages.all().filter(type='point').first()):
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(GeographicFeatureMetaData, self).get_required_missing_elements()
        if not self.originalcoverage.all().first():
            missing_required_elements.append('Spatial Reference')

        # if not self.field_info.all().first():
        #     missing_required_elements.append('FieldInfomation')

        return missing_required_elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(GeographicFeatureMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # # inject netcdf resource specific metadata element 'variable' to container element
        # for variable in self.variables.all():
        #     md_fields = {
        #         "md_element": "netcdfVariable",
        #         "name": "name",
        #         "unit": "unit",
        #         "type": "type",
        #         "shape": "shape",
        #         "descriptive_name": "longName",
        #         "method": "comment"
        #     }  # element name : name in xml
        #     self.add_metadata_element_to_xml(container, variable, md_fields)

        if self.originalcoverage.all().first():
            hsterms_ori_cov = etree.SubElement(container, '{%s}spatialReference' % self.NAMESPACES['hsterms'])
            hsterms_ori_cov_rdf_Description = etree.SubElement(hsterms_ori_cov, '{%s}Description' % self.NAMESPACES['rdf'])
            ori_cov_obj = self.originalcoverage.all().first()

            # add extent info
            if ori_cov_obj.extent:
                cov_box = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s' \
                        %(ori_cov_obj.extent['northlimit'], ori_cov_obj.extent['eastlimit'],
                          ori_cov_obj.extent['southlimit'], ori_cov_obj.extent['westlimit'])

                hsterms_ori_cov_box = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}extent' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_box.text = cov_box


            if ori_cov_obj.projection_string:
                hsterms_ori_cov_projection = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}crsRepresentationText' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_projection.text = ori_cov_obj.projection_string


        return etree.tostring(RDF_ROOT, pretty_print=True)

    def add_metadata_element_to_xml(self, root, md_element, md_fields):
        from lxml import etree
        element_name = md_fields.get('md_element') if md_fields.get('md_element') else md_element.term

        hsterms_newElem = etree.SubElement(root,
                                           "{{{ns}}}{new_element}".format(ns=self.NAMESPACES['hsterms'],
                                                                          new_element=element_name))
        hsterms_newElem_rdf_Desc = etree.SubElement(hsterms_newElem,
                                                    "{{{ns}}}Description".format(ns=self.NAMESPACES['rdf']))
        for md_field in md_fields.keys():
            if hasattr(md_element, md_field):
                attr = getattr(md_element, md_field)
                if attr:
                    field = etree.SubElement(hsterms_newElem_rdf_Desc,
                                             "{{{ns}}}{field}".format(ns=self.NAMESPACES['hsterms'],
                                                                      field=md_fields[md_field]))
                    field.text = str(attr)

import receivers # never delete this otherwise non of the receiver function will work