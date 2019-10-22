# Test discovery content types as inferred from resource contents.
import os

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin, TestCaseCommonUtilities
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


class TestContentTypes(MockIRODSTestCaseMixin,
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

    def tearDown(self):
        super(TestContentTypes, self).tearDown()
        for f in self.filenames:
            os.remove(f)

    def test_generic_data_classification(self):
        """ files with recognized extensions are classified properly """
        # resource should not have any files at this point
        self.assertEqual(self.res.files.all().count(), 0,
                         msg="resource file count didn't match")

        # add one file to the resource
        for f in self.filenames:
            test_file_handle = open(f, 'r')
            hydroshare.add_resource_files(self.res.short_id, test_file_handle)

        self.assertEqual(self.res.files.all().count(), 5,
                         msg="resource file count didn't match")

        types = get_content_types(self.res)
        self.assertTrue(is_equal_to_as_set(
                            types[0],
                            ['Composite', 'Document', 'Presentation', 'Spreadsheet',
                             'Jupyter Notebook']))

        self.assertTrue(is_equal_to_as_set(types[1], []))  # no left-over extensions

        # delete resources to clean up
        hydroshare.delete_resource(self.res.short_id)
