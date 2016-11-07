from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

class FunctionalTests(StaticLiveServerTestCase):
    """Iteractive tests with selenium."""

    @classmethod
    def setUpClass(cls):
        cls.desktop_browser = webdriver.PhantomJS()
        cls.desktop_browser.set_window_size(width=1024, height=1024)
        cls.mobile_browser = webdriver.PhantomJS()
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
        self.mobile_browser.get_screenshot_as_file("mobile.png")
        self.assertFalse(mobile_login_link.is_displayed(), 'Login link should not be visible on mobile.')

    def test_show_login_link_desktop(self):
        """The login link but not form should be displayed on the home page"""
        self.desktop_browser.get(self.live_server_url)
        desktop_login_link = self.desktop_browser.find_element_by_id('signin-menu')
        self.desktop_browser.get_screenshot_as_file("desktop.png")
        self.assertTrue(desktop_login_link.is_displayed(), 'Login link should be visible on desktop.')
