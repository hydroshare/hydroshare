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
    #original extent
    _extent = models.CharField(max_length=1024, null=False, blank=False)
    #eg., prj string
    projection_string = models.TextField(max_length=1024, null=True, blank=True)
    projection_name = models.TextField(max_length=256, null=True, blank=True)
    datum = models.TextField(max_length=256, null=True, blank=True)
    unit = models.TextField(max_length=256, null=True, blank=True)

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
                    if key in ('projection_string','projection_name','datum','unit'):
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
                if key in ('projection_string','projection_name','datum','unit'):
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
            raise ObjectDoesNotExist("No original coverage element exists for id: %d."%element_id)


class FieldInformation(AbstractMetaDataElement):
    term = 'FieldInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    fieldName = models.CharField(max_length=128, null=False, blank=False)
    fieldType = models.CharField(max_length=128, null=False, blank=False)
    fieldTypeCode = models.CharField(max_length=50, null=True, blank=True)
    fieldWidth = models.IntegerField(null=True, blank=True)
    fieldPrecision = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        self.fieldName
    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new BandInformation meta instance
        if 'fieldName' in kwargs:
            if not 'fieldType' in kwargs:
                raise ValidationError("fieldType of FieldInformation is missing.")
            
            # check if the variable metadalta already exists
            metadata_obj = kwargs['content_object']
            field_info = FieldInformation.objects.create(fieldName = kwargs['fieldName'], fieldType=kwargs['fieldType'],content_object=metadata_obj,)
            # # update projection string info
            for key, value in kwargs.iteritems():
                if key in ('fieldTypeCode', 'fieldWidth', 'fieldPrecision'):
                    setattr(field_info, key, value)
                    field_info.save()
            return field_info
        else:
            raise ValidationError("fieldName of FieldInformation is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        field_info = FieldInformation.objects.get(id=element_id)
        if field_info:
            for key, value in kwargs.iteritems():
                if key in ('fieldName', 'fieldTypeCode', 'fieldType', 'fieldWidth', 'fieldPrecision'):
                    setattr(field_info, key, value)
            field_info.save()
        else:
            raise ObjectDoesNotExist("No FieldInformation element can be found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("FieldInformation element of the geographic feature resource cannot be deleted.")


class GeometryInformation(AbstractMetaDataElement):
    term = 'GeometryInformation'
    # required fields
    # has to call the field name rather than bandName, which seems to be enforced by the AbstractMetaDataElement;
    # otherwise, got an error indicating required "name" field does not exist
    featureCount = models.IntegerField(null=False, blank=False, default=0)
    geometryType = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    def __unicode__(self):
        self.fieldName
    @classmethod
    def create(cls, **kwargs):
        # Check the required fields and create new BandInformation meta instance
        if 'geometryType' in kwargs:
            if not 'featureCount' in kwargs:
                raise ValidationError("featureCount of GeometryInformation is missing.")

            # check if the variable metadalta already exists
            metadata_obj = kwargs['content_object']
            geom_info = GeometryInformation.objects.create(geometryType = kwargs['geometryType'], featureCount=kwargs['featureCount'],content_object=metadata_obj,)

            # for key, value in kwargs.iteritems():
            #     if key in ('fieldTypeCode', 'fieldWidth', 'fieldPrecision'):
            #         setattr(field_info, key, value)
            #         geom_info.save()
            return geom_info
        else:
            raise ValidationError("geometryType of GeometryInformation is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        geom_info = GeometryInformation.objects.get(id=element_id)
        if geom_info:
            for key, value in kwargs.iteritems():
                if key in ('geometryType', 'featureCount'):
                    setattr(geom_info, key, value)
            geom_info.save()
        else:
            raise ObjectDoesNotExist("No GeometryInformation element can be found for the provided id: %s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("GeometryInformation element of the geographic feature resource cannot be deleted.")

# Define the netCDF resource
class GeographicFeatureResource(Page, AbstractResource):

    @property
    def metadata(self):
        md = GeographicFeatureMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # 3 file types are supported
        return (".shp", ".shx", ".dbf", ".prj", ".sbx", ".sbn", ".cpg")

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file or more
        return True

    def can_add(self, request):
        #return AbstractResource.can_add(self, request)
        #what does this attribute mean?
        return False

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
    geometryinformation = generic.GenericRelation(GeometryInformation)
    fieldinformation = generic.GenericRelation(FieldInformation)
    originalcoverage = generic.GenericRelation(OriginalCoverage)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(GeographicFeatureMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('FieldInformation')
        elements.append('OriginalCoverage')
        elements.append('GeometryInformation')
        return elements

    def has_all_required_elements(self):
        if not super(GeographicFeatureMetaData, self).has_all_required_elements():  # check required meta
            return False
        if not self.field_info.all():
            return False
        if not self.originalcoverage.all().first():
            return False
        if not self.geometryinformation.all().first():
            return False
        if not (self.coverages.all().filter(type='box').first() or self.coverages.all().filter(type='point').first()):
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(GeographicFeatureMetaData, self).get_required_missing_elements()
        if not self.originalcoverage.all().first():
            missing_required_elements.append('Spatial Reference')
        if not self.geometryinformation.all().first():
            missing_required_elements.append('Geometry Infomation')
        # if not self.field_info.all().first():
        #     missing_required_elements.append('FieldInformation')

        return missing_required_elements

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(GeographicFeatureMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

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
                hsterms_ori_cov_box.text = str(cov_box)
            if ori_cov_obj.projection_string:
                hsterms_ori_cov_projection = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}crsRepresentationText' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_projection.text = str(ori_cov_obj.projection_string)


        hsterms_geom_info = etree.SubElement(container, '{%s}geometryInfomation' % self.NAMESPACES['hsterms'])
        hsterms_geom_info_rdf_Description = etree.SubElement(hsterms_geom_info, '{%s}Description' % self.NAMESPACES['rdf'])
        geom_info_obj = self.geometryinformation.all().first()
        if geom_info_obj:
            hsterms_geom_info_geom_type = etree.SubElement(hsterms_geom_info_rdf_Description, '{%s}geomtryType' % self.NAMESPACES['hsterms'])
            hsterms_geom_info_geom_type.text = str(geom_info_obj.geometryType)
            hsterms_geom_info_fea_count = etree.SubElement(hsterms_geom_info_rdf_Description, '{%s}featureCount' % self.NAMESPACES['hsterms'])
            hsterms_geom_info_fea_count.text = str(geom_info_obj.featureCount)

        hsterms_field_info = etree.SubElement(container, '{%s}fieldInfomation' % self.NAMESPACES['hsterms'])
        field_info_obj_list = self.fieldinformation.all()
        if field_info_obj_list:
            for field in field_info_obj_list:
                hsterms_field_info_rdf_Description = etree.SubElement(hsterms_field_info, '{%s}Description' % self.NAMESPACES['rdf'])
                hsterms_field_info_fieldName = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldName' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldName.text = str(field.fieldName)
                hsterms_field_info_fieldType = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldType' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldType.text = str(field.fieldType)
                hsterms_field_info_fieldTypeCode = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldTypeCode' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldTypeCode.text = str(field.fieldTypeCode)
                hsterms_field_info_fieldWidth = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldWidth' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldWidth.text = str(field.fieldWidth)
                hsterms_field_info_fieldPrecision = etree.SubElement(hsterms_field_info_rdf_Description, '{%s}fieldPrecision' % self.NAMESPACES['hsterms'])
                hsterms_field_info_fieldPrecision.text = str(field.fieldPrecision)

        return etree.tostring(RDF_ROOT, pretty_print=True)

    # What does this func do?
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