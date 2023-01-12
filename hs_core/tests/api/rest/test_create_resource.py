import json
import time
from unittest import skip

from dateutil import parser
from django.test import override_settings
from rest_framework import status

from hs_core.hydroshare.utils import get_resource_by_shortkey
from .base import HSRESTTestCase


class TestCreateResource(HSRESTTestCase):
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_UPLIFTED_post_resource_get_sysmeta(self):
        rtype = 'CompositeResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif', 'rb'),
                           'image/tiff')}
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content.decode())
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # Get the resource system metadata to make sure the resource was
        # properly created.
        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content.decode())
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        # Get resource bag
        response = self.getResourceBag(res_id)
        if response['Content-Type'] == 'application/json':
            content = json.loads(response.content.decode())
            if content['status'] != "Completed":
                # wait for 10 seconds to give task a chance to run and finish
                time.sleep(10)
                task_id = content['id']
                status_response = self.getDownloadTaskStatus(task_id)
                status_content = json.loads(status_response.content.decode())
                if status_content['status']:
                    # bag creation task succeeds, get bag again
                    response = self.getResourceBag(res_id)
                    self.assertEqual(response['Content-Type'], 'application/zip')
                    self.assertGreater(int(response['Content-Length']), 0)
        else:
            self.assertEqual(response['Content-Type'], 'application/zip')
            self.assertGreater(int(response['Content-Length']), 0)

    def test_post_resource_get_sysmeta(self):
        rtype = 'CompositeResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif', 'rb'),
                           'image/tiff')}
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content.decode())
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # Get the resource system metadata to make sure the resource was
        # properly created.
        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content.decode())
        # generic has been deprecated and now defaults to Composite (#2575)
        self.assertEqual(content['resource_type'], "CompositeResource")
        self.assertEqual(content['resource_title'], title)
        # Get resource bag
        response = self.getResourceBag(res_id)
        if response['Content-Type'] == 'application/json':
            content = json.loads(response.content.decode())
            if content['status'] != "Completed":
                # wait for 10 seconds to give task a chance to run and finish
                time.sleep(10)
                task_id = content['id']
                status_response = self.getDownloadTaskStatus(task_id)
                status_content = json.loads(status_response.content.decode())
                if status_content['status']:
                    # bag creation task succeeds, get bag again
                    response = self.getResourceBag(res_id)
                    self.assertEqual(response['Content-Type'], 'application/zip')
                    self.assertGreater(int(response['Content-Length']), 0)
        else:
            self.assertEqual(response['Content-Type'], 'application/zip')
            self.assertGreater(int(response['Content-Length']), 0)

    @skip("TODO: was not running before python3 upgrade")
    def test_resource_create_with_core_metadata(self):
        """
        The followings are the core metadata elements that can be passed as part of the
        'metadata' parameter when creating a resource:

        coverage
        creator
        contributor
        source,
        relation,
        geospatialrelation,
        identifier,
        fundingagency

        """
        rtype = 'CompositeResource'
        title = 'My Test resource'
        metadata = []
        metadata.append({'coverage': {'type': 'period', 'value': {'start': '01/01/2000',
                                                                  'end': '12/12/2010'}}})
        statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
        url = 'http://creativecommons.org/licenses/by/4.0/'
        metadata.append({'rights': {'statement': statement, 'url': url}})
        metadata.append({'language': {'code': 'fre'}})

        # contributor
        con_name = 'Mike Sundar'
        con_org = "USU"
        con_email = 'mike.sundar@usu.edu'
        con_address = "11 River Drive, Logan UT-84321, USA"
        con_phone = '435-567-0989'
        con_homepage = 'http://usu.edu/homepage/001'
        con_identifiers = {'ORCID': 'https://orcid.org/mike_s',
                           'ResearchGateID': 'https://www.researchgate.net/mike_s'}
        metadata.append({'contributor': {'name': con_name,
                                         'organization': con_org, 'email': con_email,
                                         'address': con_address, 'phone': con_phone,
                                         'homepage': con_homepage,
                                         'identifiers': con_identifiers}})

        # creator
        cr_name = 'John Smith'
        cr_org = "USU"
        cr_email = 'jsmith@gmail.com'
        cr_address = "101 Clarson Ave, Provo UT-84321, USA"
        cr_phone = '801-567=9090'
        cr_homepage = 'http://byu.edu/homepage/002'
        cr_identifiers = {'ORCID': 'https://orcid.org/john_smith',
                          'ResearchGateID': 'https://www.researchgate.net/john_smith'}
        metadata.append({'creator': {'name': cr_name, 'organization': cr_org,
                                     'email': cr_email, 'address': cr_address,
                                     'phone': cr_phone, 'homepage': cr_homepage,
                                     'identifiers': cr_identifiers}})

        # relation
        metadata.append({'relation': {'type': 'isPartOf',
                                      'value': 'http://hydroshare.org/resource/001'}})

        # geospatialrelation
        metadata.append({'geospatialrelation': {'type': 'relation',
                                                'value': 'https://geoconnex.us/ref/dams/1083460',
                                                'text': 'Bonnie Meade [dams/1083460]'}})

        # identifier
        metadata.append({'identifier': {'name': 'someIdentifier', 'url': 'http://some.org/001'}})

        # fundingagency
        agency_name = 'NSF'
        award_title = "Cyber Infrastructure"
        award_number = "NSF-101-20-6789"
        agency_url = "http://www.nsf.gov"
        metadata.append({'fundingagency': {'agency_name': agency_name, 'award_title': award_title,
                                           'award_number': award_number, 'agency_url': agency_url}})
        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif', 'rb'),
                           'image/tiff')}
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content.decode())
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)
        self.assertEqual(resource.metadata.coverages.all().count(), 1)
        self.assertEqual(resource.metadata.coverages.filter(type='period').count(), 1)
        coverage = resource.metadata.coverages.all().first()
        self.assertEqual(parser.parse(coverage.value['start']).date(),
                         parser.parse('01/01/2000').date())
        self.assertEqual(parser.parse(coverage.value['end']).date(),
                         parser.parse('12/12/2010').date())
        self.assertEqual(resource.metadata.rights.statement, statement)
        self.assertEqual(resource.metadata.rights.url, url)
        self.assertEqual(resource.metadata.language.code, 'fre')

        # there should be 1 contributor
        self.assertEqual(resource.metadata.contributors.all().count(), 1)
        contributor = resource.metadata.contributors.all().first()
        self.assertEqual(contributor.name, con_name)
        self.assertEqual(contributor.organization, con_org)
        self.assertEqual(contributor.email, con_email)
        self.assertEqual(contributor.address, con_address)
        self.assertEqual(contributor.phone, con_phone)
        self.assertEqual(contributor.homepage, con_homepage)

        # there should be 1 creator (based on the metadata we provided for one creator)
        # system automatically adds the user who creates the resource as the creator
        # only in the case where not metadata for creator is provided.
        self.assertEqual(resource.metadata.creators.all().count(), 1)
        creator = resource.metadata.creators.filter(name=cr_name).first()
        self.assertEqual(creator.name, cr_name)
        self.assertEqual(creator.organization, cr_org)
        self.assertEqual(creator.email, cr_email)
        self.assertEqual(creator.address, cr_address)
        self.assertEqual(creator.phone, cr_phone)
        self.assertEqual(creator.homepage, cr_homepage)

        # there should be 1 relation element
        self.assertEqual(resource.metadata.relations.all().count(), 1)
        relation = resource.metadata.relations.all().first()
        self.assertEqual(relation.type, 'isPartOf')
        self.assertEqual(relation.value, 'http://hydroshare.org/resource/001')

        # there should be 1 geospatialrelation element
        self.assertEqual(resource.metadata.geospatialrelations.all().count(), 1)
        geospatialrelation = resource.metadata.geospatialrelations.all().first()
        self.assertEqual(geospatialrelation.type, 'relation')
        self.assertEqual(geospatialrelation.value, 'https://geoconnex.us/ref/dams/1083460')
        self.assertEqual(geospatialrelation.text, 'Bonnie Meade [dams/1083460]')

        # there should be 2 identifiers
        self.assertEqual(resource.metadata.identifiers.all().count(), 2)
        identifier = resource.metadata.identifiers.filter(name='someIdentifier').first()
        self.assertEqual(identifier.url, 'http://some.org/001')

        # there should be 1 fundingagency
        self.assertEqual(resource.metadata.funding_agencies.all().count(), 1)
        agency = resource.metadata.funding_agencies.all().first()
        self.assertEqual(agency.agency_name, agency_name)
        self.assertEqual(agency.award_title, award_title)
        self.assertEqual(agency.award_number, award_number)
        self.assertEqual(agency.agency_url, agency_url)

        self.resources_to_delete.append(res_id)

    def test_resource_create_with_core_and_extra_metadata(self):

        rtype = 'CompositeResource'
        title = 'My Test resource'
        metadata = []
        metadata.append({'coverage': {'type': 'period', 'value': {'start': '01/01/2000',
                                                                  'end': '12/12/2010'}}})
        extra_metadata = {'latitude': '40', 'longitude': '-110'}

        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  'extra_metadata': json.dumps(extra_metadata)}

        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # test core metadata
        content = json.loads(response.content.decode())
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)
        self.assertEqual(resource.metadata.coverages.all().count(), 1)
        self.assertEqual(resource.metadata.coverages.filter(type='period').count(), 1)
        coverage = resource.metadata.coverages.all().first()
        self.assertEqual(parser.parse(coverage.value['start']).date(),
                         parser.parse('01/01/2000').date())
        self.assertEqual(parser.parse(coverage.value['end']).date(),
                         parser.parse('12/12/2010').date())

        # test extra metadata
        self.assertEqual(resource.extra_metadata.get('latitude'), '40')
        self.assertEqual(resource.extra_metadata.get('longitude'), '-110')

        self.resources_to_delete.append(res_id)

    def test_resource_create_with_extra_metadata(self):
        rtype = 'CompositeResource'
        title = 'My Test resource'
        extra_metadata = {'latitude': '40', 'longitude': '-110'}

        params = {'resource_type': rtype,
                  'title': title,
                  'extra_metadata': json.dumps(extra_metadata)}

        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content.decode())
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)

        # test extra metadata
        self.assertEqual(resource.extra_metadata.get('latitude'), '40')
        self.assertEqual(resource.extra_metadata.get('longitude'), '-110')

        self.resources_to_delete.append(res_id)

    def test_create_resource_not_allowed_valid_metadata_elements(self):
        """
        This is to test that the following core valid metadata elements can't be passed using the
        'metadata' parameter

        title
        description (abstract)
        subject (keyword)
        format
        date
        publisher
        type

        :return:
        """

        rtype = 'CompositeResource'
        title = 'My Test resource'
        # test title
        metadata = []
        metadata.append({'title': {'value': "This is a resource"}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test description
        metadata = []
        metadata.append({'description': {'abstract': "This is a great resource"}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test subject
        metadata = []
        metadata.append({'subject': {'value': "sample"}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test format
        metadata = []
        metadata.append({'format': {'value': 'text/csv'}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test date
        metadata = []
        metadata.append({'date': {'type': 'created', 'start_date': '01/01/2016'}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        metadata = []
        metadata.append({'date': {'type': 'modified', 'start_date': '01/01/2016'}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test publisher
        metadata = []
        metadata.append({'publisher': {'name': 'USGS', 'url': 'http://usgs.gov'}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

        # test type
        metadata = []
        metadata.append({'type': {'url': "http://hydroshare.org/composite"}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

    def _get_params(self, rtype, title, metadata):
        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif', 'rb'),
                           'image/tiff')}
        return params

    def _test_not_allowed_element(self, params):
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
