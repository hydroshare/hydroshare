import json
import requests
from dateutil import parser
import time
from unittest import skip

from django.test import override_settings
from rest_framework import status

from hs_core.hydroshare.utils import get_resource_by_shortkey
from .base import HSRESTTestCase


class TestCreateResource(HSRESTTestCase):
    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_UPLIFTED_post_resource_get_sysmeta(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # Get the resource system metadata to make sure the resource was
        # properly created.
        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        # Get resource bag
        response = self.getResourceBag(res_id)
        if response['Content-Type'] == 'application/json':
            content = json.loads(response.content)
            if content['bag_status'] == "Not ready":
                # wait for 10 seconds to give task a chance to run and finish
                time.sleep(10)
                task_id = content['task_id']
                status_response = self.getDownloadTaskStatus(task_id)
                status_content = json.loads(status_response.content)
                if status_content['status']:
                    # bag creation task succeeds, get bag again
                    response = self.getResourceBag(res_id)
                    self.assertEqual(response['Content-Type'], 'application/zip')
                    self.assertGreater(int(response['Content-Length']), 0)
        else:
            self.assertEqual(response['Content-Type'], 'application/zip')
            self.assertGreater(int(response['Content-Length']), 0)

    def test_post_resource_get_sysmeta(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # Get the resource system metadata to make sure the resource was
        # properly created.
        sysmeta_url = "/hsapi/resource/{res_id}/sysmeta/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        # Get resource bag
        response = self.getResourceBag(res_id)
        if response['Content-Type'] == 'application/json':
            content = json.loads(response.content)
            if content['bag_status'] == "Not ready":
                # wait for 10 seconds to give task a chance to run and finish
                time.sleep(10)
                task_id = content['task_id']
                status_response = self.getDownloadTaskStatus(task_id)
                status_content = json.loads(status_response.content)
                if status_content['status']:
                    # bag creation task succeeds, get bag again
                    response = self.getResourceBag(res_id)
                    self.assertEqual(response['Content-Type'], 'application/zip')
                    self.assertGreater(int(response['Content-Length']), 0)
        else:
            self.assertEqual(response['Content-Type'], 'application/zip')
            self.assertGreater(int(response['Content-Length']), 0)

    def test_resource_create_with_core_metadata(self):
        """
        The followings are the core metadata elements that can be passed as part of the
        'metadata' parameter when creating a resource:

        coverage
        creator
        contributor
        source,
        relation,
        identifier,
        fundingagency

        """
        rtype = 'GenericResource'
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
        # source
        metadata.append({'source': {'derived_from': 'http://hydroshare.org/resource/0001'}})

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
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
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

        # there should be 1 source element
        self.assertEqual(resource.metadata.sources.all().count(), 1)
        source = resource.metadata.sources.all().first()
        self.assertEqual(source.derived_from, 'http://hydroshare.org/resource/0001')

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

    def test_resource_create_with_extended_metadata(self):
        """
        The followings are the extended metadata elements for the NetCDF resource that can be
        passed as part of the 'metadata' parameter when creating a resource:

        originalcoverage
        variable

        """
        rtype = 'NetcdfResource'
        title = 'My Test resource'
        metadata = []
        # originalcover
        value = {"northlimit": 12, "projection": "transverse_mercator", "units": "meter",
                 "southlimit": 10, "eastlimit": 23, "westlimit": 2}

        metadata.append({'originalcoverage': {'value': value,
                                              'projection_string_text': '+proj=tmerc +lon_0=-111.0 '
                                                                        '+lat_0=0.0 +x_0=500000.0 '
                                                                        '+y_0=0.0 +k_0=0.9996',
                                              'projection_string_type': 'Proj4 String'}})

        # variable (this element is defined in multiple resource types including
        # NetcdfResource type)
        var_name = 'SWE'
        var_type = 'Float'
        var_shape = 'y,x,time'
        var_unit = 'm'
        var_missing_value = '-9999'
        var_des_name = 'Snow water equivalent'
        var_method = 'model simulation of UEB'
        metadata.append({'variable': {'name': var_name, 'type': var_type, 'shape': var_shape,
                                      'unit': var_unit, 'missing_value': var_missing_value,
                                      'descriptive_name': var_des_name, 'method': var_method}})
        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  }
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)

        # there should be 1 originalcoverage element
        self.assertEqual(resource.metadata.ori_coverage.all().count(), 1)
        ori_coverage = resource.metadata.ori_coverage.all().first()
        self.assertEquals(ori_coverage.value, value)
        self.assertEquals(ori_coverage.projection_string_text, '+proj=tmerc +lon_0=-111.0 '
                                                               '+lat_0=0.0 +x_0=500000.0 '
                                                               '+y_0=0.0 +k_0=0.9996')
        self.assertEquals(ori_coverage.projection_string_type, 'Proj4 String')

        # there should be 1 variable element
        self.assertEqual(resource.metadata.variables.all().count(), 1)
        variable = resource.metadata.variables.all().first()
        self.assertEqual(variable.name, var_name)
        self.assertEqual(variable.type, var_type)
        self.assertEqual(variable.shape, var_shape)
        self.assertEqual(variable.unit, var_unit)
        self.assertEqual(variable.missing_value, var_missing_value)
        self.assertEqual(variable.descriptive_name, var_des_name)
        self.assertEqual(variable.method, var_method)

        self.resources_to_delete.append(res_id)

    def test_resource_create_with_core_and_extra_metadata(self):

        rtype = 'GenericResource'
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
        content = json.loads(response.content)
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
        self.assertEquals(resource.extra_metadata.get('latitude'), '40')
        self.assertEquals(resource.extra_metadata.get('longitude'), '-110')

        self.resources_to_delete.append(res_id)

    def test_resource_create_with_extra_metadata(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        extra_metadata = {'latitude': '40', 'longitude': '-110'}

        params = {'resource_type': rtype,
                  'title': title,
                  'extra_metadata': json.dumps(extra_metadata)}

        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)

        # test extra metadata
        self.assertEquals(resource.extra_metadata.get('latitude'), '40')
        self.assertEquals(resource.extra_metadata.get('longitude'), '-110')

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

        rtype = 'GenericResource'
        title = 'My Test resource'
        # test title
        metadata = []
        metadata.append({'title': {'value': "This is a generic resource"}})
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
        metadata.append({'type': {'url': "http://hydroshare.org/generic"}})
        params = self._get_params(rtype, title, metadata)
        self._test_not_allowed_element(params)

    def _get_params(self, rtype, title, metadata):
        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        return params

    def _test_not_allowed_element(self, params):
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @skip("skip this test until we find out how to mock it up")
    def test_refts_creation_via_rest_api(self):

        rtype = 'RefTimeSeriesResource'
        title = 'My Test RefTS res'

        ref_url = "http://data.iutahepscor.org/LoganRiverWOF/REST/waterml_1_1.svc/datavalues?" \
                  "location=iutah:LR_WaterLab_AA&variable=iutah:WaterTemp_EXO&" \
                  "startDate=2014-12-02T19:45:00Z&endDate=2014-12-05T19:45:00Z"
        ref_type = "rest"

        # test the "ref_url" rest endpoint is up
        response = requests.get(ref_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        metadata = []
        # add core metadata
        metadata.append({'relation': {'type': 'isPartOf',
                                      'value': 'http://hydroshare.org/resource/001'}})
        # add refts-specific metadata
        metadata.append({"referenceurl":
                        {"value": ref_url,
                         "type": ref_type}})

        # post to rest api
        params = {'resource_type': rtype,
                  'title': title,
                  'metadata': json.dumps(metadata),
                  }
        rest_url = '/hsapi/resource/'
        response = self.client.post(rest_url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        resource = get_resource_by_shortkey(res_id)

        # test core metadata
        self.assertEqual(resource.metadata.relations.all().count(), 1)
        relation = resource.metadata.relations.all().first()
        self.assertEqual(relation.type, 'isPartOf')
        self.assertEqual(relation.value, 'http://hydroshare.org/resource/001')

        # test resource-specific metadata
        self.assertEqual(resource.resource_type.lower(), "reftimeseriesresource")

        self.assertEqual(resource.metadata.referenceURLs.all().count(), 1)
        referenceURLs = resource.metadata.referenceURLs.all().first()
        self.assertEquals(referenceURLs.value, ref_url)
        self.assertEquals(referenceURLs.type, ref_type)

        self.assertEqual(resource.metadata.sites.all().count(), 1)
        sites = resource.metadata.sites.all().first()
        self.assertEquals(sites.code, "LR_WaterLab_AA")

        self.assertEqual(resource.metadata.variables.all().count(), 1)
        variables = resource.metadata.variables.all().first()
        self.assertEquals(variables.code, "WaterTemp_EXO")

        self.resources_to_delete.append(res_id)
