import signal

from django.contrib.auth.models import Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from selenium import webdriver
from selenium.webdriver.common import desired_capabilities, keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from hs_core import hydroshare
from hs_core.models import BaseResource


class FunctionalTestsCases(object):
    """
    Shared Mobile and Desktop test cases (all are run twice, so use sparingly)
    For single browser cases see desired browser specific classes below.
    All test cases can safely assume that the home page is loaded.
    """
    fixtures = ['theme/tests/fixtures.json']

    def setUp(self):
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
        super(FunctionalTestsCases, self).setUp()

    def tearDown(self):
        self.driver.close()
        # see Selenium bug: https://github.com/seleniumhq/selenium/issues/767
        self.driver.service.process.send_signal(signal.SIGTERM)
        self.driver.quit()
        super(FunctionalTestsCases, self).tearDown()

    def _login_helper(self, login_name, user_password):
        # home page: click to login
        for e in self.driver.find_elements_by_xpath("//a[contains(text(),'Sign In')]"):
            if e.is_displayed():
                e.click()
                break

        # login page: fill login form
        username_field = self.driver.find_element_by_name('username')
        password_field = self.driver.find_element_by_name('password')
        submit = self.driver.find_element_by_xpath("//input[@type='submit']")

        username_field.send_keys(login_name, keys.Keys.TAB)
        self.assertEquals(self.driver.switch_to.active_element, password_field)
        password_field.send_keys(user_password, keys.Keys.TAB)
        self.assertEquals(self.driver.switch_to.active_element, submit)
        submit.send_keys(keys.Keys.ENTER)

    def _logout_helper(self):
        xpath_query = "//li[@id='profile-menu']/a[@class='dropdown-toggle']"
        dropdown = self.driver.find_element_by_xpath(xpath_query)
        dropdown.click()
        signout = dropdown.find_element_by_xpath("//a[@id='signout-menu']")
        signout.click()
        self.driver.delete_all_cookies()

    def test_register_account(self):
        for e in self.driver.find_elements_by_xpath("//a[contains(text(),'Sign In')]"):
            if e.is_displayed():
                e.click()
                break

        self.driver.find_element_by_name('username').click()
        self.assertTrue('accounts/login' in self.driver.current_url)
        self.driver.find_element_by_link_text('join HydroShare').click()
        form = self.driver.find_element_by_id('form-signup')
        self.assertTrue(form.is_displayed())

    def test_login_email(self):
        self._login_helper(self.user.email, self.user_password)
        self.assertEqual(self.live_server_url + "/", self.driver.current_url)
        self.assertTrue('Successfully logged in' in self.driver.page_source)

    def test_logout_email(self):
        self._login_helper(self.user.email, self.user_password)
        self._logout_helper()

    def test_create_resource(self):
        RESOURCE_TITLE = 'Selenium resource creation test'
        UPLOAD_FILE_PATH = '/hydroshare/manage.py'
        self._login_helper(self.user.email, self.user_password)

        # load my resources & click create new
        my_res_lnk = self.driver.find_element_by_xpath("//a[contains(text(),'My Resources')]")
        my_res_lnk.click()
        create_new_lnk = self.driver.find_element_by_link_text('Create new')
        create_new_lnk.click()

        # complete new resource form
        title_field = self.driver.find_element_by_name('title')
        file_field = self.driver.find_element_by_name('files')
        submit_btn = self.driver.find_element_by_xpath("//button[@type='submit']")

        self.assertTrue(title_field.is_displayed())
        title_field.send_keys(RESOURCE_TITLE)
        file_field.send_keys(UPLOAD_FILE_PATH + ',', keys.Keys.ENTER)
        submit_btn.click()

        # check results
        title = self.driver.find_element_by_xpath("//h2[@id='resource-title']").text
        self.assertEqual(title, RESOURCE_TITLE)
        citation = self.driver.find_element_by_xpath("//input[@id='citation-text']")
        citation_text = citation.get_attribute('value')
        import re
        m = re.search('HydroShare, http://www.hydroshare.org/resource/(.*)$', citation_text)
        shortkey = m.groups(0)[0]
        resource = BaseResource.objects.get()
        self.assertEqual(resource.title, RESOURCE_TITLE)
        self.assertEqual(resource.short_id, shortkey)
        # Unsure why the following is not working currently.
        # self.assertTrue("Congratulations!" in self.driver.page_source)


