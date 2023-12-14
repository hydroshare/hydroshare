import os
import shutil

from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.urls import reverse

from rest_framework import status

from hs_core.testing import ViewTestCase
from hs_core import hydroshare
from hs_core.views import create_user_group, update_user_group, delete_user_group, \
    restore_user_group


class TestGroupCRUD(ViewTestCase):

    def setUp(self):
        super(TestGroupCRUD, self).setUp()
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
            'mk@gmail.com',
            username='mikeJ',
            first_name='Mike',
            last_name='Johnson',
            superuser=False,
            password='mkmypassword',
            groups=[]
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestGroupCRUD, self).tearDown()

    def test_create_group(self):
        # here we are testing the create_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        post_data = {'name': "Test Group", 'description': "This is great group",
                     'purpose': "To have fun", 'auto_approve': False, 'privacy_level': 'public'}
        url = reverse('create_user_group', kwargs={})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        expected_new_group_id = Group.objects.all().order_by("-id").first().id + 1
        request.META['HTTP_REFERER'] = '/group/{}'.format(expected_new_group_id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        # there should be 2 group at this point
        self.assertEqual(Group.objects.count(), 2)

    def test_create_group_failure(self):
        # here we are testing the create_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # post data missing data for the required field 'description'
        post_data = {'name': "Test Group",
                     'purpose': "To have fun", 'auto_approve': False, 'privacy_level': 'public'}
        url = reverse('create_user_group', kwargs={})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        expected_new_group_id = Group.objects.all().order_by("-id").first().id + 1
        request.META['HTTP_REFERER'] = '/group/{}'.format(expected_new_group_id - 1)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = create_user_group(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertNotEqual(response['Location'], '/group/{}'.format(expected_new_group_id))
        flag_messages = get_messages(request)
        err_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(err_messages), 0)
        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)

    def test_update_group(self):
        # here we are testing the update_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)

        # update new_group
        post_data = {'name': "Test Group-1", 'description': "This is great group",
                     'purpose': "To have fun", 'auto_approve': False, 'privacy_level': 'public'}
        url = reverse('update_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = update_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        # there should be 2 group at this point
        self.assertEqual(Group.objects.count(), 2)

    def test_update_group_failure(self):
        # here we are testing the update_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)

        # update new_group (missing required field 'description')
        post_data = {'name': "Test Group-1",
                     'purpose': "To have fun", 'auto_approve': False, 'privacy_level': 'public'}
        url = reverse('update_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = update_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        err_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(err_messages), 0)
        # there should be 2 group at this point
        self.assertEqual(Group.objects.count(), 2)

    def test_delete_group(self):
        # here we are testing the delete_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(new_group.gaccess.active, True)

        # delete new_group (which sets the active status to false)
        post_data = {}
        url = reverse('delete_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        new_group.gaccess.refresh_from_db()
        self.assertEqual(new_group.gaccess.active, False)

    def test_delete_group_failure(self):
        # here we are testing the delete_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(new_group.gaccess.active, True)

        # delete new_group (which sets the active status to false)
        post_data = {}
        url = reverse('delete_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        # mike does not have permission to delete this group - delete should fail
        request.user = self.mike
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        err_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(err_messages), 0)
        new_group.gaccess.refresh_from_db()
        # group should still be active
        self.assertEqual(new_group.gaccess.active, True)

    def test_restore_group(self):
        # here we are testing the restore_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(new_group.gaccess.active, True)
        # make the group inactive
        new_group.gaccess.active = False
        new_group.gaccess.save()

        # restore new_group (which sets the active status to true)
        post_data = {}
        url = reverse('restore_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        request.user = self.john
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = restore_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        success_messages = [m for m in flag_messages if m.tags == 'success']
        self.assertNotEqual(len(success_messages), 0)
        new_group.gaccess.refresh_from_db()
        # group should be active
        self.assertEqual(new_group.gaccess.active, True)

    def test_restore_group_failure(self):
        # here we are testing the restore_user_group view function

        # there should be 1 group at this point
        self.assertEqual(Group.objects.count(), 1)
        # let john create a new group
        new_group = self.john.uaccess.create_group(title='Test Group',
                                                   description='This is a great group',
                                                   purpose='To have fun',
                                                   auto_approve=True)

        # there should be 2 groups at this point
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(new_group.gaccess.active, True)
        # make the group inactive
        new_group.gaccess.active = False
        new_group.gaccess.save()

        # restore new_group (which sets the active status to true)
        post_data = {}
        url = reverse('restore_user_group', kwargs={'group_id': new_group.id})

        request = self.factory.post(url, data=post_data)
        # mike does not have permission over new_group - restore should fail
        request.user = self.mike
        request.META['HTTP_REFERER'] = '/group/{}'.format(new_group.id)
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = restore_user_group(request, group_id=new_group.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], request.META['HTTP_REFERER'])
        flag_messages = get_messages(request)
        err_messages = [m for m in flag_messages if m.tags == 'error']
        self.assertNotEqual(len(err_messages), 0)
        new_group.gaccess.refresh_from_db()
        # group should still be inactive
        self.assertEqual(new_group.gaccess.active, False)
