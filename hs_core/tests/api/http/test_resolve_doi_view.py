__author__ = 'shaunjl'

"""
Tastypie REST API tests for ResolveDOI(View)

"""
from tastypie.test import ResourceTestCase, TestApiClient
from django.contrib.auth.models import User
from hs_core import hydroshare
from tastypie.serializers import Serializer

class TestResolveDOIView(ResourceTestCase):

    serializer = Serializer()

    def setUp(self):
        self.api_client = TestApiClient()
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username='user0',
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )

        self.res = hydroshare.create_resource('GenericResource', user, 'myres')
        hydroshare.publish_resource(self.res.short_id)

    def tearDown(self):
        User.objects.all().delete()
        hydroshare.delete_resource(self.res.short_id)

    def test_get(self):

        url = 'hsapi/resolveDOI/{0}/'.format(self.res.doi)
        resp = self.api_client.get(url)

        self.assertValidJSONResponse(resp)

        resp_pk = self.deserialize(resp)

        self.assertEqual(self.res.short_id, resp_pk)

    def test_bad_doi(self):

        url = 'hsapi/resolveDOI/{0}/'.format('bad_doi')
        resp = self.api_client.get(url)

        self.assertEqual(resp.status_code, 404)
