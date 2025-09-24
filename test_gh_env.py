from django.test import TestCase
from django.conf import settings


class TestSettingsVariables(TestCase):
    def test_aaa_settings_are_loaded(self):
        """Test that settings variables are set correctly before publishing tests."""
        print("\n--- Django Settings Dump ---")
        for setting in dir(settings):
            if setting.isupper():
                if not setting.startswith('DATACITE_'):
                    continue
                try:
                    value = getattr(settings, setting)
                    if any(s in setting for s in ['PASSWORD', 'SECRET', 'TOKEN', 'KEY']):
                        if value is None:
                            print(f"{setting}: None")
                        elif isinstance(value, str) and not value.strip():
                            print(f"{setting}: [EMPTY STRING]")
                        else:
                            print(f"{setting}: [REDACTED]")
                    else:
                        print(f"{setting}: {value}")
                except Exception as e:
                    print(f"{setting}: [ERROR] {e}")
        print("--- End of Settings Dump ---\n")
        self.assertIsNotNone(settings.DATACITE_USERNAME, "DATACITE_USERNAME is not set")
        self.assertTrue(bool(settings.DATACITE_USERNAME.strip()), "DATACITE_USERNAME is empty")
        self.assertIsNotNone(settings.DATACITE_PASSWORD, "DATACITE_PASSWORD is not set")
        self.assertTrue(bool(settings.DATACITE_PASSWORD.strip()), "DATACITE_PASSWORD is empty")
        self.assertIn("10.", settings.DATACITE_PREFIX, "DATACITE_PREFIX does not look valid")
        self.assertTrue(settings.TEST_DATACITE_API_URL.startswith("https://"), "TEST_DATACITE_API_URL is invalid")
        self.assertTrue(settings.DATACITE_API_URL.startswith("https://"), "DATACITE_API_URL is invalid")
