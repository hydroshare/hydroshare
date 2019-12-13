from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import PrivilegeCodes

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin

from hs_access_control.tests.utilities import global_reset, is_equal_to_as_set


class T09GroupPublic(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(T09GroupPublic, self).setUp()
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

        self.dog = hydroshare.create_account(
            'dog@gmail.com',
            username='dog',
            first_name='a little arfer',
            last_name='last_name_dog',
            superuser=False,
            groups=[]
        )

        self.squirrels = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about chasing squirrels',
            metadata=[],
        )

        self.holes = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.dog,
            title='all about storing bones in holes',
            metadata=[],
        )

        # dog owns canines group
        self.canines = self.dog.uaccess.create_group(
            title='canines', description="We are the canines")

    def test_public_resources(self):
        """ public resources contain those resources that are public and discoverable """

        res = self.canines.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set(res, []))
        self.dog.uaccess.share_resource_with_group(self.squirrels, self.canines,
                                                   PrivilegeCodes.VIEW)
        self.dog.uaccess.share_resource_with_group(self.holes, self.canines,
                                                   PrivilegeCodes.VIEW)
        res = self.canines.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set(res, []))
        self.holes.raccess.public = True
        self.holes.raccess.discoverable = True
        self.holes.raccess.save()  # this avoids regular requirements for "public"
        res = self.canines.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set(res, [self.holes]))
        for r in res:
            self.assertEqual(r.public, r.raccess.public)
            self.assertEqual(r.discoverable, r.raccess.discoverable)
            self.assertEqual(r.published, r.raccess.published)
            self.assertEqual(r.group_name, self.canines.name)
            self.assertEqual(r.group_id, self.canines.id)
        self.squirrels.raccess.discoverable = True
        self.squirrels.raccess.save()
        res = self.canines.gaccess.public_resources
        self.assertTrue(is_equal_to_as_set(res, [self.holes, self.squirrels]))
        for r in res:
            self.assertEqual(r.public, r.raccess.public)
            self.assertEqual(r.discoverable, r.raccess.discoverable)
            self.assertEqual(r.published, r.raccess.published)
            self.assertEqual(r.group_name, self.canines.name)
            self.assertEqual(r.group_id, self.canines.id)
