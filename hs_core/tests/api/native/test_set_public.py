
import os
import tempfile
import zipfile
import shutil
from dateutil import parser
from unittest import TestCase
import datetime as dtime

from django.contrib.auth.models import Group, User
from django.utils import timezone

from hs_core.hydroshare import resource, get_resource_by_shortkey
from hs_core.tests.api.utils import MyTemporaryUploadedFile
from hs_core.models import GenericResource
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_core.hydroshare.utils import QuotaException, resource_pre_create_actions


class TestCreateResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCreateResource, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )
        # create files
        file_one = os.path.join(self.tmp_dir,"test1.txt") 

        open(file_one, "w").close()

        # open files for read and upload
        self.file_one = open(file_one, "r")

        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource',
            files=(self.file_one,)
            )

    def tearDown(self):
        super(TestCreateResource, self).tearDown()

        shutil.rmtree(self.tmp_dir)

        self.res.delete()
        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()

        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        self.file_one.close()
        os.remove(self.file_one.name)

    def test_resource_setAVU_and_getAVU(self):
        """ test that setAVU and getAVU work predictably """
        self.res.setAVU("foo", "bar")
        self.assertEqual(self.res.getAVU("foo"), "bar")
        self.res.setAVU("foo", "cat") 
        self.assertEqual(self.res.getAVU("foo"), "cat")

    def test_set_public_and_set_discoverable(self):
        """ test that resource.set_public and resource.set_discoverable work properly. """

        # default resource was constructed to be publishable 
        self.assertTrue(self.res.can_be_public_or_discoverable) 
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
        self.res.set_public(False) 
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
        self.res.set_discoverable(True) 
        self.assertTrue(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
        self.res.set_discoverable(False) 
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.res.set_public(True) 
        self.assertTrue(self.res.raccess.discoverable) 
        self.assertTrue(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'true') 
        self.res.set_discoverable(False) 
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
        
        # now try some things that won't work 
        # first make the resource unacceptable to be discoverable
        self.res.metadata.title.value = ''
        self.res.metadata.title.save()
        self.assertFalse(self.res.can_be_public_or_discoverable) 
        with self.assertRaises(ValidationError):
            self.res.set_public(True) 
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
        with self.assertRaises(ValidationError):
            self.res.set_discoverable(True) 

    def test_update_public_and_discoverable(self):
        """ test that resource.update_public_and_discoverable works properly. """

        self.assertTrue(self.res.can_be_public_or_discoverable) 
        self.res.update_public_and_discoverable()
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 

        # intentionally and greviously violate constraints
        self.res.raccess.discoverable = True
        self.res.raccess.public = True
        self.res.raccess.save()
        self.res.setAVU('isPublic', True) 

        # There's a problem now 
        self.assertFalse(self.res.can_be_public_or_discoverable) 
        self.assertEqual(self.res.getAVU('isPublic'), 'true') 

        # update should correct the problem
        self.res.update_public_and_discoverable()
        self.assertFalse(self.res.raccess.discoverable) 
        self.assertFalse(self.res.raccess.public) 
        self.assertEqual(self.res.getAVU('isPublic'), 'false') 
