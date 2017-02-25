from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class FunctionalTests(StaticLiveServerTestCase):
    """Iteractive tests with selenium."""

    @classmethod
    def setUpClass(cls):
        desktop_dcap = dict(DesiredCapabilities.PHANTOMJS)
        desktop_dcap["phantomjs.page.settings.userAgent"] = (
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/27.0.1453.93 Safari/537.36")

        mobile_dcap = dict(DesiredCapabilities.PHANTOMJS)
        mobile_dcap["phantomjs.page.settings.userAgent"] = (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) "
                    "AppleWebKit/534.46 (KHTML, like Gecko) "
                    "Version/5.1 Mobile/9A334 Safari/7534.48.3")

        cls.desktop_browser = webdriver.PhantomJS(desired_capabilities=desktop_dcap)
        cls.desktop_browser.set_window_size(width=1024, height=1024)
        cls.mobile_browser = webdriver.PhantomJS(desired_capabilities=mobile_dcap)
        cls.mobile_browser.set_window_size(width=375, height=375)
        super(FunctionalTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.desktop_browser.quit()
        cls.mobile_browser.quit()
        super(FunctionalTests, cls).tearDownClass()

    def test_show_login_link_mobile(self):
        """The login link and form should not be displayed on the home page on mobile"""
        self.mobile_browser.get(self.live_server_url)
        mobile_login_link = self.mobile_browser.find_element_by_id('signin-menu')
        self.assertFalse(mobile_login_link.is_displayed(),
                         'Login link should not be visible on mobile.')

    def test_show_login_link_desktop(self):
        """The login link but not form should be displayed on the home page"""
        self.desktop_browser.get(self.live_server_url)
        desktop_login_link = self.desktop_browser.find_element_by_id('signin-menu')
        self.assertTrue(desktop_login_link.is_displayed(),
                        'Login link should be visible on desktop.')
