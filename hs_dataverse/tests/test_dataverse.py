import tempfile
import shutil

from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare

from hs_dataverse.utils import export_bag
from hs_dataverse.tests.utilities import global_reset


class T01CheckMetadata(TestCase):

    def setUp(self):
        """
        sets up the object inherited from TestCase for testing

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        global_reset()
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

        metadata = [
            {'title': {'value': 'Updated Resource Title'}},
            {'description': {'abstract': 'Updated Resource Abstract'}},
            {'date': {'type': 'valid', 'start_date': '1/26/2016', 'end_date': '12/31/2016'}},
            {'date': {'type': 'created', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'modified', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'published', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'date': {'type': 'available', 'start_date': '1/26/2016'}},   # will be ignored without error
            {'creator': {'name': 'John Smith', 'email': 'jsmith@gmail.com'}},
            {'creator': {'name': 'Jane Smith', 'email': 'jsmith@gmail.com'}},
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
            {'language': {'code': 'fre'}},
            {'relation': {'type': 'isPartOf', 'value': 'http://hydroshare.org/resource/001'}},
            {'rights': {'statement': 'This is the rights statement for this resource', 'url': 'http://rights.ord/001'}},
            {'source': {'derived_from': 'http://hydroshare.org/resource/0001'}},
            {'subject': {'value': 'sub-1'}},
            {'subject': {'value': 'sub-2'}}
        ]

        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about dog holes',
            metadata = metadata
        )

        self.res.extra_metadata = {'name': 'John Jackson', 'email': 'jj@gmail.com'}
        self.res.save()

        options = {'verbosity': 1, 'settings': None, 'pythonpath': None, 'traceback': False,
                   'no_color': False, 'resource_ids': [self.res.short_id],
                   'generate_metadata': False, 'generate_bag': False}

        self.temp_dir = export_bag(self.res.short_id, options)
        x = evaluate_json_template('hs_dataverse/templates/template.json', self.temp_dir)
        self.meta_dict = json.loads(x)

    def tearDown(self):
        """
        tears down the object inherited from TestCase for testing, kills the things from setup including tempdir

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        super(T01CheckMetadata, self).tearDown()
        shutil.rmtree(self.temp_dir)

    def test_title(self):
        """
        tests that the title is extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        self.assertEqual(self.res.metadata.title.value,
                         self.meta_dict['datasetVersion']['metadataBlocks']['citation']['fields'][0]['value'])

    def test_authors(self):
        """
        tests that the authors are extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for i, c in enumerate(self.res.metadata.creators.all()):
            self.assertEqual(c.name,
                             self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                           ['fields'][3]['value'][i]['authorName']['value'])

    def test_contacts(self):
        """
        tests that the contacts are extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        self.assertEqual(self.res.metadata.creators.first().name,
                         self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                       ['fields'][4]['value'][0]['datasetContactName']['value'])
        # also, the owners are the other contacts, but as of now this is not tested

    def test_description(self):
        """
        tests that the description is extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        self.assertEqual(self.res.metadata.description.abstract,
                         self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                       ['fields'][5]['value'][0]['dsDescriptionValue']['value'])

    def test_keywords(self):
        """
        tests that the keywords are extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for i, keyword in enumerate(self.res.metadata.subjects.all()):
            self.assertEqual(keyword.value,
                             self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                           ['fields'][7]['value'][i]['keywordValue']['value'])

    def test_related_resources(self):
        """
        tests that the related resources are extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for related_res in self.res.metadata.relations.all():
            if (related_res.type == 'IsDescribedBy'):
                self.assertEqual(related_res.value,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                               ['fields'][21]['value'])

    def test_notes(self):
        """
        tests that the notes extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        notes_text = ''
        for key, value in list(self.res.extra_metadata.items()):
            notes_text = notes_text + '{}: {}'.format(key, value) + '\n'
        self.assertEqual(notes_text,
                         self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                       ['fields'][9]['value'])

    def test_contributors(self):
        """
        tests that the contributors are extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for contributor in self.res.metadata.contributors.all():
            self.assertEqual(contributor.name,
                             self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                           ['fields'][11]['value'][0]['contributorName']['value'])

    def test_grant_info(self):
        """
        tests that the grant info is extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for funding_agency in self.res.metadata.funding_agencies.all():
            self.assertEqual(funding_agency.agency_name,
                             self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                           ['fields'][12]['value']['grantNumberAgency']['value'])
            self.assertEqual(funding_agency.award_number,
                             self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                           ['fields'][12]['value']['grantNumberValue']['value'])

    def test_date_modified(self):
        """
        tests that the date modified is extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        if self.res.metadata.dates.all().filter(type='modified'):
            mod_date = self.res.metadata.dates.all().filter(type='modified')[0]
        self.assertIn(self.meta_dict['datasetVersion']['metadataBlocks']['citation']
                                    ['fields'][5]['value'][0]['dsDescriptionDate']['value'],
                      str(mod_date.start_date))

    def test_coverage(self):
        """
        tests that the coverage data is extracted correctly

        :param self: an instance of the T01CheckMetadta object
        :return: nothing
        """
        for x in self.res.metadata.coverages.all():
            if x.type == 'box':  # For now this doesn't evaluate to true, so this is not tested
                self.assertEqual(x.value.eastlimit,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][2]['value']['eastLongitude']['value'])
                self.assertEqual(x.value.northlimit,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][2]['value']['northLongitude']['value'])
                self.assertEqual(x.value.westlimit,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][2]['value']['westLongitude']['value'])
                self.assertEqual(x.value.southlimit,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][2]['value']['southLongitude']['value'])
                self.assertEqual(x.value.units,
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][1]['value'][0])
            if x.type == 'point':
                self.assertEqual(x.value['east'],
                                 float(self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                                     ['fields'][2]['value'][0]['westLongitude']['value']))
                self.assertEqual(x.value['north'],
                                 float(self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                                     ['fields'][2]['value'][0]['southLongitude']['value']))
                self.assertEqual(x.value['units'],
                                 self.meta_dict['datasetVersion']['metadataBlocks']['geospatial']
                                               ['fields'][1]['value'][0])
