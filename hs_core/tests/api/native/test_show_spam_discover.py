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
        self.resource = hydroshare.create_resource(
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
        hydroshare.add_resource_files(self.resource.short_id, self.test_file1, self.test_file2)

        self.resource.raccess.discoverable = True
        self.resource.raccess.save()

    def tearDown(self):
        super(TestSpamDiscover, self).tearDown()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_spam_title(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.metadata.title.value = "Escort"
        self.resource.metadata.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.title.value = "Test Composite Resource"
        self.resource.metadata.save()

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

    def test_spam_abstract(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        # add Abstract (element name is description)
        elem = self.resource.metadata.create_element("description", abstract="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.update_element("description", elem.id, value="Test Composite Resource")

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

    def test_spam_subject(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        # add keywords (element name is subject)
        elem = self.resource.metadata.create_element("subject", value="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.update_element("subject", elem.id, value="Test subject")

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

    def test_admin_allowlist(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.metadata.title.value = "Escort"
        self.resource.metadata.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.spam_allowlist = True
        self.resource.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.spam_allowlist = False
        self.resource.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.title.value = "Test Composite Resource"
        self.resource.metadata.save()

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)
