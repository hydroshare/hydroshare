import os
import shutil
import json
from mock import patch

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.http import int_to_base36

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import create_user_group, update_user_group, share_group_with_user, unshare_group_with_user, \
    make_group_membership_request, act_on_group_membership_request, share_resource_with_group, \
    unshare_resource_with_group, delete_user_group, restore_user_group
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase
from hs_access_control.models import PrivilegeCodes
from theme.backends import without_login_date_token_generator


class TestGroup(MockIRODSTestCaseMixin, ViewTestCase):

    def setUp(self):
        super(TestGroup, self).setUp()
        patcher_email_send_call = patch('hs_core.views.send_action_to_take_email')
        patcher_email_send_call.start()
        self.addCleanup(patcher_email_send_call.stop)

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )
        self.mike = hydroshare.create_account(
            'mike@gmail.com',
            username='mike',
            first_name='Mike',
            last_name='Jensen',
            superuser=False,
            groups=[]
        )

        # create a resource for sharing with group
        self.resource = hydroshare.create_resource(resource_type='CompositeResource',
                                                   owner=self.john,
                                                   title='Test Resource',
                                                   metadata=[]
                                                   )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestGroup, self).tearDown()

    def test_create_group(self):
        # TODO: test with picture file upload for the group
        url = reverse('create_user_group')
        # test passing privacy_level = 'public'
        grp_data = {'name': 'Test Group-1', 'description': 'This is a cool group-1', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        response = create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-1').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-1')
        self.assertEqual(new_group.gaccess.public, True)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], reverse('group', args=[new_group.id]))

        # test passing privacy_level = 'private'
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2', 'privacy_level': 'private'}
        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.public, False)
        self.assertEqual(new_group.gaccess.discoverable, False)

        # test passing privacy_level = 'discoverable'
        grp_data = {'name': 'Test Group-3', 'description': 'This is a cool group-3', 'privacy_level': 'discoverable'}
        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-3').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-3')
        self.assertEqual(new_group.gaccess.public, False)
        self.assertEqual(new_group.gaccess.discoverable, True)

    def test_group_create_failures(self):
        # test that post data for 'name' and 'description' are required
        # for creating a group. Also post data must have a key 'privacy_level'
        # with one of these values ('public', 'private', 'discoverable'). Duplicate group names are
        # not allowed

        # at this point there should be only one group
        self.assertEqual(Group.objects.count(), 1)
        url = reverse('create_user_group')
        # test 'name' is required
        grp_data = {'description': 'This is a cool group', 'privacy_level': 'public'}

        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        new_group = Group.objects.filter(gaccess__description='This is a cool group').first()
        self.assertEqual(new_group, None)
        # at this point there should be only one group
        self.assertEqual(Group.objects.count(), 1)

        # test 'description' is required
        grp_data = {'name': 'Test Group', 'privacy_level': 'public'}

        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        new_group = Group.objects.filter(name='Test Group').first()
        self.assertEqual(new_group, None)
        # at this point there should be only one group
        self.assertEqual(Group.objects.count(), 1)

        # test 'privacy_level' is required
        grp_data = {'name': 'Test Group', 'description': 'This is a cool group'}

        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        new_group = Group.objects.filter(name='Test Group').first()
        self.assertEqual(new_group, None)
        # at this point there should be only one group
        self.assertEqual(Group.objects.count(), 1)

        # test 'privacy_level' should have one of these values (public, private, discoverable)
        grp_data = {'name': 'Test Group', 'description': 'This is a cool group', 'privacy_level': 'some-level'}

        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        new_group = Group.objects.filter(name='Test Group').first()
        self.assertEqual(new_group, None)
        # at this point there should be only one group
        self.assertEqual(Group.objects.count(), 1)

        # test that duplicate group names are not allowed
        grp_data = {'name': 'Test Group', 'description': 'This is a cool group', 'privacy_level': 'private'}
        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # at this point there should be 2 groups
        self.assertEqual(Group.objects.count(), 2)

        # create a group with duplicate name
        grp_data = {'name': 'Test Group', 'description': 'This is a very cool group', 'privacy_level': 'private'}
        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)

        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        # had to do this as a transaction for some reason, otherwise the last statement
        # of this function generates a transaction error
        with transaction.atomic():
            response = create_user_group(request)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
            # at this point there should be still 2 groups
        self.assertEqual(Group.objects.count(), 2)

    def test_update_group(self):
        # TODO: test with picture file upload for the group

        # first create a group to test updating group
        url = reverse('create_user_group')
        grp_data = {'name': 'Test Group-1', 'description': 'This is a cool group-1',
                    'purpose': 'This group has no purpose', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        response = create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-1').first()
        self.assertEqual(new_group.gaccess.active, True)
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-1')
        self.assertEqual(new_group.gaccess.purpose, 'This group has no purpose')
        self.assertEqual(new_group.gaccess.public, True)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(new_group.gaccess.active, True)
        self.assertEqual(new_group.gaccess.shareable, True)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], reverse('group', args=[new_group.id]))

        # now test updating new_group
        url_params = {'group_id': new_group.id}
        url = reverse('update_user_group', kwargs=url_params)
        # update name, description, purpose
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2',
                    'purpose': 'This group now has purpose', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.purpose, 'This group now has purpose')
        self.assertEqual(new_group.gaccess.public, True)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # update group to remove purpose
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2',
                    'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.purpose, '')
        self.assertEqual(new_group.gaccess.public, True)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # update privacy_level (set to private)- this set public to false and discoverable to false
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2',
                    'privacy_level': 'private'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.purpose, '')
        self.assertEqual(new_group.gaccess.public, False)
        self.assertEqual(new_group.gaccess.discoverable, False)
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # update privacy_level (set to public) - this set public to true and discoverable to true
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2',
                    'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.purpose, '')
        self.assertEqual(new_group.gaccess.public, True)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # update privacy_level (set to discoverable) - this should set discoverable to
        # true and public to false
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group-2',
                    'privacy_level': 'discoverable'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-2').first()
        self.assertNotEqual(new_group, None)
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.purpose, '')
        self.assertEqual(new_group.gaccess.public, False)
        self.assertEqual(new_group.gaccess.discoverable, True)
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def test_delete_restore_group(self):
        # test a group can be deleted or restored

        # first create a group to test updating group
        url = reverse('create_user_group')
        grp_data = {'name': 'Test Group-1', 'description': 'This is a cool group-1',
                    'purpose': 'This group has no purpose', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-1').first()
        self.assertEqual(new_group.gaccess.active, True)

        post_data = {'group_id': new_group.id}
        url = reverse('delete_user_group', kwargs=post_data)
        request = self.factory.post(url, data=post_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = delete_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-1').first()
        self.assertEqual(new_group.gaccess.active, False)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # test undeleting the group
        url = reverse('restore_user_group', kwargs=post_data)
        request = self.factory.post(url, data=post_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = restore_user_group(request, group_id=new_group.id)
        new_group = Group.objects.filter(name='Test Group-1').first()
        self.assertEqual(new_group.gaccess.active, True)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def test_group_update_failure(self):
        # test that post data for 'name', 'description', and 'privacy_level' are required
        # when updating a group

        # first create a group to test updating group
        url = reverse('create_user_group')
        grp_data = {'name': 'Test Group-1', 'description': 'This is a cool group-1',
                    'purpose': 'This group has purpose', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        response = create_user_group(request)
        new_group = Group.objects.filter(name='Test Group-1').first()

        # now test updating new_group
        url_params = {'group_id': new_group.id}
        url = reverse('update_user_group', kwargs=url_params)
        # test name is required -> update should fail
        grp_data = {'description': 'This is a cool group-2', 'purpose': 'This group has purpose'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        # description has not changed proves update failed
        self.assertNotEqual(new_group.gaccess.description, 'This is a cool group-2')
        self.assertEqual(new_group.gaccess.description, 'This is a cool group-1')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # test description is required -> update should fail
        grp_data = {'name': 'Test Group-2', 'purpose': 'This group has purpose',
                    'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self._update_failure(new_group, request)

        # test privacy_level is required -> update should fail
        grp_data = {'name': 'Test Group-2', 'description': 'This is a cool group',
                    'purpose': 'This group has purpose'}
        request = self.factory.post(url, data=grp_data)

        self._update_failure(new_group, request)

        # test trying to update group with a duplicate name ('HydroShare Author') should fail
        grp_data = {'name': 'Hydroshare Author', 'description': 'This is a cool group-1',
                    'purpose': 'This group has purpose'}
        request = self.factory.post(url, data=grp_data)
        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=new_group.id)
        # name has not changed proves update failed
        self.assertEqual(Group.objects.filter(name='Hydroshare Author').count(), 1)
        updated_group = Group.objects.filter(name='Hydroshare Author').first()
        self.assertNotEqual(updated_group.id, new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def test_share_group_with_user(self):
        # create a group to share
        new_group = self._create_group()

        # check mike is not a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)

        # John to share 'Test Group' with user Mike with 'view' privilege
        self._share_group_with_user(new_group, 'view')

        # John to share 'Test Group' with user Mike with 'edit' privilege
        self._share_group_with_user(new_group, 'edit')

        # John to share 'Test Group' with user Mike with 'edit' privilege
        self._share_group_with_user(new_group, 'edit')

        # John to share 'Test Group' with user Mike with 'owner' privilege
        self._share_group_with_user(new_group, 'owner')

    def test_share_group_with_user_invalid_privilege(self):
        # a group can shared with a user with privilege of one of these (view, edit or owner)

        # create a group to share
        new_group = self._create_group()

        # John to share 'Test Group' with user Mike with invalid privilege
        url_params = {'group_id': new_group.id, 'user_id': self.mike.id, 'privilege': "badprivilege"}
        url = reverse('share_group_with_user', kwargs=url_params)
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self.set_request_message_attributes(request)
        request.user = self.john
        response = share_group_with_user(request, group_id=new_group.id, user_id=self.mike.id, privilege="badprivilege")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # check mike is not a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)

    def test_unshare_group_with_user(self):
        # create a group to share
        new_group = self._create_group()

        # John to share 'Test Group' with user Mike with 'view' privilege
        self._share_group_with_user(new_group, 'view')
        # check mike is a member of the group
        self.assertIn(self.mike, new_group.gaccess.members)

        # unshare test group with mike
        url_params = {'group_id': new_group.id, 'user_id': self.mike.id}
        url = reverse('unshare_group_with_user', kwargs=url_params)
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self.set_request_message_attributes(request)
        request.user = self.john
        response = unshare_group_with_user(request, group_id=new_group.id, user_id=self.mike.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        # check mike is not a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)

    def test_share_resource_with_group(self):
        # create a group to share with a resource
        new_group = self._create_group()

        # let group owner john share resource with view privilege
        response = self._share_resource_with_group(group=new_group, privilege='view')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content.decode())
        self.assertEqual(response_content['status'], 'success')
        self.assertIn(self.resource, new_group.gaccess.view_resources)

        # share resource with group with edit privilege
        # first unshare resource with group
        self.john.uaccess.unshare_resource_with_group(self.resource, new_group)
        self.assertNotIn(self.resource, new_group.gaccess.view_resources)
        response = self._share_resource_with_group(group=new_group, privilege='edit')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content.decode())
        self.assertEqual(response_content['status'], 'success')
        self.assertIn(self.resource, new_group.gaccess.edit_resources)

        # test a group can't have owner privilege over a resource
        # first unshare resource with group
        self.john.uaccess.unshare_resource_with_group(self.resource, new_group)
        self.assertNotIn(self.resource, new_group.gaccess.view_resources)

        response = self._share_resource_with_group(group=new_group, privilege='owner')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_content = json.loads(response.content.decode())
        self.assertEqual(response_content['status'], 'error')
        self.assertNotIn(self.resource, new_group.gaccess.view_resources)

    def test_unshare_resource_with_group(self):
        # create a group to share/unshare with a resource
        new_group = self._create_group()

        # first share the resource with the group
        self.john.uaccess.share_resource_with_group(self.resource, new_group, PrivilegeCodes.VIEW)
        self.assertIn(self.resource, new_group.gaccess.view_resources)

        # now unshare the resource with the group
        url_params = {'shortkey': self.resource.short_id, 'group_id': new_group.id}
        url = reverse('unshare_resource_with_group', kwargs=url_params)
        request = self.factory.post(url)
        request.user = self.john
        response = unshare_resource_with_group(request, shortkey=self.resource.short_id,
                                               group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content.decode())
        self.assertEqual(response_content['status'], 'success')
        self.assertNotIn(self.resource, new_group.gaccess.view_resources)

        # test group member (non-owner) unsharing a resource with a group
        # returns response status as 'error' and the group is not unshared

        # let make mike a member of group
        self.john.uaccess.share_group_with_user(new_group, self.mike, PrivilegeCodes.VIEW)
        self.assertIn(new_group, self.mike.uaccess.view_groups)

        # let john share the resource with group
        self.john.uaccess.share_resource_with_group(self.resource, new_group, PrivilegeCodes.VIEW)
        self.assertIn(self.resource, new_group.gaccess.view_resources)

        # let mike unshare the resource with group
        request.user = self.mike
        response = unshare_resource_with_group(request, shortkey=self.resource.short_id,
                                               group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_content = json.loads(response.content.decode())
        self.assertEqual(response_content['status'], 'error')
        self.assertIn(self.resource, new_group.gaccess.view_resources)

    def test_make_group_membership_request(self):
        # test that user can make request to join a group

        # create a group
        new_group = self._create_group()

        # now there should be no GroupMembershipRequest associated with Mile
        self.assertEqual(self.mike.uaccess.group_membership_requests.count(), 0)

        # test that user mike can make a request to join the new_group
        url_params = {'group_id': new_group.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.META['HTTP_REFERER'] = "/some_url/"
        request.user = self.mike
        response = make_group_membership_request(request, group_id=new_group.id)
        response_content = json.loads(response.content)
        self.assertEqual(response_content["status"], 'success')
        # now there should be one GroupMembershipRequest associated with Mike
        self.assertEqual(self.mike.uaccess.group_membership_requests.count(), 1)

        # test user making request more than once for the same group should fail
        response = make_group_membership_request(request, group_id=new_group.id)
        response_content = json.loads(response.content)
        self.assertEqual(response_content["status"], 'error')
        # there should be still one GroupMembershipRequest associated with Mike
        self.assertEqual(self.mike.uaccess.group_membership_requests.count(), 1)

    def test_make_group_membership_invitation(self):
        # test group owner inviting a user to join a group

        # create a group
        new_group = self._create_group()

        # there should be no GroupMembershipRequest associated with John
        self.assertEqual(self.john.uaccess.group_membership_requests.count(), 0)
        # test that group owner john can invite mike to join the new_group
        url_params = {'group_id': new_group.id, 'user_id': self.mike.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.META['HTTP_REFERER'] = "/some_url/"
        request.user = self.john
        response = make_group_membership_request(request, group_id=new_group.id, user_id=self.mike.id)
        response_content = json.loads(response.content)
        self.assertEqual(response_content["status"], 'success')
        # now there should be one GroupMembershipRequest associated with John
        self.assertEqual(self.john.uaccess.group_membership_requests.count(), 1)

        # test group owner inviting same user to the same group more than once should fail
        response = make_group_membership_request(request, group_id=new_group.id, user_id=self.mike.id)
        response_content = json.loads(response.content)
        self.assertEqual(response_content["status"], 'error')
        # there should be still one GroupMembershipRequest associated with John
        self.assertEqual(self.john.uaccess.group_membership_requests.count(), 1)

    def test_act_on_group_membership_request(self):
        # test group owner accepting/declining a request from a user to join a group

        # let user mike make a request
        # create a group
        new_group = self._create_group()

        # let user mike make a request to join the new_group
        membership_request = self._generate_user_request_to_join_group(new_group)

        # test john can accept the request

        # check mike is not a member of the group yet
        self.assertNotIn(self.mike, new_group.gaccess.members)

        # john accepts mike's request
        self._owner_act_on_request(membership_request, 'accept')

        # check mike is now a member of the group
        self.assertIn(self.mike, new_group.gaccess.members)

        # test owner decline user request

        # remove mike from group
        self.john.uaccess.unshare_group_with_user(new_group, self.mike)
        # check mike is no more a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)
        # let mike again make a request
        membership_request = self._generate_user_request_to_join_group(new_group)
        # let john decline mike's request
        self._owner_act_on_request(membership_request, 'decline')
        # check mike is not a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)

    def test_act_on_group_membership_invitation(self):
        # test user invited to join a group can accept/decline the invitation

        # create a group
        new_group = self._create_group()

        # let john invite mike
        membership_request = self._generate_owner_invitation_to_join_group(new_group)

        # check mike is not a member of the group yet
        self.assertNotIn(self.mike, new_group.gaccess.members)

        # test mike is a member of the group after accepting john's request
        self._user_act_on_invitation(membership_request, 'accept')

        # check mike is now a member of the group
        self.assertIn(self.mike, new_group.gaccess.members)

        # test mike can decline invitation to join a group
        # remove mike from group
        self.john.uaccess.unshare_group_with_user(new_group, self.mike)
        # check mike is no more a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)
        # let john invite mike again
        membership_request = self._generate_owner_invitation_to_join_group(new_group)
        # let mike decline john's invitation
        self._user_act_on_invitation(membership_request, 'decline')
        # check mike is no more a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)

    def test_group_membership_acceptance_via_email_link(self):
        # here we are testing group_membership view function which is invoked
        # when the user clicks the link provided in the email

        # create a group
        new_group = self._create_group()

        # test user accepting group owner's invitation
        # check mike is no more a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)
        # let john invite mike to join group
        membership_request = self.john.uaccess.create_group_membership_request(new_group, self.mike)
        # create the link that mike should find in his email
        uidb36 = int_to_base36(self.mike.id)
        token = without_login_date_token_generator.make_token(self.mike)
        url_params = {"uidb36": uidb36, "token": token, "membership_request_id": membership_request.id}
        url = reverse('group_membership', kwargs=url_params)
        # due to session requirement of the view being tested, using the Client class
        client = Client()
        # let mike click the link in the email
        response = client.get(url)
        redirect_url = '/group/{}/'.format(new_group.id)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response['Location'].endswith(redirect_url))
        # check mike is now a member of the group
        self.assertIn(self.mike, new_group.gaccess.members)

        # test group owner (john) accepting user (mike) request to join a group

        # remove mike from group
        self.john.uaccess.unshare_group_with_user(new_group, self.mike)
        # check mike is no more a member of the group
        self.assertNotIn(self.mike, new_group.gaccess.members)
        # let mike make a request to join group
        membership_request = self.mike.uaccess.create_group_membership_request(new_group)
        # create the link that john should find in his email
        uidb36 = int_to_base36(self.john.id)
        token = without_login_date_token_generator.make_token(self.john)
        url_params = {"uidb36": uidb36, "token": token, "membership_request_id": membership_request.id}
        url = reverse('group_membership', kwargs=url_params)
        # let john click the link
        response = client.get(url)
        redirect_url = '/group/{}/'.format(new_group.id)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response['Location'].endswith(redirect_url))
        # check mike is now a member of the group
        self.assertIn(self.mike, new_group.gaccess.members)

    def _update_failure(self, group, request):
        group_name = group.name
        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = update_user_group(request, group_id=group.id)
        # name has not changed proves update failed
        updated_group = Group.objects.filter(name='Test Group-2').first()
        self.assertEqual(updated_group, None)
        original_group = Group.objects.filter(name=group_name).first()
        self.assertNotEqual(original_group, None)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def _share_resource_with_group(self, group, privilege):
        url_params = {'shortkey': self.resource.short_id, 'privilege': privilege, 'group_id': group.id}
        url = reverse('share_resource_with_group', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.user = self.john
        response = share_resource_with_group(request, shortkey=self.resource.short_id, privilege=privilege,
                                             group_id=group.id)
        return response

    def _owner_act_on_request(self, membership_request, action):
        url_params = {'membership_request_id': membership_request.id, 'action': action}
        url = reverse('act_on_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.user = self.john
        request.META['HTTP_REFERER'] = "/some_url/"
        response = act_on_group_membership_request(request, membership_request_id=membership_request.id,
                                                   action=action)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def _user_act_on_invitation(self, membership_request, action):
        url_params = {'membership_request_id': membership_request.id, 'action': action}
        url = reverse('act_on_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.user = self.mike
        request.META['HTTP_REFERER'] = "/some_url/"
        response = act_on_group_membership_request(request, membership_request_id=membership_request.id,
                                                   action=action)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

    def _generate_user_request_to_join_group(self, group):
        url_params = {'group_id': group.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.META['HTTP_REFERER'] = "/some_url/"
        request.user = self.mike
        make_group_membership_request(request, group_id=group.id)
        membership_request = self.mike.uaccess.group_membership_requests.first()
        return membership_request

    def _generate_owner_invitation_to_join_group(self, group):
        url_params = {'group_id': group.id, 'user_id': self.mike.id}
        url = reverse('make_group_membership_request', kwargs=url_params)
        request = self.factory.post(url)
        self.set_request_message_attributes(request)
        request.META['HTTP_REFERER'] = "/some_url/"
        request.user = self.john
        make_group_membership_request(request, group_id=group.id, user_id=self.mike.id)
        membership_request = self.john.uaccess.group_membership_requests.first()
        return membership_request

    def _create_group(self):
        url = reverse('create_user_group')
        # test passing privacy_level = 'public'
        grp_data = {'name': 'Test Group', 'description': 'This is a cool group', 'privacy_level': 'public'}
        request = self.factory.post(url, data=grp_data)

        self.set_request_message_attributes(request)
        request.user = self.john
        create_user_group(request)
        new_group = Group.objects.filter(name='Test Group').first()
        return new_group

    def _share_group_with_user(self, group, privilege):
        url_params = {'group_id': group.id, 'user_id': self.mike.id, 'privilege': privilege}
        url = reverse('share_group_with_user', kwargs=url_params)
        request = self.factory.post(url)
        request.META['HTTP_REFERER'] = "/some_url/"
        self.set_request_message_attributes(request)
        request.user = self.john
        response = share_group_with_user(request, group_id=group.id, user_id=self.mike.id, privilege=privilege)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])

        # check mike is a member of the group
        self.assertIn(self.mike, group.gaccess.members)
        # check mike has the specified privilege over the group
        if privilege == 'view':
            self.assertIn(self.mike, group.gaccess.get_users_with_explicit_access(PrivilegeCodes.VIEW))
        elif privilege == 'edit':
            self.assertIn(self.mike, group.gaccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE))
        else:
            self.assertIn(self.mike, group.gaccess.get_users_with_explicit_access(PrivilegeCodes.OWNER))
