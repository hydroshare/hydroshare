import os
import unittest

from django.contrib.auth.models import User, Group

from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.hydroshare.users import create_account
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin
from hs_core.exceptions import QuotaException


class TestAddResourceFiles(MockS3TestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestAddResourceFiles, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        # create files
        self.n1 = "test1.txt"
        self.n2 = "test2.txt"
        self.n3 = "test3.txt"

        test_file = open(self.n1, 'w')
        test_file.write("Test text file in test1.txt")
        test_file.close()

        test_file = open(self.n2, 'w')
        test_file.write("Test text file in test2.txt")
        test_file.close()

        test_file = open(self.n3, 'w')
        test_file.write("Test text file in test3.txt")
        test_file.close()

        # open files for read and upload
        self.myfile1 = open(self.n1, "rb")
        self.myfile2 = open(self.n2, "rb")
        self.myfile3 = open(self.n3, "rb")

        self.res = create_resource(resource_type='CompositeResource',
                                   owner=self.user,
                                   title='Test Resource',
                                   metadata=[], )

    def tearDown(self):
        super(TestAddResourceFiles, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()
        self.myfile1.close()
        os.remove(self.myfile1.name)
        self.myfile2.close()
        os.remove(self.myfile2.name)
        self.myfile3.close()
        os.remove(self.myfile3.name)

    def test_no_files_default_size(self):
        """
        Test that when a user is a quota_holder for no resources/files, the quota size defaults to 0.
        """
        uquota = self.user.quotas.first()
        self.assertEqual(uquota.size, 0)
        self.assertEqual(uquota.unit, 'GB')

        # check that the resource has no files
        self.assertEqual(self.res.files.all().count(), 0)
        self.assertEqual(self.res.size, 0)

        # check that the user is a quota holder for just this resource
        self.assertTrue(self.user.is_quota_holder(self.res.short_id))
        self.assertEqual(self.user.quotas.count(), 1)

    def test_add_files(self):

        self.assertEqual(0, self.res.size)

        # add files - this is the api we are testing
        add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        # resource should have 3 files
        self.assertEqual(self.res.files.all().count(), 3)
        self.assertEqual(81, self.res.size)

        # add each file of resource to list
        file_list = []
        for f in self.res.files.all():
            file_list.append(f.resource_file.name.split('/')[-1])

        # check if the file name is in the list of files
        self.assertTrue(self.n1 in file_list, "file 1 has not been added")
        self.assertTrue(self.n2 in file_list, "file 2 has not been added")
        self.assertTrue(self.n3 in file_list, "file 3 has not been added")

    def test_add_files_over_quota(self):

        uquota = self.user.quotas.first()
        # make user's quota over hard limit 125%
        from hs_core.tests.utils.test_utils import set_quota_usage_over_hard_limit
        set_quota_usage_over_hard_limit(uquota)

        # add files should raise quota exception now that the quota holder is over limit
        files = [self.myfile1, self.myfile2, self.myfile3]
        with self.assertRaises(QuotaException):
            add_resource_files(self.res.short_id, *files)

        uquota.save_allocated_value(20, "GB")
        # add files should not raise quota exception since they have not exceeded quota
        try:
            add_resource_files(self.res.short_id, *files)
        except QuotaException as ex:
            self.fail("add resource file action should not raise QuotaException for "
                      "over quota cases if quota is not enforced - Quota Exception: " + str(ex))

    def test_add_files_toggles_bag_flag(self):
        self.res.setAVU('bag_modified', 'false')
        self.assertFalse(self.res.getAVU('bag_modified'))
        # add files - this is the api we are testing
        add_resource_files(self.res.short_id, self.myfile1, self.myfile2, self.myfile3)

        self.assertTrue(self.res.getAVU('bag_modified'))
