from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.testing import MockS3TestCaseMixin


class TestHStore(MockS3TestCaseMixin, TestCase):

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
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

    def test_extra_metadata(self):
        # create/add extra metadata
        self.assertEqual(self.res.extra_metadata, {})
        self.res.extra_metadata = {'name': 'John Jackson'}
        self.res.save()
        self.res.refresh_from_db()

        self.assertNotEqual(self.res.extra_metadata, {})
        self.assertEqual(self.res.extra_metadata['name'], 'John Jackson')

        # update extra metadata (add email)
        self.res.extra_metadata = {'name': 'John Jackson', 'email': 'jj@gmail.com'}
        self.res.save()
        self.res.refresh_from_db()
        self.assertEqual(self.res.extra_metadata['name'], 'John Jackson')
        self.assertEqual(self.res.extra_metadata['email'], 'jj@gmail.com')

        # update extra metadata (remove email)
        self.res.extra_metadata = {'name': 'John Jackson'}
        self.res.save()
        self.res.refresh_from_db()
        self.assertEqual(self.res.extra_metadata['name'], 'John Jackson')
        self.assertEqual(self.res.extra_metadata.get('email', None), None)

        # delete all extra metadata
        self.res.extra_metadata = {}
        self.res.save()
        self.res.refresh_from_db()
        self.assertEqual(self.res.extra_metadata, {})
