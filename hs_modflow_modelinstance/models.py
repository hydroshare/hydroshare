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
    totalLength = models.CharField(max_length=100, null=True, blank=True,
                                   verbose_name='Study area total length in meters')
    totalWidth = models.CharField(max_length=100, null=True, blank=True,
                                  verbose_name='Study area total width in meters')
    maximumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Study area maximum elevation in meters')
    minimumElevation = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Study area minimum elevation in meters')

    def __unicode__(self):
        return self.totalLength

    class Meta:
        # StudyArea element is not repeatable
        unique_together = ("content_type", "object_id")


class GridDimensions(AbstractMetaDataElement):
    term = 'GridDimensions'
    gridTypeChoices = (('Regular', 'Regular'), ('Irregular', 'Irregular'),)

    numberOfLayers = models.CharField(max_length=100, null=True, blank=True, verbose_name='Number of model grid layers')
    typeOfRows = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True)
    numberOfRows = models.CharField(max_length=100, null=True, blank=True)
    typeOfColumns = models.CharField(max_length=100, choices=gridTypeChoices, null=True, blank=True)
    numberOfColumns = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.numberOfLayers

    class Meta:
        # GridDimensions element is not repeatable
        unique_together = ("content_type", "object_id")


class StressPeriod(AbstractMetaDataElement):
    term = 'StressPeriod'
    stressPeriodTypeChoices = (('Steady', 'Steady'), ('Transient', 'Transient'),
                               ('Steady and Transient', 'Steady and Transient'),)
    transientStateValueTypeChoices = (('Annually', 'Annually'), ('Monthly', 'Monthly'),
                                      ('Daily', 'Daily'), ('Hourly', 'Hourly'),)

    stressPeriodType = models.CharField(max_length=100, choices=stressPeriodTypeChoices, null=True, blank=True)
    steadyStateValue = models.CharField(max_length=100, null=True, blank=True,
                                        verbose_name='Length of steady state stress period(s)')
    transientStateValueType = models.CharField(max_length=100, choices=transientStateValueTypeChoices, null=True)
    transientStateValue = models.CharField(max_length=100, null=True, blank=True,
                                           verbose_name='Length of transient state stress period(s)')

    def __unicode__(self):
        return self.stressPeriodType

    class Meta:
        # StressPeriod element is not repeatable
        unique_together = ("content_type", "object_id")


class GroundWaterFlow(AbstractMetaDataElement):
    term = 'GroundWaterFlow'
    flowPackageChoices = (('BCF6', 'BCF6'), ('LPF', 'LPF'), ('HUF2', 'HUF2'),
                          ('UPW', 'UPW'), ('HFB6', 'HFB6'), ('UZF', 'UZF'), ('SWI2', 'SWI2'),)
    flowParameterChoices = (('Hydraulic Conductivity', 'Hydraulic Conductivity'),
                            ('Transmissivity', 'Transmissivity'),)

    flowPackage = models.CharField(max_length=100, choices=flowPackageChoices, null=True, blank=True)
    flowParameter = models.CharField(max_length=100, choices=flowParameterChoices, null=True, blank=True)

    def __unicode__(self):
        return self.flowPackage

    class Meta:
        # GroundWaterFlow element is not repeatable
        unique_together = ("content_type", "object_id")


class BoundaryConditionTypeChoices(models.Model):
    description = models.CharField(max_length=300)


class BoundaryConditionPackageChoices(models.Model):
    description = models.CharField(max_length=300)


