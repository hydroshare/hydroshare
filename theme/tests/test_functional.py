from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common import desired_capabilities, keys

from hs_core import hydroshare

class FunctionalTests(StaticLiveServerTestCase):
    """Iteractive tests with selenium."""
    fixtures = ['theme/tests/fixtures.json']

    @classmethod
    def setUpClass(cls):
        desktop_dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        desktop_dcap["phantomjs.page.settings.userAgent"] = (
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/27.0.1453.93 Safari/537.36")

        mobile_dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        mobile_dcap["phantomjs.page.settings.userAgent"] = (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) "
                    "AppleWebKit/534.46 (KHTML, like Gecko) "
                    "Version/5.1 Mobile/9A334 Safari/7534.48.3")

        cls.drvr = webdriver.PhantomJS(desired_capabilities=desktop_dcap)
        cls.drvr.set_window_size(width=1024, height=1024)
        cls.drvr.implicitly_wait(10)
        cls.mobile_drvr = webdriver.PhantomJS(desired_capabilities=mobile_dcap)
        cls.mobile_drvr.set_window_size(width=375, height=375)

        cls.user_password = "Users_Cats_FirstName"
        group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        cls.user = hydroshare.create_account(
            'user10@example.com',
            username='user10',
            first_name='User_FirstName',
            last_name='User_LastName',
            password=cls.user_password,
            groups = [group]
        )
        cls.user.save()
        super(FunctionalTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.drvr.quit()
        cls.mobile_drvr.quit()
        super(FunctionalTests, cls).tearDownClass()

    def test_show_login_link_mobile(self):
        """The login link and form should not be displayed on the home page on mobile"""
        self.mobile_drvr.get(self.live_server_url)
        mobile_login_link = self.mobile_drvr.find_element_by_id('signin-menu')
        self.assertFalse(mobile_login_link.is_displayed(),
                         'Login link should not be visible on mobile.')

    def test_show_login_link_desktop(self):
        """The login link but not form should be displayed on the home page"""
        self.drvr.get(self.live_server_url)
        desktop_login_link = self.drvr.find_element_by_id('signin-menu')
        self.assertTrue(desktop_login_link.is_displayed(),
                        'Login link should be visible on desktop.')

    def test_register_account(self):
        """The login link but not form should be displayed on the home page"""
        with self.settings(CSP_DICT = {'default-src': 'unsafe-eval'}):
            self.drvr.get(self.live_server_url)
            self.drvr.find_element_by_class_name('glyphicon-log-in').click()
            self.drvr.find_element_by_id('id_username').click()
            self.assertTrue('accounts/login' in self.drvr.current_url)
            self.drvr.find_element_by_link_text('join HydroShare').click()
            form = self.drvr.find_element_by_id('form-signup')
            self.assertTrue(form.is_displayed())


    def _login_helper(self, login_name, user_password):
        with self.settings(CSRF_COOKIE_SECURE = False,
                           SESSION_COOKIE_SECURE = False,
                           CSP_DICT = {'default-src': 'unsafe-eval'}):
            # home page: click to login
            self.drvr.get(self.live_server_url)
            self.drvr.find_element_by_class_name('glyphicon-log-in').click()

            # login page: fill login form
            username_field = self.drvr.find_element_by_id('id_username')
            password_field = self.drvr.find_element_by_id('id_password')
            submit = self.drvr.find_element_by_xpath("//input[@type='submit']")

            username_field.send_keys(login_name, keys.Keys.TAB)
            self.assertEquals(self.drvr.switch_to.active_element, password_field)
            password_field.send_keys(user_password, keys.Keys.TAB)
            self.assertEquals(self.drvr.switch_to.active_element, submit)
            submit.send_keys(keys.Keys.ENTER)
            self.drvr.save_screenshot('enter_pressed' + login_name + '.png')

            # home page: returned after successful login
            self.assertTrue('Successfully logged in' in self.drvr.page_source)
            self.assertEqual(self.live_server_url + "/", self.drvr.current_url)
            profile = self.drvr.find_element_by_id('profile-menu')
            profile.click()
            self.assertTrue(profile.is_displayed())
            email_elem = self.drvr.find_element_by_id('profile-menu-email')
            self.assertEquals(self.user.email, email_elem.get_attribute('innerHTML').strip())
            name_elem = self.drvr.find_element_by_id('profile-menu-fullname')
            self.assertTrue(self.user.first_name in name_elem.get_attribute('innerHTML').strip())
            self.assertTrue(self.user.last_name in name_elem.get_attribute('innerHTML').strip())


    #def test_login_username(self):
    #    self._login_helper(self.user.username, self.user_password)

    def test_email_username(self):
        self._login_helper(self.user.email, self.user_password)
