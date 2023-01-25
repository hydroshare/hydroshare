from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.hydroshare import hs_bagit
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.tasks import create_bag_by_irods
from hs_core.models import BaseResource
from django_irods.storage import IrodsStorage
from hs_core.task_utils import _retrieve_task_id


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

    def tearDown(self):
        super(TestBagIt, self).tearDown()
        if self.test_res:
            self.test_res.delete()
        BaseResource.objects.all().delete()

    def test_create_bag_files(self):
        # this is the api call we are testing
        irods_storage_obj = hs_bagit.create_bag_metadata_files(self.test_res)
        self.assertTrue(isinstance(irods_storage_obj, IrodsStorage))

    def test_bag_creation_and_deletion(self):
        status = create_bag_by_irods(self.test_res.short_id)
        self.assertTrue(status)
        # test checksum will be computed for published resource
        self.test_res.raccess.published = True
        self.test_res.raccess.save()
        status = create_bag_by_irods(self.test_res.short_id)
        self.assertTrue(status)
        res = get_resource_by_shortkey(self.test_res.short_id)
        self.assertNotEqual(res.bag_checksum, '', msg='bag_checksum property is empty')

        self.test_res.raccess.published = False
        self.test_res.raccess.save()
        hs_bagit.delete_files_and_bag(self.test_res)
        # resource should not have any bags
        istorage = self.test_res.get_irods_storage()
        bag_path = self.test_res.bag_path
        self.assertFalse(istorage.exists(bag_path))

    def test_retrieve_create_bag_by_irods_task_id(self):
        mock_res_id = '84d1b8b60f274ba4be155881129561a9'
        mock_active_and_reserved_job_id = '04ee96ac-1cf2-459f-b497-3b2ac04b3877'
        mock_active_and_reserved_jobs = {
            'celery@6337f5f9054c': [{'args': [mock_res_id],
                                     'time_start': 4415073.585907947,
                                     'name': 'hs_core.tasks.create_bag_by_irods',
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
                                         'name': 'hs_core.tasks.create_bag_by_irods',
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
        job_name = 'hs_core.tasks.create_bag_by_irods'
        ret_id = _retrieve_task_id(job_name, mock_res_id, mock_active_and_reserved_jobs)
        self.assertEqual(ret_id, mock_active_and_reserved_job_id, msg="retrieved task id not equal to "
                                                                      "mock_active_and_reserved_job_id")
        ret_id = _retrieve_task_id(job_name, mock_res_id, mock_scheduled_jobs)
        self.assertEqual(ret_id, mock_scheduled_job_id, msg="retrieved task id not equal to mock_scheduled_job_id")
