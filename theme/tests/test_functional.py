import time
import os
from uuid import uuid4

from django.contrib.auth.models import User, Group, Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common import desired_capabilities, keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from hs_core import hydroshare
from hs_core.models import BaseResource


def create_driver(platform='desktop', driver_name='phantomjs'):
    if platform is 'desktop':
        user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/27.0.1453.93 Safari/537.36')
        driver_kwargs = {'width': 800,
                         'height': 1000}
    elif platform is 'mobile':
        user_agent = ('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) '
                      'AppleWebKit/534.46 (KHTML, like Gecko) '
                      'Version/5.1 Mobile/9A334 Safari/7534.48.3')
        driver_kwargs = {'width': 640,
                         'height': 1136}
    else:
        raise ValueError('Unknown platform')

    if driver_name is 'phantomjs':
        dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = user_agent
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        driver.implicitly_wait(10)
    elif driver_name is 'firefox':
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", user_agent)
        cap = webdriver.common.desired_capabilities.DesiredCapabilities.FIREFOX
        cap['marionette'] = True
        driver = webdriver.Firefox(profile,
                                   capabilities=cap)
        driver.implicitly_wait(20)
    else:
        raise ValueError('Unknown driver')

    driver.set_window_size(**driver_kwargs)

    return driver


def upload_file(driver, file_field, local_upload_path):
    # TODO: Temporary workaround for PhantomJS bug.
    #   See: https://github.com/ariya/phantomjs/issues/10993

    if type(driver) == webdriver.PhantomJS:
        driver.execute_script("return arguments[0].multiple = false", file_field)
        file_field.send_keys(local_upload_path)
    elif type(driver) == webdriver.Firefox or type(driver) == webdriver.FirefoxProfile:
        file_field._execute(Command.SEND_KEYS_TO_ELEMENT, {'value': list(os.path.abspath(local_upload_path))})
    else:
        raise ValueError('Unkonwn driver')