@override_settings(
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False,
    CSP_DICT={'default-src': 'unsafe-eval'}
)
class DesktopTests(FunctionalTestsCases, StaticLiveServerTestCase):
    def setUp(self):
        desktop_dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        desktop_dcap["phantomjs.page.settings.userAgent"] = (
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/27.0.1453.93 Safari/537.36")

        self.driver = webdriver.PhantomJS(desired_capabilities=desktop_dcap)
        self.driver.set_window_size(width=1920, height=1200)
        self.driver.implicitly_wait(10)
        self.driver.get(self.live_server_url)
        super(DesktopTests, self).setUp()

    def test_login_email(self):
        super(DesktopTests, self).test_login_email()

        # home page: returned after successful login with profile info in dropdown
        xpath_query = "//li[@id='profile-menu']/a[@class='dropdown-toggle']"
        dropdown = self.driver.find_element_by_xpath(xpath_query)
        dropdown.click()
        email_elem = self.driver.find_element_by_id('profile-menu-email')
        self.assertEquals(self.user.email, email_elem.get_attribute('innerHTML').strip())
        name_elem = self.driver.find_element_by_id('profile-menu-fullname')
        self.assertTrue(self.user.first_name in name_elem.get_attribute('innerHTML').strip())
        self.assertTrue(self.user.last_name in name_elem.get_attribute('innerHTML').strip())

    def test_show_login_link_desktop(self):
        self.driver.get(self.live_server_url)
        desktop_login_link = self.driver.find_element_by_id('signin-menu')
        self.assertTrue(desktop_login_link.is_displayed())


@override_settings(
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False,
    CSP_DICT={'default-src': 'unsafe-eval'}
)
class MobileTests(FunctionalTestsCases, StaticLiveServerTestCase):
    def setUp(self):
        mobile_dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        mobile_dcap["phantomjs.page.settings.userAgent"] = (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) "
                    "AppleWebKit/534.46 (KHTML, like Gecko) "
                    "Version/5.1 Mobile/9A334 Safari/7534.48.3")

        self.driver = webdriver.PhantomJS(desired_capabilities=mobile_dcap)
        # iPhone 5 resolution
        self.driver.set_window_size(width=640, height=1136)
        self.driver.get(self.live_server_url)
        super(MobileTests, self).setUp()

    def _open_nav_menu(self):
        toggle = self.driver.find_element_by_xpath("//button[contains(@class,'navbar-toggle')]")
        navbar = self.driver.find_element_by_xpath("//ul[contains(@class,'navbar-nav')]")
        if navbar.is_displayed():
            return
        toggle.click()
        try:
            WebDriverWait(self.driver, 20).until(EC.visibility_of(navbar))
        finally:
            if not navbar.is_displayed():
                self.fail()

    def _login_helper(self, login_name, user_password):
        self._open_nav_menu()
        super(MobileTests, self)._login_helper(login_name, user_password)
        self._open_nav_menu()

    def _logout_helper(self):
        self._open_nav_menu()
        logout = self.driver.find_element_by_xpath("//a[contains(text(),'Sign Out')]")
        logout.click()
        self.driver.delete_all_cookies()

    def test_register_account(self):
        self._open_nav_menu()
        super(MobileTests, self).test_register_account()

    def test_show_login_link_mobile(self):
        desktop_login = self.driver.find_element_by_id('signin-menu')
        mobile_login = self.driver.find_element_by_xpath("//li[contains(@class,'visible-xs')]/a")
        self.assertFalse(desktop_login.is_displayed())
        self.assertFalse(mobile_login.is_displayed())
        self._open_nav_menu()
        self.assertTrue(mobile_login.is_displayed())
