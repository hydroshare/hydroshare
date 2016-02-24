__author__ = 'Mohamed Morsy'
from lxml import etree

from django.contrib.contenttypes import generic
from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, CoreMetaData, AbstractMetaDataElement
from hs_core.hydroshare import utils

from hs_model_program.models import ModelProgramResource
from hs_modelinstance.models import ModelInstanceMetaData, ModelOutput, ExecutedBy

class ModelOutput(ModelOutput):
    class Meta:
        proxy = True

class ExecutedBy(ExecutedBy):
    class Meta:
        proxy = True

# extended metadata elements for MODFLOW Model Instance resource type
class StudyArea(AbstractMetaDataElement):
    term = 'StudyArea'

class GridDimensions(AbstractMetaDataElement):
    term = 'GridDimensions'

class StressPeriod(AbstractMetaDataElement):
    term = 'StressPeriod'

class GroundWaterFlow(AbstractMetaDataElement):
    term = 'GroundWaterFlow'

class BoundaryCondition(AbstractMetaDataElement):
    term = 'BoundaryCondition'

class ModelCalibration(AbstractMetaDataElement):
    term = 'ModelCalibration'

class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'

class GeneralElements(AbstractMetaDataElement):
    term = 'GeneralElements'