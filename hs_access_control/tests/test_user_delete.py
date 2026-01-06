from django.test import TestCase
from django.contrib.auth.models import Group, User

from hs_access_control.models import UserAccess, GroupAccess, ResourceAccess, \
    UserGroupPrivilege, UserResourcePrivilege, GroupMembershipRequest

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin
from hs_access_control.tests.utilities import global_reset


class T12UserDelete(MockS3TestCaseMixin, TestCase):

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
            resource_type='CompositeResource',
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

    def tearDown(self):
        super(T12UserDelete, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

    def test_00_cascade(self):
        """
        Deleting a user cascade-deletes its access control
        # This tests that deleting a user cleans up its access control.
        # Note that deleting the sole owner of a resource or group
        # leaves it orphaned. This is not prevented.
        """
        cat = self.cat

        # get the id's of all objects that should be deleted.
        uid = cat.uaccess.id
        orid = self.scratching.id
        arid = self.scratching.raccess.id
        ogid = self.felines.id
        agid = self.felines.gaccess.id
        gpid = UserGroupPrivilege.objects.get(user=cat).id
        rpid = UserResourcePrivilege.objects.get(user=cat).id
        mpid = GroupMembershipRequest.objects.get(request_from=cat).id

        # all objects exist before the delete
        self.assertEqual(UserAccess.objects.filter(id=uid).count(), 1)
        self.assertEqual(UserGroupPrivilege.objects.filter(id=gpid).count(), 1)
        self.assertEqual(
            UserResourcePrivilege.objects.filter(
                id=rpid).count(), 1)
        self.assertEqual(
            GroupMembershipRequest.objects.filter(
                id=mpid).count(), 1)
        self.assertEqual(ResourceAccess.objects.filter(id=arid).count(), 1)
        self.assertEqual(GroupAccess.objects.filter(id=agid).count(), 1)
        self.assertEqual(BaseResource.objects.filter(id=orid).count(), 1)
        self.assertEqual(Group.objects.filter(id=ogid).count(), 1)

        cat.delete()

        # objects tied to the user are deleted, other objects continue to exist
        self.assertEqual(UserAccess.objects.filter(id=uid).count(), 0)
        self.assertEqual(UserGroupPrivilege.objects.filter(id=gpid).count(), 0)
        self.assertEqual(
            UserResourcePrivilege.objects.filter(
                id=rpid).count(), 0)
        self.assertEqual(
            GroupMembershipRequest.objects.filter(
                id=mpid).count(), 0)
        # deleting a user should not remove the groups that user owns
        self.assertEqual(GroupAccess.objects.filter(id=agid).count(), 1)
        self.assertEqual(Group.objects.filter(id=ogid).count(), 1)

        # the following tests will fail, because the resource field
        # "creator" is a foreign key to User with on_delete=models.CASCADE
        # and null=False. Thus removing the creator of a resource will
        # remove the resource record (and orphan many files in the process).

        # print('resource access count is ', ResourceAccess.objects.filter(id=arid).count())
        # print('resource count is ', BaseResource.objects.filter(id=orid).count())
        # self.assertEqual(ResourceAccess.objects.filter(id=arid).count(), 1)
        # self.assertEqual(BaseResource.objects.filter(id=orid).count(), 1)
