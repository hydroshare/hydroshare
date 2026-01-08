from unittest import TestCase
from datetime import date

from hs_core.hydroshare import resource
from django.contrib.auth.models import Group, User
from hs_core.models import BaseResource, Creator
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin


class TestGetCitation(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestGetCitation, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='A resource',
            keywords=['kw1', 'kw2']
        )

    def tearDown(self):
        super(TestGetCitation, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()
        Creator.objects.all().delete()

    def test_one_author(self):
        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C. ({}). A resource, HydroShare, {}'\
            .format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_two_authors_no_comma(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id, 'creator', name='John Smith')

        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C., ' \
                           'J. Smith ({}). A resource, HydroShare, {}'.format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_two_authors_comma(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id, 'creator', name='Smith, John')

        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C., ' \
                           'J. Smith ({}). A resource, HydroShare, {}'.format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_two_authors_multiple_first_and_last_names_comma(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id, 'creator',
                                         name='Smith William, John Mason Jingle')

        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C., ' \
                           'J. M. J. Smith William ' \
                           '({}). A resource, HydroShare, {}'.format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_two_authors_multiple_first_and_last_names_no_comma(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id, 'creator',
                                         name='John Mason Jingle Smith William')

        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C., ' \
                           'J. M. J. S. William ' \
                           '({}). A resource, HydroShare, {}'.format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_two_authors_and_organization(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id, 'creator',
                                         name='Smith William, John Mason Jingle')
        resource.create_metadata_element(self.res.short_id, 'creator',
                                         organization='U.S. Geological Survey')

        citation = self.res.get_citation()
        hs_identifier = self.res.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        hs_url = hs_identifier.url
        hs_date = str(date.today().year)
        correct_citation = 'Creator_LastName, C., ' \
                           'J. M. J. Smith William, ' \
                           'U.S. Geological Survey ' \
                           '({}). A resource, HydroShare, {}'.format(hs_date, hs_url)
        self.assertEqual(citation, correct_citation)

    def test_parse_citation_name(self):
        name = "John Morley Smith"
        parsed_name = self.res.parse_citation_name(name, first_author=True)
        self.assertEqual(parsed_name, 'Smith, J. M., ')

        name = "John Morley Smith"
        parsed_name = self.res.parse_citation_name(name)
        self.assertEqual(parsed_name, 'J. M. Smith, ')

        name = "Smith Tanner, John Morley"
        parsed_name = self.res.parse_citation_name(name, first_author=True)
        self.assertEqual(parsed_name, 'Smith Tanner, J. M., ')

        name = "Smith Tanner, John Morley"
        parsed_name = self.res.parse_citation_name(name)
        self.assertEqual(parsed_name, 'J. M. Smith Tanner, ')
