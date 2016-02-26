__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms

from crispy_forms import layout
from crispy_forms.layout import Layout, Field, HTML

from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users

from hs_modelinstance.models import ModelOutput, ExecutedBy

boundaryConditionTypeChoices = (('Specified Head Boundaries', 'Specified Head Boundaries'),
                                    ('Specified Flux Boundaries', 'Specified Flux Boundaries'),
                                    ('Head-Dependent Flux Boundary', 'Head-Dependent Flux Boundary'),)
boundaryConditionPackageChoices = (('BFH', 'BFH'), ('CHD', 'CHD'), ('FHB', 'FHB'), ('RCH', 'RCH'),
                                   ('WEL', 'WEL'), ('DAF', 'DAF'), ('DAFG', 'DAFG'), ('DRN', 'DRN'),
                                   ('DRT', 'DRT'), ('ETS', 'ETS'), ('EVT', 'EVT'), ('GHB', 'GHB'),
                                   ('LAK', 'LAK'), ('MNW1', 'MNW1'), ('MNW2', 'MNW2'), ('RES', 'RES'),
                                   ('RIP', 'RIP'), ('RIV', 'RIV'), ('SFR', 'SFR'), ('STR', 'STR'), ('UZF', 'UZF'),)

