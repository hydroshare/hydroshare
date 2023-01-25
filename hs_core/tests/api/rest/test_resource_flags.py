import os
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestPublicResourceFlagsEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicResourceFlagsEndpoint, self).setUp()
        self.tmp_dir = tempfile.mkdtemp()

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        metadata_dict = [
            {'description': {'abstract': 'My test abstract'}},
            {'subject': {'value': 'sub-1'}}
        ]
        file_one = "test1.txt"
        open(file_one, "w").close()
        self.file_one = open(file_one, "rb")
        self.txt_file_path = os.path.join(self.tmp_dir, 'text.txt')
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res_two = resource.create_resource(self.rtype,
                                           self.user,
                                           self.title,
                                           files=(self.file_one,),
                                           metadata=metadata_dict)

        self.pid = res.short_id
        self.pid_two = res_two.short_id

        self.resources_to_delete.append(self.pid)
        self.resources_to_delete.append(self.pid_two)

    def test_set_resource_flag_make_public(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "flag": "make_public"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        flag_url = "/hsapi/resource/%s/flag/" % self.pid_two
        response = self.client.post(flag_url, {
            "flag": "make_public"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_private(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "flag": "make_private"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_discoverable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid_two
        response = self.client.post(flag_url, {
            "flag": "make_discoverable"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_not_discoverable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "flag": "make_not_discoverable"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_not_shareable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "flag": "make_not_shareable"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_set_resource_flag_make_shareable(self):
        flag_url = "/hsapi/resource/%s/flag/" % self.pid
        response = self.client.post(flag_url, {
            "flag": "make_shareable"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
