import json

from rest_framework import status

from hs_core.hydroshare.utils import get_resource_by_shortkey
from .base import HSRESTTestCase


class TestCreateResource(HSRESTTestCase):

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
        sysmeta_url = "/hsapi/sysmeta/{res_id}/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)

        # Get resource bag
        response = self.getResourceBag(res_id)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertTrue(int(response['Content-Length']) > 0)

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
        metadata.append({'contributor': {'name': con_name,
                                         'organization': con_org, 'email': con_email,
                                         'address': con_address, 'phone': con_phone,
                                         'homepage': con_homepage}})

        # creator
        cr_name = 'John Smith'
        cr_org = "USU"
        cr_email = 'jsmith@gmail.com'
        cr_address = "101 Clarson Ave, Provo UT-84321, USA"
        cr_phone = '801-567=9090'
        cr_homepage = 'http://byu.edu/homepage/002'
        metadata.append({'creator': {'name': cr_name, 'organization': cr_org,
                                     'email': cr_email, 'address': cr_address,
                                     'phone': cr_phone, 'homepage': cr_homepage}})

        # relation
        metadata.append({'relation': {'type': 'isPartOf',
                                      'value': 'http://hydroshare.org/resource/001'}})
        # source
        metadata.append({'source': {'derived_from': 'http://hydroshare.org/resource/0001'}})

        # identifier
        metadata.append({'identifier': {'name': 'someIdentifier', 'url': 'http://some.org/001'}})

        # fundingagency
        agency_name = 'NSF'
        award_title="Cyber Infrastructure"
        award_number="NSF-101-20-6789"
        agency_url="http://www.nsf.gov"
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

        # there should be 2 creators
        self.assertEqual(resource.metadata.creators.all().count(), 2)
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

