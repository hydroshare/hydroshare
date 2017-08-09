from rest_framework import status

from django.contrib.auth.models import Group

from hs_core import hydroshare
from .base import HSRESTTestCase
from hs_core.testing import TestCaseCommonUtilities


class TestReplicateBagToUserZoneREST(HSRESTTestCase, TestCaseCommonUtilities):
    def setUp(self):
        super(TestReplicateBagToUserZoneREST, self).setUp()
        if not super(TestReplicateBagToUserZoneREST, self).is_federated_irods_available():
            return

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        # create corresponding irods account in user zone
        super(TestReplicateBagToUserZoneREST, self).create_irods_user_in_user_zone()

        self.gen_res = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic Resource Key/Value Metadata Testing'
        )

        print(self.gen_res)
        self.pid = self.gen_res.short_id

    def test_replicate_public_endpoint(self):
        replicate_url = "/hsapi/resource/%s/functions/rep-res-bag-to-irods-user-zone/" % \
                        self.gen_res.short_id
        response = self.client.post(replicate_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
