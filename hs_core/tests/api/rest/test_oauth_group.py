from hs_core.hydroshare import users
from django.urls import reverse
from django.contrib.auth.models import Group
from django.test.testcases import TestCase, Client
from django.conf import settings


class TestSettingsVariables(TestCase):
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


class TestOauthGroup(TestCase):
    def setUp(self):
        super(TestOauthGroup, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.client = Client()
        self.user = users.create_account(
            'test_user1@email.com',
            username='testuser1',
            password='abc123',
            first_name='some_first_name1',
            last_name='some_last_name1',
            groups=[],
            superuser=False)
        self.user.set_password("abc123")
        self.user2 = users.create_account(
            'test_user2@email.com',
            username='testuser2',
            password='abc123',
            first_name='some_first_name2',
            last_name='some_last_name2',
            groups=[],
            superuser=False)
        self.user2.set_password("abc123")
        self.testGroup1 = self.user.uaccess.create_group(
            title="Test Group",
            description="Group for testing")

    def tearDown(self):
        super(TestOauthGroup, self).tearDown()
        self.user.delete()
        self.user2.delete()
        self.testGroup1.delete()
        self.group.delete()

    def test_application_group(self):
        # register the application
        self.client.login(username=self.user.username, password='abc123')
        form_data = {
            "name": "Foo app",
            "client_id": "nfd0fufZtcuNQT2Uzoag19TqTWE6CJtPusKD268B",
            "client_secret": "client_secret",
            "client_type": "public",
            "redirect_uris": "https://www.google.com",
            "authorization_grant_type": "authorization-code",
        }
        response = self.client.post(reverse("oauth2_provider:register"), form_data)
        self.assertEqual(response.status_code, 302)
        group_authorize = '/o/groupauthorize/{}/?redirect_uri=https://www.google.com&' \
                          'client_id=nfd0fufZtcuNQT2Uzoag19TqTWE6CJtPusKD268B&' \
                          'response_type=code'.format(self.testGroup1.pk)
        # check user in group can authenticate
        response = self.client.get(group_authorize, follow=True)
        self.assertEqual(response.status_code, 200)
        # check user not in group cannot authenticate
        self.client.logout()
        self.client.login(username=self.user2.username, password='abc123')
        response = self.client.get(group_authorize, follow=True)
        self.assertEqual(response.redirect_chain, [('/group/{}'.format(self.testGroup1.pk), 302)])
