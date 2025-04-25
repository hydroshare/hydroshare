
from django.test import TestCase
from django.contrib.auth.models import Group

from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin
from hs_access_control.models import PrivilegeCodes

from hs_access_control.tests.utilities import global_reset


class T13Delete(MockS3TestCaseMixin, TestCase):

    def setUp(self):
        super(T13Delete, self).setUp()
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

        self.bat = hydroshare.create_account(
            'bat@gmail.com',
            username='bat',
            first_name='not a man',
            last_name='last_name_bat',
            superuser=False,
            groups=[]
        )

        self.nobody = hydroshare.create_account(
            'nobody@gmail.com',
            username='nobody',
            first_name='no one in particular',
            last_name='last_name_nobody',
            superuser=False,
            groups=[]
        )

        self.wombat = hydroshare.create_account(
            'wombat@gmail.com',
            username='wombat',
            first_name='some random ombat',
            last_name='last_name_wombat',
            superuser=False,
            groups=[]
        )

        self.verdi = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.dog,
            title='Guiseppe Verdi',
            metadata=[],
        )

        self.operas = self.dog.uaccess.create_group(
            title="operas", description="We are the operas")
        self.dog.uaccess.share_resource_with_user(
            self.verdi, self.cat, PrivilegeCodes.CHANGE)
        self.dog.uaccess.share_resource_with_group(
            self.verdi, self.operas, PrivilegeCodes.CHANGE)
        self.singers = self.dog.uaccess.create_group(
            title='singers', description="We are the singers")
        self.dog.uaccess.share_group_with_user(
            self.singers, self.cat, PrivilegeCodes.CHANGE)

    def test_01_delete_resource(self):
        """Delete works for resources: privileges are deleted with resource"""
        verdi = self.verdi
        dog = self.dog
        self.assertTrue(dog.uaccess.can_delete_resource(verdi))
        hydroshare.delete_resource(verdi.short_id)
        self.assertFalse(dog.uaccess.can_delete_resource(verdi))

    def test_02_delete_group(self):
        """Delete works for groups: privileges are deleted with group"""

        dog = self.dog
        singers = self.singers
        self.assertTrue(dog.uaccess.can_delete_group(singers))
        dog.uaccess.delete_group(singers)
        self.assertFalse(dog.uaccess.can_delete_group(singers))
