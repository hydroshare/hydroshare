__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms

from crispy_forms import layout
from crispy_forms.layout import Layout, Field, HTML

from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users

from hs_modelinstance.models import ModelOutput, ExecutedBy
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource, StudyArea, GridDimensions,\
    StressPeriod, GroundWaterFlow, BoundaryCondition, ModelCalibration, ModelInput, GeneralElements


gridTypeChoices = (('Regular', 'Regular'), ('Irregular', 'Irregular'),)
stressPeriodTypeChoices = (('Steady', 'Steady'), ('Transient', 'Transient'),
                           ('Steady and Transient', 'Steady and Transient'),)
transientStateValueTypeChoices = (('Annually', 'Annually'), ('Monthly', 'Monthly'),
                                  ('Daily', 'Daily'), ('Hourly', 'Hourly'),)
flowPackageChoices = (('BCF6', 'BCF6'), ('LPF', 'LPF'), ('HUF2', 'HUF2'),
                      ('UPW', 'UPW'), ('HFB6', 'HFB6'), ('UZF', 'UZF'), ('SWI2', 'SWI2'),)
flowParameterChoices = (('Hydraulic Conductivity', 'Hydraulic Conductivity'),
                        ('Transmissivity', 'Transmissivity'),)
boundaryConditionTypeChoices = (('Specified Head Boundaries', 'Specified Head Boundaries'),
                                ('Specified Flux Boundaries', 'Specified Flux Boundaries'),
                                ('Head-Dependent Flux Boundary', 'Head-Dependent Flux Boundary'),)
boundaryConditionPackageChoices = (('BFH', 'BFH'), ('CHD', 'CHD'), ('FHB', 'FHB'), ('RCH', 'RCH'),
                                   ('WEL', 'WEL'), ('DAF', 'DAF'), ('DAFG', 'DAFG'), ('DRN', 'DRN'),
                                   ('DRT', 'DRT'), ('ETS', 'ETS'), ('EVT', 'EVT'), ('GHB', 'GHB'),
                                   ('LAK', 'LAK'), ('MNW1', 'MNW1'), ('MNW2', 'MNW2'), ('RES', 'RES'),
                                   ('RIP', 'RIP'), ('RIV', 'RIV'), ('SFR', 'SFR'), ('STR', 'STR'), ('UZF', 'UZF'),)
observationProcessPackageChoices = (('ADV2', 'ADV2'), ('CHOB', 'CHOB'), ('DROB', 'DROB'),
                                    ('DTOB', 'DTOB'), ('GBOB', 'GBOB'), ('HOB', 'HOB'),
                                    ('OBS', 'OBS'), ('RVOB', 'RVOB'), ('STOB', 'STOB'),)
modelSolverChoices = (('DE4', 'DE4'), ('GMG', 'GMG'), ('LMG', 'LMG'), ('PCG', 'PCG'),
                      ('PCGN', 'PCGN'), ('SIP', 'SIP'), ('SOR', 'SOR'), ('NWT', 'NWT'),)
outputControlPackageChoices = (('GAGE', 'GAGE'), ('HYD', 'HYD'), ('LMT6', 'LMT6'), ('MNWI', 'MNWI'), ('OC', 'OC'),)
subsidencePackageChoices = (('IBS', 'IBS'), ('SUB', 'SUB'), ('SWT', 'SWT'),)


class MetadataField(layout.Field):
          def __init__(self, *args, **kwargs):
              kwargs['css_class'] = 'form-control input-sm'
              super(MetadataField, self).__init__(*args, **kwargs)

