__author__ = 'Mohamed Morsy'
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



class modelObjective(AbstractMetaDataElement):
    term = 'modelObjective'
    objective_choices = (('Hydrology', 'Hydrology'), ('Water quality', 'Water quality'), ('BMPs', 'BMPs'), ('Climate / Landuse Change', 'Climate / Landuse Change'), ('Other', 'Other'))
    swat_model_objective = models.CharField(max_length=100, choices=objective_choices)
    other_objectives = models.CharField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        self.other_objectives

    @classmethod
    def create(cls, **kwargs):
        if 'swat_model_objective' in kwargs:
            if not kwargs['swat_model_objective'] in ['Hydrology', 'Water quality', 'BMPs', 'Climate / Landuse Change', 'Other']:
                raise ValidationError('Invalid swat_model_objective:%s' % kwargs['type'])
        else:
            raise ValidationError("swat_model_objective is missing.")
        if not 'other_objectives' in kwargs:
            raise ValidationError("modelObjective other_objectives is missing.")
        metadata_obj = kwargs['content_object']
        return modelObjective.objects.create(swat_model_objective=kwargs['swat_model_objective'], other_objectives=kwargs['other_objectives'], content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        model_objective = modelObjective.objects.get(id=element_id)
        if model_objective:
            for key, value in kwargs.iteritems():
                if key in ('swat_model_objective', 'other_objectives'):
                    setattr(model_objective, key, value)
            model_objective.save()
        else:
            raise ObjectDoesNotExist("No modelObjective element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("modelObjective element of a resource can't be deleted.")

class simulationType(AbstractMetaDataElement):
    term = 'simulationType'
    type_choices = (('Normal Simulation', 'Normal Simulation'), ('Sensitivity Analysis', 'Sensitivity Analysis'), ('Auto-Calibration', 'Auto-Calibration'))
    simulation_type_name = models.CharField(max_length=100, choices=type_choices)

    def __unicode__(self):
        self.simulation_type

    @classmethod
    def create(cls, **kwargs):
        if 'simulation_type_name' in kwargs:
            if not kwargs['simulation_type_name'] in ['Normal Simulation', 'Sensitivity Analysis', 'Auto-Calibration']:
                raise ValidationError('Invalid simulation type:%s' % kwargs['type'])
        else:
            raise ValidationError("simulation type is missing.")

        metadata_obj = kwargs['content_object']
        return simulationType.objects.create(simulation_type_name=kwargs['simulation_type_name'], content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        simulation_type = simulationType.objects.get(id=element_id)
        if simulation_type:
            for key, value in kwargs.iteritems():
                if key in ('simulation_type_name'):
                    setattr(simulation_type, key, value)
            simulation_type.save()
        else:
            raise ObjectDoesNotExist("No simulationType element was found for the provided id:%s" % kwargs['id'])

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("simulationType element of a resource can't be deleted.")


class SWATmodelParameters(AbstractMetaDataElement):
    term = 'SWATmodelParameters'
    has_crop_rotation = models.BooleanField(default=False)
    has_title_drainage = models.BooleanField(default=False)
    has_point_source = models.BooleanField(default=False)
    has_fertilizer = models.BooleanField(default=False)
    has_tillage_operation = models.BooleanField(default=False)
    has_inlet_of_draining_watershed = models.BooleanField(default=False)
    has_irrigation_operation = models.BooleanField(default=False)
    has_other_parameters = models.CharField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        self.has_other_parameters

    @classmethod
    def create(cls, **kwargs):
        if not 'has_crop_rotation' in kwargs:
            raise ValidationError("SWATmodelParameters has_crop_rotation is missing.")
        if not 'has_title_drainage' in kwargs:
            raise ValidationError("SWATmodelParameters has_title_drainage is missing.")
        if not 'has_point_source' in kwargs:
            raise ValidationError("SWATmodelParameters has_point_source is missing.")
        if not 'has_fertilizer' in kwargs:
            raise ValidationError("SWATmodelParameters has_fertilizer is missing.")
        if not 'has_tillage_operation' in kwargs:
            raise ValidationError("SWATmodelParameters has_tillage_operation is missing.")
        if not 'has_inlet_of_draining_watershed' in kwargs:
            raise ValidationError("SWATmodelParameters has_inlet_of_draining_watershed is missing.")
        if not 'has_irrigation_operation' in kwargs:
            raise ValidationError("SWATmodelParameters has_irrigation_operation is missing.")
        if not 'has_other_parameters' in kwargs:
            raise ValidationError("SWATmodelParameters has_other_parameters is missing.")

        metadata_obj = kwargs['content_object']
        return SWATmodelParameters.objects.create(has_crop_rotation=kwargs['has_crop_rotation'], has_title_drainage=kwargs['has_title_drainage'], has_point_source=kwargs['has_point_source'],
                                            has_fertilizer=kwargs['has_fertilizer'], has_tillage_operation=kwargs['has_tillage_operation'], has_inlet_of_draining_watershed=kwargs['has_inlet_of_draining_watershed'],
                                            has_irrigation_operation=kwargs['has_irrigation_operation'], has_other_parameters=kwargs['has_other_parameters'], content_object=metadata_obj)

    @classmethod
    def update(cls, element_id, **kwargs):
        swat_model_parameters = SWATmodelParameters.objects.get(id=element_id)
        if swat_model_parameters:
            for key, value in kwargs.iteritems():
                if key in ('has_crop_rotation', 'has_title_drainage', 'has_point_source', 'has_fertilizer', 'has_tillage_operation', 'has_inlet_of_draining_watershed', 'has_irrigation_operation', 'has_other_parameters'):
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
    _model_objective = generic.GenericRelation(modelObjective)
    _simulation_type = generic.GenericRelation(simulationType)
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
    def model_objective(self):
        return self._model_objective.all().first()

    @property
    def simulation_type(self):
        return self._simulation_type.all().first()

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
        elements.append('modelObjective')
        elements.append('simulationType')
        elements.append('SWATmodelParameters')
        return elements

    def has_all_required_elements(self):
        if not super(SWATModelInstanceMetaData, self).has_all_required_elements():
            return False
        if not self.model_output:
            return False
        if not self.executed_by:
            return False
        if not self.model_objective:
            return False
        return True

    def get_required_missing_elements(self):
        missing_required_elements = super(SWATModelInstanceMetaData, self).get_required_missing_elements()
        if not self.model_output:
            missing_required_elements.append('ModelOutput')
        if not self.executed_by:
            missing_required_elements.append('ExecutedBy')
        if not self.model_objective:
            missing_required_elements.append('modelObjective')
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
            hsterms_model_output = etree.SubElement(container, '{%s}ModelOutput' % self.NAMESPACES['hsterms'])
            hsterms_model_output_rdf_Description = etree.SubElement(hsterms_model_output, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_output_value = etree.SubElement(hsterms_model_output_rdf_Description, '{%s}IncludesModelOutput' % self.NAMESPACES['hsterms'])
            if self.model_output.includes_output == True: hsterms_model_output_value.text = "Yes"
            else: hsterms_model_output_value.text = "No"
        if self.executed_by:
            hsterms_executed_by = etree.SubElement(container, '{%s}ExecutedBy' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_rdf_Description = etree.SubElement(hsterms_executed_by, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_executed_by_name = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}ModelProgramName' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_name.text = self.executed_by.name
            hsterms_executed_by_url = etree.SubElement(hsterms_executed_by_rdf_Description, '{%s}ModelProgramURL' % self.NAMESPACES['hsterms'])
            hsterms_executed_by_url.text = self.executed_by.url
        if self.model_objective:
            hsterms_model_objective = etree.SubElement(container, '{%s}modelObjective' % self.NAMESPACES['hsterms'])
            hsterms_model_objective_rdf_Description = etree.SubElement(hsterms_model_objective, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_model_objective_swat_model_objective = etree.SubElement(hsterms_model_objective_rdf_Description, '{%s}modelObjective' % self.NAMESPACES['hsterms'])
            hsterms_model_objective_swat_model_objective.text = self.model_objective.swat_model_objective
            hsterms_model_objective_other_objectives = etree.SubElement(hsterms_model_objective_rdf_Description, '{%s}otherObjectives' % self.NAMESPACES['hsterms'])
            hsterms_model_objective_other_objectives.text = self.model_objective.other_objectives
        if self.simulation_type:
            hsterms_simulation_type = etree.SubElement(container, '{%s}simulationType' % self.NAMESPACES['hsterms'])
            hsterms_simulation_type_rdf_Description = etree.SubElement(hsterms_simulation_type, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_simulation_type_name = etree.SubElement(hsterms_simulation_type_rdf_Description, '{%s}simulationType' % self.NAMESPACES['hsterms'])
            hsterms_simulation_type_name.text = self.simulation_type.simulation_type_name
        if self.swat_model_parameters:
            hsterms_swat_model_parameters = etree.SubElement(container, '{%s}SWATmodelParameters' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_rdf_Description = etree.SubElement(hsterms_swat_model_parameters, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_swat_model_parameters_has_crop_rotation = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasCropRotation' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_title_drainage = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasTitleDrainage' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_point_source = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasPointSource' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_fertilizer = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasFertilizer' % self.NAMESPACES['hsterms'])
            hsterms_swat_model_parameters_has_tillage_operation = etree.SubElement(hsterms_swat_model_parameters_rdf_Description, '{%s}hasTillageOperation' % self.NAMESPACES['hsterms'])
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
            if self.swat_model_parameters.has_tillage_operation == True: hsterms_swat_model_parameters_has_tillage_operation.text = "Yes"
            else: hsterms_swat_model_parameters_has_tillage_operation.text = "No"
            if self.swat_model_parameters.has_inlet_of_draining_watershed == True: hsterms_swat_model_parameters_has_inlet_of_draining_watershed.text = "Yes"
            else: hsterms_swat_model_parameters_has_inlet_of_draining_watershed.text = "No"
            if self.swat_model_parameters.has_irrigation_operation == True: hsterms_swat_model_parameters_has_irrigation_operation.text = "Yes"
            else: hsterms_swat_model_parameters_has_irrigation_operation.text = "No"
        return etree.tostring(RDF_ROOT, pretty_print=True)

import receivers