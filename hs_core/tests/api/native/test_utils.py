from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.test import TestCase

from mezzanine.conf import settings

from hs_core.hydroshare import utils
from hs_core.models import GenericResource, BaseResource
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestUtils(MockIRODSTestCaseMixin, TestCase):
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

        self.res = hydroshare.create_resource(
            'GenericResource',
            self.user,
            'test resource',
        )
        self.res.doi = 'doi1000100010001'
        self.res.save()

    def test_get_resource_types(self):
        res_types = utils.get_resource_types()
        self.assertIn(GenericResource, res_types)

        for res_type in res_types:
            self.assertTrue(issubclass(res_type, BaseResource))

    def test_get_resource_instance(self):
        self.assertEqual(
            utils.get_resource_instance('hs_core', 'GenericResource', self.res.pk),
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
        self.assertEquals(self.user.userprofile, utils.get_profile(self.user))

    def test_get_mime_type(self):
        test_file = 'my_file.txt'
        self.assertEquals(utils.get_file_mime_type(test_file), 'text/plain')
        test_file = 'my_file.tif'
        self.assertEquals(utils.get_file_mime_type(test_file), 'image/tiff')
        test_file = 'my_file.abc'
        self.assertEquals(utils.get_file_mime_type(test_file), 'application/abc')

    def test_get_current_site_url(self):
        current_site = Site.objects.get_current()
        protocol = getattr(settings, 'MY_SITE_PROTOCOL', 'http')
        url = '%s://%s' % (protocol, current_site.domain)
        self.assertEquals(utils.current_site_url(), url)

    def test_resource_modified(self):
        modified_date1 = self.res.metadata.dates.filter(type='modified').first()
        self.assertEquals(self.res.last_changed_by, self.user)
        utils.resource_modified(self.res, self.user2)
        modified_date2 = self.res.metadata.dates.filter(type='modified').first()
        self.assertTrue((modified_date2.start_date - modified_date1.start_date).total_seconds() > 0)
        self.assertEquals(self.res.last_changed_by, self.user2)