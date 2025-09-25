from django.test import TestCase
from django.contrib.auth.models import User, Group

from hs_core.models import BaseResource
from hs_core import hydroshare
from hs_access_control.models import PrivilegeCodes, UserResourcePermission


class TestUserResourcePermission(TestCase):
    def setUp(self):
        super(TestUserResourcePermission, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create 2 users
        self.user1 = hydroshare.create_account(
            'user1@gmail.com',
            username='user1',
            first_name='user1_first',
            last_name='user1_last',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'user2@gmail.com',
            username='user2',
            first_name='user2_first',
            last_name='user2_last',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user1,
            title='Test Resource'
        )

    def tearDown(self):
        super(TestUserResourcePermission, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        UserResourcePermission.objects.all().delete()

    def test_update_on_user_resource_update(self):
        # testing user permission update on a resource

        # at this point user1 is the owner of the resource
        # there should be a record in UserResourcePermission table
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        urp = UserResourcePermission.objects.first()
        self.assertEqual(urp.user_id, self.user1.id)
        self.assertEqual(urp.resource_id, self.res.short_id)
        self.assertEqual(urp.privilege, PrivilegeCodes.OWNER)

        # grant user2 view permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW).exists())
        # update user2 permission to change
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.CHANGE)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # revoke user2 permission
        self.user1.uaccess.unshare_resource_with_user(self.res, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        self.assertFalse(UserResourcePermission.objects.filter(user_id=self.user2.id).exists())

    def test_update_on_user_group_update_single_group(self):
        # testing user join/leave a group

        # create a group
        group = self.user1.uaccess.create_group(title='Test Group', description='This is a test group')
        # grant group view permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group, PrivilegeCodes.VIEW)
        # add user2 to the group
        self.user1.uaccess.share_group_with_user(group, self.user2, PrivilegeCodes.VIEW)
        # at this point user2 should have view permission on the resource
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW).exists())
        # remove user2 from the group
        self.user1.uaccess.unshare_group_with_user(group, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        # user2 should have no permission on the resource
        self.assertFalse(UserResourcePermission.objects.filter(user_id=self.user2.id).exists())

        # tests the case when user2 has direct permission on the resource as well as via group
        # grant user2 edit permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.CHANGE)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # add user2 to the group (group has view permission on the resource)
        self.user1.uaccess.share_group_with_user(group, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # grant group edit permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group, PrivilegeCodes.CHANGE)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should still have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # remove user2 from the group
        self.user1.uaccess.unshare_group_with_user(group, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should still have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # grant user2 view permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # add user2 to the group (group has edit permission on the resource)
        self.user1.uaccess.share_group_with_user(group, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # remove user2 from the group
        self.user1.uaccess.unshare_group_with_user(group, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have view permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW).exists())

    def test_update_on_user_group_update_multiple_groups(self):
        # testing user join/leave multiple groups

        # create 2 groups
        group1 = self.user1.uaccess.create_group(title='Test Group 1', description='This is a test group 1')
        group2 = self.user1.uaccess.create_group(title='Test Group 2', description='This is a test group 2')
        # grant group1 view permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group1, PrivilegeCodes.VIEW)
        # grant group2 edit permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group2, PrivilegeCodes.CHANGE)
        # add user2 to group1
        self.user1.uaccess.share_group_with_user(group1, self.user2, PrivilegeCodes.VIEW)
        # add user2 to group2
        self.user1.uaccess.share_group_with_user(group2, self.user2, PrivilegeCodes.VIEW)
        # at this point user2 should have edit permission on the resource
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # remove user2 from group2
        self.user1.uaccess.unshare_group_with_user(group2, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have view permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW).exists())
        # add user2 to group2
        self.user1.uaccess.share_group_with_user(group2, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())
        # remove user2 from group1 and group2
        self.user1.uaccess.unshare_group_with_user(group2, self.user2)
        self.user1.uaccess.unshare_group_with_user(group1, self.user2)
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        self.assertFalse(UserResourcePermission.objects.filter(user_id=self.user2.id).exists())


    def test_update_on_group_resource_update(self):
        # testing group permission update on a resource

        # create a group
        group = self.user1.uaccess.create_group(title='Test Group', description='This is a test group')
        # add user2 to the group
        self.user1.uaccess.share_group_with_user(group, self.user2, PrivilegeCodes.VIEW)
        # grant group view permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group, PrivilegeCodes.VIEW)
        # at this point user2 should have view permission on the resource
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW).exists())

        # grant group edit permission to the resource
        self.user1.uaccess.share_resource_with_group(self.res, group, PrivilegeCodes.CHANGE)
        self.assertEqual(UserResourcePermission.objects.count(), 2)
        # user2 should have edit permission on the resource
        self.assertTrue(UserResourcePermission.objects.filter(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE).exists())

        # revoke group permission from the resource
        self.user1.uaccess.unshare_resource_with_group(self.res, group)
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        # user2 should have no permission on the resource
        self.assertFalse(UserResourcePermission.objects.filter(user_id=self.user2.id).exists())

    def test_update_on_resource_delete(self):
        # testing resource delete
        self.assertEqual(UserResourcePermission.objects.count(), 1)
        self.res.delete()
        self.assertEqual(UserResourcePermission.objects.count(), 0)

    def test_get_privilege(self):
        # user1 is owner
        self.assertEqual(UserResourcePermission.get_privilege(user_id=self.user1.id, resource_id=self.res.short_id),
                         PrivilegeCodes.OWNER)
        # user2 has no permission
        self.assertEqual(UserResourcePermission.get_privilege(user_id=self.user2.id, resource_id=self.res.short_id),
                         PrivilegeCodes.NONE)
        # grant user2 view permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.VIEW)
        self.assertEqual(UserResourcePermission.get_privilege(user_id=self.user2.id, resource_id=self.res.short_id),
                         PrivilegeCodes.VIEW)

    def test_has_permission(self):
        # user1 is owner
        self.assertTrue(UserResourcePermission.has_permission(user_id=self.user1.id, resource_id=self.res.short_id,
                                                              privilege=PrivilegeCodes.OWNER))
        self.assertTrue(UserResourcePermission.has_permission(user_id=self.user1.id, resource_id=self.res.short_id,
                                                              privilege=PrivilegeCodes.CHANGE))
        self.assertTrue(UserResourcePermission.has_permission(user_id=self.user1.id, resource_id=self.res.short_id,
                                                              privilege=PrivilegeCodes.VIEW))
        # user2 has no permission
        self.assertFalse(UserResourcePermission.has_permission(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.VIEW))
        # make resource public
        self.res.raccess.public = True
        self.res.raccess.save()
        self.assertTrue(UserResourcePermission.has_permission(user_id=self.user2.id, resource_id=self.res.short_id,
                                                              privilege=PrivilegeCodes.VIEW))
        self.assertFalse(UserResourcePermission.has_permission(user_id=self.user2.id, resource_id=self.res.short_id,
                                                               privilege=PrivilegeCodes.CHANGE))

    def test_has_view_permission(self):
        # user1 is owner
        self.assertTrue(UserResourcePermission.has_view_permission(user_id=self.user1.id, resource_id=self.res.short_id))
        # user2 has no permission
        self.assertFalse(UserResourcePermission.has_view_permission(user_id=self.user2.id, resource_id=self.res.short_id))
        # make resource public
        self.res.raccess.public = True
        self.res.raccess.save()
        self.assertTrue(UserResourcePermission.has_view_permission(user_id=self.user2.id, resource_id=self.res.short_id))

    def test_has_change_permission(self):
        # user1 is owner
        self.assertTrue(UserResourcePermission.has_change_permission(user_id=self.user1.id, resource_id=self.res.short_id))
        # user2 has no permission
        self.assertFalse(UserResourcePermission.has_change_permission(user_id=self.user2.id, resource_id=self.res.short_id))
        # grant user2 view permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.VIEW)
        self.assertFalse(UserResourcePermission.has_change_permission(user_id=self.user2.id, resource_id=self.res.short_id))
        # grant user2 change permission
        self.user1.uaccess.share_resource_with_user(self.res, self.user2, PrivilegeCodes.CHANGE)
        self.assertTrue(UserResourcePermission.has_change_permission(user_id=self.user2.id, resource_id=self.res.short_id))
