
from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes, GroupAccess

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set


class T01PublicGroups(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(T01PublicGroups, self).setUp()
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

        self.cats = self.cat.uaccess.create_group(
            title='cats', description="We are the cats")

        self.posts = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[],
        )

        self.cat.uaccess.share_resource_with_group(self.posts, self.cats, PrivilegeCodes.VIEW)

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='not a cat',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.dogs = self.dog.uaccess.create_group(
            title='dogs', description="We are the dogs")

        self.bones = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.dog,
            title='all about bones',
            metadata=[],
        )

        self.dog.uaccess.share_resource_with_group(self.bones, self.dogs, PrivilegeCodes.VIEW)

        self.pets = self.dog.uaccess.create_community(
            'all kinds of pets',
            'collaboration on how to be a better pet.')

        self.pets.active = True
        self.pets.save()

        # Make cats and dogs part of community pets
        self.dog.uaccess.share_community_with_group(self.pets, self.dogs, PrivilegeCodes.VIEW)
        self.cat.uaccess.share_group_with_user(self.cats, self.dog, PrivilegeCodes.OWNER)
        self.dog.uaccess.share_community_with_group(self.pets, self.cats, PrivilegeCodes.VIEW)
        self.cat.uaccess.unshare_group_with_user(self.cats, self.dog)

    def test_01_groups(self):
        "basic function: groups appear and disappear according to access rules "

        # flag state
        self.assertFalse(self.posts.raccess.discoverable)

        groups = GroupAccess.groups_with_public_resources()
        self.assertTrue(is_equal_to_as_set([], groups))

        # override policies for discoverable data
        self.posts.raccess.discoverable = True
        self.posts.raccess.save()

        # group should appear in list
        groups = GroupAccess.groups_with_public_resources()
        self.assertTrue(is_equal_to_as_set([self.cats], groups))

        # group should contain a public resource
        resources = self.cats.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set([self.posts], resources))

        self.bones.raccess.discoverable = True
        self.bones.raccess.save()

        # Now group dogs should appear in list
        groups = GroupAccess.groups_with_public_resources()
        print(groups)
        self.assertTrue(is_equal_to_as_set([self.cats, self.dogs], groups))

        # group should contain a public resource
        resources = self.dogs.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set([self.bones], resources))

    def test_02_communities(self):
        "groups appear and disappear from communities according to access rules "

        # flag state
        self.assertFalse(self.posts.raccess.discoverable)

        groups = self.pets.groups_with_public_resources()
        self.assertTrue(is_equal_to_as_set([], groups))

        # override policies for discoverable data
        self.posts.raccess.discoverable = True
        self.posts.raccess.save()

        # group should appear in list
        groups = self.pets.groups_with_public_resources()
        self.assertTrue(is_equal_to_as_set([self.cats], groups))

        # group should contain a public resource
        resources = self.pets.public_resources
        self.assertTrue(is_equal_to_as_set([self.posts], resources))

        self.bones.raccess.discoverable = True
        self.bones.raccess.save()

        # Now group dogs should appear in list
        groups = self.pets.groups_with_public_resources()
        self.assertTrue(is_equal_to_as_set([self.cats, self.dogs], groups))

        # group should contain a public resource
        resources = self.pets.public_resources
        self.assertTrue(is_equal_to_as_set([self.posts, self.bones], resources))
