import tempfile
import shutil
import os

from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset

from hs_dataverse.utils import create_metadata_dict 
from hs_dataverse.management.commands.dataverse import export_bag

class T01CheckMetadata(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='last_name_admin',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'tom@gmail.com',
            username='tom',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.mouse = hydroshare.create_account(
            'jerry@gmail.com',
            username='jerry',
            first_name='not a cat',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about dog holes',
            metadata=[],
        )

    def tearDown(self):
        super(T01CheckMetadata, self).tearDown()
        # same pattern as setUp, kill everything I put in
        # also delete all tempfiles and tempdirs
        shutil.rmtree(self.temp_dir)

        # self.file_one.close()
        # os.remove(self.file_one.name)

    def update_metadata(self):
        # add these new metadata elements
        metadata_dict = [
            {'title': {'value': 'Updated Resource Title'}},
            {'description': {'abstract': 'Updated Resource Abstract'}},
            {'date': {'type': 'valid', 'start_date': '1/26/2016', 'end_date': '12/31/2016'}},
            {'date': {'type': 'created', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'modified', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'published', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'available', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Lisa Molley', 'email': 'lmolley@gmail.com'}},
            {'contributor': {'name': 'Kelvin Marshal', 'email': 'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'identifiers': {'ORCID': 'https://orcid.org/john',
                                             'ResearchGateID': 'https://www.researchgate.net/john'}
                             }},
            {'coverage': {'type': 'period', 'value': {'name': 'Name for period coverage', 'start': '1/1/2000',
                                                      'end': '12/12/2012'}}},
            {'coverage': {'type': 'point', 'value': {'name': 'Name for point coverage', 'east': '56.45678',
                                                     'north': '12.6789', 'units': 'decimal deg'}}},
            {'format': {'value': 'txt/csv'}},   # will be ignored without error
            {'format': {'value': 'zip'}},   # will be ignored without error
            {'identifier': {'name': 'someIdentifier', 'url': "http://some.org/002"}},
            {'identifier': {'name': 'hydroShareIdentifier', 'url': "http://hydroshare.org/001"}},   # will be ignored
            {'language': {'code': 'fre'}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource', 'url': 'http://rights.ord/001'}},
            {'source': {'derived_from': 'http://hydroshare.org/resource/0001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}},
        ]

        hydroshare.update_science_metadata(pk=self.res.short_id, metadata=metadata_dict,
                                           user=self.admin)


        self.res.extra_metadata = {'name': 'John Jackson', 'email': 'jj@gmail.com'}
        self.res.save()


    def test_extract_metadata(self):
        options = {'generage_bag': None, 'generate_metadata': None}
        self.temp_dir = export_bag(self.res.short_id, options)
        meta_dict = create_metadata_dict(self.temp_dir)

        self.assertEqual(self.res.metadata.title.value, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][0]['value'])

        self.assertEqual(self.res.creator.first_name + ' ' + self.res.creator.last_name, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][3]['value'][0]['authorName']['value']) # for now, only checks one creator

        self.assertEqual(self.res.creator.last_name + ', ' + self.res.creator.first_name, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][4]['value'][0]['datasetContactName']['value'])

#        self.assertEqual(self.res.metadata.description.abstract.value, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][5]['value'][0]['dsDescriptionValue'])

#        self.assertEqual(self.res.metadata.date.modified.value, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][5]['value'][0]['dsDescriptionDate'])

#        self.assertEqual(self.res.metadata.contributor.name, meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][11]['value'][0]['contributorName']['value'])

        self.assertEqual(self.res.metadata.coverage.value.east, meta_dict['datasetVersion']['metadataBlocks']['citation']['geofields'][2]['value']['eastLongitude']['value'])

