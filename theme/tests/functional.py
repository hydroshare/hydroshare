import time

from django.core.urlresolvers import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By

from theme.tests.multiplatform import SeleniumTestsParentClass, create_driver


class DesktopTests(SeleniumTestsParentClass.MultiPlatformTests):
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
        self.wait_for_visible(By.CSS_SELECTOR, 'li[id="profile-menu"] a[class="dropdown-toggle"]').click()
        email = self.wait_for_visible(By.CSS_SELECTOR, '#profile-menu-email').get_attribute('innerHTML').strip()
        self.assertEquals(self.user.email, email)
        full_name = self.wait_for_visible(By.CSS_SELECTOR, '#profile-menu-fullname').get_attribute('innerHTML').strip()
        self.assertTrue(self.user.first_name in full_name)
        self.assertTrue(self.user.last_name in full_name)

    def test_show_login_link_desktop(self):
        self.driver.get(self.live_server_url)
        self.wait_for_visible(By.CSS_SELECTOR, '#signin-menu')

    def test_folder_drag(self):
        self._login_helper(self.user.email, self.user_password)
        self._create_resource_helper('./manage.py')

        self.wait_for_visible(By.CSS_SELECTOR, '#edit-metadata').click()

        # Find the files area and click button to create new folder
        self.wait_for_visible(By.CSS_SELECTOR, '#fb-files-container')
        self.wait_for_visible(By.CSS_SELECTOR, '.fb-file-name').click()
        self.wait_for_visible(By.CSS_SELECTOR, '#fb-create-folder').click()

        # Fill in new folder modal
        self.wait_for_visible(By.CSS_SELECTOR, '#txtFolderName').send_keys('Button Folder')
        self.wait_for_visible(By.CSS_SELECTOR, '#btn-create-folder').click()

        # TODO: try context click for creating a new folder

        # drag and drop into new folder
        folder_drag_dest = self.wait_for_visible(By.CSS_SELECTOR, '.fb-folder')
        file_to_drag = self.wait_for_visible(By.CSS_SELECTOR, '.fb-file')
        action_chain = webdriver.ActionChains(self.driver)
        action_chain.drag_and_drop(file_to_drag, folder_drag_dest).perform()
        time.sleep(3)

        # Enter new folder and verify contents
        self.wait_for_visible(By.CSS_SELECTOR, '#fb-files-container').click()
        folder = self.driver.find_element_by_css_selector('#hs-file-browser li.fb-folder')

        # Create a mouse down (not click) event on the folder in order to select it prior to sending the double click.
        webdriver.ActionChains(self.driver).move_to_element(folder).click_and_hold().release().double_click().perform()
        self.wait_for_visible(By.XPATH, "//li[@class='active']/span[contains(text(),'Button Folder')]")
        self.assertEqual(self.driver.find_element_by_class_name('fb-file-name').text, 'manage.py')


class MobileTests(SeleniumTestsParentClass.MultiPlatformTests):
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
        self.wait_for_visible(By.CSS_SELECTOR, 'a[href="{}"]'.format(reverse('logout')))

    def test_register_account(self):
        self.driver.get(self.live_server_url)
        self._open_nav_menu_helper()
        super(MobileTests, self).test_register_account()

    def test_show_login_link_mobile(self):
        self.driver.get(self.live_server_url)
        desktop_login = self.driver.find_element_by_css_selector('#signin-menu')
        mobile_login = self.driver.find_element_by_css_selector('li.visible-xs a')

        self.assertFalse(desktop_login.is_displayed())
        self.assertFalse(mobile_login.is_displayed())
        self._open_nav_menu_helper()
        self.assertTrue(mobile_login.is_displayed())
