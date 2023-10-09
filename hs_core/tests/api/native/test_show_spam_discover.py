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

        self.resource.raccess.discoverable = True
        self.resource.raccess.save()

    def tearDown(self):
        super(TestSpamDiscover, self).tearDown()

    def test_spam_title(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.metadata.update_element('title', self.resource.metadata.title.id, value="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.update_element('title', self.resource.metadata.title.id, value="Test Composite Resource")

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

    def test_spam_abstract(self):
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        # add Abstract (element name is description)
        elem = self.resource.metadata.create_element("description", abstract="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.update_element("description", elem.id, abstract="Test Composite Resource")

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

        self.resource.metadata.update_element('title', self.resource.metadata.title.id, value="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.spam_allowlisted = True
        self.resource.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.spam_allowlisted = False
        self.resource.save()

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.metadata.update_element('title', self.resource.metadata.title.id, value="Test Composite Resource")

        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

    def test_published_with_spam(self):
        """Published resources should always show in discover, even if they contain spam patterns
        """
        self.assertIsNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)

        self.resource.metadata.update_element('title', self.resource.metadata.title.id, value="Escort")

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertFalse(self.resource.show_in_discover)

        self.resource.raccess.published = True

        self.assertIsNotNone(self.resource.spam_patterns)
        self.assertTrue(self.resource.show_in_discover)
