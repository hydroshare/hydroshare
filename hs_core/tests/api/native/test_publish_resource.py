import tempfile
import os
import shutil
import json
import re

import arrow
from freezegun import freeze_time
from rest_framework import status
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from hs_access_control.models.privilege import UserResourcePrivilege, PrivilegeCodes
from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.testing import MockS3TestCaseMixin
from hs_core.views.utils import get_default_admin_user, get_default_support_user
from django.core.exceptions import ValidationError, PermissionDenied
from theme.backends import without_login_date_token_generator


# Control-char sanitizer used by tests to assert expected sanitized form.
_CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')


class TestPublishResource(MockS3TestCaseMixin, TestCase):
    def test_aaa_settings_are_loaded(self):
        """Test that settings variables are set correctly before publishing tests."""
        print("\n--- Django Settings Dump ---")
        for setting in dir(settings):
            if setting.isupper():
                try:
                    value = getattr(settings, setting)
                    if any(s in setting for s in ['PASSWORD', 'SECRET', 'TOKEN', 'KEY']):
                        print(f"{setting}: [REDACTED]")
                    else:
                        print(f"{setting}: {value}")
                except Exception as e:
                    print(f"{setting}: [ERROR] {e}")
        print("--- End of Settings Dump ---\n")
        self.assertIsNotNone(settings.DATACITE_USERNAME, "DATACITE_USERNAME is not set")
        self.assertIsNotNone(settings.DATACITE_PASSWORD, "DATACITE_PASSWORD is not set")
        self.assertTrue(bool(settings.DATACITE_USERNAME.strip()), "DATACITE_USERNAME is empty")
        self.assertTrue(bool(settings.DATACITE_PASSWORD.strip()), "DATACITE_PASSWORD is empty")
        self.assertIn("10.", settings.DATACITE_PREFIX, "DATACITE_PREFIX does not look valid")
        self.assertTrue(settings.TEST_DATACITE_API_URL.startswith("https://"), "TEST_DATACITE_API_URL is invalid")
        self.assertTrue(settings.DATACITE_API_URL.startswith("https://"), "DATACITE_API_URL is invalid")

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

        # create a 2nd user
        self.user2 = hydroshare.create_account(
            'user2@usu.edu',
            username='user2',
            first_name='user2_FirstName',
            last_name='user2_LastName',
            superuser=False,
            groups=[]
        )

        # create a published user
        self.user2 = hydroshare.create_account(
            'publisher@usu.edu',
            username='published',
            first_name='user2_FirstName',
            last_name='user2_LastName',
            superuser=False,
        )

        # create a resource
        self.res = hydroshare.create_resource(
            'CompositeResource',
            self.user,
            'Test Resource',
            edit_users=[self.user2]
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
            edit_users=[self.user2],
            files=(self.file_one,),
            keywords=('a', 'b', 'c'),
        )
        self.complete_res.metadata.create_element("description", abstract="new abstract for the resource " * 10)

    def tearDown(self):
        super(TestPublishResource, self).tearDown()
        self.res.delete()
        self.complete_res.delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        BaseResource.objects.all().delete()
        shutil.rmtree(self.tmp_dir)

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
        self.assertFalse(self.complete_res.metadata.dates.filter(type='published').exists())

        admin_user = get_default_admin_user()
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)

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

        # Published resource should have any bags
        istorage = self.pub_res.get_s3_storage()
        bag_path = self.pub_res.bag_path
        self.assertTrue(istorage.exists(bag_path))

    def test_publish_via_email_link(self):
        """
        Test case for publishing a resource via email link.

        This test verifies that a resource can be published by clicking on the approval link
        received via email. It checks that the resource is initially not published, submits
        the resource for review, generates the approval link, and then simulates clicking on
        the link. Finally, it checks that the resource is published and no longer in review.
        """
        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)

        support = get_default_support_user()
        token = without_login_date_token_generator.make_token(support)
        uidb64 = urlsafe_base64_encode(force_bytes(support.pk))
        url = reverse('metadata_review', kwargs={
            "shortkey": self.complete_res.short_id,
            "action": "approve",
            "uidb64": uidb64,
            "token": token,
        })

        client = Client()
        # let support click the link in the email
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        pub_res = hydroshare.get_resource_by_shortkey(self.complete_res.short_id)

        self.assertTrue(
            pub_res.raccess.published,
            msg='The resource is not published'
        )
        self.assertFalse(
            pub_res.raccess.review_pending,
            msg='The resource is still in review'
        )

    def test_reject_publish_via_email_link(self):
        """
        Test case to verify the rejection of resource publishing via email link.

        This test checks if the resource is not published and then submits the resource for review.
        It generates an email link for rejecting the review and simulates the support user clicking the link.
        Finally, it verifies that the resource is not published and the review status is not pending.
        """
        self.assertFalse(
            self.res.raccess.published,
            msg='The resource is published'
        )

        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)

        support = get_default_support_user()
        token = without_login_date_token_generator.make_token(support)
        uidb64 = urlsafe_base64_encode(force_bytes(support.pk))
        url = reverse('metadata_review', kwargs={
            "shortkey": self.complete_res.short_id,
            "action": "reject",
            "uidb64": uidb64,
            "token": token,
        })

        client = Client()
        # let support click the link in the email
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        potentially_pub_res = hydroshare.get_resource_by_shortkey(self.complete_res.short_id)

        self.assertFalse(
            potentially_pub_res.raccess.published,
            msg='The resource is not published'
        )
        self.assertFalse(
            potentially_pub_res.raccess.review_pending,
            msg='The resource is still in review'
        )

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
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)

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

        with self.assertRaises(ValidationError):
            hydroshare.submit_resource_for_review(pk=self.res.short_id, user=self.user)

        # submit with complete res should be successful
        hydroshare.submit_resource_for_review(pk=self.complete_res.short_id, user=self.user)

    def test_last_updated(self):
        """Test that publishing a resource updates last_changed_by user and last_updated date"""
        admin_user = get_default_admin_user()
        res = self.complete_res

        # the last_changed_by should be the user who created the resource
        self.assertEqual(res.last_changed_by, self.user)

        # only the owner or admin can submit a resource for review
        with self.assertRaises(PermissionDenied):
            hydroshare.submit_resource_for_review(pk=res.short_id, user=self.user2)

        # add user2 as an owner
        UserResourcePrivilege.share(user=self.user2,
                                    resource=res,
                                    privilege=PrivilegeCodes.OWNER,
                                    grantor=self.user)

        hydroshare.submit_resource_for_review(pk=res.short_id, user=self.user2)
        res.refresh_from_db()

        # The last_changed_by should now be the user2 who submitted the resource for review
        self.assertEqual(self.user2, res.last_changed_by)
        time_after_submit = res.last_updated

        hydroshare.publish_resource(user=admin_user, pk=res.short_id)

        # the last_changed_by should still be the user2 who submitted the resource for review
        self.assertEqual(res.last_changed_by, self.user2)
        self.assertTrue(res.metadata.dates.filter(type='published').exists())

        # last_updated date should be updated when the resource is published, even though the last_changed_by is not
        res.refresh_from_db(fields=['cached_metadata'])
        self.assertGreater(res.last_updated, time_after_submit)

    def create_json_test_resource(self):
        """
        Build metadata that get_datacite_deposit_json() expects:
          - description.abstract
          - multiple creators (org + person w/ ORCID)
          - hydroShareIdentifier (REQUIRED for attributes.url)
          - rights (optional)
        """
        # abstract
        if not getattr(self.res.metadata, "description", None):
            self.res.metadata.create_element('description', abstract='This is a test abstract')
        else:
            self.res.metadata.update_element(
                'description', self.res.metadata.description.id, abstract='This is a test abstract'
            )

        # creators: organization + person with ORCID
        self.res.metadata.create_element('creator', organization='Utah State University')
        identifiers = {"ORCID": 'https://orcid.org/0000-0002-1825-0097'}
        self.res.metadata.create_element('creator', name='John Smith', identifiers=identifiers)

        # funders (optional; covered via get_funding_references downstream)
        self.res.metadata.create_element(
            'fundingagency',
            agency_name='National Science Foundation',
            award_title='NSF Award',
            award_number='12345',
            agency_url='https://nsf.gov'
        )
        self.res.metadata.create_element('fundingagency', agency_name='Utah Water Research Laboratory')

        # REQUIRED: hydroShareIdentifier used for attributes.url
        site_url = hydroshare.utils.current_site_url()
        if not self.res.metadata.identifiers.filter(name='hydroShareIdentifier').exists():
            self.res.metadata.create_element(
                'identifier',
                name='hydroShareIdentifier',
                url=f'{site_url}/resource/{self.res.short_id}'
            )

        # optional rights for wider coverage
        if not getattr(self.res.metadata, "rights", None):
            self.res.metadata.create_element('rights', statement='CC-BY 4.0',
                                             url='http://creativecommons.org/licenses/by/4.0/')

    def freeze_and_assert_json(self):
        """
        Freeze (to mimic prior pattern) and assert key DataCite JSON fields.
        Unlike XML, we assert field-by-field (JSON ordering is not guaranteed).
        """
        freeze = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        freezer = freeze_time(freeze)
        freezer.start()

        raw = self.res.get_datacite_deposit_json()
        payload = json.loads(raw)

        # Core shape
        self.assertIn("data", payload)
        data = payload["data"]
        self.assertEqual(data.get("type"), "dois")
        attrs = data.get("attributes", {})

        # Publisher
        pub = attrs.get("publisher", {})
        self.assertEqual(pub.get("name"),
                         "Consortium of Universities for the Advancement of Hydrologic Science, Inc")
        self.assertEqual(pub.get("publisherIdentifier"), "https://ror.org/04s2bx355")
        self.assertEqual(pub.get("publisherIdentifierScheme"), "ROR")
        self.assertEqual(pub.get("schemeUri"), "https://ror.org")

        # DOI / prefix / suffix
        self.assertEqual(attrs.get("prefix"), f"{settings.DATACITE_PREFIX}")
        self.assertEqual(attrs.get("suffix"), self.res.short_id)
        self.assertEqual(attrs.get("doi"), f"{settings.DATACITE_PREFIX}/{self.res.short_id}")

        # URL from hydroShareIdentifier
        site_url = hydroshare.utils.current_site_url()
        expected_url = f"{site_url}/resource/{self.res.short_id}"
        self.assertEqual(attrs.get("url"), expected_url)

        # Titles / language / state
        self.assertTrue(attrs.get("titles"))
        self.assertIn("title", attrs["titles"][0])
        self.assertEqual(attrs.get("language"), "en")
        self.assertEqual(attrs.get("state"), "findable")

        # Publication year (string in your builder)
        self.assertEqual(attrs.get("publicationYear"), str(self.res.updated.year))

        # Creators present
        creators = attrs.get("creators", [])
        self.assertTrue(creators, "creators must not be empty")
        self.assertIn("name", creators[0])
        self.assertIn("nameType", creators[0])

        # Description present and clean for the clean test
        descs = attrs.get("descriptions", [])
        self.assertTrue(descs, "descriptions should include Abstract")
        self.assertEqual(descs[0].get("descriptionType"), "Abstract")
        self.assertNotRegex(descs[0].get("description", ""), _CONTROL_CHARS,
                            "Abstract should not contain control characters")

        freezer.stop()

    def test_datacite_deposit_json(self):
        """Datacite JSON generation test (clean abstract)"""
        self.create_json_test_resource()
        self.freeze_and_assert_json()

    def test_datacite_deposit_dirty_json(self):
        """Datacite JSON generation test (dirty abstract)"""
        self.create_json_test_resource()

        # inject control char like old XML test
        self.res.metadata.update_element(
            'description', self.res.metadata.description.id, abstract='This is a test abstract\x1F'
        )

        raw = self.res.get_datacite_deposit_json()
        payload = json.loads(raw)
        attrs = payload["data"]["attributes"]
        descs = attrs.get("descriptions", [])
        self.assertTrue(descs, "descriptions should include Abstract")
        got = descs[0].get("description", "")
        self.assertNotRegex(got, _CONTROL_CHARS, "Control characters must be sanitized from abstract")
        expected = _CONTROL_CHARS.sub('', 'This is a test abstract\x1F').strip()
        self.assertEqual(got, expected)
