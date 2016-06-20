
from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
     UserGroupPrivilege, UserResourcePrivilege, GroupMembershipRequest

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_access_control.tests.utilities import global_reset


class T12UserDelete(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(T12UserDelete, self).setUp()

        global_reset()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='administrator',
            last_name='couch',
            superuser=True,
            groups=[]
        )

        self.cat = hydroshare.create_account(
            'cat@gmail.com',
            username='cat',
            first_name='not a dog',
            last_name='last_name_cat',
            superuser=False,
            groups=[]
        )

        self.scratching = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.cat,
            title='all about sofas as scratching posts',
            metadata=[]
        )

        self.felines = self.cat.uaccess.create_group(
            title='felines',
            description="We are the felines"
        )

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.arfers = self.dog.uaccess.create_group(
            title='arfers',
            description='animals that bark'
        )

        self.cat.uaccess.create_group_membership_request(self.arfers)

    def test_00_cascade(self):
        "Deleting a user cascade-deletes its access control"
        # This tests that deleting a user cleans up its access control.
        # Note that deleting the sole owner of a resource or group
        # leaves it orphaned. This is not prevented.
        cat = self.cat

        # get the id's of all objects that should be deleted.
        uid = cat.uaccess.id
        rid = self.scratching.raccess.id
        gid = self.felines.gaccess.id
        gpid = UserGroupPrivilege.objects.get(user=cat).id
        rpid = UserResourcePrivilege.objects.get(user=cat).id
        mpid = GroupMembershipRequest.objects.get(request_from=cat).id

        # all objects exist before the delete
        self.assertEqual(UserAccess.objects.filter(id=uid).count(), 1)
        self.assertEqual(ResourceAccess.objects.filter(id=rid).count(), 1)
        self.assertEqual(GroupAccess.objects.filter(id=gid).count(), 1)
        self.assertEqual(UserGroupPrivilege.objects.filter(id=gpid).count(), 1)
        self.assertEqual(UserResourcePrivilege.objects.filter(id=rpid).count(), 1)
        self.assertEqual(GroupMembershipRequest.objects.filter(id=mpid).count(), 1)

        cat.delete()

        # objects tied to the user are deleted, other objects continue to exist
        self.assertEqual(UserAccess.objects.filter(id=uid).count(), 0)
        self.assertEqual(ResourceAccess.objects.filter(id=rid).count(), 1)
        self.assertEqual(GroupAccess.objects.filter(id=gid).count(), 1)
        self.assertEqual(UserGroupPrivilege.objects.filter(id=gpid).count(), 0)
        self.assertEqual(UserResourcePrivilege.objects.filter(id=rpid).count(), 0)
        self.assertEqual(GroupMembershipRequest.objects.filter(id=mpid).count(), 0)
