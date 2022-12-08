import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin, TestCaseCommonUtilities


class TestResourceFileFolderOprsAPI(MockIRODSTestCaseMixin,
                                    TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestResourceFileFolderOprsAPI, self).setUp()
        self.hydroshare_author_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user to be used for creating the resource
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

        # create three files
        self.test_file_name1 = 'file1.txt'
        self.test_file_name2 = 'file2.txt'
        self.test_file_name3 = 'file3.txt'
        self.file_name_list = [self.test_file_name1, self.test_file_name2, self.test_file_name3]
        test_file = open(self.test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        test_file = open(self.test_file_name2, 'w')
        test_file.write("Test text file in file2.txt")
        test_file.close()

        test_file = open(self.test_file_name3, 'w')
        test_file.write("Test text file in file3.txt")
        test_file.close()

        self.test_file_1 = open(self.test_file_name1, 'rb')
        self.test_file_2 = open(self.test_file_name2, 'rb')
        self.test_file_3 = open(self.test_file_name3, 'rb')

        # use existing test data file
        self.test_data_file_name = "test.txt"
        self.test_data_file_path = f"hs_core/tests/data/{self.test_data_file_name}"
        self.test_data_zip_file_name = "test.zip"
        self.test_data_zip_file_path = f"hs_core/tests/data/{self.test_data_zip_file_name}"
        self.test_data_file = open(self.test_data_file_path, 'rb')
        self.test_data_zip_file = open(self.test_data_zip_file_path, 'rb')

    def tearDown(self):
        super(TestResourceFileFolderOprsAPI, self).tearDown()
        self.test_file_1.close()
        os.remove(self.test_file_1.name)
        self.test_file_2.close()
        os.remove(self.test_file_2.name)
        self.test_file_3.close()
        os.remove(self.test_file_3.name)
        self.test_data_file.close()
        self.test_data_zip_file.close()

    def test_resource_file_folder_oprs(self):
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add the three files to the resource
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1, self.test_file_2,
                                      self.test_file_3)

        # resource should has only three files at this point
        self.assertEqual(self.res.files.all().count(), 3,
                         msg="resource file count didn't match")
        super(TestResourceFileFolderOprsAPI, self).resource_file_oprs()

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)
