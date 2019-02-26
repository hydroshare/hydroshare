import os
import unittest

from django.contrib.auth.models import User, Group

from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.hydroshare.users import create_account
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.hydroshare.utils import QuotaException, resource_file_add_pre_process
from theme.models import QuotaMessage


class TestAddResourceFiles(MockIRODSTestCaseMixin, unittest.TestCase):
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
        self.myfile1 = open(self.n1, "r")
        self.myfile2 = open(self.n2, "r")
        self.myfile3 = open(self.n3, "r")

    def tearDown(self):
        super(TestAddResourceFiles, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        self.myfile1.close()
        os.remove(self.myfile1.name)
        self.myfile2.close()
        os.remove(self.myfile2.name)
        self.myfile3.close()
        os.remove(self.myfile3.name)

    def test_add_files(self):
        # create a resource
        res = create_resource(resource_type='GenericResource',
                              owner=self.user,
                              title='Test Resource',
                              metadata=[],)

        self.assertEqual(0, res.size)

        # add files - this is the api we are testing
        add_resource_files(res.short_id, self.myfile1, self.myfile2, self.myfile3)

        # resource should have 3 files
        self.assertEquals(res.files.all().count(), 3)
        self.assertEqual(81, res.size)

        # add each file of resource to list
        file_list = []
        for f in res.files.all():
            file_list.append(f.resource_file.name.split('/')[-1])

        # check if the file name is in the list of files
        self.assertTrue(self.n1 in file_list, "file 1 has not been added")
        self.assertTrue(self.n2 in file_list, "file 2 has not been added")
        self.assertTrue(self.n3 in file_list, "file 3 has not been added")
        res.delete()

    def test_add_files_over_quota(self):
        # create a resource
        res = create_resource(resource_type='GenericResource',
                              owner=self.user,
                              title='Test Resource',
                              metadata=[],)

        if not QuotaMessage.objects.exists():
            QuotaMessage.objects.create()
        qmsg = QuotaMessage.objects.first()
        qmsg.enforce_quota = True
        qmsg.save()

        uquota = self.user.quotas.first()
        # make user's quota over hard limit 125%
        uquota.used_value = uquota.allocated_value * 1.3
        uquota.save()

        # add files should raise quota exception now that the quota holder is over hard limit
        # and quota enforce flag is set to True
        files = [self.myfile1, self.myfile2, self.myfile3]
        with self.assertRaises(QuotaException):
            resource_file_add_pre_process(resource=res, files=files,
                                          user=self.user,
                                          extract_metadata=False)

        qmsg.enforce_quota = False
        qmsg.save()
        # add files should not raise quota exception since enforce_quota flag is set to False
        try:
            resource_file_add_pre_process(resource=res, files=files,
                                          user=self.user,
                                          extract_metadata=False)
        except QuotaException as ex:
            self.fail("add resource file action should not raise QuotaException for "
                      "over quota cases if quota is not enforced - Quota Exception: " + ex.message)

        res.delete()
