from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.db import models
from mezzanine.pages.models import Page, RichText
from mezzanine.core.models import Ownable
from mezzanine.pages.page_processors import processor_for
from hs_core.models import AbstractResource, resource_processor, CoreMetaData, AbstractMetaDataElement




# extended metadata elements for SWAT Model Instance resource type
class ModelOutput(AbstractMetaDataElement):
    term = 'ModelOutput'
    includes_output = models.BooleanField(default=False)

    @classmethod
    def create(cls, **kwargs):
        return ModelOutput.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_output = ModelOutput.objects.get(id=element_id)
        if model_output:
            for key, value in kwargs.iteritems():
                setattr(model_output, key, value)

            model_output.save()
        else:
            raise ObjectDoesNotExist("No ModelOutput element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ModelOutput element of a resource can't be deleted.")


class ExecutedBy(AbstractMetaDataElement):
    term = 'ExecutedBY'
    name = models.CharField(max_length=500)
    url = models.URLField()

    def __unicode__(self):
        self.name

    @classmethod
    def create(cls, **kwargs):
        return ExecutedBy.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        executed_by = ExecutedBy.objects.get(id=element_id)
        if executed_by:
            for key, value in kwargs.iteritems():
                setattr(executed_by, key, value)

            executed_by.save()
        else:
            raise ObjectDoesNotExist("No ExecutedBy element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("ExecutedBy element of a resource can't be deleted.")

class SWATmodelParameters(AbstractMetaDataElement):
    term = 'SWATmodelParameters'
    has_crop_rotation = models.BooleanField(default=False)
    has_title_drainage = models.BooleanField(default=False)
    has_point_source = models.BooleanField(default=False)
    has_fertilizer = models.BooleanField(default=False)
    has_tilage_operation = models.BooleanField(default=False)
    has_inlet_of_draining_watershed = models.BooleanField(default=False)
    has_irrigation_operation = models.BooleanField(default=False)
    has_other_parameters = models.CharField(max_length=500)

    def __unicode__(self):
        self.has_other_parameters

    @classmethod
    def create(cls, **kwargs):
        return SWATmodelParameters.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = SWATmodelParameters.objects.get(id=element_id)
        if swat_model_parameters:
            for key, value in kwargs.iteritems():
                setattr(swat_model_parameters, key, value)

            swat_model_parameters.save()
        else:
            raise ObjectDoesNotExist("No SWATmodelParameters element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SWATmodelParameters element of a resource can't be deleted.")



#SWAT Model Instance Resource type
class SWATModelInstanceResource(Page, AbstractResource):

    class Meta:
        verbose_name = 'SWAT Model Instance Resource'


    @property
    def metadata(self):
        md = SWATModelInstanceMetaData()
        return self._get_metadata(md)

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)

processor_for(SWATModelInstanceResource)(resource_processor)

# metadata container class
class SWATModelInstanceMetaData(CoreMetaData):
    _model_output = generic.GenericRelation(ModelOutput)
    _executed_by = generic.GenericRelation(ExecutedBy)
    _swat_model_parameters = generic.GenericRelation(SWATmodelParameters)
    _swat_model_instance_resource = generic.GenericRelation(SWATModelInstanceResource)

    @property
    def resource(self):
        return self._swat_model_instance_resource.all().first()

    @property
    def model_output(self):
        return self._model_output.all().first()

    @property
    def executed_by(self):
        return self._executed_by.all().first()

    @property
    def swat_model_parameters(self):
        return self._swat_model_parameters.all().first()

    @classmethod
    def get_supported_element_names(cls):
        # get the names of all core metadata elements
        elements = super(SWATModelInstanceMetaData, cls).get_supported_element_names()
        # add the name of any additional element to the list
        elements.append('ModelOutput')
        elements.append('ExecutedBy')
        elements.append('SWATmodelParameters')
        return elements

    def has_all_required_elements(self):
        if not super(SWATModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_output:
            return False
        if not self.executed_by:
            return False
        if not self.swat_model_parameters:
            return False

        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(SWATModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_output:
            missing_required_elements.append('ModelOutput')
        if not self.executed_by:
            missing_required_elements.append('ExecutedBy')
        if not self.swat_model_parameters:
            missing_required_elements.append('SWATmodelParameters')
        return missing_required_elements


    def get_xml(self, pretty_print=True):
        from lxml import etree
        # get the xml string representation of the core metadata elements
        xml_string = super(SWATModelInstanceMetaData, self).get_xml(pretty_print=False)

        # create an etree xml object
        RDF_ROOT = etree.fromstring(xml_string)

        # get root 'Description' element that contains all other elements
        container = RDF_ROOT.find('rdf:Description', namespaces=self.NAMESPACES)

        if self.model_output:
            hsterms_model_output = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_model_output_rdf_Description = etree.SubElement(hsterms_model_output, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_output_value = etree.SubElement(hsterms_model_output_rdf_Description, '{%s}IncludesModelOutput' % self.NAMESPACES['hsterms'])
            if self.model_output.includes_output == True:
                hsterms_model_output_value.text = "Yes"
            else:
                hsterms_model_output_value.text = "No"
        if self.executed_by:
            hsterms_executed_by = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_rdf_Description = etree.SubElement(hsterms_executed_by, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_executed_by_name = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}ModelProgramName' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_name.text = self.executed_by.name
            hsterms_executed_by_url = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}ModelProgramURL' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_url.text = self.executed_by.url
        if self.swat_model_parameters:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}variable' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_rdf_Description = etree.SubElement(hsterms_swat_model_parameters, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_swat_model_parameters_has_crop_rotation = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasCropRotation' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_title_drainage = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasTitleDrainage' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_point_source = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasPointSource' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_fertilizer = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasFertilizer' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_tilage_operation = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasTilageOperation' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_inlet_of_draining_watershed = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasInletOfDrainingWatershed' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_irrigation_operation = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasIrrigationOperation' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_other_parameters = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasOtherParameters' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_other_parameters.text = self.swat_model_parameters.has_other_parameters
            if self.swat_model_parameters.has_crop_rotation == True: hsterms_swat_model_parameters_has_crop_rotation.text = "Yes"
            else: hsterms_swat_model_parameters_has_crop_rotation.text = "No"
            if self.swat_model_parameters.has_title_drainage == True: hsterms_swat_model_parameters_has_title_drainage.text = "Yes"
            else: hsterms_swat_model_parameters_has_title_drainage.text = "No"
            if self.swat_model_parameters.has_point_source == True: hsterms_swat_model_parameters_has_point_source.text = "Yes"
            else: hsterms_swat_model_parameters_has_point_source.text = "No"
            if self.swat_model_parameters.has_fertilizer == True: hsterms_swat_model_parameters_has_fertilizer.text = "Yes"
            else: hsterms_swat_model_parameters_has_fertilizer.text = "No"
            if self.swat_model_parameters.has_tilage_operation == True: hsterms_swat_model_parameters_has_tilage_operation.text = "Yes"
            else: hsterms_swat_model_parameters_has_tilage_operation.text = "No"
            if self.swat_model_parameters.has_inlet_of_draining_watershed == True: hsterms_swat_model_parameters_has_inlet_of_draining_watershed.text = "Yes"
            else: hsterms_swat_model_parameters_has_inlet_of_draining_watershed.text = "No"
            if self.swat_model_parameters.has_irrigation_operation == True: hsterms_swat_model_parameters_has_irrigation_operation.text = "Yes"
            else: hsterms_swat_model_parameters_has_irrigation_operation.text = "No"
        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers