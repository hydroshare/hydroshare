# Test discovery content types as inferred from resource contents.
import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin, TestCaseCommonUtilities
from hs_core.search_indexes import get_content_types


def is_equal_to_as_set(l1, l2):
    """ return true if two lists contain the same content
    :param l1: first list
    :param l2: second list
    :return: whether lists match
    """
    # Note specifically that set(l1) == set(l2) does not work as expected.
    return len(set(l1) & set(l2)) == len(set(l1)) and \
        len(set(l1) | set(l2)) == len(set(l1))


class TestContentTypes(MockS3TestCaseMixin,
                       TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestContentTypes, self).setUp()
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

        # create empty files with appropriate extensions
        self.filenames = ['file.pdf', 'file.doc', 'file.ppt', 'file.csv', 'file.ipynb']
        self.content_types = ['Document', 'Document', 'Presentation', 'Spreadsheet',
                              'Jupyter Notebook']
        for f in self.filenames:
            test_file = open(f, 'w')
            test_file.close()

        # create empty files with non-conforming extensions
        self.weird_filenames = ['file.foo', 'file.bar']
        self.weird_extensions = ['foo', 'bar']
        for f in self.weird_filenames:
            test_file = open(f, 'w')
            test_file.close()

    def tearDown(self):
        super(TestContentTypes, self).tearDown()
        for f in self.filenames:
            os.remove(f)
        for f in self.weird_filenames:
            os.remove(f)

    def test_file_extension_classification(self):
        """ files with recognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add all files to the resource
        for f in self.filenames:
            test_file_handle = open(f, 'r')
            hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 5,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        self.assertTrue(is_equal_to_as_set(
            types[0],
            ['Resource', 'Document', 'Presentation', 'Spreadsheet',
             'Jupyter Notebook']))

        self.assertTrue(is_equal_to_as_set(types[1], []))  # no left-over extensions

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_pdf_classification(self):
        """ files with recognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add one file to the resource
        test_file_handle = open(self.filenames[0], 'r')
        hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        self.assertTrue(is_equal_to_as_set(types[0], ['Resource', self.content_types[0]]))

        self.assertTrue(is_equal_to_as_set(types[1], []))  # no left-over extensions

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_ppt_classification(self):
        """ files with recognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add one file to the resource
        test_file_handle = open(self.filenames[2], 'r')
        hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        self.assertTrue(is_equal_to_as_set(types[0], ['Resource', self.content_types[2]]))

        self.assertTrue(is_equal_to_as_set(types[1], []))  # no left-over extensions

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_csv_classification(self):
        """ files with recognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add one file to the resource
        test_file_handle = open(self.filenames[3], 'r')
        hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 1,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        self.assertTrue(is_equal_to_as_set(types[0], ['Resource', self.content_types[3]]))

        self.assertTrue(is_equal_to_as_set(types[1], []))  # no left-over extensions

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)

    def test_weird_extensions(self):
        """ files with unrecognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add all files to the resource
        for f in self.weird_filenames:
            test_file_handle = open(f, 'r')
            hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 2,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        # no extensions match content types
        self.assertTrue(is_equal_to_as_set(types[0], ['Resource', 'Generic Data']))
        # extensions are flagged as not matching
        self.assertTrue(is_equal_to_as_set(types[1], self.weird_extensions))

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)
