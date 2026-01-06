from django.test import TestCase
from django.contrib.auth.models import Group, User

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin

from hs_composite_resource.models import CompositeResource

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set, \
    assertUserResourceState, assertResourceUserState


class T03CreateResource(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(T03CreateResource, self).setUp()
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

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )
        # a resource
        self.holes = None

    def tearDown(self):
        super(T03CreateResource, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()

    def test_01_create(self):
        """Resource creator has appropriate access"""
        cat = self.cat
        # check that user cat owns and holds nothing
        assertUserResourceState(self, cat, [], [], [])

        # create a resource
        self.holes = self._create_resource()
        holes = self.holes

        assertUserResourceState(self, cat, [holes], [], [])

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # unsharing with cat would violate owner constraint
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertFalse(
            cat.uaccess.can_unshare_resource_with_user(
                holes, cat))

    def test_02_isolate(self):
        """A user who didn't create a resource cannot access it"""
        cat = self.cat
        dog = self.dog
        self.holes = self._create_resource()
        holes = self.holes

        # check that resource was created
        assertUserResourceState(self, cat, [holes], [], [])

        # check that resource is not accessible to others
        assertUserResourceState(self, dog, [], [], [])

        # metadata should be the same as before
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for non-owner
        self.assertFalse(dog.uaccess.owns_resource(holes))
        self.assertFalse(dog.uaccess.can_change_resource(holes))
        self.assertFalse(dog.uaccess.can_view_resource(holes))

        # composite django state for non-owner
        self.assertFalse(dog.uaccess.can_change_resource_flags(holes))
        self.assertFalse(dog.uaccess.can_delete_resource(holes))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertFalse(
            dog.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # test list access functions for unshare targets
        # these return empty because allowing this would violate the last owner
        # rule
        self.assertTrue(
            is_equal_to_as_set(
                [], cat.uaccess.get_resource_unshare_users(holes)))
        self.assertTrue(
            is_equal_to_as_set(
                [], dog.uaccess.get_resource_unshare_users(holes)))

    def test_06_check_flag_immutable(self):
        """Resource owner can set and reset immutable flag"""
        cat = self.cat
        dog = self.dog

        # create a resource
        self.holes = self._create_resource()
        holes = self.holes

        assertUserResourceState(self, cat, [holes], [], [])
        assertResourceUserState(self, holes, [cat], [], [])

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # make it immutable: what changes?
        holes.raccess.immutable = True
        holes.raccess.save()

        # metadata state
        self.assertTrue(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        assertUserResourceState(self, cat, [holes], [], [])
        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # django admin access
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource(holes))
        self.assertTrue(self.admin.uaccess.can_view_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # change squash
        self.cat.uaccess.share_resource_with_user(
            holes, dog, PrivilegeCodes.CHANGE)

        # CHANGE squashed to VIEW
        assertUserResourceState(self, dog, [], [], [holes])

        # now no longer immutable
        holes.raccess.immutable = False
        holes.raccess.save()

        assertUserResourceState(self, dog, [], [holes], [])

        self.cat.uaccess.unshare_resource_with_user(holes, dog)

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

    def test_07_check_flag_discoverable(self):
        """Resource owner can set and reset discoverable flag"""
        cat = self.cat

        # create a resource
        self.holes = self._create_resource()
        holes = self.holes

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # is it listed as discoverable?
        self.assertTrue(
            is_equal_to_as_set(
                [], CompositeResource.discoverable_resources.all()))
        self.assertTrue(
            is_equal_to_as_set(
                [], CompositeResource.public_resources.all()))

        # make it discoverable
        holes.raccess.discoverable = True
        holes.raccess.save()

        # is it listed as discoverable?
        self.assertTrue(
            is_equal_to_as_set(
                [holes],
                CompositeResource.discoverable_resources.all()))
        self.assertTrue(
            is_equal_to_as_set(
                [], CompositeResource.public_resources.all()))

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertTrue(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # make it not discoverable
        holes.raccess.discoverable = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # django admin should have full access to any not discoverable
        # resource
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # TODO: test get_discoverable_resources and get_public_resources

    def test_08_check_flag_published(self):
        """Resource owner can set and reset published flag"""

        cat = self.cat

        # create a resource
        self.holes = self._create_resource()
        holes = self.holes

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # make it published
        holes.raccess.published = True
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertTrue(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertFalse(cat.uaccess.can_change_resource_flags(holes))
        self.assertFalse(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # django admin access for published resource
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource(holes))
        self.assertTrue(self.admin.uaccess.can_view_resource(holes))

        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        # admin even can delete a published resource
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # make it not published
        holes.raccess.published = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

    def test_09_check_flag_public(self):
        """Resource owner can set and reset public flag"""

        cat = self.cat

        # create a resource
        self.holes = self._create_resource()
        holes = self.holes

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # is it listed as discoverable?
        self.assertTrue(
            is_equal_to_as_set(
                [], CompositeResource.discoverable_resources.all()))
        self.assertTrue(
            is_equal_to_as_set(
                [], CompositeResource.public_resources.all()))

        # make it public
        holes.raccess.public = True
        holes.raccess.save()

        # is it listed as discoverable?
        self.assertTrue(
            is_equal_to_as_set(
                [holes],
                CompositeResource.discoverable_resources.all()))
        self.assertTrue(
            is_equal_to_as_set(
                [holes],
                CompositeResource.public_resources.all()))

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertTrue(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # make it not public
        holes.raccess.public = False
        holes.raccess.save()

        # metadata state
        self.assertFalse(holes.raccess.immutable)
        self.assertFalse(holes.raccess.published)
        self.assertFalse(holes.raccess.discoverable)
        self.assertFalse(holes.raccess.public)
        self.assertTrue(holes.raccess.shareable)

        # protection state for owner
        self.assertTrue(cat.uaccess.owns_resource(holes))
        self.assertTrue(cat.uaccess.can_change_resource(holes))
        self.assertTrue(cat.uaccess.can_view_resource(holes))

        # composite django state
        self.assertTrue(cat.uaccess.can_change_resource_flags(holes))
        self.assertTrue(cat.uaccess.can_delete_resource(holes))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            cat.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

        # django admin should have full access to any private resource
        self.assertFalse(self.admin.uaccess.owns_resource(holes))
        self.assertTrue(self.admin.uaccess.can_change_resource_flags(holes))
        self.assertTrue(self.admin.uaccess.can_delete_resource(holes))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.OWNER))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.CHANGE))
        self.assertTrue(
            self.admin.uaccess.can_share_resource(
                holes, PrivilegeCodes.VIEW))

    def _create_resource(self):
        return hydroshare.create_resource(resource_type='CompositeResource',
                                          owner=self.cat,
                                          title='all about dog holes',
                                          metadata=[], )
