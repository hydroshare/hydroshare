from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common import desired_capabilities, keys

from hs_core import hydroshare
from hs_core.models import BaseResource


class FunctionalTests(StaticLiveServerTestCase):
    fixtures = ['theme/tests/fixtures.json']

    def setUp(self):
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

        self.drvr = webdriver.PhantomJS(desired_capabilities=desktop_dcap)
        self.drvr.set_window_size(width=1024, height=1024)
        self.drvr.implicitly_wait(10)

        self.mobile_drvr = webdriver.PhantomJS(desired_capabilities=mobile_dcap)
        self.mobile_drvr.set_window_size(width=375, height=375)

        self.user_password = "Users_Cats_FirstName"
        group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user30@example.com',
            username='user30',
            first_name='User_FirstName',
            last_name='User_LastName',
            password=self.user_password,
            groups=[group]
        )
        self.user.save()
        super(FunctionalTests, self).setUp()

    def tearDown(self):
        self.drvr.quit()
        self.mobile_drvr.quit()
        super(FunctionalTests, self).tearDown()

    def test_show_login_link_mobile(self):
        """The login link should not be displayed on the home page on mobile"""
        self.mobile_drvr.get(self.live_server_url)
        mobile_login_link = self.mobile_drvr.find_element_by_id('signin-menu')
        self.assertFalse(mobile_login_link.is_displayed(),
                         'Login link should not be visible on mobile.')

    def test_show_login_link_desktop(self):
        """The login link should be displayed on the home page"""
        self.drvr.get(self.live_server_url)
        desktop_login_link = self.drvr.find_element_by_id('signin-menu')
        self.assertTrue(desktop_login_link.is_displayed(),
                        'Login link should be visible on desktop.')

    def test_register_account(self):
        with self.settings(CSP_DICT={'default-src': 'unsafe-eval'}):
            self.drvr.get(self.live_server_url)
            login = self.drvr.find_element_by_xpath("//li[@id='signin-menu']/a")
            self.assertTrue(login.is_displayed())
            login.click()
            self.drvr.find_element_by_id('id_username').click()
            self.assertTrue('accounts/login' in self.drvr.current_url)
            self.drvr.find_element_by_link_text('join HydroShare').click()
            form = self.drvr.find_element_by_id('form-signup')
            self.assertTrue(form.is_displayed())

    def _login_helper(self, login_name, user_password):
        with self.settings(CSRF_COOKIE_SECURE=False,
                           SESSION_COOKIE_SECURE=False,
                           CSP_DICT={'default-src': 'unsafe-eval'}):
            # home page: click to login
            self.drvr.get(self.live_server_url)
            login = self.drvr.find_element_by_xpath("//li[@id='signin-menu']/a")
            self.assertTrue(login.is_displayed())
            login.click()

            # login page: fill login form
            username_field = self.drvr.find_element_by_id('id_username')
            password_field = self.drvr.find_element_by_id('id_password')
            submit = self.drvr.find_element_by_xpath("//input[@type='submit']")

            username_field.send_keys(login_name, keys.Keys.TAB)
            self.assertEquals(self.drvr.switch_to.active_element, password_field)
            password_field.send_keys(user_password, keys.Keys.TAB)
            self.assertEquals(self.drvr.switch_to.active_element, submit)
            submit.send_keys(keys.Keys.ENTER)

            # home page: returned after successful login with profile info in dropdown
            xpath_query = "//li[@id='profile-menu']/a[@class='dropdown-toggle']"
            dropdown = self.drvr.find_element_by_xpath(xpath_query)
            self.assertTrue(dropdown.is_displayed())
            dropdown.click()
            email_elem = self.drvr.find_element_by_id('profile-menu-email')
            self.assertEquals(self.user.email, email_elem.get_attribute('innerHTML').strip())
            name_elem = self.drvr.find_element_by_id('profile-menu-fullname')
            self.assertTrue(self.user.first_name in name_elem.get_attribute('innerHTML').strip())
            self.assertTrue(self.user.last_name in name_elem.get_attribute('innerHTML').strip())
            self.assertEqual(self.live_server_url + "/", self.drvr.current_url)
            self.assertTrue('Successfully logged in' in self.drvr.page_source)

    def _logout_helper(self):
        self.drvr.get(self.live_server_url)
        xpath_query = "//li[@id='profile-menu']/a[@class='dropdown-toggle']"
        dropdown = self.drvr.find_element_by_xpath(xpath_query)
        dropdown.click()
        signout = dropdown.find_element_by_xpath("//a[@id='signout-menu']")
        signout.click()
        self.drvr.delete_all_cookies()

    def test_login_logout_email(self):
        self._login_helper(self.user.email, self.user_password)
        self._logout_helper()

    def test_create_resource(self):
        with self.settings(CSRF_COOKIE_SECURE=False,
                           SESSION_COOKIE_SECURE=False):
            RESOURCE_TITLE = 'Selenium resource creation test'
            UPLOAD_FILE_PATH = '/hydroshare/manage.py'
            self._login_helper(self.user.email, self.user_password)
            self.drvr.get(self.live_server_url)

            # load my resources & click create new
            my_res_lnk = self.drvr.find_element_by_xpath("//a[contains(text(),'My Resources')]")
            self.assertTrue(my_res_lnk.is_displayed())
            my_res_lnk.click()
            create_new_lnk = self.drvr.find_element_by_link_text('Create new')
            self.assertTrue(create_new_lnk.is_displayed())
            create_new_lnk.click()

            # complete new resource form
            title_field = self.drvr.find_element_by_id('title')
            file_field = self.drvr.find_element_by_id('select-file')
            submit_btn = self.drvr.find_element_by_xpath("//button[@type='submit']")

            self.assertTrue(title_field.is_displayed())
            title_field.send_keys(RESOURCE_TITLE)
            file_field.send_keys(UPLOAD_FILE_PATH + ',', keys.Keys.ENTER)
            submit_btn.click()

            # check results
            login = self.drvr.find_element_by_xpath("//h2[@id='resource-title']")
            self.assertEqual(login.text, RESOURCE_TITLE)
            citation = self.drvr.find_element_by_xpath("//input[@id='citation-text']")
            citation_text = citation.get_attribute('value')
            import re
            m = re.search('HydroShare, http://www.hydroshare.org/resource/(.*)$', citation_text)
            shortkey = m.groups(0)[0]
            resource = BaseResource.objects.get()
            self.assertEqual(resource.title, RESOURCE_TITLE)
            self.assertEqual(resource.short_id, shortkey)
            #self.assertTrue("Congratulations!" in self.drvr.page_source)
