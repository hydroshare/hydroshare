from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.test import TestCase

from mezzanine.conf import settings

from hs_core.hydroshare import utils
from hs_core.models import BaseResource
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin
from hs_composite_resource.models import CompositeResource


class TestUtils(MockS3TestCaseMixin, TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.user2 = hydroshare.create_account(
            'user2@nowhere.com',
            username='user2',
            first_name='user2_FirstName',
            last_name='user2_LastName',
            superuser=False,
            groups=[]
        )

        self.admin_user = hydroshare.create_account(
            'admin@nowhere.com',
            username='admin',
            first_name='admin_FirstName',
            last_name='admin_LastName',
            superuser=True,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'test resource',
        )

        self.admin_res = hydroshare.create_resource(
            'CompositeResource',
            self.admin_user,
            'admin test resource',
        )
        self.res.doi = 'doi1000100010001'
        self.res.save()

    def tearDown(self):
        super(TestUtils, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        self.res.delete()
        BaseResource.objects.all().delete()

    def test_get_resource_types(self):
        res_types = utils.get_resource_types()
        self.assertIn(CompositeResource, res_types)

        for res_type in res_types:
            self.assertTrue(issubclass(res_type, BaseResource))

    def test_get_resource_instance(self):
        self.assertEqual(
            utils.get_resource_instance('hs_composite_resource', 'CompositeResource', self.res.pk),
            self.res
        )

    def test_get_resource_by_shortkey(self):
        self.assertEqual(
            utils.get_resource_by_shortkey(self.res.short_id),
            self.res
        )

    def test_get_resource_by_doi(self):
        self.assertEqual(
            utils.get_resource_by_doi('doi1000100010001'),
            self.res
        )

    def test_user_from_id(self):
        self.assertEqual(
            utils.user_from_id(self.user),
            self.user,
            msg='user passthrough failed'
        )

        self.assertEqual(
            utils.user_from_id('user1@nowhere.com'),
            self.user,
            msg='lookup by email address failed'
        )

        self.assertEqual(
            utils.user_from_id('user1'),
            self.user,
            msg='lookup by username failed'
        )

    def test_group_from_id(self):
        self.assertEqual(
            utils.group_from_id(self.group),
            self.group,
            msg='group passthrough failed'
        )

        self.assertEqual(
            utils.group_from_id('Hydroshare Author'),
            self.group,
            msg='lookup by group name failed'
        )

    def test_get_user_profile(self):
        self.assertEqual(self.user.userprofile, utils.get_profile(self.user))

    def test_get_mime_type(self):
        test_file = 'my_file.txt'
        self.assertEqual(utils.get_file_mime_type(test_file), 'text/plain')
        test_file = 'my_file.tif'
        self.assertEqual(utils.get_file_mime_type(test_file), 'image/tiff')
        test_file = 'my_file.abc'
        self.assertEqual(utils.get_file_mime_type(test_file), 'text/vnd.abc')

    def test_get_current_site_url(self):
        current_site = Site.objects.get_current()
        protocol = getattr(settings, 'MY_SITE_PROTOCOL', 'http')
        url = '%s://%s' % (protocol, current_site.domain)
        self.assertEqual(utils.current_site_url(), url)

    def test_resource_modified(self):
        # Test owner can set resource_modified on their resource
        modified_date1 = self.res.metadata.dates.filter(type='modified').first()
        self.assertEqual(self.res.last_changed_by, self.user)
        utils.resource_modified(self.res, self.user)
        modified_date2 = self.res.metadata.dates.filter(type='modified').first()
        self.assertTrue((modified_date2.start_date - modified_date1.start_date).total_seconds() > 0)
        self.assertEqual(self.res.last_changed_by, self.user)
        self.assertEqual(self.res.last_updated, modified_date2.start_date)

    def test_resource_modified_non_owner(self):
        # Test non-owner can NOT set resource_modified on a resource
        modified_date1 = self.res.metadata.dates.filter(type='modified').first()
        self.assertEqual(self.res.last_changed_by, self.user)
        utils.resource_modified(self.res, self.user2)
        modified_date2 = self.res.metadata.dates.filter(type='modified').first()
        self.assertFalse((modified_date2.start_date - modified_date1.start_date).total_seconds() > 0)
        self.assertNotEqual(self.res.last_changed_by, self.user2)

    def test_resource_modified_admin(self):
        # Test admin cannot set resource_modified on a resource
        modified_date1 = self.res.metadata.dates.filter(type='modified').first()
        self.assertEqual(self.res.last_changed_by, self.user)
        utils.resource_modified(self.res, self.admin_user)
        modified_date2 = self.res.metadata.dates.filter(type='modified').first()
        self.assertFalse((modified_date2.start_date - modified_date1.start_date).total_seconds() > 0)
        self.assertNotEqual(self.res.last_changed_by, self.user2)

    def test_resource_modified_admin_owner(self):
        # Test admin can set resource_modified on their resource (which they own)
        modified_date1 = self.admin_res.metadata.dates.filter(type='modified').first()
        self.assertEqual(self.admin_res.last_changed_by, self.admin_user)
        utils.resource_modified(self.admin_res, self.admin_user)
        modified_date2 = self.admin_res.metadata.dates.filter(type='modified').first()
        self.assertTrue((modified_date2.start_date - modified_date1.start_date).total_seconds() > 0)
        self.assertEqual(self.admin_res.last_changed_by, self.admin_user)
        self.assertEqual(self.admin_res.last_updated, modified_date2.start_date)
