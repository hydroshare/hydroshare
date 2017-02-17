from datetime import datetime, timedelta
import csv
from cStringIO import StringIO

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client

from mock import patch, Mock

from .models import Variable, Session, Visitor, SESSION_TIMEOUT, VISITOR_FIELDS


class TrackingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', email='testuser@example.com')
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
        return request

    def test_record_variable(self):
        self.session.record('int', 42)
        self.session.record('float', 3.14)
        self.session.record('true', True)
        self.session.record('false', False)
        self.session.record('text', "Hello, World")

        self.assertEqual("42", self.session.variable_set.get(name='int').value)
        self.assertEqual("3.14", self.session.variable_set.get(name='float').value)
        self.assertEqual("true", self.session.variable_set.get(name='true').value)
        self.assertEqual("false", self.session.variable_set.get(name='false').value)
        self.assertEqual('Hello, World', self.session.variable_set.get(name='text').value)

    def test_record_bad_value(self):
        self.assertRaises(TypeError, self.session.record, 'bad', ['oh no i cannot handle arrays'])

    def test_get(self):
        self.assertEqual(42, Variable(name='var', value='42', type=0).get_value())
        self.assertEqual(3.14, Variable(name='var', value='3.14', type=1).get_value())
        self.assertEqual(True, Variable(name='var', value='true', type=3).get_value())
        self.assertEqual(False, Variable(name='var', value='false', type=3).get_value())
        self.assertEqual("X", Variable(name='var', value='X', type=2).get_value())
        self.assertEqual(None, Variable(name='var', value='', type=4).get_value())

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
        self.assertEqual(var1.name, 'begin_session')
        self.assertEqual(var1.value, 'none')
        self.assertEqual(var2.name, 'login')
        self.assertEqual(var2.value, 'none')

        client.logout()

        self.assertEqual(Variable.objects.count(), 3)
        var = Variable.objects.latest('timestamp')
        self.assertEqual(var.name, 'logout')
        self.assertEqual(var.value, 'none')
