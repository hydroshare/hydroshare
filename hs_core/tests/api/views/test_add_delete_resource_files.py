import os
import shutil

from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status

from hs_core import hydroshare
from hs_core.models import ResourceFile
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase
from hs_core.views import (add_files_to_resource, delete_file,
                           delete_multiple_files)


class TestAddDeleteResourceFiles(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestAddDeleteResourceFiles, self).setUp()
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
        self.gen_res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Resource Key/Value Metadata Testing'
        )

        # Make a text file
        self.txt_file_name_1 = 'text-1.txt'
        self.txt_file_path_1 = os.path.join(self.temp_dir, self.txt_file_name_1)
        txt = open(self.txt_file_path_1, 'w')
        txt.write("Hello World-1\n")
        txt.close()

        self.txt_file_name_2 = 'text-2.txt'
        self.txt_file_path_2 = os.path.join(self.temp_dir, self.txt_file_name_2)
        txt = open(self.txt_file_path_2, 'w')
        txt.write("Hello World-2\n")
        txt.close()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestAddDeleteResourceFiles, self).tearDown()

    def test_add_files(self):
        # here we are testing add_files_to_resource view function

        # There should be no files for the resource now
        self.assertEqual(self.gen_res.files.count(), 0)

        # add a file
        post_data = {'files': (self.txt_file_name_1, open(self.txt_file_path_1), 'text/plain')}
        url_params = {'shortkey': self.gen_res.short_id}

        url = reverse('add_files_to_resource', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = add_files_to_resource(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # there should be 1 file
        self.assertEqual(self.gen_res.files.count(), 1)

        # test adding a file to a deep folder
        res_file = self.gen_res.files.first()
        hydroshare.delete_resource_file(self.gen_res.short_id, res_file.id, self.user)
        # there should be no file
        self.assertEqual(self.gen_res.files.count(), 0)
        ResourceFile.create_folder(resource=self.gen_res, folder="foo")
        post_data = {'files': (self.txt_file_name_1, open(self.txt_file_path_1), 'text/plain'),
                     'file_folder': 'foo'}
        url_params = {'shortkey': self.gen_res.short_id}

        url = reverse('add_files_to_resource', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = add_files_to_resource(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # there should be 1 file
        self.assertEqual(self.gen_res.files.count(), 1)
        hydroshare.delete_resource(self.gen_res.short_id)

    def test_delete_file(self):
        # here we are testing delete_file view function

        # There should be no files for the resource now
        self.assertEqual(self.gen_res.files.count(), 0)

        # add a file
        post_data = {'files': (self.txt_file_name_1, open(self.txt_file_path_1), 'text/plain')}
        url_params = {'shortkey': self.gen_res.short_id}

        url = reverse('add_files_to_resource', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        add_files_to_resource(request, shortkey=self.gen_res.short_id)
        res_file = self.gen_res.files.first()

        # test the delete_file view function

        url_params = {'shortkey': self.gen_res.short_id, 'f': res_file.id}

        url = reverse('delete_file', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        request.META['HTTP_REFERER'] = 'some-url'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_file(request, shortkey=self.gen_res.short_id, f=res_file.id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response["Location"], request.headers["referer"])
        self.assertEqual(self.gen_res.files.count(), 0)

        hydroshare.delete_resource(self.gen_res.short_id)

    def test_delete_multiple_files(self):
        # here we are testing delete_multiple_files view function

        # There should be no files for the resource now
        self.assertEqual(self.gen_res.files.count(), 0)

        # add 2 files
        post_data = {'file1': (self.txt_file_name_1, open(self.txt_file_path_1), 'text/plain'),
                     'file2': (self.txt_file_name_2, open(self.txt_file_path_2), 'text/plain')}
        url_params = {'shortkey': self.gen_res.short_id}

        url = reverse('add_files_to_resource', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        add_files_to_resource(request, shortkey=self.gen_res.short_id)
        self.assertEqual(self.gen_res.files.count(), 2)

        # test the delete_multiple_files view function
        file_ids = ','.join([str(f.id) for f in self.gen_res.files.all()])
        post_data = {'file_ids': file_ids}
        url_params = {'shortkey': self.gen_res.short_id}
        url = reverse('delete_multiple_files', kwargs=url_params)
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        request.META['HTTP_REFERER'] = 'some-url'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_multiple_files(request, shortkey=self.gen_res.short_id)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response["Location"], request.headers["referer"])
        self.assertEqual(self.gen_res.files.count(), 0)

        hydroshare.delete_resource(self.gen_res.short_id)
