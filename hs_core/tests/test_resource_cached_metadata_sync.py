"""
Tests updates to cached metadata when metadata elements change.

This test module covers:
CRUD operations on metadata elements and their effects on cached metadata
for metadata elements (Creator, Title, Subject, Date).
"""

from datetime import datetime
import uuid
from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare


class TestDenormalizedMetadataSync(TestCase):
    """Test signal handlers that keep cached metadata in sync with actual metadata elements."""

    def setUp(self):
        """Set up test data."""
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='testuser' + uuid.uuid4().hex,
            first_name='Test',
            last_name='User',
            superuser=False,
            groups=[self.group]
        )

        # Create a test resource using hydroshare.create_resource to properly initialize metadata
        self.resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Resource'
        )

    def tearDown(self):
        """Clean up after tests."""
        self.resource.delete()
        self.user.delete()
        self.group.delete()

    def test_cached_metadata_on_resource_creation(self):
        """Test that cached metadata is properly initialized when a resource is created."""

        # Check that cached metadata is initialized correctly
        self.resource.refresh_from_db()
        self.assertIn('creators', self.resource.cached_metadata)
        self.assertIn('title', self.resource.cached_metadata)
        self.assertIn('subjects', self.resource.cached_metadata)
        self.assertIn('created', self.resource.cached_metadata)
        self.assertIn('modified', self.resource.cached_metadata)
        self.assertIn('status', self.resource.cached_metadata)

    def test_creator_post_save_updates_cached_metadata(self):
        """Test that creating/updating a Creator element triggers cached metadata update."""

        # Initially, cached metadata should contain the resource creator
        # (the creating user is automatically added as the first creator)
        self.resource.refresh_from_db()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 1)
        self.assertEqual(creators[0]['name'], f"{self.user.last_name}, {self.user.first_name}")
        modified_date1 = self.resource.cached_metadata['modified']

        # Create a new creator
        creator = self.resource.metadata.create_element(
            'creator',
            name='John Doe',
            email='john@example.com'
        )

        # Refresh from database and check that cached metadata was updated for creators
        self.resource.refresh_from_db()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 2)  # Now should have 2 creators
        creator_names = [c['name'] for c in creators]
        self.assertIn('John Doe', creator_names)
        # test that the modified date was updated
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update the creator
        # use the update method instead of directly changing the name and saving
        self.resource.metadata.update_element('creator', creator.id, name='Jane Doe')

        # Check that cached metadata was updated for creators
        self.resource.refresh_from_db()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 2)
        creator_names = [c['name'] for c in creators]
        self.assertIn('Jane Doe', creator_names)
        self.assertNotIn('John Doe', creator_names)
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_title_post_save_updates_cached_metadata(self):
        """Test that updating a Title element triggers cached metadata update."""

        # Initially, cached metadata should be empty or have default title
        self.resource.refresh_from_db()

        # get the modified date before updating the title
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Update the title
        # use the update method instead of directly changing the value and saving
        title = self.resource.metadata.title
        self.resource.metadata.update_element('title', title.id, value='Updated Test Resource')

        # Check that cached metadata was updated for title
        self.resource.refresh_from_db()
        title = self.resource.cached_metadata.get('title', '')
        self.assertEqual(title, 'Updated Test Resource')
        # test that the modified date was updated
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_subject_create_updates_cached_metadata(self):
        """Test that creating Subject elements triggers cached metadata update."""

        # Initially, cached metadata should have no subjects
        self.resource.refresh_from_db()
        self.assertEqual(self.resource.cached_metadata.get('subjects', []), [])
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a subject
        self.resource.metadata.create_element('subject', value='hydrology')

        # Check that cached metadata was updated for subjects
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 1)
        self.assertIn('hydrology', subjects)
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Create another subject
        self.resource.metadata.create_element('subject', value='water quality')

        # Check that cached metadata now has both subjects
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 2)
        self.assertIn('hydrology', subjects)
        self.assertIn('water quality', subjects)

    def test_date_post_save_updates_cached_metadata(self):
        """Test that creating/updating Date elements triggers cached metadata update."""

        self.resource.refresh_from_db()
        # test that the created and modified date keys are in the cached metadata
        self.assertIn('created', self.resource.cached_metadata)
        self.assertIn('modified', self.resource.cached_metadata)
        created_date = datetime.fromisoformat(self.resource.cached_metadata['created'])
        modified_date1 = datetime.fromisoformat(self.resource.cached_metadata['modified'])
        self.assertIsInstance(created_date, datetime)
        self.assertIsInstance(modified_date1, datetime)
        # Create a date of type valid
        self.resource.metadata.create_element(
            'date',
            type='valid',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )

        # Check that cached metadata was updated with dates
        self.resource.refresh_from_db()
        # test that the created and modified date keys are in the cached metadata
        self.assertIn('created', self.resource.cached_metadata)
        self.assertIn('modified', self.resource.cached_metadata)
        created_date = datetime.fromisoformat(self.resource.cached_metadata['created'])
        modified_date2 = datetime.fromisoformat(self.resource.cached_metadata['modified'])
        self.assertIsInstance(created_date, datetime)
        self.assertIsInstance(modified_date2, datetime)
        # test the the modified date was updated
        self.assertGreater(modified_date2, modified_date1)

    def test_creator_post_delete_updates_cached_metadata(self):
        """Test that deleting a Creator element triggers cached metadata update."""

        # get the modified date before creating additional creators
        self.resource.refresh_from_db()
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        # Create additional creators (note: there's already 1 creator from resource creation)
        creator1 = self.resource.metadata.create_element(
            'creator',
            name='John Doe',
            email='john@example.com'
        )
        self.resource.metadata.create_element(
            'creator',
            name='Jane Smith',
            email='jane@example.com'
        )

        # Verify all creators are in cached metadata (original creator + 2 new ones)
        self.resource.refresh_from_db()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 3)

        # Track which creators we've found
        found_user = False
        found_john = False
        found_jane = False

        for cr in creators:
            if cr['name'] == f"{self.user.last_name}, {self.user.first_name}":
                self.assertEqual(cr['order'], 1)
                self.assertEqual(cr['hs_user_id'], self.user.id)
                found_user = True
            elif cr['name'] == 'John Doe':
                self.assertEqual(cr['order'], 2)
                self.assertEqual(cr['hs_user_id'], None)
                found_john = True
            elif cr['name'] == 'Jane Smith':
                self.assertEqual(cr['order'], 3)
                self.assertEqual(cr['hs_user_id'], None)
                found_jane = True

        # Verify all expected creators were found
        self.assertTrue(found_user, "User creator not found")
        self.assertTrue(found_john, "John Doe creator not found")
        self.assertTrue(found_jane, "Jane Smith creator not found")

        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Delete one creator
        creator1.delete()

        # Track which creators we've found
        found_user = False
        found_jane = False

        # Check that cached metadata was updated for creators
        self.resource.refresh_from_db()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 2)
        creator_names = [c['name'] for c in creators]
        self.assertIn('Jane Smith', creator_names)
        self.assertNotIn('John Doe', creator_names)
        # check creator ordering
        for cr in creators:
            if cr['name'] == f"{self.user.last_name}, {self.user.first_name}":
                self.assertEqual(cr['order'], 1)
                self.assertEqual(cr['hs_user_id'], self.user.id)
                found_user = True
            elif cr['name'] == 'Jane Smith':
                self.assertEqual(cr['order'], 2)
                self.assertEqual(cr['hs_user_id'], None)
                found_jane = True

        # Verify all expected creators were found
        self.assertTrue(found_user, "User creator not found")
        self.assertTrue(found_jane, "Jane Smith creator not found")

        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_subject_post_delete_updates_cached_metadata(self):
        """Test that deleting Subject elements triggers cached metadata update."""

        # get the modified date before creating subjects
        self.resource.refresh_from_db()
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create 3 subjects first
        self.resource.metadata.create_element('subject', value='hydrology')
        subject2 = self.resource.metadata.create_element('subject', value='water quality')
        subject3 = self.resource.metadata.create_element('subject', value='environmental science')

        # Verify all subjects are in cached metadata
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 3)
        self.assertIn('hydrology', subjects)
        self.assertIn('water quality', subjects)
        self.assertIn('environmental science', subjects)
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Delete one subject
        subject2.delete()

        # Check that cached metadata was updated for subjects
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 2)
        self.assertIn('hydrology', subjects)
        self.assertNotIn('water quality', subjects)
        self.assertIn('environmental science', subjects)
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

        # Delete another subject using remove method this time - note deleteing all subjects is not allowed
        subject3.remove(element_id=subject3.id)

        # Check that cached metadata reflects only one subject
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 1)
        modified_date4 = self.resource.cached_metadata['modified']
        modified_date4 = datetime.fromisoformat(modified_date4)
        self.assertGreater(modified_date4, modified_date3)

    def test_date_post_delete_updates_cached_metadata(self):
        """Test that deleting Date elements triggers cached metadata update."""

        # get the modified date before creating a date element
        self.resource.refresh_from_db()
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        # Create a date element first
        valid_date = self.resource.metadata.create_element(
            'date',
            type='valid',
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )

        # Verify the modified date is updated in cached metadata
        self.resource.refresh_from_db()
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Delete the date
        valid_date.delete()

        # Check that modified date is updated in cached metadata
        self.resource.refresh_from_db()
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_multiple_signal_triggers_in_sequence(self):
        """Test that multiple rapid signal triggers work correctly."""

        # Create multiple subjects in quick succession
        subjects_data = ['hydrology', 'water quality', 'environmental science', 'geology']

        for subject_value in subjects_data:
            self.resource.metadata.create_element('subject', value=subject_value)

        # Verify all subjects are in cached metadata
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 4)
        for subject_value in subjects_data:
            self.assertIn(subject_value, cached_subjects)

        # Delete subjects one by one except the last one - as the last one can't be deleted
        for sub in self.resource.metadata.subjects.all():
            if sub.value != 'geology':
                sub.delete()

        # Verify only the last subject remains
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 1)

    def test_cached_metadata_consistency_after_bulk_operations(self):
        """Test cached metadata consistency after bulk create/delete operations."""

        # Create multiple metadata elements
        subjects_to_create = ['subject1', 'subject2', 'subject3', 'subject4', 'subject5']

        for subject_value in subjects_to_create:
            self.resource.metadata.create_element('subject', value=subject_value)

        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 5)
        self.assertEqual(set(cached_subjects), set(subjects_to_create))

        # Bulk delete by deleting all subjects will not trigger the update of cached metadata
        self.resource.metadata.subjects.all().delete()
        self.assertEqual(self.resource.metadata.subjects.all().count(), 0)

        # Verify cached metadata got updated for subjects
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 0)

        # Create multiple metadata elements
        subjects_to_create = ['subject1', 'subject2', 'subject3', 'subject4', 'subject5']
        for subject_value in subjects_to_create:
            self.resource.metadata.create_element('subject', value=subject_value)

        # delete all subjects one by one except one - as the last one can't be deleted
        for sub in self.resource.metadata.subjects.all():
            if sub.value != 'subject5':
                sub.delete()
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 1)

    def test_signal_handler_with_concurrent_metadata_updates(self):
        """Test signal handlers work correctly with concurrent metadata element updates."""

        # Create additional creators
        self.resource.metadata.create_element(
            'creator',
            name='Creator1',
            email='creator1@example.com'
        )
        self.resource.metadata.create_element(
            'creator',
            name='Creator2',
            email='creator2@example.com'
        )

        # Verify cached metadata is updated with new creators
        self.resource.refresh_from_db()
        cached_creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(cached_creators), 3)
        creator_names = [c['name'] for c in cached_creators]
        self.assertIn('Creator1', creator_names)
        self.assertIn('Creator2', creator_names)

        # update creator ordering
        creator1 = self.resource.metadata.creators.all().filter(name='Creator1').first()
        creator2 = self.resource.metadata.creators.all().filter(name='Creator2').first()

        # update using update method instead of directly changing the order and saving
        self.resource.metadata.update_element('creator', creator1.id, order=3)
        self.resource.metadata.update_element('creator', creator2.id, order=1)

        # Verify cached metadata is updated with updated creator ordering
        self.resource.refresh_from_db()
        cached_creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(cached_creators), 3)
        creator_names = [c['name'] for c in cached_creators]
        self.assertIn('Creator1', creator_names)
        self.assertIn('Creator2', creator_names)
        # check creator ordering in cached metadata
        for cr in cached_creators:
            if cr['name'] == 'Creator1':
                self.assertEqual(cr['order'], 3)
            elif cr['name'] == 'Creator2':
                self.assertEqual(cr['order'], 1)

    def test_cached_modified_date_update_on_abstract_update(self):
        """Test that cached metadata modified date is updated on abstract update."""

        # get the modified date before creating abstract
        self.resource.refresh_from_db()
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create abstract first
        self.resource.metadata.create_element('description', abstract='This is a test resource')

        # Verify the modified date is updated in cached metadata
        self.resource.refresh_from_db()
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)
        # update abstract
        self.resource.metadata.update_element('description', self.resource.metadata.description.id,
                                              abstract='This is an updated abstract')
        # Verify the modified date is updated in cached metadata
        self.resource.refresh_from_db()
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)
