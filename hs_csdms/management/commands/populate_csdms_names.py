"""
This populates CSDMS names to the database that is used
for extracting keywords from resources' abstracts.
"""
from hs_csdms.models import CSDMSName
from django.core.management.base import BaseCommand
from hs_csdms.utils import split_csdms_names


def populate_csdms_names():
    """ Store each part from split_csdms into LDAWord model
    """
    csdms_names, csdms_decors, csdms_measures = split_csdms_names()
    for csdms_name in csdms_names:
        if len(csdms_name) > 1:
            csdms_record = CSDMSName()
            csdms_record.source = 'CSDMSName'
            csdms_record.part = 'name'
            csdms_record.value = csdms_name
            csdms_record.save()

    for csdms_decor in csdms_decors:
        if len(csdms_decor) > 1:
            csdms_record = CSDMSName()
            csdms_record.source = 'CSDMSName'
            csdms_record.part = 'decoration'
            csdms_record.value = csdms_decor
            csdms_record.save()

    for csdms_measure in csdms_measures:
        if len(csdms_measure) > 1:
            csdms_record = CSDMSName()
            csdms_record.source = 'CSDMSName'
            csdms_record.part = 'measure'
            csdms_record.value = csdms_measure
            csdms_record.save()


class Command(BaseCommand):
    help = "Filling stop words used in the LDA algorithm"

    def handle(self, *args, **options):
        print("populate CSDMS Names")
        populate_csdms_names()
