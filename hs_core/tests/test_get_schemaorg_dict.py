"""Tests for AbstractResource.get_schemaorg_dict(), which builds the schema.org/JSON-LD
dict shown in the resource landing page's ``<script id="schemaorg">`` tag.
"""

import uuid

from django.contrib.auth.models import Group
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from hs_core import hydroshare
from hs_core import page_processors
from hs_core.enums import RelationTypes


class TestGetSchemaorgDict(TestCase):
    """Test AbstractResource.get_schemaorg_dict()."""

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='testuser' + uuid.uuid4().hex,
            first_name='Test',
            last_name='User',
            superuser=False,
            groups=[self.group],
        )
        self.resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Resource',
        )

    def tearDown(self):
        self.resource.delete()
        self.user.delete()
        self.group.delete()

    # ------------------------------------------------------------------
    # @id / url / status branches
    # ------------------------------------------------------------------

    def test_private_resource_basic_fields(self):
        schemaorg = self.resource.get_schemaorg_dict()

        short_id = self.resource.short_id
        self.assertEqual(schemaorg['@context'], 'https://schema.org')
        self.assertEqual(schemaorg['schemaVersion'], 'http://datacite.org/schema/kernel-4')
        self.assertEqual(schemaorg['@id'], f'https://www.hydroshare.org/resource/{short_id}#schemaorg')
        self.assertEqual(schemaorg['url'], f'https://www.hydroshare.org/resource/{short_id}')
        self.assertNotIn('sameAs', schemaorg)
        self.assertEqual(schemaorg['@type'], 'Dataset')
        self.assertEqual(schemaorg['name'], 'Test Resource')
        self.assertEqual(schemaorg['creativeWorkStatus'], 'Private')
        self.assertEqual(schemaorg['inLanguage'], 'en-US')
        self.assertNotIn('publisher', schemaorg)
        self.assertNotIn('isAccessibleForFree', schemaorg)
        self.assertNotIn('datePublished', schemaorg)

    def test_discoverable_resource_status(self):
        self.resource.raccess.discoverable = True
        self.resource.raccess.save()
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['creativeWorkStatus'], 'Discoverable')
        self.assertNotIn('isAccessibleForFree', schemaorg)
        self.assertNotIn('datePublished', schemaorg)

    def test_public_resource_status_and_free_access(self):
        self.resource.raccess.public = True
        self.resource.raccess.save()
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['creativeWorkStatus'], 'Public')
        self.assertTrue(schemaorg['isAccessibleForFree'])
        self.assertNotIn('datePublished', schemaorg)

    def test_obsolete_resource_status(self):
        """A resource with an isReplacedBy relation, that is not published/public/discoverable,
        reports creativeWorkStatus 'Obsolete'."""
        self.resource.metadata.create_element(
            'relation',
            type=RelationTypes.isReplacedBy.value,
            value='https://www.hydroshare.org/resource/somenewerversion',
        )
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['creativeWorkStatus'], 'Obsolete')

    def test_published_resource_ids_and_status(self):
        self.resource.set_published(True)
        self.resource.metadata.create_element(
            'date', type='published', start_date=self.resource.updated)

        schemaorg = self.resource.get_schemaorg_dict()
        short_id = self.resource.short_id
        self.assertEqual(schemaorg['@id'], f'https://doi.org/10.4211/hs.{short_id}#schemaorg')
        self.assertEqual(schemaorg['sameAs'], f'https://www.hydroshare.org/resource/{short_id}')
        self.assertEqual(schemaorg['url'], f'https://doi.org/10.4211/hs.{short_id}')
        self.assertEqual(schemaorg['creativeWorkStatus'], 'Published')
        self.assertIn('datePublished', schemaorg)
        self.assertTrue(schemaorg['isAccessibleForFree'])

    # ------------------------------------------------------------------
    # identifier
    # ------------------------------------------------------------------

    def test_identifier_unpublished_excludes_only_hydroshare_identifier(self):
        self.resource.doi = 'doi1000100010001'
        self.resource.save()
        doi_url = f'https://doi.org/10.4211/hs.{self.resource.short_id}'
        self.resource.metadata.create_element('identifier', name='doi', url=doi_url)

        schemaorg = self.resource.get_schemaorg_dict()
        identifiers = schemaorg['identifier']
        # bare hydroshare url + a PropertyValue for the doi identifier
        self.assertEqual(len(identifiers), 2)
        self.assertEqual(identifiers[0], f'https://www.hydroshare.org/resource/{self.resource.short_id}')
        doi_entries = [i for i in identifiers if isinstance(i, dict) and i.get('propertyID') == 'doi']
        self.assertEqual(len(doi_entries), 1)
        self.assertEqual(doi_entries[0]['value'], doi_url)

    def test_identifier_published_excludes_hydroshare_and_doi(self):
        self.resource.doi = 'doi1000100010001'
        self.resource.save()
        doi_url = f'https://doi.org/10.4211/hs.{self.resource.short_id}'
        self.resource.metadata.create_element('identifier', name='doi', url=doi_url)
        self.resource.set_published(True)
        self.resource.metadata.create_element(
            'date', type='published', start_date=self.resource.updated)

        schemaorg = self.resource.get_schemaorg_dict()
        identifiers = schemaorg['identifier']
        short_id = self.resource.short_id
        # the DOI PropertyValue block + bare hydroshare url; no extra 'doi' entry from cached identifiers
        self.assertEqual(len(identifiers), 2)
        self.assertEqual(identifiers[0]['@id'], f'https://doi.org/10.4211/hs.{short_id}')
        self.assertEqual(identifiers[0]['value'], f'doi:10.4211/hs.{short_id}')
        self.assertEqual(identifiers[1], f'https://www.hydroshare.org/resource/{short_id}')

    # ------------------------------------------------------------------
    # creator / contributor
    # ------------------------------------------------------------------

    def test_creator_contact_point_on_first_creator(self):
        schemaorg = self.resource.get_schemaorg_dict()
        creators = schemaorg['creator']
        self.assertEqual(len(creators), 1)
        self.assertIn('contactPoint', creators[0])
        self.assertEqual(creators[0]['contactPoint']['@type'], 'ContactPoint')

    def test_contributor_absent_when_no_contributors(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertNotIn('contributor', schemaorg)

    def test_contributor_present_when_contributors_exist(self):
        self.resource.metadata.create_element(
            'contributor', name='Jane Contributor', organization='USU')
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertIn('contributor', schemaorg)
        self.assertEqual(len(schemaorg['contributor']), 1)
        self.assertEqual(schemaorg['contributor'][0]['name'], 'Jane Contributor')

    def test_creator_with_all_metadata_fields_and_contact_point(self):
        """A creator with every Party field set (name, organization, email, address,
        phone, homepage, identifiers) that is first by 'order' should produce a fully
        populated Person dict, including the merged contactPoint."""
        # demote the auto-created owner creator so our new creator is order=1 (the contact)
        owner_creator = self.resource.metadata.creators.first()
        self.resource.metadata.update_element('creator', owner_creator.id, order=2)
        creator = self.resource.metadata.create_element(
            'creator',
            name='Doe, Jane',
            organization='Utah State University',
            email='jane@example.com',
            address='123 Main St',
            phone='555-1234',
            homepage='https://example.com/jane',
            identifiers={'ORCID': 'https://orcid.org/0000-0002-1825-0097'},
        )
        self.resource.metadata.update_element('creator', creator.id, order=1)

        schemaorg = self.resource.get_schemaorg_dict()
        creators = schemaorg['creator']
        self.assertEqual(len(creators), 2)
        jane = creators[0]

        self.assertEqual(jane['@type'], 'Person')
        self.assertEqual(jane['name'], 'Jane Doe')
        self.assertEqual(
            jane['affiliation'], {'@type': 'Organization', 'name': 'Utah State University'})
        self.assertEqual(jane['email'], 'jane@example.com')
        self.assertEqual(jane['address'], {'@type': 'PostalAddress', 'streetAddress': '123 Main St'})
        # a single identifier + a homepage => two urls, so 'url' is a list
        self.assertEqual(
            sorted(jane['url']),
            sorted(['https://example.com/jane', 'https://orcid.org/0000-0002-1825-0097']))
        self.assertEqual(jane['identifier'], 'https://orcid.org/0000-0002-1825-0097')
        self.assertEqual(jane['sameAs'], 'https://orcid.org/0000-0002-1825-0097')

        contact_point = jane['contactPoint']
        self.assertEqual(contact_point['@type'], 'ContactPoint')
        self.assertEqual(contact_point['name'], 'Jane Doe')
        self.assertEqual(contact_point['email'], 'jane@example.com')
        self.assertEqual(contact_point['telephone'], '555-1234')
        self.assertEqual(
            sorted(contact_point['url']),
            sorted(['https://example.com/jane', 'https://orcid.org/0000-0002-1825-0097']))

        # the demoted owner creator (order=2) must not have a contactPoint
        self.assertNotIn('contactPoint', creators[1])

    def test_creator_organization_only_has_no_affiliation(self):
        """A creator with only an organization (no personal name) is an Organization,
        not a Person, and has no nested 'affiliation'."""
        self.resource.metadata.create_element(
            'creator', organization='Utah State University', email='usu@example.com')
        schemaorg = self.resource.get_schemaorg_dict()
        org_creator = next(c for c in schemaorg['creator'] if c.get('email') == 'usu@example.com')
        self.assertEqual(org_creator['@type'], 'Organization')
        self.assertEqual(org_creator['name'], 'Utah State University')
        self.assertNotIn('affiliation', org_creator)

    def test_creator_relative_uri_becomes_hydroshare_profile_url(self):
        """The auto-created owner creator is a real HydroShare user, so its 'url' should
        be derived from its relative_uri (hydroshare profile link), not a homepage/identifier."""
        schemaorg = self.resource.get_schemaorg_dict()
        owner_creator = schemaorg['creator'][0]
        self.assertEqual(
            owner_creator['url'], f'https://www.hydroshare.org/user/{self.user.id}/')

    def test_contributor_with_all_metadata_fields(self):
        """A contributor with every Party field set, including multiple identifiers,
        should be fully represented but never gets a contactPoint (creators only)."""
        self.resource.metadata.create_element(
            'contributor',
            name='Smith, John',
            organization='Utah State University',
            email='john@example.com',
            address='456 Elm St',
            phone='555-6789',
            homepage='https://example.com/john',
            identifiers={
                'ORCID': 'https://orcid.org/0000-0002-1825-0097',
                'ResearchGateID': 'https://www.researchgate.net/profile/John_Smith',
            },
        )
        schemaorg = self.resource.get_schemaorg_dict()
        john = schemaorg['contributor'][0]

        self.assertEqual(john['@type'], 'Person')
        self.assertEqual(john['name'], 'John Smith')
        self.assertEqual(
            john['affiliation'], {'@type': 'Organization', 'name': 'Utah State University'})
        self.assertEqual(john['email'], 'john@example.com')
        self.assertEqual(john['address'], {'@type': 'PostalAddress', 'streetAddress': '456 Elm St'})
        self.assertEqual(
            sorted(john['identifier']),
            sorted(['https://orcid.org/0000-0002-1825-0097',
                    'https://www.researchgate.net/profile/John_Smith']))
        self.assertEqual(sorted(john['sameAs']), sorted(john['identifier']))
        self.assertEqual(
            sorted(john['url']),
            sorted(['https://example.com/john',
                    'https://orcid.org/0000-0002-1825-0097',
                    'https://www.researchgate.net/profile/John_Smith']))
        # phone/contactPoint only apply to the creator list, never to contributors
        self.assertNotIn('contactPoint', john)
        self.assertNotIn('phone', john)

    # ------------------------------------------------------------------
    # temporal / spatial coverage
    # ------------------------------------------------------------------

    def test_temporal_coverage_absent_by_default(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertNotIn('temporalCoverage', schemaorg)

    def test_temporal_coverage_present(self):
        self.resource.metadata.create_element(
            'coverage', type='period',
            value={'name': 'Test Period', 'start': '2020-01-01', 'end': '2020-12-31'})
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['temporalCoverage'], '2020-01-01/2020-12-31')

    def test_spatial_coverage_absent_by_default(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertNotIn('spatialCoverage', schemaorg)

    def test_spatial_coverage_point(self):
        self.resource.metadata.create_element(
            'coverage', type='point',
            value={'name': 'Test Point', 'east': -111.123456, 'north': 40.456789,
                   'units': 'Decimal degrees'})
        schemaorg = self.resource.get_schemaorg_dict()
        spatial = schemaorg['spatialCoverage']
        self.assertEqual(spatial['@type'], 'Place')
        self.assertEqual(spatial['name'], 'Test Point')
        geo = spatial['geo']
        self.assertEqual(geo['@type'], 'GeoCoordinates')
        self.assertEqual(geo['latitude'], 40.4568)
        self.assertEqual(geo['longitude'], -111.1235)
        self.assertIsInstance(geo['latitude'], float)

    def test_spatial_coverage_box(self):
        self.resource.metadata.create_element(
            'coverage', type='box',
            value={'name': 'Test Box', 'northlimit': 41.5, 'eastlimit': -110.0,
                   'southlimit': 40.0, 'westlimit': -112.0, 'units': 'Decimal degrees'})
        schemaorg = self.resource.get_schemaorg_dict()
        spatial = schemaorg['spatialCoverage']
        geo = spatial['geo']
        self.assertEqual(geo['@type'], 'GeoShape')
        self.assertEqual(geo['box'], '40.0000 -112.0000 41.5000 -110.0000')

    # ------------------------------------------------------------------
    # license / rights
    # ------------------------------------------------------------------

    def test_license_default_rights_statement_and_url(self):
        # every resource is created with a default CC-BY rights statement and url
        schemaorg = self.resource.get_schemaorg_dict()
        license_dict = schemaorg['license']
        self.assertEqual(license_dict['@type'], 'CreativeWork')
        self.assertIn('Creative Commons', license_dict['text'])
        self.assertIn('url', license_dict)
        self.assertNotIn('name', license_dict)

    def test_license_statement_only(self):
        rights = self.resource.metadata.rights
        self.resource.metadata.update_element(
            'rights', rights.id, statement='Custom statement', url=None)
        schemaorg = self.resource.get_schemaorg_dict()
        license_dict = schemaorg['license']
        self.assertEqual(license_dict['text'], 'Custom statement')
        self.assertEqual(license_dict['name'], 'Customized license')
        self.assertNotIn('url', license_dict)

    def test_license_url_only(self):
        rights = self.resource.metadata.rights
        self.resource.metadata.update_element(
            'rights', rights.id, statement='', url='https://example.com/license')
        schemaorg = self.resource.get_schemaorg_dict()
        license_dict = schemaorg['license']
        self.assertEqual(license_dict['url'], 'https://example.com/license')
        self.assertNotIn('text', license_dict)
        self.assertNotIn('name', license_dict)

    # ------------------------------------------------------------------
    # citation / funding
    # ------------------------------------------------------------------

    def test_citation_uses_get_citation(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(
            schemaorg['citation'], self.resource.get_citation(forceHydroshareURI=False))
        self.assertIn(self.resource.short_id, schemaorg['citation'])

    def test_funding_absent_by_default(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertNotIn('funding', schemaorg)

    def test_funding_present_with_none_award_number(self):
        self.resource.metadata.create_element(
            'fundingagency', agency_name='National Science Foundation',
            award_title=None, award_number=None, agency_url=None)
        schemaorg = self.resource.get_schemaorg_dict()
        funding = schemaorg['funding']
        self.assertEqual(len(funding), 1)
        self.assertEqual(funding[0]['@type'], 'Grant')
        self.assertEqual(funding[0]['identifier'], '')
        self.assertEqual(funding[0]['name'], '')
        self.assertEqual(funding[0]['funder']['name'], 'National Science Foundation')
        self.assertEqual(funding[0]['funder']['identifier'], '')

    def test_funding_present_with_award_number(self):
        self.resource.metadata.create_element(
            'fundingagency', agency_name='National Science Foundation',
            award_title='Test Award', award_number='NSF-12345',
            agency_url='https://nsf.gov')
        schemaorg = self.resource.get_schemaorg_dict()
        funding = schemaorg['funding']
        self.assertEqual(len(funding), 1)
        self.assertEqual(funding[0]['@type'], 'Grant')
        self.assertEqual(funding[0]['identifier'], 'NSF-12345')
        self.assertEqual(funding[0]['name'], 'Test Award')
        self.assertEqual(funding[0]['funder']['name'], 'National Science Foundation')
        self.assertEqual(funding[0]['funder']['identifier'], 'https://nsf.gov')

    # ------------------------------------------------------------------
    # encodingFormat / distribution / subjectOf / provider
    # ------------------------------------------------------------------

    def test_encoding_format_absent_without_files(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertNotIn('encodingFormat', schemaorg)

    def test_encoding_format_present(self):
        self.resource.metadata.create_element('format', value='text/csv')
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['encodingFormat'], ['text/csv'])

    def test_provider_and_catalog_static_blocks(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertEqual(schemaorg['provider']['name'], 'HydroShare')
        self.assertEqual(schemaorg['includedInDataCatalog']['name'], 'HydroShare')

    def test_subject_of_uses_short_id(self):
        schemaorg = self.resource.get_schemaorg_dict()
        self.assertIn(self.resource.short_id, schemaorg['subjectOf']['url'])

    def test_distribution_unpublished_identifier(self):
        schemaorg = self.resource.get_schemaorg_dict()
        distribution = schemaorg['distribution']
        self.assertEqual(
            distribution['identifier'],
            [f'https://www.hydroshare.org/resource/{self.resource.short_id}'])
        self.assertEqual(distribution['contentSize'], '0\xa0bytes')

    def test_distribution_published_identifier_includes_md5(self):
        self.resource.bag_checksum = 'abc123checksum'
        self.resource.save()
        self.resource.set_published(True)
        self.resource.metadata.create_element(
            'date', type='published', start_date=self.resource.updated)

        schemaorg = self.resource.get_schemaorg_dict()
        distribution = schemaorg['distribution']
        identifiers = distribution['identifier']
        self.assertEqual(len(identifiers), 2)
        md5_entry = identifiers[1]
        self.assertEqual(md5_entry['propertyID'], 'MD5')
        self.assertEqual(md5_entry['value'], 'abc123checksum')
        self.assertEqual(md5_entry['identifier'], 'md5:abc123checksum')

    # ------------------------------------------------------------------
    # page processor wiring
    # ------------------------------------------------------------------

    def _build_request(self):
        request = RequestFactory().get('/')
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        request.user = self.user
        return request

    def test_page_context_includes_schemaorg_json(self):
        # get_page_context is the single dispatcher used by every resource type's page
        # processor; both edit and readonly branches should get the schemaorg_json key.
        for resource_edit in (False, True):
            with self.subTest(resource_edit=resource_edit):
                context = page_processors.get_page_context(
                    self.resource, self.user, resource_edit=resource_edit,
                    request=self._build_request(), content_model=self.resource)
                self.assertEqual(context['schemaorg_json'], self.resource.get_schemaorg_dict())
