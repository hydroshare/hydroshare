import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin, TestCaseCommonUtilities
from hs_core.management.utils import check_s3_files

from hs_core.models import ResourceFile


class TestResourceFileAPI(MockS3TestCaseMixin,
                          TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestResourceFileAPI, self).setUp()
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

        # create a file
        self.test_file_name1 = 'file1.txt'
        self.file_name_list = [self.test_file_name1, ]

        # put predictable contents into these
        test_file = open(self.test_file_name1, 'w')
        test_file.write("Test text file in file1.txt")
        test_file.close()

        self.test_file_1 = open(self.test_file_name1, 'rb')

    def tearDown(self):
        super(TestResourceFileAPI, self).tearDown()
        self.test_file_1.close()
        os.remove(self.test_file_1.name)

    def test_unfederated_root_path_checks(self):
        """ an unfederated file in the root folder has the proper state after state changes """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        check_s3_files(self.res, stop_on_error=True)

        # add one file to the resource
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1)

        # should succeed without errors
        check_s3_files(self.res, stop_on_error=True)

        # cleaning should not change anything
        check_s3_files(self.res, stop_on_error=True, log_errors=False, return_errors=True,
                          clean_s3=True, clean_django=True, sync_ispublic=True)

        # resource should has only one file at this point
        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        # get the handle of the file created above
        resfile = self.res.files.all()[0]

        # determine where that file should live
        shortpath = os.path.join(self.res.short_id, "data", "contents", "file1.txt")

        self.assertEqual(resfile.file_folder, '')
        self.assertEqual(resfile.storage_path, shortpath)

        self.assertTrue(resfile.path_is_acceptable(shortpath))

        # now try to intentionally corrupt it
        resfile.set_short_path("fuzz.txt")

        # should raise exception
        with self.assertRaises(ValidationError):
            check_s3_files(self.res, stop_on_error=True)

        # now don't raise exception and read error
        errors, ecount, _, _ = check_s3_files(self.res, return_errors=True, log_errors=False)

        self.assertTrue(errors[0].endswith(
            'data/contents/fuzz.txt does not exist in S3'))
        self.assertTrue(errors[1].endswith(
            'data/contents/file1.txt in S3 does not exist in Django'))
        self.assertTrue(errors[2].endswith(
            "type is CompositeResource, title is 'My Test Resource'"))

        # now try to clean it up
        errors, ecount, _, _ = check_s3_files(self.res, return_errors=True, log_errors=False,
                                                 clean_s3=True, clean_django=True)
        self.assertTrue(errors[0].endswith(
            'data/contents/fuzz.txt does not exist in S3 (DELETED FROM DJANGO)'))
        self.assertTrue(errors[1].endswith(
            'data/contents/file1.txt in S3 does not exist in Django (DELETED FROM S3)'))
        self.assertTrue(errors[2].endswith(
            "type is CompositeResource, title is 'My Test Resource'"))

        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # now check should succeed
        errors, ecount, _, _ = check_s3_files(self.res, stop_on_error=True, log_errors=False)
        self.assertEqual(ecount, 0)

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_unfederated_folder_path_checks(self):
        """ an unfederated file in a subfolder has the proper state after state changes """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        ResourceFile.create_folder(self.res, 'foo')

        # should succeed without errors
        check_s3_files(self.res, stop_on_error=True)

        # add one file to the resource
        hydroshare.add_resource_files(self.res.short_id, self.test_file_1, folder='foo')

        # should succeed without errors
        check_s3_files(self.res, stop_on_error=True)

        # resource should has only one file at this point
        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        # get the handle of the file created above
        resfile = self.res.files.all()[0]

        # determine where that file should live
        fullpath = os.path.join(self.res.short_id, "data",
                                "contents", "foo", "file1.txt")

        self.assertEqual(resfile.file_folder, "foo")
        self.assertEqual(resfile.storage_path, fullpath)

        # now try to intentionally corrupt it
        resfile.set_short_path("fuzz.txt")

        # should raise exception
        with self.assertRaises(ValidationError):
            check_s3_files(self.res, stop_on_error=True)

        # now don't raise exception and read error
        errors, ecount, _, _ = check_s3_files(self.res, return_errors=True, log_errors=False)

        self.assertTrue(errors[0].endswith(
            'data/contents/fuzz.txt does not exist in S3'))
        self.assertTrue(errors[1].endswith(
            'data/contents/foo/file1.txt in S3 does not exist in Django'))
        self.assertTrue(errors[2].endswith(
            "type is CompositeResource, title is 'My Test Resource'"))

        # now try to clean it up
        errors, ecount, _, _ = check_s3_files(self.res, return_errors=True, log_errors=False,
                                                 clean_s3=True, clean_django=True)
        self.assertTrue(errors[0].endswith(
            'data/contents/fuzz.txt does not exist in S3 (DELETED FROM DJANGO)'))
        self.assertTrue(errors[1].endswith(
            'data/contents/foo/file1.txt in S3 does not exist in Django (DELETED FROM S3)'))
        self.assertTrue(errors[2].endswith(
            "type is CompositeResource, title is 'My Test Resource'"))

        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # now check should succeed
        errors, ecount, _, _ = check_s3_files(self.res, stop_on_error=True, log_errors=False)
        self.assertEqual(ecount, 0)

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)
