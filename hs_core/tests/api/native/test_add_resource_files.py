import os
import unittest

from django.contrib.auth.models import User, Group

from hs_core.hydroshare.resource import add_resource_files, create_resource
from hs_core.hydroshare.users import create_account
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin


class TestAddResourceFiles(MockIRODSTestCaseMixin, unittest.TestCase):
    def setUp(self):
        super(TestAddResourceFiles, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

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
        user = create_account(
            'shauntheta@gmail.com',
            username='shaun',
            first_name='Shaun',
            last_name='Livingston',
            superuser=False,
            groups=[]
        )

        # create files
        n1 = "test1.txt"
        n2 = "test2.txt"
        n3 = "test3.txt"

        open(n1, "w").close()
        open(n2, "w").close()
        open(n3, "w").close()

        # open files for read and upload
        self.myfile1 = open(n1, "r")
        self.myfile2 = open(n2, "r")
        self.myfile3 = open(n3, "r")

        # create a resource
        res = create_resource(resource_type='GenericResource',
                              owner=user,
                              title='Test Resource',
                              metadata=[],)

        # delete all resource files for created resource
        res.files.all().delete()

        # add files - this is the api we are testing
        add_resource_files(res.short_id, self.myfile1, self.myfile2, self.myfile3)

        # resource should have 3 files
        self.assertEquals(res.files.all().count(), 3)

        # add each file of resource to list
        file_list = []
        for f in res.files.all():
            file_list.append(f.resource_file.name.split('/')[-1])

        # check if the file name is in the list of files
        self.assertTrue(n1 in file_list, "file 1 has not been added")
        self.assertTrue(n2 in file_list, "file 2 has not been added")
        self.assertTrue(n3 in file_list, "file 3 has not been added")