class BoundaryCondition(AbstractMetaDataElement):
    term = 'BoundaryCondition'
    boundaryConditionType = models.ManyToManyField(BoundaryConditionTypeChoices, null=True, blank=True)
    boundaryConditionPackage = models.ManyToManyField(BoundaryConditionPackageChoices, null=True, blank=True)

    # may be this could cause a problem
    def __unicode__(self):
        return self.boundaryConditionType

    class Meta:
        # BoundaryCondition element is not repeatable
        unique_together = ("content_type", "object_id")

    @classmethod
    def _add_boundary_types(cls, boundary_choices, choices):
        for type_choices in choices:
            qs = BoundaryConditionTypeChoices.objects.filter(description__exact=type_choices)
            if qs.exists():
                boundary_choices.boundaryConditionType.add(qs[0])
            else:
                boundary_choices.boundaryConditionType.create(description=type_choices)

    @classmethod
    def _add_boundary_packages(cls, boundary_packages, packages):
        for package in packages:
            qs = BoundaryConditionPackageChoices.objects.filter(description__exact=package)
            if qs.exists():
                boundary_packages.boundaryConditionPackage.add(qs[0])
            else:
                boundary_packages.boundaryConditionPackage.create(description=package)

    # need to define create and update methods

    @classmethod
    def _validate_boundary_condition_types(cls, types):
        for boundary_types in types:
            if boundary_types not in ['Specified Head Boundaries', 'Specified Flux Boundaries',
                                      'Head-Dependent Flux Boundary']:
                raise ValidationError('Invalid Boundary Condition Type:%s' % types)

    @classmethod
    def _validate_boundary_condition_packages(cls, packages):
        for boundary_packages in packages:
            if boundary_packages not in ['BFH', 'CHD', 'FHB', 'RCH', 'WEL', 'DAF', 'DAFG', 'DRN', 'DRT', 'ETS', 'EVT',
                                         'GHB', 'LAK', 'MNW1', 'MNW2', 'RES', 'RIP', 'RIV', 'SFR', 'STR', 'UZF']:
                raise ValidationError('Invalid Boundary Condition Type:%s' % packages)


class ModelCalibration(AbstractMetaDataElement):
    term = 'ModelCalibration'
    observationProcessPackageChoices = (('ADV2', 'ADV2'), ('CHOB', 'CHOB'), ('DROB', 'DROB'),
                                        ('DTOB', 'DTOB'), ('GBOB', 'GBOB'), ('HOB', 'HOB'),
                                        ('OBS', 'OBS'), ('RVOB', 'RVOB'), ('STOB', 'STOB'),)

    calibratedParameter = models.CharField(max_length=200, null=True, blank=True)
    observationType = models.CharField(max_length=200, null=True, blank=True)
    observationProcessPackage = models.CharField(max_length=100, choices=observationProcessPackageChoices, null=True,
                                               blank=True)
    calibrationMethod = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return self.calibratedParameter

    class Meta:
        # ModelCalibration element is not repeatable
        unique_together = ("content_type", "object_id")


class ModelInput(AbstractMetaDataElement):
    term = 'ModelInput'
    inputType = models.CharField(max_length=200, null=True, blank=True)
    inputSourceName = models.CharField(max_length=200, null=True, blank=True)
    inputSourceURL = models.URLField(null=True, blank=True, verbose_name='Input source URL')

    def __unicode__(self):
        return self.inputType


class GeneralElements(AbstractMetaDataElement):
    term = 'GeneralElements'
    modelSolverChoices = (('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'),
                          ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT'),)
    outputControlPackageChoices = (('GAGE', 'GAGE'), ('HYD', 'HYD'), ('LMT6', 'LMT6'), ('MNWI', 'MNWI'), ('OC', 'OC'),)
    subsidencePackageChoices = (('IBS', 'IBS'), ('SUB', 'SUB'), ('SWT', 'SWT'),)

    modelParameter = models.CharField(max_length=200, null=True, blank=True)
    modelSolver = models.CharField(max_length=100, choices=modelSolverChoices, null=True, blank=True)
    outputControlPackage = models.CharField(max_length=100, choices=outputControlPackageChoices, null=True, blank=True)
    subsidencePackage = models.CharField(max_length=100, choices=subsidencePackageChoices, null=True, blank=True)

    def __unicode__(self):
        return self.modelParameter

    class Meta:
        # GeneralElements element is not repeatable
        unique_together = ("content_type", "object_id")