class FunctionalTestsCases(object):
    """
    Shared Mobile and Desktop test cases (all are run twice, so use sparingly)
    For single browser cases see desired browser specific classes below.
    All test cases can safely assume that the home page is loaded.
    """
    fixtures = ['theme/tests/fixtures.json']

    def setUp(self):
        super(FunctionalTestsCases, self).setUp()

        self.driver = None
        self.user_password = "Users_Cats_FirstName"
        if not User.objects.filter(email='user30@example.com'):
            group, _ = Group.objects.get_or_create(name='Hydroshare Author')

            # Permissions model level permissions are required for some actions because of legacy Mezzanine
            # It also relies on the magic "Hydroshare Author" group which is not created via a migration :/
            hs_perms = Permission.objects.filter(content_type__app_label__startswith="hs_")

            group.permissions.add(*list(hs_perms))
            self.user = hydroshare.create_account(
                'user30@example.com',
                username='user30',
                first_name='User_FirstName',
                last_name='User_LastName',
                password=self.user_password,
                groups=[group]
            )
            self.user.save()
        else:
            self.user = User.objects.get(email='user30@example.com')

    def tearDown(self):
        self.driver.save_screenshot('tests-debug-teardown.png')
        self.driver.quit()
        super(FunctionalTestsCases, self).tearDown()

    def wait_for_visible(self, selector_method, selector_str,except_fail=True):
        elem = False
        selector = (selector_method, selector_str)
        try:
            WebDriverWait(self.driver, 5).until(
                expected_conditions.visibility_of_element_located(selector)
            )
            elem = self.driver.find_element(*selector)
        except TimeoutException:
            self.driver.save_screenshot('visible' + selector[1].replace(' ', '') + '.png')
            if except_fail:
                self.fail(selector[1] + " not visible within timeout")
        return elem

    def _login_helper(self, login_name, user_password):
        # home page: click to login. Uses generic xpath for Mobile & Desktop
        for e in self.driver.find_elements_by_xpath("//a[contains(text(),'Sign In')]"):
            if e.is_displayed():
                e.click()
                break

        # login page: fill login form
        self.wait_for_visible(By.TAG_NAME, 'html')
        self.assertTrue('accounts/login/' in self.driver.current_url)
        self.wait_for_visible(By.CSS_SELECTOR, 'input[name="username"]').send_keys(login_name, keys.Keys.TAB)
        self.wait_for_visible(By.CSS_SELECTOR, 'input[name="password"]').send_keys(user_password, keys.Keys.TAB)
        self.wait_for_visible(By.CSS_SELECTOR, 'input[type="submit"]').send_keys(keys.Keys.ENTER)
        self.wait_for_visible(By.CSS_SELECTOR, '.home-page-block-title')

    def _logout_helper(self):
        pass

    def _create_resource_helper(self, upload_file_path, resource_title=None):
        if not resource_title:
            resource_title = str(uuid4())
        upload_file_path = os.path.abspath(upload_file_path)

        """
        # complete new resource form
        title_field = self.driver.find_element_by_css_selector('#txtTitle')
        # file_field = self.driver.find_element_by_name('files')
        self.driver.execute_script(
            var myZone = Dropzone.forElement('#hsDropzone');
            var blob = new Blob(new Array(), {type: 'image/png'});
            blob.name = 'filename.png'
            myZone.addFile(blob);  
        )
        submit_btn = self.driver.find_element_by_css_selector(".btn-create-resource")

        self.assertTrue(title_field.is_displayed())
        title_field.send_keys(RESOURCE_TITLE)
        submit_btn.click()
        """

        # load my resources & click create new
        my_resources = self.driver.find_element_by_xpath("//a[contains(text(),'My Resources')]")
        try:
            WebDriverWait(self.driver, 5).until(expected_conditions.visibility_of(my_resources))
        except TimeoutException:
            self.driver.save_screenshot('myresources-not-found.png')
            self.fail('My resources link not visible')
        my_resources.click()

        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located(
                    (By.LINK_TEXT, "Create new")
                )
            )
        except TimeoutException:
            self.driver.save_screenshot('create-new-not-found.png')
            self.fail('Create new resource link not available')

        self.driver.find_element_by_link_text('Create new').click()

        # complete new resource form
        self.driver.find_element_by_name('title').send_keys(resource_title)
        file_field = self.driver.find_element_by_name('files')
        upload_file(self.driver, file_field, upload_file_path)
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        resource_detail_page_tag = self.driver.find_element_by_id('resource-title')
        self.assertTrue(resource_detail_page_tag.is_displayed())
        return resource_title

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
        self.driver.get(self.live_server_url)
        self._login_helper(self.user.email, self.user_password)
        self.assertEqual(self.live_server_url + "/", self.driver.current_url)
        self.assertTrue('Successfully logged in' in self.driver.page_source)

    def test_logout_email(self):
        self._login_helper(self.user.email, self.user_password)
        self._logout_helper()

    def test_create_resource(self):
        self._login_helper(self.user.email, self.user_password)
        resource_title = self._create_resource_helper('./manage.py')

        """
        # check results
        title_field = self.driver.find_element_by_css_selector("#resource-title")
        self.assertTrue(title_field.is_displayed())
        self.assertEqual(title_field.text, RESOURCE_TITLE)
        citation_text = self.driver.find_element_by_css_selector("#citation-text").text
        """

        title = self.driver.find_element_by_xpath("//h2[@id='resource-title']").text
        self.assertEqual(title, resource_title)
        citation = self.driver.find_element_by_xpath("//input[@id='citation-text']")
        citation_text = citation.get_attribute('value')
        import re
        m = re.search('HydroShare, http.*/resource/(.*)$', citation_text)
        shortkey = m.groups(0)[0]
        resource = BaseResource.objects.get()
        self.assertEqual(resource.title, resource_title)
        self.assertEqual(resource.short_id, shortkey)
        self.assertEqual(resource.creator, self.user)
        # Unsure why the following is not working currently.
        self.assertTrue("Congratulations!" in self.driver.page_source)


