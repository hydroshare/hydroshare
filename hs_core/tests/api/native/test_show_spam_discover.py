import os

from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare


class TestSpamDiscover(TestCase):
    def setUp(self):
        super(TestSpamDiscover, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user who is the owner of the resource to be versioned
        self.owner = hydroshare.create_account(
            'owner@gmail.edu',
            username='owner',
            first_name='owner_firstname',
            last_name='owner_lastname',
            superuser=False,
            groups=[]
        )
        # create a composite resource
        self.copy0 = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Composite Resource'
        )
        test_file1 = open('test1.txt', 'w')
        test_file1.write("Test text file in test1.txt")
        test_file1.close()
        test_file2 = open('test2.txt', 'w')
        test_file2.write("Test text file in test2.txt")
        test_file2.close()
        self.test_file1 = open('test1.txt', 'rb')
        self.test_file2 = open('test2.txt', 'rb')
        hydroshare.add_resource_files(self.copy0.short_id, self.test_file1, self.test_file2)

        self.copy0.raccess.discoverable = True

    def tearDown(self):
        super(TestSpamDiscover, self).tearDown()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_spam_title(self):
        self.assertTrue(self.copy0.show_in_discover)

        self.copy0.metadata.title.value = "Escort spam"
        self.copy0.save()
        self.assertFalse(self.copy0.show_in_discover)
        self.copy0.metadata.title.value = "Test Composite Resource"
        self.copy0.save()
        self.assertTrue(self.copy0.show_in_discover)

    def test_spam_abstract(self):
        metadata = self.copy0.metadata
        # add Abstract (element name is description)
        elem = metadata.create_element("description", abstract="Escore spam")
        self.assertFalse(self.copy0.show_in_discover)

        metadata.delete_element(elem)

        self.assertTrue(self.copy0.show_in_discover)

    def test_spam_subject(self):
        metadata = self.copy0.metadata
        # add keywords (element name is subject)
        elem = metadata.create_element("subject", value="Escort spam")
        self.assertFalse(self.copy0.show_in_discover)

        metadata.delete_element(elem)

        self.assertTrue(self.copy0.show_in_discover)

    def test_admin_allowlist(self):
        self.copy0.metadata.title.value = "Escort spam"
        self.copy0.save()
        self.assertFalse(self.copy0.show_in_discover)

        self.copy0.spam_allowlist = True
        self.copy0.save()
        self.assertTrue(self.copy0.show_in_discover)
        self.copy0.spam_allowlist = False
        self.copy0.save()
        self.assertFalse(self.copy0.show_in_discover)
