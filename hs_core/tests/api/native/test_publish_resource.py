import difflib
import unittest

import arrow
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestPublishResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestPublishResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'Test Resource'
        )

    def tearDown(self):
        super(TestPublishResource, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()

    # TODO: This test needs to be enabled once the publish_resource() function is updated to register resource DOI
    # with crossref. At that point the call to crossref needs to be mocked here in this test (IMPORTANT)
    @unittest.skip
    def test_publish_resource(self):
        # check status prior to publishing the resource
        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertFalse(
            self.res.doi,
            msg='doi is assigned'
        )

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        # publish resource - this is the api we are testing
        hydroshare.publish_resource(self.res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.raccess.published,
            msg='The resource is not published'
        )

        # test frozen state
        self.assertTrue(
            self.pub_res.raccess.immutable,
            msg='The resource is not frozen'
        )

        # test if doi is assigned
        self.assertTrue(
            self.pub_res.doi,
            msg='No doi is assigned with the published resource.'
        )

        # there should now published date type metadata element
        self.assertTrue(self.pub_res.metadata.dates.filter(type='published').exists())

    def test_crossref_deposit_xml(self):
        """Test that the crossref deposit xml is generated correctly for a resource"""

        # create abstract metadata element
        self.res.metadata.create_element('description', abstract='This is a test abstract')
        # add an organization as an author
        self.res.metadata.create_element('creator', organization='Utah State University')
        # add a person with ORCID identifier as an author
        identifiers = {"ORCID": 'https://orcid.org/0000-0002-1825-0097'}
        self.res.metadata.create_element('creator', name='John Smith', identifiers=identifiers)
        # add a funder
        self.res.metadata.create_element('fundingagency', agency_name='National Science Foundation',
                                         award_title='NSF Award', award_number='12345', agency_url='https://nsf.gov')
        # generate crossref deposit xml in debug mode
        settings.DEBUG = True
        crossref_xml = self.res.get_crossref_deposit_xml()
        # turn off debug mode - the default mode is False by Django during testing
        settings.DEBUG = False
        crossref_xml = crossref_xml.strip()
        timestamp = arrow.get(self.res.updated).format("YYYYMMDDHHmmss")
        res_id = self.res.short_id
        created_date = self.res.created
        updated_date = self.res.updated
        # use updated date as published date as we don't have a published date for this test resource
        # also when we do real publication the publication date is the same as updated date at the time of publication
        published_date = updated_date
        site_url = hydroshare.utils.current_site_url()
        expected_xml = self._get_expected_crossref_xml(res_id=res_id, timestamp=timestamp,
                                                       created_date=created_date, updated_date=updated_date,
                                                       published_date=published_date, site_url=site_url)
        expected_xml = expected_xml.strip()
        self.assertTrue(len(crossref_xml) == len(expected_xml))
        match_ratio = difflib.SequenceMatcher(None, crossref_xml.splitlines(), expected_xml.splitlines()).ratio()
        self.assertTrue(match_ratio == 1.0, msg="crossref xml is not as expected")

    @staticmethod
    def _get_expected_crossref_xml(res_id, timestamp, created_date, updated_date, published_date, site_url):
        expected_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<doi_batch xmlns="http://www.crossref.org/schema/5.3.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:fr="http://www.crossref.org/fundref.xsd" xmlns:ai="http://www.crossref.org/AccessIndicators.xsd" version="5.3.1" xsi:schemaLocation="http://www.crossref.org/schema/5.3.1 http://www.crossref.org/schemas/crossref5.3.1.xsd">
  <head>
    <doi_batch_id>{res_id}</doi_batch_id>
    <timestamp>{timestamp}</timestamp>
    <depositor>
      <depositor_name>HydroShare</depositor_name>
      <email_address>help@cuahsi.org</email_address>
    </depositor>
    <registrant>Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)</registrant>
  </head>
  <body>
    <database>
      <database_metadata language="en">
        <titles>
          <title>HydroShare Resources</title>
        </titles>
      </database_metadata>
      <dataset dataset_type="record">
        <contributors>
          <person_name contributor_role="author" sequence="first">
            <given_name>Creator_FirstName</given_name>
            <surname>Creator_LastName</surname>
          </person_name>
          <organization contributor_role="author" sequence="additional">Utah State University</organization>
          <person_name contributor_role="author" sequence="additional">
            <given_name>John</given_name>
            <surname>Smith</surname>
            <ORCID>https://orcid.org/0000-0002-1825-0097</ORCID>
          </person_name>
        </contributors>
        <titles>
          <title>Test Resource</title>
        </titles>
        <database_date>
          <creation_date>
            <month>{created_date.month}</month>
            <day>{created_date.day}</day>
            <year>{created_date.year}</year>
          </creation_date>
          <publication_date>
            <month>{published_date.month}</month>
            <day>{published_date.day}</day>
            <year>{published_date.year}</year>
          </publication_date>
          <update_date>
            <month>{updated_date.month}</month>
            <day>{updated_date.day}</day>
            <year>{updated_date.year}</year>
          </update_date>
        </database_date>
        <description>This is a test abstract</description>
        <fr:program name="fundref">
          <fr:assertion name="fundgroup">
            <fr:assertion name="funder_name">National Science Foundation<fr:assertion name="funder_identifier">https://nsf.gov</fr:assertion></fr:assertion>
            <fr:assertion name="award_number">12345</fr:assertion>
          </fr:assertion>
        </fr:program>
        <ai:program name="AccessIndicators">
          <ai:license_ref applies_to="vor" start_date="{published_date.strftime("%Y-%m-%d")}">http://creativecommons.org/licenses/by/4.0/</ai:license_ref>
        </ai:program>
        <doi_data>
          <doi>10.4211/hs.{res_id}</doi>
          <resource>{site_url}/resource/{res_id}</resource>
        </doi_data>
      </dataset>
    </database>
  </body>
</doi_batch>"""
        return expected_xml
