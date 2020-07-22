from django.db import models, transaction
from .utils import split_csdms_names


class CSDMSName(models.Model):
    """ Maintain a cached copy of the CSDMS standard name database inside HydroShare
        This maintains a copy of the CSDMS database maintained at
        https://csdms.colorado.edu/wiki/CSDMS_Standard_Names
    """
    source = models.CharField(max_length=256, editable=False, null=False, blank=False,
                              help_text='The source file from CSDMS')
    part = models.CharField(max_length=16, choices=(('name', 'name'), ('decoration', 'decoration'),
                            ('measure', 'measure')),
                            help_text='The standard names can be splitted to three parts,\
                                       name, decoration, and measurement')
    value = models.CharField(max_length=255, editable=False, null=False, blank=False,
                             help_text='The value for the corresponding part')

    @staticmethod
    def add_word(s, p, v):
        """ add a record to the CSDMS Database
            :param s, a choice from source describes where the word from
            :param p, a choice from part describes which part the word is extracted from
            :param, v, a string value for the word to be added
        """
        object, _ = CSDMSName.objects.get_or_create(source=s, part=p, value=v)

        return object

    @staticmethod
    def populate_csdms_names():
        """ Store each part from split_csdms into LDAWord model
        """
        csdms_names, csdms_decors, csdms_measures = split_csdms_names()
        for csdms_name in csdms_names:
            if len(csdms_name) > 1:
                CSDMSName.add_word('CSDMSName', 'name', csdms_name)

        for csdms_decor in csdms_decors:
            if len(csdms_decor) > 1:
                CSDMSName.add_word('CSDMSName', 'decoration', csdms_decor)

        for csdms_measure in csdms_measures:
            if len(csdms_measure) > 1:
                CSDMSName.add_word('CSDMSName', 'measure', csdms_measure)

    @staticmethod
    def list_all_names():
        raw_names = CSDMSName.objects.filter(part='name').values_list('value').order_by('value')
        list_names = [name[0] for name in raw_names]
        return list_names

    @staticmethod
    def list_all_decors():
        raw_decors = CSDMSName.objects.filter(part='decoration').values_list('value').order_by('value')
        list_decors = [decor[0] for decor in raw_decors]
        return list_decors

    @staticmethod
    def list_all_measures():
        raw_measures = CSDMSName.objects.filter(part='measure').values_list('value').order_by('value')
        list_measures = [measure[0] for measure in raw_measures]
        return list_measures

    @staticmethod
    def clear():
        """ clear all data records """
        CSDMSName.objects.all().delete()
