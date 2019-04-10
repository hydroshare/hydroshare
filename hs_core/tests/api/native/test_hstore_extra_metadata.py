from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.testing import MockIRODSTestCaseMixin


class TestHStore(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestHStore, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])

        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

    def test_extra_metadata(self):
        # create/add extra metadata
        self.assertEquals(self.res.extra_metadata, {})
        self.res.extra_metadata = {'name': 'John Jackson'}
        self.res.save()

        self.assertNotEquals(self.res.extra_metadata, {})
        self.assertEquals(self.res.extra_metadata['name'], 'John Jackson')

        # update extra metadata (add email)
        self.res.extra_metadata = {'name': 'John Jackson', 'email': 'jj@gmail.com'}
        self.res.save()
        self.assertEquals(self.res.extra_metadata['name'], 'John Jackson')
        self.assertEquals(self.res.extra_metadata['email'], 'jj@gmail.com')

        # update extra metadata (remove email)
        self.res.extra_metadata = {'name': 'John Jackson'}
        self.res.save()
        self.assertEquals(self.res.extra_metadata['name'], 'John Jackson')
        self.assertEquals(self.res.extra_metadata.get('email', None), None)

        # delete all extra metadata
        self.res.extra_metadata = {}
        self.res.save()
        self.assertEquals(self.res.extra_metadata, {})

