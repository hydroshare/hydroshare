
from django.test import TestCase
from django.contrib.auth.models import Group

from hs_access_control.models import UserAccess

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

    def test_00_cascade(self):
        "Deleting a user cascade-deletes its access control"
        cat = self.cat
        caccess = cat.uaccess
        id = caccess.id

        self.assertEqual(UserAccess.objects.filter(id=id).count(), 1)
        cat.delete()
        self.assertEqual(UserAccess.objects.filter(id=id).count(), 0)
