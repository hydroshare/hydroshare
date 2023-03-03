import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group, User
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import rep_res_bag_to_irods_user_zone
from hs_core.testing import TestCaseCommonUtilities


class TestReplicateBagToUserZone(TestCaseCommonUtilities, TestCase):
    def setUp(self):
        super(TestReplicateBagToUserZone, self).setUp()
        super(TestReplicateBagToUserZone, self).assert_federated_irods_available()

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
        super(TestReplicateBagToUserZone, self).create_irods_user_in_user_zone()

        self.gen_res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Resource Key/Value Metadata Testing'
        )

        self.factory = RequestFactory()

    def tearDown(self):
        super(TestReplicateBagToUserZone, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.gen_res.delete()

    def test_replicate_bag(self):
        # here we are testing rep_res_bag_to_irods_user_zone view function
        super(TestReplicateBagToUserZone, self).assert_federated_irods_available()

        url_params = {'shortkey': self.gen_res.short_id}
        url = reverse('replicate_bag_user_zone', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = rep_res_bag_to_irods_user_zone(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content.decode())
        self.assertIn('resource copy to user zone', response_data.values())
        # clean up
        hydroshare.delete_resource(self.gen_res.short_id)
