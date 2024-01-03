
import tempfile
import os

from django.contrib.auth.models import Group
from django.test import TestCase

from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import get_default_admin_user
from django.core.exceptions import ValidationError


class TestPublishResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestPublishResource, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'creator@usu.edu',
            username='creator',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'Test Resource'
        )

        self.tmp_dir = tempfile.mkdtemp()
        file_one = os.path.join(self.tmp_dir, "test1.txt")

        file_one_write = open(file_one, "w")
        file_one_write.write("Putting something inside")
        file_one_write.close()

        # open files for read and upload
        self.file_one = open(file_one, "rb")

        self.complete_res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource ' * 10,
            files=(self.file_one,),
            keywords=('a', 'b', 'c'),
        )
        self.complete_res.metadata.create_element("description", abstract="new abstract for the resource " * 10)

    def test_publish_resource(self):
        # check status prior to publishing the resource
        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertFalse(
            self.res.doi,
            msg='doi is assigned'
        )

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        admin_user = get_default_admin_user()
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=admin_user)

        # publish resource - this is the api we are testing
        hydroshare.publish_resource(user=admin_user, pk=self.complete_res.short_id)
        self.pub_res = hydroshare.get_resource_by_shortkey(self.complete_res.short_id)

        # test publish state
        self.assertTrue(
            self.pub_res.raccess.published,
            msg='The resource is not published'
        )

        # test frozen state
        self.assertTrue(
            self.pub_res.raccess.immutable,
            msg='The resource is not frozen'
        )

        # test if doi is assigned
        self.assertTrue(
            self.pub_res.doi,
            msg='No doi is assigned with the published resource.'
        )

        # there should now published date type metadata element
        self.assertTrue(self.pub_res.metadata.dates.filter(type='published').exists())

    def test_only_admin_can_publish_resource(self):
        # check status prior to publishing the resource
        self.assertFalse(
            self.complete_res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.complete_res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertFalse(
            self.complete_res.doi,
            msg='doi is assigned'
        )

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        admin_user = get_default_admin_user()
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=admin_user)

        with self.assertRaises(ValidationError):
            hydroshare.publish_resource(user=self.user, pk=self.complete_res.short_id)

        # publish with admin user should be successful
        hydroshare.publish_resource(user=admin_user, pk=self.complete_res.short_id)

    def test_incomplete_resource_cant_publish(self):
        # check status prior to publishing the resource
        self.assertFalse(
            self.complete_res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.complete_res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertFalse(
            self.complete_res.doi,
            msg='doi is assigned'
        )

        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        self.assertFalse(
            self.res.raccess.immutable,
            msg='The resource is frozen'
        )

        self.assertFalse(
            self.res.doi,
            msg='doi is assigned'
        )

        # there should not be published date type metadata element
        self.assertFalse(self.res.metadata.dates.filter(type='published').exists())

        admin_user = get_default_admin_user()
        with self.assertRaises(ValidationError):
            hydroshare.submit_resource_for_review(pk=self.res.short_id, user=admin_user)

        # submit with complete res should be successful
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=admin_user)

    def test_last_updated(self):
        admin_user = get_default_admin_user()
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)
        hydroshare.publish_resource(user=admin_user, pk=self.complete_res.short_id)

        self.assertEqual(self.complete_res.last_changed_by, self.user)
