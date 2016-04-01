from datetime import datetime, timedelta

from django.test import TestCase
from django.contrib.auth.models import User

from mock import patch, Mock

from .models import Variable, Session, Visitor, SESSION_TIMEOUT


class TrackingTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser', email='testuser@example.com')
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
        self.assertEqual('"Hello, World"', self.session.variable_set.get(name='text').value)

    def test_get(self):
        self.assertEqual(42, Variable(name='var', value='42').get_value())
        self.assertEqual(3.14, Variable(name='var', value='3.14').get_value())
        self.assertEqual(True, Variable(name='var', value='true').get_value())
        self.assertEqual(False, Variable(name='var', value='false').get_value())
        self.assertEqual("X", Variable(name='var', value='"X"').get_value())

    def test_for_request_new(self):
        request = self.createRequest(user=self.user)
        request.session = {}
        session = Session.objects.for_request(request)
        self.assertTrue(request.session.has_key('hs_tracking_id'))

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
