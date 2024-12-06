from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models.shortcut import zone_of_influence, zone_of_publicity
from hs_access_control.models.privilege import PrivilegeCodes
from hs_access_control.models import PolymorphismError

from hs_core import hydroshare

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set


class T05ShareResource(TestCase):

    def setUp(self):
        super(T05ShareResource, self).setUp()
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

        # use this as non owner
        self.mouse = hydroshare.create_account(
            'mouse@gmail.com',
            username='mouse',
            first_name='first_name_mouse',
            last_name='last_name_mouse',
            superuser=False,
            groups=[]
        )

        self.holes = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about dog holes',
            metadata=[],
        )

        self.posts = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.cat,
            title='all about scratching posts',
            metadata=[],
        )

        self.meowers = self.cat.uaccess.create_group(
            title='some random meowers', description="some random group")

    def test_01_zone_of_influence(self):
        """Zone of influence is correctly determined"""
        holes = self.holes
        posts = self.posts
        meowers = self.meowers
        cat = self.cat
        dog = self.dog

        (foo, bar) = zone_of_influence(send=False, user=dog, resource=holes)
        self.assertTrue(is_equal_to_as_set(foo, [(dog.email, dog.username, dog.is_superuser, dog.id)]))
        self.assertTrue(is_equal_to_as_set(bar, [holes.short_id]))

        (foo, bar) = zone_of_influence(send=False, user=dog, group=meowers)
        self.assertTrue(is_equal_to_as_set(foo, [(dog.email, dog.username, dog.is_superuser, dog.id)]))
        self.assertTrue(is_equal_to_as_set(bar, []))

        (foo, bar) = zone_of_influence(send=False, group=meowers, resource=posts)

        self.assertTrue(is_equal_to_as_set(foo, [(cat.email, cat.username, cat.is_superuser, cat.id)]))
        self.assertTrue(is_equal_to_as_set(bar, [posts.short_id]))

        cat.uaccess.share_resource_with_group(
            holes, meowers, PrivilegeCodes.CHANGE)

        cat.uaccess.share_resource_with_group(
            posts, meowers, PrivilegeCodes.CHANGE)

        (foo, bar) = zone_of_influence(send=False, user=dog, group=meowers)
        self.assertTrue(is_equal_to_as_set(foo, [(dog.email, dog.username, dog.is_superuser, cat.id)]))
        self.assertTrue(is_equal_to_as_set(bar, [holes.short_id, posts.short_id]))

        (foo, bar) = zone_of_influence(send=False, group=meowers, resource=posts)
        self.assertTrue(is_equal_to_as_set(foo, [(cat.email, cat.username, cat.is_superuser, cat.id)]))
        self.assertTrue(is_equal_to_as_set(bar, [posts.short_id]))

    def test_02_polymorphism_error(self):
        """Invalid calls throw exceptions"""
        holes = self.holes
        meowers = self.meowers
        cat = self.cat
        dog = self.dog

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_influence(send=False)
        self.assertEqual(str(cm.exception), 'Too few arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_influence(send=False, user=dog)
        self.assertEqual(str(cm.exception), 'Too few arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_influence(send=False, group=meowers)
        self.assertEqual(str(cm.exception), 'Too few arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_influence(send=False, resource=holes)
        self.assertEqual(str(cm.exception), 'Too few arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_influence(send=False, user=cat, group=meowers, resource=holes)
        self.assertEqual(str(cm.exception), 'Too many arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False, user=cat, resource=holes)
        self.assertEqual(str(cm.exception), 'Too many arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False, group=meowers, resource=holes)
        self.assertEqual(str(cm.exception), 'Too many arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False, group=meowers, resource=holes, user=cat)
        self.assertEqual(str(cm.exception), 'Too many arguments')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False, group=meowers)
        self.assertEqual(str(cm.exception), 'Invalid argument')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False, user=cat)
        self.assertEqual(str(cm.exception), 'Invalid argument')

        with self.assertRaises(PolymorphismError) as cm:
            (foo, bar) = zone_of_publicity(send=False)
        self.assertEqual(str(cm.exception), 'Too few arguments')

    def test_03_publicity(self):
        """ zone_of_publicity """
        posts = self.posts
        (foo, bar) = zone_of_publicity(send=False, resource=posts)
        self.assertTrue(is_equal_to_as_set(foo, []))
        self.assertTrue(is_equal_to_as_set(bar, [posts.short_id]))