@override_settings(
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False,
    CSP_DICT={'default-src': 'unsafe-eval'}
)
class DesktopTests(FunctionalTestsCases, StaticLiveServerTestCase):
    allow_database_queries = True

    def setUp(self, driver=None):
        super(DesktopTests, self).setUp()
        self.driver = driver
        if not driver:
            self.driver = create_driver('desktop')
        self.driver.get(self.live_server_url)

    def _logout_helper(self):
        self.driver.get(self.live_server_url)
        self.wait_for_visible(By.CSS_SELECTOR, '#profile-menu .dropdown-toggle').click()
        self.wait_for_visible(By.CSS_SELECTOR, '#signout-menu').click()

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

    def test_folder_drag(self):
        self._login_helper(self.user.email, self.user_password)
        self._create_resource_helper('./manage.py')

        self.driver.find_element_by_id('edit-metadata').click()

        # create new folder
        self.assertTrue(self.driver.find_element_by_id('fb-files-container').is_displayed())
        self.driver.find_element_by_xpath("//h3[text() = 'Content']").location_once_scrolled_into_view
        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.visibility_of_element_located(
                    (By.CLASS_NAME, 'fb-file-name')
                )
            )
        except TimeoutException:
            self.driver.save_screenshot('resource-contents-display-timeout.png')
            self.fail('Create folder modal not available')
        self.driver.find_element_by_id('fb-files-container').click()
        self.assertTrue(self.driver.find_element_by_id('fb-create-folder').is_enabled())
        self.driver.find_element_by_id('fb-create-folder').click()
        # wait for modal to appear
        try:
            WebDriverWait(self.driver, 10).until(
                expected_conditions.visibility_of_element_located(
                    (By.ID, 'txtFolderName')
                )
            )
        except TimeoutException:
            self.driver.save_screenshot('create-folder-modal-timeout.png')
            self.fail('Create folder modal not available')
        self.driver.find_element_by_id('txtFolderName').send_keys('Button Folder')
        self.driver.find_element_by_id('btn-create-folder').click()

        # TODO: try context click for creating a new folder

        # drag and drop into new folder
        time.sleep(3)
        self.assertEqual(len(self.driver.find_elements_by_class_name('fb-file-name')), 2)
        file_el = self.driver.find_element_by_class_name('fb-file')
        folder_el = self.driver.find_element_by_class_name('fb-folder')
        action_chain = webdriver.ActionChains(self.driver)
        action_chain.drag_and_drop(file_el, folder_el).perform()
        time.sleep(10)

        # double click on new folder
        #folder_el = self.driver.find_element_by_class_name('fb-folder')
        #self.driver.find_element_by_id('fb-files-container').click()
        #webdriver.ActionChains(self.driver).move_to_element(folder_el).double_click(folder_el).perform()
        folder_el = self.driver.find_element_by_css_selector('#hs-file-browser li.fb-folder')
        webdriver.ActionChains(self.driver).move_to_element(folder_el).click().perform()
        time.sleep(3)
        self.driver.execute_script("$('#hs-file-browser li.fb-folder').dblclick()")
        time.sleep(2)
        self.assertEqual(self.driver.find_element_by_class_name('fb-file-name').text, 'manage.py')

@override_settings(
    CSRF_COOKIE_SECURE=False,
    SESSION_COOKIE_SECURE=False,
    CSP_DICT={'default-src': 'unsafe-eval'}
)
class MobileTests(FunctionalTestsCases, StaticLiveServerTestCase):
    def setUp(self, driver=None):
        super(MobileTests, self).setUp()
        self.driver = driver
        if not driver:
            self.driver = create_driver('mobile')
        self.driver.get(self.live_server_url)

    def _open_nav_menu_helper(self):
        if self.wait_for_visible(By.CSS_SELECTOR, 'ul.navbar-nav', except_fail=False):
            return
        self.wait_for_visible(By.CSS_SELECTOR, 'button.navbar-toggle').click()
        self.wait_for_visible(By.CSS_SELECTOR, 'ul.navbar-nav')

    def _login_helper(self, login_name, user_password):
        self._open_nav_menu_helper()
        super(MobileTests, self)._login_helper(login_name, user_password)
        self._open_nav_menu_helper()

    def _logout_helper(self):
        self._open_nav_menu_helper()
        logout = self.driver.find_element_by_xpath("//a[contains(text(),'Sign Out')]")
        logout.click()
        self.driver.delete_all_cookies()

    def test_register_account(self):
        self._open_nav_menu_helper()
        super(MobileTests, self).test_register_account()

    def test_show_login_link_mobile(self):
        self.driver.get(self.live_server_url)
        desktop_login = self.driver.find_element_by_id('signin-menu')
        mobile_login = self.driver.find_element_by_xpath("//li[contains(@class,'visible-xs')]/a")
        self.assertFalse(desktop_login.is_displayed())
        self.assertFalse(mobile_login.is_displayed())
        self._open_nav_menu_helper()
        self.assertTrue(mobile_login.is_displayed())
