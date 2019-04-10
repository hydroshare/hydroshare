import os
import shutil
import json

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import UploadedFile


from hs_core import hydroshare
from hs_core.views import set_resource_flag
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase


class TestSetResourceFlag(MockIRODSTestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestSetResourceFlag, self).setUp()
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
        self.gen_res_one = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic Resource Set Flag Testing-1'
        )

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.temp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()
        self.txt_file = open(self.txt_file_path, 'r')
        files = [UploadedFile(self.txt_file, name=self.txt_file_name)]
        metadata_dict = [
            {'description': {'abstract': 'My test abstract'}},
            {'subject': {'value': 'sub-1'}}
        ]
        self.gen_res_two = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic Resource Set Flag Testing-2',
            files=files,
            metadata=metadata_dict
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestSetResourceFlag, self).tearDown()

    def test_set_resource_flag_make_public(self):
        # here we are testing the set_resource_flag view function to make a resource public

        # test that trying set the resource flag to public  when there is no content file
        # or required metadata it should not change the resource flag

        # test that the resource is not public
        self.assertEqual(self.gen_res_one.raccess.public, False)
        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_public'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        # check that the resource is still not public
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.public, False)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')

        # setting flag to public for 2nd resource should succeed
        # test that the resource is not public
        self.assertEqual(self.gen_res_two.raccess.public, False)
        url_params = {'shortkey': self.gen_res_two.short_id}
        post_data = {'flag': 'make_public'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_two.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # check that the resource is public now
        self.gen_res_two.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_two.raccess.public, True)

        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)

    def test_set_resource_flag_make_private(self):
        # here we are testing the set_resource_flag view function to make a resource private

        # test that the resource is not public
        self.assertEqual(self.gen_res_one.raccess.public, False)
        # set it to public
        self.gen_res_one.raccess.public = True
        self.gen_res_one.raccess.save()

        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_private'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # check that the resource is private now
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.public, False)
        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)

    def test_set_resource_flag_make_discoverable(self):
        # here we are testing the set_resource_flag view function to make a resource discoverable

        # test that trying set the resource discoverable when there is no content file
        # or required metadata it should not make the resource discoverable

        # test that the resource is not discoverable
        self.assertEqual(self.gen_res_one.raccess.discoverable, False)
        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_discoverable'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        # check that the resource is still not discoverable
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.discoverable, False)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'error')

        # setting flag to discoverable for 2nd resource should succeed
        # test that the resource is not discoverable
        self.assertEqual(self.gen_res_two.raccess.discoverable, False)
        url_params = {'shortkey': self.gen_res_two.short_id}
        post_data = {'flag': 'make_discoverable'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_two.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # check that the resource is discoverable now
        self.gen_res_two.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_two.raccess.discoverable, True)

        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)

    def test_set_resource_flag_make_not_discoverable(self):
        # here we are testing the set_resource_flag view function to make a resource
        # not discoverable

        # test that the resource is not discoverable
        self.assertEqual(self.gen_res_one.raccess.discoverable, False)
        # make it discoverable
        self.gen_res_one.raccess.discoverable = True
        self.gen_res_one.raccess.save()

        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_not_discoverable'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # check that the resource is not discoverable now
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.discoverable, False)

        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)

    def test_set_resource_flag_make_shareable(self):
        # here we are testing the set_resource_flag view function to make a resource shareable

        # test that the resource is  shareable
        self.assertEqual(self.gen_res_one.raccess.shareable, True)
        # set it not shareable
        self.gen_res_one.raccess.shareable = False
        self.gen_res_one.raccess.save()

        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_shareable'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')

        # check that the resource is shareable now
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.shareable, True)
        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)

    def test_set_resource_flag_make_not_shareable(self):
        # here we are testing the set_resource_flag view function to make a resource not shareable

        # test that the resource is  shareable
        self.assertEqual(self.gen_res_one.raccess.shareable, True)

        url_params = {'shortkey': self.gen_res_one.short_id}
        post_data = {'flag': 'make_not_shareable'}
        url = reverse('set_resource_flag', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user

        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = set_resource_flag(request, shortkey=self.gen_res_one.short_id)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['status'], 'success')
        # check that the resource is not shareable now
        self.gen_res_one.raccess.refresh_from_db()
        self.assertEqual(self.gen_res_one.raccess.shareable, False)
        # clean up
        hydroshare.delete_resource(self.gen_res_one.short_id)
        hydroshare.delete_resource(self.gen_res_two.short_id)
