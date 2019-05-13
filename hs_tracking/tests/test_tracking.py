from datetime import datetime, timedelta
import csv
from cStringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.http import HttpRequest, QueryDict, response
from mock import patch, Mock

from hs_tracking.models import Variable, Session, Visitor, SESSION_TIMEOUT, VISITOR_FIELDS
from hs_tracking.views import AppLaunch
import hs_tracking.utils as utils
import urllib
from pprint import pprint


class ViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser',
                                        email='testuser@example.com')
        self.user.set_password('password')
        self.user.save()
        profile = self.user.userprofile
        profile_data = {
            'country': 'USA',
        }
        for field in profile_data:
            setattr(profile, field, profile_data[field])
        profile.save()
        self.visitor = Visitor.objects.create()
        self.session = Session.objects.create(visitor=self.visitor)

    def createRequest(self, user=None):
        self.request = Mock()
        if user is not None:
            self.request.user = user

        # sample request with mocked ip address
        self.request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.255.182, 10.0.0.0,' +
                                    '127.0.0.1, 198.84.193.157, '
            '177.139.233.139',
            'HTTP_X_REAL_IP': '177.139.233.132',
            'REMOTE_ADDR': '177.139.233.133',
        }
        self.request.method = 'GET'
        self.request.session = {}
        return self.request

    def test_get(self):

        # check that there are no logs for app_launch
        app_lauch_cnt = Variable.objects.filter(name='app_launch').count()
        self.assertEqual(app_lauch_cnt, 0)

        # create a mock request object
        r = self.createRequest(self.user)

        # build request 'GET'
        res_id = 'D7a7de92941a044049a7b8ad09f4c75bb'
        res_type = 'GenericResource'
        app_name = 'test'
        request_url = 'https://apps.hydroshare.org/apps/hydroshare-gis/' \
                      '?res_id=%s&res_type=%s' % (res_id, res_type)

        app_url = urllib.quote(request_url)
        href = 'url=%s;name=%s' % (app_url, app_name)
        r.GET = QueryDict(href)

        # invoke the app logging endpoint
        app_logging = AppLaunch()
        url_redirect = app_logging.get(r)

        # validate response
        self.assertTrue(type(url_redirect) == response.HttpResponseRedirect)
        self.assertTrue(url_redirect.url == request_url)

        # validate logged data
        app_lauch_cnt = Variable.objects.filter(name='app_launch').count()
        self.assertEqual(app_lauch_cnt, 1)
        data = list(Variable.objects.filter(name='app_launch'))
        values = dict(tuple(pair.split('=')) for pair in data[0].value.split('|'))

        self.assertTrue('res_type' in values.keys())
        self.assertTrue('name' in values.keys())
        self.assertTrue('user_email_domain' in values.keys())
        self.assertTrue('user_type' in values.keys())
        self.assertTrue('user_ip' in values.keys())
        self.assertTrue('res_id' in values.keys())

        self.assertTrue(values['res_type'] == res_type)
        self.assertTrue(values['name'] == app_name)
        self.assertTrue(values['user_email_domain'] == self.user.email[-3:])
        self.assertTrue(values['user_type'] == 'Unspecified')
        self.assertTrue(values['user_ip'] == '198.84.193.157')
        self.assertTrue(values['res_id'] == res_id)


class TrackingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser',
                                        email='testuser@example.com')
        self.user.set_password('password')
        self.user.save()
        profile = self.user.userprofile
        profile_data = {
            'country': 'USA',
        }
        for field in profile_data:
            setattr(profile, field, profile_data[field])
        profile.save()
        self.visitor = Visitor.objects.create()
        self.session = Session.objects.create(visitor=self.visitor)

    def createRequest(self, user=None):
        request = Mock()
        if user is not None:
            request.user = user

        # sample request with mocked ip address
        request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.255.182, 10.0.0.0, ' +
                                    '127.0.0.1, 198.84.193.157, '
            '177.139.233.139',
            'HTTP_X_REAL_IP': '177.139.233.132',
            'REMOTE_ADDR': '177.139.233.133',
        }

        return request

    def test_record_variable(self):
        self.session.record('integer', 42)
        self.session.record('float', 3.14)
        self.session.record('true', True)
        self.session.record('false', False)
        self.session.record('text', "Hello, World")

        pprint(self.session.get(name='false'))
        self.assertEqual(42, self.session.get(name='integer'))
        self.assertEqual(3.14, self.session.get(name='float'))
        self.assertEqual(True, self.session.get(name='true'))
        self.assertEqual(False, self.session.get(name='false'))
        self.assertEqual('Hello, World', self.session.get(name='text'))

    def test_record_bad_value(self):
        self.assertRaises(TypeError, self.session.record, 'bad', ['oh no i cannot handle arrays'])

    def test_get(self):
        v = Variable(name='foo', value='0', type=3)
        pprint(v)
        print("value={}, type={}".format(v.value, v.type))
        self.assertEqual(42, Variable(name='var', value='42', type=0).get_value())
        self.assertEqual(3.14, Variable(name='var', value='3.14', type=1).get_value())
        self.assertEqual("X", Variable(name='var', value='X', type=2).get_value())
        self.assertEqual(None, Variable(name='var', value='false', type=4).get_value())
        self.assertEqual(True, Variable(name='var', value='true', type=3).get_value())
        self.assertEqual(False, Variable(name='var', value='0', type=3).get_value())

    def test_for_request_new(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session = Session.objects.for_request(request)
        self.assertIn('hs_tracking_id', request.session)
        self.assertEqual(session.visitor.user.id, self.user.id)

    def test_for_request_existing(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session1 = Session.objects.for_request(request)
        session2 = Session.objects.for_request(request)
        self.assertEqual(session1.id, session2.id)

    def test_for_request_expired(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session1 = Session.objects.for_request(request)
        with patch('hs_tracking.models.datetime') as dt_mock:
            dt_mock.now.return_value = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
            session2 = Session.objects.for_request(request)
        self.assertNotEqual(session1.id, session2.id)
        self.assertEqual(session1.visitor.id, session2.visitor.id)

    def test_for_other_user(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session1 = Session.objects.for_request(request)

        user2 = User.objects.create(username='testuser2', email='testuser2@example.com')
        request = self.createRequest(user=user2)
        request.session = {}
        session2 = Session.objects.for_request(request)

        self.assertNotEqual(session1.id, session2.id)
        self.assertNotEqual(session1.visitor.id, session2.visitor.id)

    def test_export_visitor_info(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session1 = Session.objects.for_request(request)
        info = session1.visitor.export_visitor_information()

        self.assertEqual(info['country'], 'USA')
        self.assertEqual(info['username'], 'testuser')

    def test_tracking_view(self):
        self.user.is_staff = True
        self.user.save()
        client = Client()
        client.login(username=self.user.username, password='password')

        response = client.get('/tracking/reports/profiles/')
        reader = csv.reader(StringIO(response.content))
        rows = list(reader)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(rows[0], VISITOR_FIELDS)
        i = VISITOR_FIELDS.index('username')
        # Row 1 is the original unauthenticated session created in setUp()
        self.assertEqual(rows[1][i], '')
        # Row 2 is the user we just authenticated
        self.assertEqual(rows[2][i], self.user.username)

    def test_history_empty(self):
        self.user.is_staff = True
        self.user.save()
        client = Client()
        response = client.get('/tracking/reports/history/')
        self.assertEqual(response.status_code, 200)
        reader = csv.reader(StringIO(response.content))
        rows = list(reader)
        count = Variable.objects.all().count()
        self.assertEqual(len(rows), count + 1)  # +1 to account for the session header

    def test_history_variables(self):
        self.user.is_staff = True
        self.user.save()
        client = Client()

        variable = self.session.record('testvar', "abcdef")
        self.assertEqual(variable.session.id, self.session.id)

        response = client.get('/tracking/reports/history/')
        self.assertEqual(response.status_code, 200)
        reader = csv.DictReader(StringIO(response.content))
        rows = list(reader)
        data = rows[-1]

        self.assertEqual(int(data['session']), self.session.id)
        self.assertEqual(int(data['visitor']), self.visitor.id)
        self.assertEqual(data['variable'], "testvar")
        self.assertEqual(data['value'], "abcdef")

    def test_capture_logins_and_logouts(self):
        self.assertEqual(Variable.objects.count(), 0)

        client = Client()
        client.login(username=self.user.username, password='password')

        self.assertEqual(Variable.objects.count(), 2)
        var1, var2 = Variable.objects.all()

        kvp = dict(tuple(pair.split('=')) for pair in var1.value.split('|'))
        self.assertEqual(var1.name, 'begin_session')
        self.assertEqual(len(kvp.keys()),  3)

        kvp = dict(tuple(pair.split('=')) for pair in var2.value.split('|'))
        self.assertEqual(var2.name, 'login')
        self.assertEqual(len(kvp.keys()), 3)

        client.logout()

        self.assertEqual(Variable.objects.count(), 3)
        var = Variable.objects.latest('timestamp')
        kvp = dict(tuple(pair.split('=')) for pair in var.value.split('|'))
        self.assertEqual(var.name, 'logout')
        self.assertEqual(len(kvp.keys()), 3)

    def test_activity_parsing(self):

        client = Client()
        client.login(username=self.user.username, password='password')

        self.assertEqual(Variable.objects.count(), 2)
        var1, var2 = Variable.objects.all()

        kvp = dict(tuple(pair.split('=')) for pair in var1.value.split('|'))
        self.assertEqual(var1.name, 'begin_session')
        self.assertEqual(len(kvp.keys()),  3)

        client.logout()


class UtilsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', email='testuser@example.com')
        self.user.set_password('password')
        self.user.save()

        self.visitor = Visitor.objects.create()
        self.session = Session.objects.create(visitor=self.visitor)

        # sample request with mocked ip address
        self.request = HttpRequest()
        self.request.META = {
            'HTTP_X_FORWARDED_FOR': '192.168.255.182, 10.0.0.0, 127.0.0.1, 198.84.193.157, '
            '177.139.233.139',
            'HTTP_X_REAL_IP': '177.139.233.132',
            'REMOTE_ADDR': '177.139.233.133',
        }

    def tearDown(self):
        self.user.delete

    def test_std_log_fields(self):

        log_fields = utils.get_std_log_fields(self.request, self.session)
        self.assertTrue(len(log_fields.keys()) == 3)
        self.assertTrue('user_ip' in log_fields)
        self.assertTrue('user_type' in log_fields)
        self.assertTrue('user_email_domain' in log_fields)

    def test_ishuman(self):

        useragents = [
            ('Mozilla/5.0 (compatible; bingbot/2.0; '
             '+http://www.bing.com/bingbot.htm)', False),
            ('Googlebot/2.1 (+http://www.googlebot.com/bot.html)', False),
            ('Mozilla/5.0 (compatible; Yahoo! Slurp; '
             'http://help.yahoo.com/help/us/ysearch/slurp)', False),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) '
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36', True),
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) '
             'AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27', True),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 '
             'Firefox/21.0', True),
            ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 '
             'Edge/13.10586', True)
        ]

        for useragent, ishuman in useragents:
            self.assertEqual(ishuman, utils.is_human(useragent))

    def test_get_user_email(self):

        # list of common and unusual valid email address formats
        valid_emails = [
                ('email@example.com', 'com'),
                ('firstname.lastname@example.com', 'com'),
                ('firstname+lastname@example.com', 'com'),
                ('"email"@example.com', 'com'),
                ('1234567890@example.com', 'com'),
                ('email@example-one.com', 'com'),
                ('_______@example.com', 'com'),
                ('email@example.co.uk', 'co.uk'),
                ('firstname-lastname@example.com', 'com'),
                ('much."more\ unusual"@example.com', 'com'),
                ('very.unusual."@".unusual.com@example.com', 'com'),
                ('very."(),:;<>[]".VERY."very@\\ "very".unusual@strange.example.com', 'example.com')
                ]

        # create session for each email and test email domain parsing
        for email, dom in valid_emails:
            user = User.objects.create(username='testuser1', email=email)
            visitor = Visitor.objects.create()
            visitor.user = user
            session = Session.objects.create(visitor=visitor)
            emaildom = utils.get_user_email_domain(session)
            self.assertTrue(emaildom == dom)
            user.delete()

    def test_client_ip(self):
        ip = utils.get_ip(self.request)
        self.assertEqual(ip, "198.84.193.157")

    def test_get_user_type(self):

        user_types = ['Faculty', 'Researcher', 'Test', None]
        for user_type in user_types:
            self.user.userprofile.user_type = user_type
            visitor = Visitor.objects.create()
            visitor.user = self.user
            session = Session.objects.create(visitor=visitor)
            usrtype = utils.get_user_type(session)
            self.assertTrue(user_type == usrtype)

        del self.user.userprofile.user_type
        visitor = Visitor.objects.create()
        visitor.user = self.user
        session = Session.objects.create(visitor=visitor)
        usrtype = utils.get_user_type(session)
        # https://docs.djangoproject.com/en/2.1/releases/1.10/
        # Accessing a deleted field on a model instance reloads the field's value
        # instead of raising AttributeError
        self.assertTrue(usrtype == "Unspecified")
