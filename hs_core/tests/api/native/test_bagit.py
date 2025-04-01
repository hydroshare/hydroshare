import os
from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.hydroshare import hs_bagit
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.tasks import create_bag_by_s3
from hs_core.models import BaseResource
from django_s3.storage import S3Storage
from hs_core.task_utils import _retrieve_task_id
from django.core.files.uploadedfile import UploadedFile
from hs_core.hydroshare.resource import add_resource_files


class TestBagIt(TestCase):
    def setUp(self):
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # note: creating a resource calls the hs_bagit.create_bag() api
        self.test_res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )
        self.readme_md = "readme.md"
        self.readme_md_file = open(self.readme_md, 'w')
        self.readme_md_file.write("##This is a readme markdown file")
        self.readme_md_file.close()

    def tearDown(self):
        super(TestBagIt, self).tearDown()
        if self.test_res:
            self.test_res.delete()
        BaseResource.objects.all().delete()
        self.readme_md_file.close()
        os.remove(self.readme_md_file.name)

    def test_create_bag_files(self):
        # this is the api call we are testing
        storage_obj = hs_bagit.create_bag_metadata_files(self.test_res)
        self.assertTrue(isinstance(storage_obj, S3Storage))

    def test_bag_creation_and_deletion(self):
        status = create_bag_by_s3(self.test_res.short_id)
        self.assertTrue(status)
        # test checksum will be computed for published resource
        self.test_res.raccess.published = True
        self.test_res.raccess.save()
        status = create_bag_by_s3(self.test_res.short_id)
        self.assertTrue(status)
        res = get_resource_by_shortkey(self.test_res.short_id)
        self.assertNotEqual(res.bag_checksum, '', msg='bag_checksum property is empty')

        self.test_res.raccess.published = False
        self.test_res.raccess.save()
        hs_bagit.delete_files_and_bag(self.test_res)
        # resource should not have any bags
        istorage = self.test_res.get_s3_storage()
        bag_path = self.test_res.bag_path
        self.assertFalse(istorage.exists(bag_path))

    def test_bag_file_create_zip(self):
        def bag_modified():
            return self.test_res.getAVU('bag_modified')

        create_bag_by_s3(self.test_res.short_id, create_zip=True)
        self.assertFalse(bag_modified())

        files_to_add = [self.readme_md]
        self._add_files_to_resource(files_to_add)
        self.assertTrue(bag_modified())

        create_bag_by_s3(self.test_res.short_id, create_zip=False)
        # Bag modified doesn't get toggled when create_zip = False
        self.assertTrue(bag_modified())

    def test_retrieve_create_bag_by_s3_task_id(self):
        mock_res_id = '84d1b8b60f274ba4be155881129561a9'
        mock_active_and_reserved_job_id = '04ee96ac-1cf2-459f-b497-3b2ac04b3877'
        mock_active_and_reserved_jobs = {
            'celery@6337f5f9054c': [{'args': [mock_res_id],
                                     'time_start': 4415073.585907947,
                                     'name': 'hs_core.tasks.create_bag_by_s3',
                                     'delivery_info': {'priority': 0,
                                                       'redelivered': False,
                                                       'routing_key': 'task.default',
                                                       'exchange': 'default'},
                                     'hostname': 'celery@6337f5f9054c',
                                     'acknowledged': True,
                                     'kwargs': {},
                                     'id': mock_active_and_reserved_job_id,
                                     'worker_pid': 60}]}
        mock_scheduled_job_id = '586be52d-3409-4258-959f-f91a5b81a493'
        mock_scheduled_jobs = {
            'celery@6337f5f9054c': [{'priority': 6,
                                     'eta': '2019-12-11T19:42:51.864720+00:00',
                                     'request': {
                                         'args': [mock_res_id],
                                         'time_start': None,
                                         'name': 'hs_core.tasks.create_bag_by_s3',
                                         'delivery_info': {'priority': 0,
                                                           'redelivered': True,
                                                           'routing_key': 'task.default',
                                                           'exchange': 'default'},
                                         'hostname': 'celery@6337f5f9054c',
                                         'acknowledged': False,
                                         'kwargs': {},
                                         'id': mock_scheduled_job_id,
                                         'worker_pid': None
                                     }}]}
        job_name = 'hs_core.tasks.create_bag_by_s3'
        ret_id = _retrieve_task_id(job_name, mock_res_id, mock_active_and_reserved_jobs)
        self.assertEqual(ret_id, mock_active_and_reserved_job_id, msg="retrieved task id not equal to "
                                                                      "mock_active_and_reserved_job_id")
        ret_id = _retrieve_task_id(job_name, mock_res_id, mock_scheduled_jobs)
        self.assertEqual(ret_id, mock_scheduled_job_id, msg="retrieved task id not equal to mock_scheduled_job_id")

    def _add_files_to_resource(self, files_to_add, upload_folder=''):
        files_to_upload = []
        for fl in files_to_add:
            file_to_upload = UploadedFile(file=open(fl, 'rb'), name=os.path.basename(fl))
            files_to_upload.append(file_to_upload)
        added_resource_files = add_resource_files(self.test_res.short_id,
                                                  *files_to_upload, folder=upload_folder)
        return added_resource_files
