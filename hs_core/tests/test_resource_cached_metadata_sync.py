"""
Tests updates to cached metadata when metadata elements change.

This test module covers:
CRUD operations on metadata elements and their effects on cached metadata
for metadata elements (Creator, Title, Subject, Date, Status, etc.).
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
        self.new_resource = None

    def tearDown(self):
        """Clean up after tests."""
        self.resource.delete()
        if self.new_resource:
            self.new_resource.delete()
        self.user.delete()
        self.group.delete()

    def test_cached_metadata_on_resource_creation(self):
        """Test that cached metadata is properly initialized when a resource is created."""

        # Check that cached metadata is initialized correctly
        self.resource.refresh_from_db()
        self.assertIn('creators', self.resource.cached_metadata)
        self.assertIn('contributors', self.resource.cached_metadata)
        self.assertIn('title', self.resource.cached_metadata)
        self.assertIn('subjects', self.resource.cached_metadata)
        self.assertIn('created', self.resource.cached_metadata)
        self.assertIn('modified', self.resource.cached_metadata)
        self.assertIn('status', self.resource.cached_metadata)
        self.assertIn('abstract', self.resource.cached_metadata)
        self.assertIn('temporal_coverage', self.resource.cached_metadata)
        self.assertIn('spatial_coverage', self.resource.cached_metadata)
        self.assertIn('relations', self.resource.cached_metadata)
        self.assertIn('geospatial_relations', self.resource.cached_metadata)
        self.assertIn('funding_agencies', self.resource.cached_metadata)
        self.assertIn('rights', self.resource.cached_metadata)
        self.assertIn('language', self.resource.cached_metadata)
        self.assertIn('identifiers', self.resource.cached_metadata)
        self.assertIn('type', self.resource.cached_metadata)
        self.assertIn('publisher', self.resource.cached_metadata)

        # check the metadata that are automatically created and is not updated ever
        language = self.resource.cached_metadata.get('language', '')
        self.assertEqual(language, 'eng')
        _type = self.resource.cached_metadata.get('type', '')
        self.assertEqual(_type, f'{hydroshare.utils.current_site_url()}/terms/CompositeResource')
        hs_identifier = self.resource.cached_metadata.get('identifiers', [])
        self.assertEqual(len(hs_identifier), 1)
        self.assertEqual(hs_identifier[0]['name'], 'hydroShareIdentifier')

    def test_creator_post_save_updates_cached_metadata(self):
        """Test that creating/updating a Creator element triggers cached metadata update."""

        # Initially, cached metadata should contain the resource creator
        # (the creating user is automatically added as the first creator)
        self.resource.refresh_from_db()
        res_creator = self.resource.metadata.creators.first()
        creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(creators), 1)
        self.assertEqual(creators[0]['name'], f"{res_creator.name}")
        self.assertEqual(creators[0]['email'], res_creator.email)
        self.assertEqual(creators[0]['id'], res_creator.id)
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
        self.assertEqual(creators[1]['email'], 'john@example.com')
        self.assertEqual(creators[1]['id'], creator.id)
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
        self.assertEqual(creators[1]['email'], 'john@example.com')
        self.assertEqual(creators[1]['id'], creator.id)
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_contributor_post_save_updates_cached_metadata(self):
        """Test that creating/updating a Contributor element triggers cached metadata update."""
        # Initially, cached metadata should have no contributors
        self.resource.refresh_from_db()
        contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(contributors), 0)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        # Create a contributor
        contributor = self.resource.metadata.create_element(
            'contributor',
            name='John Doe',
            email='john@example.com'
        )

        # Refresh from database and check that cached metadata was updated for contributors
        self.resource.refresh_from_db()
        contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(contributors), 1)  # Now should have 1 contributor
        self.assertEqual(contributors[0]['id'], contributor.id)
        self.assertEqual(contributors[0]['name'], 'John Doe')
        self.assertEqual(contributors[0]['email'], 'john@example.com')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)
        # Update the contributor
        # use the update method instead of directly changing the name and saving
        self.resource.metadata.update_element('contributor', contributor.id, phone='555-555-5555')

        # Check that cached metadata was updated for contributors
        self.resource.refresh_from_db()
        contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(contributors), 1)  # Now should have 1 contributor
        self.assertEqual(contributors[0]['phone'], '555-555-5555')
        self.assertEqual(contributors[0]['id'], contributor.id)
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
        cached_title = self.resource.cached_metadata.get('title', {})
        self.assertEqual(cached_title.get('value'), 'Updated Test Resource')
        self.assertEqual(cached_title.get('id'), title.id)
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
        # test for published date
        self.resource.set_published(True)
        # create the published date
        self.resource.metadata.create_element('date', type='published', start_date=self.resource.updated)
        self.resource.refresh_from_db()
        self.assertIn('published_date', self.resource.cached_metadata)

    def test_creator_post_delete_updates_cached_metadata(self):
        """Test that deleting a Creator element triggers cached metadata update."""

        # get the modified date before creating additional creators
        self.resource.refresh_from_db()
        res_creator = self.resource.metadata.creators.first()
        cached_creators = self.resource.cached_metadata.get('creators', [])
        self.assertEqual(len(cached_creators), 1)
        self.assertEqual(cached_creators[0]['id'], res_creator.id)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        # Create additional creators (note: there's already 1 creator from resource creation)
        creator1 = self.resource.metadata.create_element(
            'creator',
            name='John Doe',
            email='john@example.com'
        )
        creator2 = self.resource.metadata.create_element(
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
            if cr['id'] == res_creator.id:
                self.assertEqual(cr['name'], f"{res_creator.name}")
                self.assertEqual(cr['email'], res_creator.email)
                self.assertEqual(cr['order'], 1)
                self.assertEqual(cr['hs_user_id'], self.user.id)
                found_user = True
            elif cr['id'] == creator1.id:
                self.assertEqual(cr['name'], 'John Doe')
                self.assertEqual(cr['email'], 'john@example.com')
                self.assertEqual(cr['order'], 2)
                self.assertEqual(cr['hs_user_id'], None)
                found_john = True
            elif cr['id'] == creator2.id:
                self.assertEqual(cr['name'], 'Jane Smith')
                self.assertEqual(cr['email'], 'jane@example.com')
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
            if cr['id'] == res_creator.id:
                self.assertEqual(cr['name'], f"{res_creator.name}")
                self.assertEqual(cr['email'], res_creator.email)
                self.assertEqual(cr['order'], 1)
                self.assertEqual(cr['hs_user_id'], self.user.id)
                found_user = True
            elif cr['id'] == creator2.id:
                self.assertEqual(cr['name'], 'Jane Smith')
                self.assertEqual(cr['email'], 'jane@example.com')
                self.assertEqual(cr['order'], 2)
                self.assertEqual(cr['hs_user_id'], None)
                found_jane = True

        # Verify all expected creators were found
        self.assertTrue(found_user, "User creator not found")
        self.assertTrue(found_jane, "Jane Smith creator not found")

        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_contributor_post_delete_updates_cached_metadata(self):
        """Test that deleting a Contributor element triggers cached metadata update."""
        # get the modified date before creating contributors
        self.resource.refresh_from_db()
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)
        # Create a contributor
        contributor = self.resource.metadata.create_element(
            'contributor',
            name='John Doe',
            email='john@example.com'
        )

        # Verify contributor is in cached metadata
        self.resource.refresh_from_db()
        contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(contributors), 1)
        self.assertEqual(contributors[0]['id'], contributor.id)
        self.assertEqual(contributors[0]['name'], 'John Doe')
        self.assertEqual(contributors[0]['email'], 'john@example.com')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Delete the contributor
        contributor.delete()

        # Check that cached metadata was updated for contributors
        self.resource.refresh_from_db()
        contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(contributors), 0)
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

        # Delete another subject using remove method this time
        subject3.remove(element_id=subject3.id)

        # Check that cached metadata reflects only one subject
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 1)
        modified_date4 = self.resource.cached_metadata['modified']
        modified_date4 = datetime.fromisoformat(modified_date4)
        self.assertGreater(modified_date4, modified_date3)

        # delete all subjects
        self.resource.metadata.subjects.all().delete()
        self.resource.refresh_from_db()
        subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(subjects), 0)
        modified_date5 = self.resource.cached_metadata['modified']
        modified_date5 = datetime.fromisoformat(modified_date5)
        self.assertGreater(modified_date5, modified_date4)

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
        res_creator = self.resource.metadata.creators.first()
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
        match_count = 0
        for cr in cached_creators:
            if cr['id'] == res_creator.id:
                self.assertEqual(cr['order'], 2)
                match_count += 1
            elif cr['id'] == creator1.id:
                self.assertEqual(cr['order'], 3)
                match_count += 1
            elif cr['id'] == creator2.id:
                self.assertEqual(cr['order'], 1)
                match_count += 1
        self.assertEqual(match_count, 3)

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

    def test_description_post_save_updates_cached_metadata(self):
        """Test that creating/updating a Description (abstract) element triggers cached metadata
        update for abstract field.
        """

        # Initially, cached metadata should have empty abstract since no description was created
        # as part of creating the resource
        self.resource.refresh_from_db()
        initial_abstract = self.resource.cached_metadata.get('abstract', {})
        self.assertEqual(initial_abstract, {})
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a description (abstract)
        abstract = 'This is a test resource abstract'
        self.resource.metadata.create_element('description', abstract=abstract)

        # Check that cached metadata was updated for abstract
        self.resource.refresh_from_db()
        cached_abstract = self.resource.cached_metadata.get('abstract', {})
        self.assertEqual(cached_abstract.get('id'), self.resource.metadata.description.id)
        self.assertEqual(cached_abstract.get('value'), abstract)

        # Test that the modified date was updated
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update the description (abstract)
        description = self.resource.metadata.description
        abstract = 'This is an updated test resource abstract'
        self.resource.metadata.update_element('description', description.id, abstract=abstract)

        # Check that cached metadata was updated for the new abstract
        self.resource.refresh_from_db()
        cached_abstract = self.resource.cached_metadata.get('abstract', {})
        self.assertEqual(cached_abstract.get('id'), self.resource.metadata.description.id)
        self.assertEqual(cached_abstract.get('value'), abstract)

        # Test that the modified date was updated again
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_coverage_temporal_post_save_updates_cached_metadata(self):
        """Test that creating/updating temporal coverage triggers cached metadata update."""
        # Initially, cached metadata should have empty temporal coverage
        self.resource.refresh_from_db()
        temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(temporal_coverage, {})
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create temporal coverage
        coverage = self.resource.metadata.create_element(
            'coverage',
            type='period',
            value={
                'name': 'Test Period',
                'start': '2020-01-01',
                'end': '2020-12-31'
            }
        )

        # Verify temporal coverage is in cached metadata
        self.resource.refresh_from_db()
        temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(temporal_coverage['id'], coverage.id)
        self.assertEqual(temporal_coverage['start_date'], '2020-01-01')
        self.assertEqual(temporal_coverage['end_date'], '2020-12-31')
        self.assertEqual(temporal_coverage['name'], 'Test Period')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update temporal coverage
        self.resource.metadata.update_element(
            'coverage',
            coverage.id,
            type='period',
            value={
                'name': 'Updated Period',
                'start': '2021-01-01',
                'end': '2021-12-31'
            }
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(temporal_coverage['id'], coverage.id)
        self.assertEqual(temporal_coverage['start_date'], '2021-01-01')
        self.assertEqual(temporal_coverage['end_date'], '2021-12-31')
        self.assertEqual(temporal_coverage['name'], 'Updated Period')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_coverage_temporal_post_delete_updates_cached_metadata(self):
        """Test that deleting temporal coverage triggers cached metadata update."""
        # Create temporal coverage first
        coverage = self.resource.metadata.create_element(
            'coverage',
            type='period',
            value={
                'name': 'Test Period',
                'start': '2020-01-01',
                'end': '2020-12-31'
            }
        )

        # Verify temporal coverage is in cached metadata
        self.resource.refresh_from_db()
        temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(temporal_coverage['id'], coverage.id)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Delete temporal coverage
        coverage.delete()

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(temporal_coverage, {})
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_coverage_spatial_point_post_save_updates_cached_metadata(self):
        """Test that creating/updating spatial coverage (point) triggers cached metadata update."""
        # Initially, cached metadata should have empty spatial coverage
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertFalse(spatial_coverage.get('exists'))
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create spatial coverage (point)
        coverage = self.resource.metadata.create_element(
            'coverage',
            type='point',
            value={
                'name': 'Test Point',
                'east': -111.123,
                'north': 40.456,
                'units': 'Decimal degrees',
                'elevation': 1500,
                'zunits': 'meters',
                'projection': 'WGS 84 EPSG:4326'
            }
        )

        # Verify spatial coverage is in cached metadata
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertTrue(spatial_coverage['exists'])
        self.assertEqual(spatial_coverage['id'], coverage.id)
        self.assertEqual(spatial_coverage['type'], 'point')
        self.assertEqual(spatial_coverage['east'], -111.123)
        self.assertEqual(spatial_coverage['north'], 40.456)
        self.assertEqual(spatial_coverage['units'], 'Decimal degrees')
        self.assertEqual(spatial_coverage['elevation'], 1500)
        self.assertEqual(spatial_coverage['zunits'], 'meters')
        self.assertEqual(spatial_coverage['projection'], 'WGS 84 EPSG:4326')
        self.assertEqual(spatial_coverage['name'], 'Test Point')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update spatial coverage
        self.resource.metadata.update_element(
            'coverage',
            coverage.id,
            type='point',
            value={
                'name': 'Updated Point',
                'east': -112.456,
                'north': 41.789,
                'units': 'Decimal degrees',
                'elevation': 2000,
                'zunits': 'meters',
                'projection': 'WGS 84 EPSG:4326'
            }
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertTrue(spatial_coverage['exists'])
        self.assertEqual(spatial_coverage['east'], -112.456)
        self.assertEqual(spatial_coverage['north'], 41.789)
        self.assertEqual(spatial_coverage['elevation'], 2000)
        self.assertEqual(spatial_coverage['name'], 'Updated Point')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_coverage_spatial_box_post_save_updates_cached_metadata(self):
        """Test that creating/updating spatial coverage (box) triggers cached metadata update."""
        # Create spatial coverage (box)
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertFalse(spatial_coverage.get('exists'))
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        coverage = self.resource.metadata.create_element(
            'coverage',
            type='box',
            value={
                'name': 'Test Box',
                'northlimit': 41.5,
                'eastlimit': -110.0,
                'southlimit': 40.0,
                'westlimit': -112.0,
                'units': 'Decimal degrees',
                'projection': 'WGS 84 EPSG:4326'
            }
        )

        # Verify spatial coverage is in cached metadata
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertTrue(spatial_coverage['exists'])
        self.assertEqual(spatial_coverage['id'], coverage.id)
        self.assertEqual(spatial_coverage['type'], 'box')
        self.assertEqual(spatial_coverage['northlimit'], 41.5)
        self.assertEqual(spatial_coverage['eastlimit'], -110.0)
        self.assertEqual(spatial_coverage['southlimit'], 40.0)
        self.assertEqual(spatial_coverage['westlimit'], -112.0)
        self.assertEqual(spatial_coverage['units'], 'Decimal degrees')
        self.assertEqual(spatial_coverage['name'], 'Test Box')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update spatial coverage
        self.resource.metadata.update_element(
            'coverage',
            coverage.id,
            type='box',
            value={
                'name': 'Updated Box',
                'northlimit': 42.0,
                'eastlimit': -109.0,
                'southlimit': 39.5,
                'westlimit': -113.0,
                'units': 'Decimal degrees',
                'projection': 'WGS 84 EPSG:4326'
            }
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertTrue(spatial_coverage['exists'])
        self.assertEqual(spatial_coverage['id'], coverage.id)
        self.assertEqual(spatial_coverage['type'], 'box')
        self.assertEqual(spatial_coverage['northlimit'], 42.0)
        self.assertEqual(spatial_coverage['eastlimit'], -109.0)
        self.assertEqual(spatial_coverage['southlimit'], 39.5)
        self.assertEqual(spatial_coverage['westlimit'], -113.0)
        self.assertEqual(spatial_coverage['units'], 'Decimal degrees')
        self.assertEqual(spatial_coverage['name'], 'Updated Box')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_coverage_spatial_post_delete_updates_cached_metadata(self):
        """Test that deleting spatial coverage triggers cached metadata update."""
        # Create spatial coverage first
        coverage = self.resource.metadata.create_element(
            'coverage',
            type='point',
            value={
                'name': 'Test Point',
                'east': -111.123,
                'north': 40.456,
                'units': 'Decimal degrees'
            }
        )

        # Verify spatial coverage is in cached metadata
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertTrue(spatial_coverage['exists'])
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Delete spatial coverage
        coverage.delete()

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertFalse(spatial_coverage['exists'])
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_relation_post_save_updates_cached_metadata(self):
        """Test that creating/updating a Relation element triggers cached metadata update."""
        # Initially, cached metadata should have empty relations
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 0)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a relation
        relation = self.resource.metadata.create_element(
            'relation',
            type='isDescribedBy',
            value='https://www.hydroshare.org/resource/12345'
        )

        # Verify relation is in cached metadata
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]['id'], relation.id)
        self.assertEqual(relations[0]['type'], 'isDescribedBy')
        self.assertEqual(relations[0]['type_description'], 'This resource is described by')
        self.assertTrue(relations[0]['is_user_editable'])
        self.assertEqual(relations[0]['value'], 'https://www.hydroshare.org/resource/12345')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update the relation
        self.resource.metadata.update_element(
            'relation',
            relation.id,
            type='isPartOf',
            value='https://www.hydroshare.org/resource/67890'
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]['id'], relation.id)
        self.assertEqual(relations[0]['type'], 'isPartOf')
        self.assertEqual(relations[0]['type_description'], 'The content of this resource is part of')
        self.assertFalse(relations[0]['is_user_editable'])
        self.assertEqual(relations[0]['value'], 'https://www.hydroshare.org/resource/67890')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_relation_post_delete_updates_cached_metadata(self):
        """Test that deleting a Relation element triggers cached metadata update."""
        # Create relations first
        relation1 = self.resource.metadata.create_element(
            'relation',
            type='isPartOf',
            value='https://www.hydroshare.org/resource/12345'
        )
        relation2 = self.resource.metadata.create_element(
            'relation',
            type='hasPart',
            value='https://www.hydroshare.org/resource/67890'
        )

        # Verify relations are in cached metadata
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 2)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Delete one relation
        relation1.delete()

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]['id'], relation2.id)
        self.assertEqual(relations[0]['type'], 'hasPart')
        self.assertEqual(relations[0]['type_description'], 'This resource includes')
        self.assertFalse(relations[0]['is_user_editable'])
        self.assertEqual(relations[0]['value'], 'https://www.hydroshare.org/resource/67890')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_geospatialrelation_post_save_updates_cached_metadata(self):
        """Test that creating/updating a GeospatialRelation element triggers cached metadata update."""
        # Initially, cached metadata should have empty geospatial relations
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 0)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a geospatial relation
        geospatial_relation = self.resource.metadata.create_element(
            'geospatialrelation',
            type='relation',
            value='https://geoconnex.us/ref/gages/123456',
            text='USGS Gage 123456'
        )

        # Verify geospatial relation is in cached metadata
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 1)
        self.assertEqual(geospatial_relations[0]['id'], geospatial_relation.id)
        self.assertEqual(geospatial_relations[0]['type'], 'relation')
        self.assertEqual(geospatial_relations[0]['value'], 'https://geoconnex.us/ref/gages/123456')
        self.assertEqual(geospatial_relations[0]['text'], 'USGS Gage 123456')
        self.assertEqual(geospatial_relations[0]['type_description'], 'The content of this resource is related to')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update the geospatial relation
        self.resource.metadata.update_element(
            'geospatialrelation',
            geospatial_relation.id,
            type='relation',
            value='https://geoconnex.us/ref/gages/789012',
            text='USGS Gage 789012'
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 1)
        self.assertEqual(geospatial_relations[0]['id'], geospatial_relation.id)
        self.assertEqual(geospatial_relations[0]['value'], 'https://geoconnex.us/ref/gages/789012')
        self.assertEqual(geospatial_relations[0]['text'], 'USGS Gage 789012')
        self.assertEqual(geospatial_relations[0]['type_description'], 'The content of this resource is related to')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_geospatialrelation_post_delete_updates_cached_metadata(self):
        """Test that deleting a GeospatialRelation element triggers cached metadata update."""
        # Create geospatial relations first
        geospatial_relation1 = self.resource.metadata.create_element(
            'geospatialrelation',
            type='relation',
            value='https://geoconnex.us/ref/gages/123456',
            text='USGS Gage 123456'
        )
        geospatial_relation2 = self.resource.metadata.create_element(
            'geospatialrelation',
            type='relation',
            value='https://geoconnex.us/ref/gages/789012',
            text='USGS Gage 789012'
        )

        # Verify geospatial relations are in cached metadata
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 2)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Delete one geospatial relation
        geospatial_relation1.delete()

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 1)
        self.assertEqual(geospatial_relations[0]['id'], geospatial_relation2.id)
        self.assertEqual(geospatial_relations[0]['text'], 'USGS Gage 789012')
        self.assertEqual(geospatial_relations[0]['type_description'], 'The content of this resource is related to')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_fundingagency_post_save_updates_cached_metadata(self):
        """Test that creating/updating a FundingAgency element triggers cached metadata update."""
        # Initially, cached metadata should have empty funding agencies
        self.resource.refresh_from_db()
        funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(funding_agencies), 0)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a funding agency
        funding_agency = self.resource.metadata.create_element(
            'fundingagency',
            agency_name='National Science Foundation',
            award_title='Hydrological Research Grant',
            award_number='NSF-12345',
            agency_url='https://www.nsf.gov'
        )

        # Verify funding agency is in cached metadata
        self.resource.refresh_from_db()
        funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(funding_agencies), 1)
        self.assertEqual(funding_agencies[0]['id'], funding_agency.id)
        self.assertEqual(funding_agencies[0]['agency_name'], 'National Science Foundation')
        self.assertEqual(funding_agencies[0]['award_title'], 'Hydrological Research Grant')
        self.assertEqual(funding_agencies[0]['award_number'], 'NSF-12345')
        self.assertEqual(funding_agencies[0]['agency_url'], 'https://www.nsf.gov')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Update the funding agency
        self.resource.metadata.update_element(
            'fundingagency',
            funding_agency.id,
            agency_name='National Science Foundation',
            award_title='Updated Hydrological Research Grant',
            award_number='NSF-67890',
            agency_url='https://www.nsf.gov'
        )

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(funding_agencies), 1)
        self.assertEqual(funding_agencies[0]['id'], funding_agency.id)
        self.assertEqual(funding_agencies[0]['award_title'], 'Updated Hydrological Research Grant')
        self.assertEqual(funding_agencies[0]['award_number'], 'NSF-67890')
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

    def test_fundingagency_post_delete_updates_cached_metadata(self):
        """Test that deleting a FundingAgency element triggers cached metadata update."""
        # Create funding agencies first
        funding_agency1 = self.resource.metadata.create_element(
            'fundingagency',
            agency_name='National Science Foundation',
            award_title='Grant 1',
            award_number='NSF-12345'
        )
        funding_agency2 = self.resource.metadata.create_element(
            'fundingagency',
            agency_name='Department of Energy',
            award_title='Grant 2',
            award_number='DOE-67890'
        )

        # Verify funding agencies are in cached metadata
        self.resource.refresh_from_db()
        funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(funding_agencies), 2)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Delete one funding agency
        funding_agency1.delete()

        # Verify cached metadata was updated
        self.resource.refresh_from_db()
        funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(funding_agencies), 1)
        self.assertEqual(funding_agencies[0]['id'], funding_agency2.id)
        self.assertEqual(funding_agencies[0]['agency_name'], 'Department of Energy')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_identifier_post_save_updates_cached_metadata(self):
        """Test that creating an Identifier element triggers cached metadata update."""

        # NOTE: The identifier metadata is created automatically by the system when a resource is created or published.
        # There is no UI for updating or deleting identifiers. So we are only testing the creation of identifiers.

        # Initially, cached metadata should have one identifier (hydroShareIdentifier)
        self.resource.refresh_from_db()
        identifiers = self.resource.cached_metadata.get('identifiers', [])
        self.assertEqual(len(identifiers), 1)  # hydroShareIdentifier is created by default
        self.assertEqual(identifiers[0]['name'], 'hydroShareIdentifier')
        self.assertEqual(identifiers[0]['id'], self.resource.metadata.identifiers.first().id)
        url = f'{hydroshare.utils.current_site_url()}/resource/{self.resource.short_id}'
        self.assertEqual(identifiers[0]['url'], url)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create an identifier
        doi_url = 'https://doi.org/10.4211/hs.{res_id}'.format(res_id=self.resource.short_id)
        self.resource.doi = 'doi1000100010001'
        self.resource.save()
        identifier = self.resource.metadata.create_element(
            'identifier',
            name='doi',
            url=doi_url
        )

        # Verify identifier is in cached metadata
        self.resource.refresh_from_db()
        identifiers = self.resource.cached_metadata.get('identifiers', [])
        self.assertEqual(len(identifiers), 2)
        # Find the DOI identifier
        doi_identifier = next((i for i in identifiers if i['name'] == 'doi'), None)
        self.assertIsNotNone(doi_identifier)
        self.assertEqual(doi_identifier['id'], identifier.id)
        self.assertEqual(doi_identifier['url'], doi_url)
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_publisher_post_save_updates_cached_metadata(self):
        """Test that creating a Publisher element triggers cached metadata update."""
        # Initially, cached metadata should have empty publisher
        self.resource.refresh_from_db()
        publisher = self.resource.cached_metadata.get('publisher', {})
        self.assertEqual(publisher, {})

        # Make the resource published so we can create a publisher
        self.resource.set_published(True)
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Create a publisher
        publisher_elem = self.resource.metadata.create_element(
            'publisher',
            name='HydroShare',
            url='https://www.hydroshare.org'
        )

        # Verify publisher is in cached metadata
        self.resource.refresh_from_db()
        publisher = self.resource.cached_metadata.get('publisher', {})
        self.assertEqual(publisher['id'], publisher_elem.id)
        self.assertEqual(publisher['name'], 'HydroShare')
        self.assertEqual(publisher['url'], 'https://www.hydroshare.org')
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

    def test_status_post_save_updates_cached_metadata(self):
        """Test that changing resource sharing status triggers cached metadata update."""
        # Initially, cached metadata should have status of private (public = False)
        self.resource.refresh_from_db()
        status = self.resource.cached_metadata.get('status', {})
        self.assertEqual(status, {
            "public": False,
            "discoverable": False,
            "published": False,
            "shareable": True
        })
        modified_date1 = self.resource.cached_metadata['modified']
        modified_date1 = datetime.fromisoformat(modified_date1)

        # Make the resource discoverable
        self.resource.raccess.discoverable = True
        self.resource.raccess.public = False
        self.resource.raccess.save()

        self.resource.refresh_from_db()
        status = self.resource.cached_metadata.get('status', {})
        self.assertEqual(status, {
            "public": False,
            "discoverable": True,
            "published": False,
            "shareable": True
        })
        modified_date2 = self.resource.cached_metadata['modified']
        modified_date2 = datetime.fromisoformat(modified_date2)
        self.assertGreater(modified_date2, modified_date1)

        # Make the resource public
        self.resource.raccess.public = True
        self.resource.raccess.save()
        self.resource.refresh_from_db()
        status = self.resource.cached_metadata.get('status', {})
        self.assertEqual(status, {
            "public": True,
            "discoverable": True,
            "published": False,
            "shareable": True
        })
        modified_date3 = self.resource.cached_metadata['modified']
        modified_date3 = datetime.fromisoformat(modified_date3)
        self.assertGreater(modified_date3, modified_date2)

        # Make the resource published
        self.resource.set_published(True)
        self.resource.refresh_from_db()
        status = self.resource.cached_metadata.get('status', {})
        self.assertEqual(status, {
            "public": True,
            "discoverable": True,
            "published": True,
            "shareable": True
        })
        modified_date4 = self.resource.cached_metadata['modified']
        modified_date4 = datetime.fromisoformat(modified_date4)
        self.assertGreater(modified_date4, modified_date3)

    def test_cached_metadata_for_copied_resource(self):
        """Test that cached metadata is generated correctly when a resource is copied over to a new resource."""

        self._test_cached_metadata_for_copyed_or_versioned_resource(action='copy')

    def test_cached_metadata_for_versioned_resource(self):
        """Test that cached metadata is generated correctly when a resource is versioned."""

        self._test_cached_metadata_for_copyed_or_versioned_resource(action='version')

    def _test_cached_metadata_for_copyed_or_versioned_resource(self, action='version'):
        """Test that cached metadata is generated correctly when a resource is copied or versioned."""

        # Create multiple metadata elements
        subjects_to_create = ['subject1', 'subject2', 'subject3', 'subject4', 'subject5']

        for subject_value in subjects_to_create:
            self.resource.metadata.create_element('subject', value=subject_value)
        # add another creator
        self.resource.metadata.create_element(
            'creator',
            name='Creator1',
            email='creator1@example.com'
        )
        # add a contributor
        self.resource.metadata.create_element(
            'contributor',
            name='Contributor1',
            email='contributor1@example.com'
        )
        # verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_contributors = self.resource.cached_metadata.get('contributors', [])
        self.assertEqual(len(cached_contributors), 1)

        # create description (abstract)
        abstract = 'This is a test resource abstract'
        self.resource.metadata.create_element('description', abstract=abstract)
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_subjects = self.resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 5)
        self.assertEqual(set(cached_subjects), set(subjects_to_create))

        # add temporal coverage
        temporal_coverage = self.resource.metadata.create_element(
            'coverage',
            type='period',
            value={
                'name': 'Test Period',
                'start': '2020-01-01',
                'end': '2020-12-31'
            }
        )
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_temporal_coverage = self.resource.cached_metadata.get('temporal_coverage', {})
        self.assertEqual(cached_temporal_coverage['id'], temporal_coverage.id)

        # add spatial coverage
        spatial_coverage = self.resource.metadata.create_element(
            'coverage',
            type='point',
            value={
                'name': 'Test Point',
                'east': '56.45678',
                'north': '12.6789',
                'units': 'Decimal degrees'
            }
        )
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_spatial_coverage = self.resource.cached_metadata.get('spatial_coverage', {})
        self.assertEqual(cached_spatial_coverage['id'], spatial_coverage.id)

        # add funding agency
        funding_agency = self.resource.metadata.create_element(
            'fundingagency',
            agency_name='National Science Foundation',
            award_title='Hydrological Research Grant',
            award_number='NSF-12345',
            agency_url='https://www.nsf.gov'
        )
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        cached_funding_agencies = self.resource.cached_metadata.get('funding_agencies', [])
        self.assertEqual(len(cached_funding_agencies), 1)
        self.assertEqual(cached_funding_agencies[0]['id'], funding_agency.id)

        # add relation
        relation = self.resource.metadata.create_element(
            'relation',
            type='isPartOf',
            value='https://www.hydroshare.org/resource/12345'
        )
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        relations = self.resource.cached_metadata.get('relations', [])
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]['id'], relation.id)

        # add geospatial relation
        geospatial_relation = self.resource.metadata.create_element(
            'geospatialrelation',
            type='relation',
            value='https://geoconnex.us/ref/gages/123456',
            text='USGS Gage 123456'
        )
        # Verify cached metadata is consistent
        self.resource.refresh_from_db()
        geospatial_relations = self.resource.cached_metadata.get('geospatial_relations', [])
        self.assertEqual(len(geospatial_relations), 1)
        self.assertEqual(geospatial_relations[0]['id'], geospatial_relation.id)

        # create a version/copy of the resource
        self.new_resource = hydroshare.create_empty_resource(self.resource.short_id, self.user, action=action)
        if action == 'version':
            new_resource = hydroshare.create_new_version_resource(self.resource, self.new_resource, self.user)
        else:
            new_resource = hydroshare.copy_resource(self.resource, self.new_resource)

        # Verify cached metadata is consistent for the new resource
        new_resource.refresh_from_db()
        _type = new_resource.cached_metadata.get('type', '')
        self.assertEqual(_type, f'{hydroshare.utils.current_site_url()}/terms/CompositeResource')

        language = new_resource.cached_metadata.get('language', '')
        self.assertEqual(language, 'eng')

        identifiers = new_resource.cached_metadata.get('identifiers', [])
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0]['name'], 'hydroShareIdentifier')

        rights = new_resource.cached_metadata.get('rights', {})
        self.assertEqual(rights['statement'], 'This resource is shared under the Creative Commons Attribution CC BY.')

        cached_subjects = new_resource.cached_metadata.get('subjects', [])
        self.assertEqual(len(cached_subjects), 5)
        self.assertEqual(set(cached_subjects), set(subjects_to_create))
        self.assertEqual(new_resource.cached_metadata['title']['value'],
                         self.resource.cached_metadata['title']['value'])
        # Compare creators after removing id fields (since IDs will differ between resources)
        original_creators = [
            {k: v for k, v in creator.items() if k != 'id'}
            for creator in self.resource.cached_metadata['creators']
        ]
        new_creators = [
            {k: v for k, v in creator.items() if k != 'id'}
            for creator in new_resource.cached_metadata['creators']
        ]
        self.assertEqual(new_creators, original_creators)
        # check the number of creators in the new resource
        self.assertEqual(len(new_resource.metadata.creators.all()), 2)
        # Compare contributors after removing id fields (since IDs will differ between resources)
        original_contributors = [
            {k: v for k, v in contributor.items() if k != 'id'}
            for contributor in self.resource.cached_metadata['contributors']
        ]
        new_contributors = [
            {k: v for k, v in contributor.items() if k != 'id'}
            for contributor in new_resource.cached_metadata['contributors']
        ]
        self.assertEqual(new_contributors, original_contributors)
        # check the number of contributors in the new resource
        self.assertEqual(len(new_resource.metadata.contributors.all()), 1)
        self.assertEqual(new_resource.cached_metadata['subjects'], self.resource.cached_metadata['subjects'])
        # check the number of subjects in the new resource
        self.assertEqual(len(new_resource.metadata.subjects.all()), 5)

        # check the status fields for the new resource
        status = new_resource.cached_metadata.get('status', {})
        self.assertEqual(status['public'], False)
        self.assertEqual(status['discoverable'], False)
        self.assertEqual(status['published'], False)
        self.assertEqual(status['shareable'], True)

        # check the abstract in cached metadata for the new resource
        self.assertEqual(new_resource.cached_metadata['abstract']['value'],
                         self.resource.cached_metadata['abstract']['value'])

        # compare the temporal coverage in cached metadata for the new resource after removing the id field
        orig_t_coverage = {k: v for k, v in self.resource.cached_metadata['temporal_coverage'].items() if k != 'id'}
        new_t_coverage = {k: v for k, v in new_resource.cached_metadata['temporal_coverage'].items() if k != 'id'}
        self.assertEqual(new_t_coverage, orig_t_coverage)

        # compare the spatial coverage in cached metadata for the new resource after removing the id field
        orig_s_coverage = {k: v for k, v in self.resource.cached_metadata['spatial_coverage'].items() if k != 'id'}
        new_s_coverage = {k: v for k, v in new_resource.cached_metadata['spatial_coverage'].items() if k != 'id'}
        self.assertEqual(new_s_coverage, orig_s_coverage)

        # compare the funding agencies in cached metadata for the new resource after removing the id field
        orig_funding_agencies = [
            {k: v for k, v in agency.items() if k != 'id'}
            for agency in self.resource.cached_metadata['funding_agencies']
        ]
        new_funding_agencies = [
            {k: v for k, v in agency.items() if k != 'id'}
            for agency in new_resource.cached_metadata['funding_agencies']
        ]
        self.assertEqual(new_funding_agencies, orig_funding_agencies)

        # compare the relations in cached metadata for the new resource after removing the id field
        orig_relations = [
            {k: v for k, v in relation.items() if k != 'id'}
            for relation in self.resource.cached_metadata['relations']
        ]
        new_relations = [
            {k: v for k, v in relation.items() if k != 'id'}
            for relation in new_resource.cached_metadata['relations']
        ]
        self.assertEqual(len(new_relations), 2)
        if action == 'copy':
            # before comparing remove the type=source relation from the new resource as that is a new relation added
            new_relations = [relation for relation in new_relations if relation['type'] != 'source']
            self.assertEqual(new_relations, orig_relations)
        else:
            # before comparing remove the type=isVersionOf relation from the new resource
            # as that is a new relation added
            new_relations = [relation for relation in new_relations if relation['type'] != 'isVersionOf']
            self.assertEqual(new_relations, orig_relations)

        # compare the geospatial relations in cached metadata for the new resource after removing the id field
        orig_geospatial_relations = [
            {k: v for k, v in relation.items() if k != 'id'}
            for relation in self.resource.cached_metadata['geospatial_relations']
        ]
        new_geospatial_relations = [
            {k: v for k, v in relation.items() if k != 'id'}
            for relation in new_resource.cached_metadata['geospatial_relations']
        ]
        self.assertEqual(new_geospatial_relations, orig_geospatial_relations)

        # check that the new resource created date is after the original resource created date
        original_resource_created_date = datetime.fromisoformat(self.resource.cached_metadata['created'])
        new_resource_created_date = datetime.fromisoformat(new_resource.cached_metadata['created'])
        self.assertGreater(new_resource_created_date, original_resource_created_date)

        # check that the new resource modified date is after the original resource modified date
        original_resource_modified_date = datetime.fromisoformat(self.resource.cached_metadata['modified'])
        new_resource_modified_date = datetime.fromisoformat(new_resource.cached_metadata['modified'])
        self.assertGreater(new_resource_modified_date, original_resource_modified_date)
