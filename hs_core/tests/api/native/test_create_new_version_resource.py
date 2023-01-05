import os

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_composite_resource.models import CompositeResource


class TestNewVersionResource(TestCase):
    def setUp(self):
        super(TestNewVersionResource, self).setUp()
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

        # create a user who is NOT the owner of the resource to be versioned
        self.nonowner = hydroshare.create_account(
            'nonowner@gmail.com',
            username='nonowner',
            first_name='nonowner_firstname',
            last_name='nonowner_lastname',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test resource versioning'
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

    def tearDown(self):
        super(TestNewVersionResource, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        self.test_file1.close()
        os.remove(self.test_file1.name)
        self.test_file2.close()
        os.remove(self.test_file2.name)

    def test_new_version_composite_resource(self):
        # test to make sure only owners can version a resource
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.resource.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.resource, self.nonowner,
                                                    PrivilegeCodes.CHANGE)
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.resource.short_id, self.nonowner)

        self.owner.uaccess.share_resource_with_user(self.resource, self.nonowner,
                                                    PrivilegeCodes.VIEW)
        with self.assertRaises(PermissionDenied):
            hydroshare.create_empty_resource(self.resource.short_id, self.nonowner)

        # add key/value metadata to original resource
        self.resource.extra_metadata = {'variable': 'temp', 'units': 'deg F'}
        self.resource.save()

        new_resource = hydroshare.create_empty_resource(self.resource.short_id, self.owner)
        # test to make sure the new versioned empty resource has no content files
        self.assertEqual(new_resource.files.all().count(), 0)

        new_resource = hydroshare.create_new_version_resource(self.resource, new_resource, self.owner)

        # test the new versioned resource has the same resource type as the original resource
        self.assertTrue(isinstance(new_resource, CompositeResource))

        # test the new versioned resource has the correct content file with correct path copied over

        self.assertEqual(new_resource.files.all().count(), 2)

        # add each file of resource to list
        new_res_file_list = []
        # TODO: revise for new file handling
        for f in new_resource.files.all():
            new_res_file_list.append(f.resource_file.name)
        for f in self.resource.files.all():
            ori_res_no_id_file_path = f.resource_file.name[len(self.resource.short_id):]
            new_res_file_path = new_resource.short_id + ori_res_no_id_file_path
            self.assertIn(new_res_file_path, new_res_file_list,
                          msg='resource content path is not created correctly '
                              'for new versioned resource')

        # test key/value metadata copied over
        self.assertEqual(new_resource.extra_metadata, self.resource.extra_metadata)
        # test science metadata elements are copied from the original resource to the new versioned
        # resource
        self.assertEqual(new_resource.metadata.title.value,
                         self.resource.metadata.title.value,
                         msg='metadata title is not copied over to the new versioned resource')
        self.assertEqual(new_resource.creator, self.owner,
                         msg='creator is not copied over to the new versioned resource')

        # test to make sure a new unique identifier has been created for the new versioned resource
        self.assertIsNotNone(
            new_resource.short_id,
            msg='Unique identifier has not been created for new versioned resource.')
        self.assertNotEqual(new_resource.short_id, self.resource.short_id)

        # test to make sure the new versioned resource has the correct identifier
        self.assertEqual(new_resource.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier',
                      [id.name for id in new_resource.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found for new versioned resource.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), new_resource.short_id)
        self.assertIn(id_url, [id.url for id in new_resource.metadata.identifiers.all()],
                      msg="Identifier url was not found for new versioned resource.")

        # test to make sure the new versioned resource is linked with the original resource via
        # isReplacedBy and isVersionOf metadata elements
        self.assertGreater(new_resource.metadata.relations.all().count(), 0,
                           msg="New versioned resource does has relation element.")

        relation_is_version_of = new_resource.metadata.relations.filter(type='isVersionOf').first()
        self.assertNotEqual(relation_is_version_of, None)
        self.assertEqual(relation_is_version_of.value, self.resource.get_citation())

        relation_is_replaced_by = self.resource.metadata.relations.filter(type='isReplacedBy').first()
        self.assertNotEqual(relation_is_replaced_by, None)
        self.assertEqual(relation_is_replaced_by.value, new_resource.get_citation())

        # test isReplacedBy is removed after the new versioned resource is deleted
        hydroshare.delete_resource(new_resource.short_id)
        self.assertNotIn('isReplacedBy',
                         [rel.type for rel in self.resource.metadata.relations.all()],
                         msg="isReplacedBy is not removed from the original resource after "
                             "its versioned resource is deleted")
        # delete the original resource to make sure iRODS files are cleaned up
        hydroshare.delete_resource(self.resource.short_id)

    def test_replaced_by_resources(self):
        """here we are testing the replaced_by() function of the resource class"""

        new_resource_v1 = hydroshare.create_empty_resource(self.resource.short_id, self.owner)

        new_resource_v1 = hydroshare.create_new_version_resource(self.resource, new_resource_v1, self.owner)

        replaced_by_resources = self.resource.replaced_by()
        self.assertEqual(len(replaced_by_resources), 1)
        self.assertEqual(new_resource_v1.short_id, replaced_by_resources[0].short_id)

        new_resource_v2 = hydroshare.create_empty_resource(new_resource_v1.short_id, self.owner)
        new_resource_v2 = hydroshare.create_new_version_resource(new_resource_v1, new_resource_v2, self.owner)

        replaced_by_resources = self.resource.replaced_by()
        self.assertEqual(len(replaced_by_resources), 2)
        self.assertIn(new_resource_v1.short_id, [res.short_id for res in replaced_by_resources])
        self.assertIn(new_resource_v2.short_id, [res.short_id for res in replaced_by_resources])
