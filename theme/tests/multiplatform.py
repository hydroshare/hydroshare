import os
import re
import time
from uuid import uuid4

from django.contrib.auth.models import User, Group, Permission
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse
from django.core import mail

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common import desired_capabilities, keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from hs_core import hydroshare
from hs_core.models import BaseResource


def create_driver(platform='desktop', driver_name='phantomjs'):
    if platform is 'desktop':
        user_agent = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/27.0.1453.93 Safari/537.36')
        window_size = {'width': 800, 'height': 1000}
    elif platform is 'mobile':
        user_agent = ('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) '
                      'AppleWebKit/534.46 (KHTML, like Gecko) '
                      'Version/5.1 Mobile/9A334 Safari/7534.48.3')
        window_size = {'width': 640, 'height': 1136}
    else:
        raise ValueError('Unknown platform')

    if driver_name is 'phantomjs':
        dcap = dict(desired_capabilities.DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = user_agent
        driver = webdriver.PhantomJS(desired_capabilities=dcap)
        driver.implicitly_wait(15)
        driver.set_page_load_timeout(20)
    elif driver_name is 'firefox':
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", user_agent)
        cap = webdriver.common.desired_capabilities.DesiredCapabilities.FIREFOX
        driver = webdriver.Firefox(profile, capabilities=cap)
        driver.implicitly_wait(15)
        driver.set_page_load_timeout(20)
    else:
        raise ValueError('Unknown driver')

    driver.set_window_size(**window_size)

    return driver


def upload_file(driver, file_field, local_upload_path):
    # XXX: Temporary workaround for PhantomJS bug.
    #   See: https://github.com/ariya/phantomjs/issues/10993

    if type(driver) == webdriver.PhantomJS:
        driver.execute_script("return arguments[0].multiple = false", file_field)
        file_field.send_keys(local_upload_path)
    elif type(driver) == webdriver.Firefox or type(driver) == webdriver.FirefoxProfile:
        full_path = os.path.abspath(local_upload_path)
        file_field._execute(Command.SEND_KEYS_TO_ELEMENT, {'value': list(full_path)})
    else:
        raise ValueError('Unkonwn driver')


class SeleniumTestsParentClass(object):
    class MultiPlatformTests(StaticLiveServerTestCase):
        """
        Shared Mobile and Desktop test cases (all are run twice, so use sparingly)
        For single browser cases see desired browser specific classes below.
        All test cases can safely assume that the home page is loaded.
        """
        fixtures = ['theme/tests/fixtures.json']

        def setUp(self):
            super(StaticLiveServerTestCase, self).setUp()
            self.driver = None
            self.user_password = 'Users_Cats_FirstName'
            if not User.objects.filter(email='user30@example.com'):
                group, _ = Group.objects.get_or_create(name='Hydroshare Author')

                # Model level permissions are required for some actions bc of legacy Mezzanine
                # Also relies on the magic "Hydroshare Author" group
                hs_perms = Permission.objects.all()
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
                group.save()
            else:
                self.user = User.objects.get(email='user30@example.com')

        def tearDown(self):
            self.driver.save_screenshot('teardown.png')
            self.driver.quit()
            super(StaticLiveServerTestCase, self).tearDown()

        def wait_for_visible(self, selector_method, selector_str, timeout=10, except_fail=True):
            selector = (selector_method, selector_str)
            try:
                WebDriverWait(self.driver, timeout).until(
                    expected_conditions.visibility_of_element_located(selector)
                )
            except TimeoutException:
                if except_fail:
                    self.driver.save_screenshot('visible' + selector[1].replace(' ', '') + '.png')
                    err_msg = '{} not visible within timeout. Screenshot saved'.format(selector[1])
                    # if there is an issue with the selector, raise a relevant an error.
                    self.assertTrue(self.driver.find_element(*selector).is_displayed(), err_msg)
                    # failsafe just in case it became visible while we were writing the screenshot
                    self.fail(err_msg)
                else:
                    return None
            return self.driver.find_element(*selector)

        def _login_helper(self, login, password):
            # home page: click to login. Uses generic xpath for Mobile & Desktop
            for e in self.driver.find_elements_by_xpath('//a[contains(text(),"Sign In")]'):
                if e.is_displayed():
                    e.click()
                    break

            # login page: fill login form
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="username"]').send_keys(login)
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="password"]').send_keys(password)
            self.wait_for_visible(
                                  By.CSS_SELECTOR, 'input[type="submit"]'
                                  ).send_keys(keys.Keys.ENTER)
            self.wait_for_visible(By.CSS_SELECTOR, '.home-page-block-title')

        def _logout_helper(self):
            raise NotImplementedError

        def _create_resource_helper(self, resource_title='Default Title'):
            if not resource_title:
                resource_title = str(uuid4())

            # load my resources & click create new
            self.wait_for_visible(By.XPATH, '//a[contains(text(),"My Resources")]').click()
            self.wait_for_visible(By.LINK_TEXT, 'Create new').click()

            # complete new resource form
            self.wait_for_visible(By.CSS_SELECTOR, '#select-resource-type').click()
            self.wait_for_visible(By.CSS_SELECTOR, 'a[data-value="GenericResource"]').click()
            self.wait_for_visible(By.CSS_SELECTOR, '#txtTitle').send_keys(resource_title)
            self.wait_for_visible(By.CSS_SELECTOR, '#hsDropzone')
            self.driver.execute_script("""
                var myZone = Dropzone.forElement('#hsDropzone');
                var blob = new Blob(new Array(), {type: 'image/png'});
                blob.name = 'file.png'
                myZone.addFile(blob);
            """)
            time.sleep(1)
            self.wait_for_visible(By.CSS_SELECTOR, '.btn-create-resource').click()
            self.wait_for_visible(By.CSS_SELECTOR, '#resource-title')
            time.sleep(1)
            self.driver.get(self.driver.current_url)
            self.wait_for_visible(By.CSS_SELECTOR, '#resource-title')
            return resource_title

        def test_register_account(self):
            usr = {
                'fn': '<strong>First</strong>',
                'ln': 'last',
                'email': 'u@example.com',
                'user': 'uname',
                'pass': 'drowssap',
                'org': 'My University',
                'title': 'Adjunct'
             }

            login_link_css_selector = 'a[href="{}"]'.format(reverse('login'))
            for e in self.driver.find_elements(By.CSS_SELECTOR, login_link_css_selector):
                if e.is_displayed():
                    e.click()
                    break

            # there is nothing to reverse() for sign-up because it is hard coded via Mezzanine
            self.wait_for_visible(By.CSS_SELECTOR, 'a[href="/sign-up/?next="]').click()
            self.wait_for_visible(By.CSS_SELECTOR, '#form-signup')

            # monkey patch SignUpForm to always verify the captcha
            from theme.forms import SignupForm

            def verify_captcha_patch(*args, **kwargs):
                return True
            SignupForm.verify_captcha = verify_captcha_patch

            # Register a new account
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="first_name"]').send_keys(usr['fn'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="last_name"]').send_keys(usr['ln'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="email"]').send_keys(usr['email'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="username"]').send_keys(usr['user'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="password1"]').send_keys(usr['pass'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="password2"]').send_keys(usr['pass'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="recaptcha_response_field"]') \
                .send_keys('response')
            self.wait_for_visible(By.CSS_SELECTOR, 'input#signup').click()

            # Verify new account by clicking on link in that came in email
            self.wait_for_visible(By.CSS_SELECTOR, '#home-page-carousel')
            alert_div = self.wait_for_visible(By.CSS_SELECTOR, '.page-tip')
            alert_text = alert_div.find_element(By.CSS_SELECTOR, 'p').text
            self.assertIn('A verification email has been sent', alert_text)

            self.assertEqual(len(mail.outbox), 1)
            url = re.search(r'(?P<url>https?://[^\s]+)', mail.outbox[0].body).groupdict()['url']
            user = User.objects.get(email=usr['email'])
            self.assertFalse(user.is_active)
            with self.assertRaises(ValueError):
                pass

            self.driver.get(url)
            # Now that we have clicked the verify URL, the user will get some popups and be verified
            self.assertTrue(User.objects.get(email=usr['email']).is_active)
            self.wait_for_visible(By.CSS_SELECTOR, '#home-page-carousel')
            alert_div = self.wait_for_visible(By.CSS_SELECTOR, '.page-tip')
            alert_text = alert_div.find_element(By.CSS_SELECTOR, 'p').text
            self.assertEqual('Successfully signed up', alert_text)

            alert_span = self.wait_for_visible(By.CSS_SELECTOR, '#universalMessage span')
            alert_span.find_element(By.LINK_TEXT, 'user profile').click()

            # The user's name should be escaped in the profile so our user name
            # should not parse as HTML.
            h2 = self.wait_for_visible(By.CSS_SELECTOR, 'h2')
            with self.assertRaises(NoSuchElementException):
                h2.find_element(By.CSS_SELECTOR, 'strong')
            self.wait_for_visible(By.CSS_SELECTOR, '#btn-edit-profile').click()

            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="organization"]') \
                .send_keys(usr['org'])
            self.wait_for_visible(By.CSS_SELECTOR, 'input[name="title"]').send_keys(usr['title'])
            upload_field = self.wait_for_visible(By.CSS_SELECTOR, 'input[name="cv"]')
            upload_file(self.driver, upload_field, './manage.py')
            self.wait_for_visible(By.CSS_SELECTOR, 'button.btn-save-profile').click()

            alert_div = self.wait_for_visible(By.CSS_SELECTOR, '.page-tip')
            alert_text = alert_div.find_element(By.CSS_SELECTOR, 'p').text
            self.assertEqual('Your profile has been successfully updated.', alert_text)

            user = User.objects.get(email=usr['email'])
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)
            self.assertTrue(user.is_active)
            self.assertEqual(user.email, usr['email'])
            self.assertEqual(user.first_name, usr['fn'])
            self.assertEqual(user.last_name, usr['ln'])
            self.assertEqual(user.userprofile.title, usr['title'])
            self.assertEqual(user.userprofile.organization, usr['org'])
            self.assertTrue(user.check_password(usr['pass']))
            self.assertNotEqual('', user.userprofile.cv.url)

        def test_login_email(self):
            self.driver.get(self.live_server_url)
            self._login_helper(self.user.email, self.user_password)
            self.assertEqual('{}/'.format(self.live_server_url), self.driver.current_url)
            self.assertTrue('Successfully logged in' in self.driver.page_source)

        def test_logout_email(self):
            self._login_helper(self.user.email, self.user_password)
            self._logout_helper()

        def test_create_resource(self):
            self._login_helper(self.user.email, self.user_password)
            resource_title = self._create_resource_helper()

            title = self.wait_for_visible(By.CSS_SELECTOR, '#resource-title').text
            self.assertEqual(title, resource_title)
            citation_text = self.wait_for_visible(By.CSS_SELECTOR, 'div#citation-text').text
            m = re.search('HydroShare, http.*/resource/(.*)$', citation_text)
            shortkey = m.groups(0)[0]
            resource = BaseResource.objects.get()
            self.assertEqual(resource.title, resource_title)
            self.assertEqual(resource.short_id, shortkey)
            self.assertEqual(resource.creator, self.user)

        def test_create_comment(self):
            self.user.first_name = '<strong>First Name</strong>'
            self.user.save()
            comment_link_text = '<a href="http://example.com/">Comment Link Test</a>'

            self._login_helper(self.user.email, self.user_password)
            self._create_resource_helper('./manage.py')

            self.wait_for_visible(By.CSS_SELECTOR, '#id_comment').send_keys(comment_link_text)
            self.driver.find_element(By.CSS_SELECTOR, 'input[value="Comment"]').click()

            self.wait_for_visible(By.CSS_SELECTOR, '.comment-form')
            self.assertTrue('#comment-' in self.driver.current_url)

            # Our new comment link should not look like HTML to our parser.
            with self.assertRaises(NoSuchElementException):
                self.driver.find_element(By.LINK_TEXT, 'Comment Link Test')

            # Add the author name should not have a <strong> element
            comment_div = self.driver.find_element(By.CSS_SELECTOR, 'div.comment-author div')
            author_link = comment_div.find_element(By.CSS_SELECTOR, 'h4 a')
            self.assertEqual("{} {}".format(self.user.first_name, self.user.last_name),
                             author_link.text)
            with self.assertRaises(NoSuchElementException):
                author_link.find_element(By.CSS_SELECTOR, 'strong')
            self.assertTrue(unicode(self.user.id) in author_link.get_attribute('href'))
