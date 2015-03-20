from django.contrib.contenttypes import generic
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.pages.page_processors import processor_for
from hs_core.models import AbstractResource
from hs_core.models import resource_processor, CoreMetaData, AbstractMetaDataElement
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import json

# Define original spatial coverage metadata info
class OriginalCoverage(AbstractMetaDataElement):
    PRO_STR_TYPES = (
        ('', '---------'),
        ('EPSG Code', 'EPSG Code'),
        ('OGC WKT Projection', 'OGC WKT Projection'),
        ('Proj4 String', 'Proj4 String')
    )

    term = 'OriginalCoverage'
    """
    _value field stores a json string. The content of the json as box coverage info
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                    'units:units applying to 4 limits (north, east, south & east),
                    'name':coverage name value here (optional),
                    'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024, null=True)
    projection_string_type = models.CharField(max_length=20, choices=PRO_STR_TYPES, null=True)
    projection_string_text = models.TextField(null=True, blank=True)

    class Meta:
        # OriginalCoverage element is not repeatable
        unique_together = ("content_type", "object_id")

    @property
    def value(self):
        print self._value
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            if isinstance(kwargs['value'], dict):
                # check that all the required sub-elements exist and create new original coverage meta
                for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                    if not value_item in kwargs['value']:
                        raise ValidationError("For original coverage meta, one or more bounding box limits or 'units' is missing.")

                value_dict = {k: v for k, v in kwargs['value'].iteritems()
                              if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'name', 'projection')}

                value_json = json.dumps(value_dict)
                metadata_obj = kwargs['content_object']
                ori_cov = OriginalCoverage.objects.create(_value=value_json, content_object=metadata_obj,)

                # check for optional fields and save them to original coverage meta
                for key, value in kwargs.iteritems():
                    if key in ('pro_str_type', 'pro_str_text'):
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
            if 'value' in kwargs:
                if not isinstance(kwargs['value'], dict):
                    raise ValidationError('Invalid coverage value format.')

                value_dict = ori_cov.value

                if 'name' in kwargs['value']:
                    value_dict['name'] = kwargs['value']['name']

                for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'projection'):
                    if item_name in kwargs['value']:
                        value_dict[item_name] = kwargs['value'][item_name]

                value_json = json.dumps(value_dict)
                ori_cov._value = value_json
                ori_cov.save()

            # update projection string info
            for key, value in kwargs.iteritems():
                if key in ('projection_string_type', 'projection_string_text'):
                    setattr(ori_cov, key, value)
                    ori_cov.save()
        else:
            raise ObjectDoesNotExist("No coverage element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Original Coverage element can't be deleted.")

# Define netCDF variable metadata
class Variable(AbstractMetaDataElement):
    # variable types are defined in OGC enhanced_data_model_extension_standard
    # left is the given value stored in database right is the value for the drop down list
    VARIABLE_TYPES = (
        ('Char', 'Char'),  # 8-bit byte that contains uninterpreted character data
        ('Byte', 'Byte'),  # integer(8bit)
        ('Short', 'Short'),  # signed integer (16bit)
        ('Int', 'Int'),  # signed integer (32bit)
        ('Float', 'Float'),  # floating point (32bit)
        ('Double', 'Double'),  # floating point(64bit)
        ('Int64', 'Int64'),  # integer(64bit)
        ('Unsigned Byte', 'Unsigned Byte'),
        ('Unsigned Short', 'Unsigned Short'),
        ('Unsigned Int', 'Unsigned Int'),
        ('Unsigned Int64', 'Unsigned Int64'),
        ('String', 'String'),  # variable length character string
        ('User Defined Type', 'User Defined Type'),  # compound, vlen, opaque, enum
        ('Unknown', 'Unknown')
    )
    term = 'Variable'
    # required variable attributes
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=VARIABLE_TYPES)
    shape = models.CharField(max_length=100)
    # optional variable attributes
    descriptive_name = models.CharField(max_length=100, null=True,blank=True)
    method = models.TextField(null=True, blank=True)
    missing_value = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        self.name

    @classmethod
    def create(cls, **kwargs):
        # Check the required attributes and create new variable meta instance
        if 'name' in kwargs:
            # check if the variable metadata already exists
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            variable = Variable.objects.filter(name__iexact=kwargs['name'], object_id=metadata_obj.id,
                                               content_type=metadata_type).first()
            if variable:
                raise ValidationError('Variable name:%s already exists' % kwargs['name'])
        else:
            raise ValidationError("Name of variable is missing.")

        if not 'unit' in kwargs:
            raise ValidationError("Variable unit is missing.")

        if 'type' in kwargs:
            if not kwargs['type'] in ['Char', 'Byte', 'Short', 'Int', 'Float', 'Double', 'Unknown', 'Int64',
                                      'Unsigned Byte', 'Unsigned Short', 'Unsigned Int', 'Unsigned Int64',
                                      'String', 'User Defined Type']:
                raise ValidationError('Invalid variable type:%s' % kwargs['type'])
        else:
            raise ValidationError("Variable type is missing.")

        if not 'shape' in kwargs:
            raise ValidationError("Variable shape is missing.")

        variable = Variable.objects.create(name=kwargs['name'], unit=kwargs['unit'], type=kwargs['type'],
                                            shape=kwargs['shape'], content_object=metadata_obj)

        # check if the optional attributes and save them to the variable metadata
        for key, value in kwargs.iteritems():
                if key in ('descriptive_name', 'method', 'missing_value'):
                    setattr(variable, key, value)

                variable.save()

        return variable


    @classmethod
    def update(cls, element_id, **kwargs):
        variable = Variable.objects.get(id=element_id)
        if variable:
            if 'name' in kwargs:
                if variable.name != kwargs['name']:
                # check this new name not already exists
                    if Variable.objects.filter(name__iexact=kwargs['name'], object_id=variable.object_id,
                                         content_type__pk=variable.content_type.id).count()> 0:
                        raise ValidationError('Variable name:%s already exists.' % kwargs['name'])

                variable.name = kwargs['name']

            for key, value in kwargs.iteritems():
                if key in ('unit', 'type', 'shape', 'descriptive_name', 'method', 'missing_value'):
                    setattr(variable, key, value)

            variable.save()
        else:
            raise ObjectDoesNotExist("No variable element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        variable = Variable.objects.get(id=element_id)
        if variable:
            # make sure we are not deleting all coverages of a resource
            if Variable.objects.filter(object_id=variable.object_id, content_type__pk=variable.content_type.id).count()== 1:
                raise ValidationError("The only variable of the resource can't be deleted.")
            variable.delete()
        else:
            raise ObjectDoesNotExist("No variable element was found for id:%d." % element_id)

# Define the netCDF resource
class NetcdfResource(Page, AbstractResource):

    @property
    def metadata(self):
        md = NetcdfMetaData()
        return self._get_metadata(md)

    @classmethod
    def get_supported_upload_file_types(cls):
        # 3 file types are supported
        return (".nc")

    @classmethod
    def can_have_multiple_files(cls):
        # can have only 1 file
        return False

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

    class Meta:
            verbose_name = 'NetCDF Resource'

processor_for(NetcdfResource)(resource_processor)

# define the netcdf metadata
class NetcdfMetaData(CoreMetaData):
    variables = generic.GenericRelation(Variable)
    ori_coverage = generic.GenericRelation(OriginalCoverage)
    _netcdf_resource = generic.GenericRelation(NetcdfResource)

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(NetcdfMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('Variable')
        elements.append('OriginalCoverage')
        return elements

    @property
    def resource(self):
        return self._netcdf_resource.all().first()
    #
    # @property
    # def originalCoverage(self):
    #     return self.ori_coverage.all().first()

    def get_xml(self):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(NetcdfMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        # inject netcdf resource specific metadata element 'variable' to container element
        for variable in self.variables.all():
            hsterms_variable = etree.SubElement(container, '{%s}netcdfVariable' % self.NAMESPACES['hsterms'])
            hsterms_variable_rdf_Description = etree.SubElement(hsterms_variable, '{%s}Description' % self.NAMESPACES['rdf'])

            hsterms_name = etree.SubElement(hsterms_variable_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = variable.name

            hsterms_unit = etree.SubElement(hsterms_variable_rdf_Description, '{%s}unit' % self.NAMESPACES['hsterms'])
            hsterms_unit.text = variable.unit

            hsterms_type = etree.SubElement(hsterms_variable_rdf_Description, '{%s}type' % self.NAMESPACES['hsterms'])
            hsterms_type.text = variable.type

            hsterms_shape = etree.SubElement(hsterms_variable_rdf_Description, '{%s}shape' % self.NAMESPACES['hsterms'])
            hsterms_shape.text = variable.shape

            if variable.descriptive_name:
                hsterms_descriptive_name = etree.SubElement(hsterms_variable_rdf_Description,'{%s}descriptiveName' % self.NAMESPACES['hsterms'])
                hsterms_descriptive_name.text = variable.descriptive_name

            if variable.method:
                hsterms_method = etree.SubElement(hsterms_variable_rdf_Description, '{%s}method' % self.NAMESPACES['hsterms'])
                hsterms_method.text = variable.method

            if variable.missing_value:
                hsterms_missing_value = etree.SubElement(hsterms_variable_rdf_Description, '{%s}missingValue' % self.NAMESPACES['hsterms'])
                hsterms_missing_value.text = variable.missing_value

        if self.ori_coverage.all().first():
            hsterms_ori_cov = etree.SubElement(container, '{%s}originalCoverage' % self.NAMESPACES['hsterms'])
            hsterms_ori_cov_rdf_Description = etree.SubElement(hsterms_ori_cov, '{%s}Description' % self.NAMESPACES['rdf'])
            ori_cov_obj = self.ori_coverage.all().first()

            if ori_cov_obj.value:
                cov_box = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                        %(ori_cov_obj.value['northlimit'], ori_cov_obj.value['eastlimit'],
                          ori_cov_obj.value['southlimit'], ori_cov_obj.value['westlimit'],ori_cov_obj.value['units'])
                if 'projection' in ori_cov_obj.value:
                    cov_box= cov_box + '; projection=%s' % ori_cov_obj.value['projection']

                hsterms_ori_cov_box = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}boundingBox' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_box.text = cov_box

            # write projection string type and text info
            if ori_cov_obj.projection_string_text:
                if ori_cov_obj.projection_string_type:
                    hsterms_ori_cov_projection_type = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}projectionStringType' % self.NAMESPACES['hsterms'])
                    hsterms_ori_cov_projection_type.text = ori_cov_obj.projection_string_type
                hsterms_ori_cov_projection_text = etree.SubElement(hsterms_ori_cov_rdf_Description, '{%s}projectionStringText' % self.NAMESPACES['hsterms'])
                hsterms_ori_cov_projection_text.text = ori_cov_obj.projection_string_text


        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers  # never delete this otherwise non of the receiver function will work
