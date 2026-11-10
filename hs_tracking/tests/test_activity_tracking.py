from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from hs_tracking.middleware import Tracking
from hs_tracking.signals import capture_download, capture_resource_download


class ActivityTrackingTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session = Mock()
        self.session.visitor.user = None
        self.session.visitor.id = 123
        self.session_lookup = patch(
            'hs_tracking.models.Session.objects.for_request',
            return_value=self.session,
        )
        self.session_lookup.start()
        self.addCleanup(self.session_lookup.stop)
        self.resource = Mock()
        self.resource.short_id = 'a' * 32
        self.resource.size = 1024
        self.resource.resource_type = 'CompositeResource'
        self.resource.title = 'Test resource'
        self.resource.doi = ''
        self.resource.absolute_url = '/resource/' + self.resource.short_id + '/'
        self.resource.raccess.published = False
        self.resource.metadata.creators.only.return_value.all.return_value = []
        self.resource.get_relation_version_res_url.return_value = None

    def requests(self, path):
        cases = [
            ('Mozilla/5.0', True, 'True'),
            ('Googlebot/2.1 (+http://www.googlebot.com/bot.html)', False, 'False'),
            (None, False, 'None'),
            ('Mozilla/5.0', None, 'True'),
        ]
        for user_agent, request_is_human, expected in cases:
            headers = {'HTTP_USER_AGENT': user_agent} if user_agent is not None else {}
            request = self.factory.get(path, **headers)
            request.user = AnonymousUser()
            if request_is_human is not None:
                request.is_human = request_is_human
            yield request, user_agent, expected

    def recorded_fields(self):
        value = self.session.record.call_args.kwargs['value']
        return dict(pair.split('=', 1) for pair in value.split('|'))

    def test_visits_record_classification_and_user_agent(self):
        middleware = Tracking(lambda request: HttpResponse())
        paths = [
            (self.resource.absolute_url, True, False),
            ('/hsapi/resource/' + self.resource.short_id + '/files/', False, True),
        ]
        for path, landing, rest in paths:
            for request, user_agent, expected in self.requests(path):
                with self.subTest(path=path, user_agent=user_agent, expected=expected):
                    self.session.record.reset_mock()
                    response = HttpResponse()
                    self.assertIs(middleware.process_response(request, response), response)
                    self.session.record.assert_called_once()
                    self.assertEqual(self.session.record.call_args.args, ('visit',))
                    fields = self.recorded_fields()
                    self.assertEqual(fields['is_human'], expected)
                    self.assertEqual(fields['user_agent'], str(user_agent))
                    self.assertEqual(fields['request_url'], path)
                    self.assertEqual(fields['http_method'], 'GET')
                    self.assertEqual(fields['http_code'], '200')
                    self.assertIn('user_ip', fields)
                    self.assertIn('user_type', fields)
                    self.assertIn('user_email_domain', fields)
                    recorded = self.session.record.call_args.kwargs
                    self.assertEqual(recorded['resource_id'], self.resource.short_id)
                    self.assertEqual(recorded['landing'], landing)
                    self.assertEqual(recorded['rest'], rest)

    @patch('hs_tracking.signals.current_site_url', return_value='https://www.hydroshare.org')
    def test_downloads_record_classification_and_user_agent(self, site_url):
        for receiver, activity in [
            (capture_download, 'download'),
            (capture_resource_download, 'resource_download'),
        ]:
            for request, user_agent, expected in self.requests('/download/'):
                with self.subTest(activity=activity, user_agent=user_agent, expected=expected):
                    self.session.record.reset_mock()
                    receiver(
                        request=request,
                        resource=self.resource,
                        file_size=512,
                        download_file_name='data.csv',
                    )
                    self.session.record.assert_called_once()
                    self.assertEqual(self.session.record.call_args.args, (activity,))
                    fields = self.recorded_fields()
                    self.assertEqual(fields['is_human'], expected)
                    self.assertEqual(fields['user_agent'], str(user_agent))
                    self.assertEqual(fields['resource_guid'], self.resource.short_id)
                    self.assertIn('resource_metadata', fields)
                    if activity == 'download':
                        self.assertEqual(fields['filename'], 'data.csv')
                        self.assertEqual(fields['file_size'], '512')
                    recorded = self.session.record.call_args.kwargs
                    self.assertEqual(recorded['resource'], self.resource)
                    self.assertEqual(recorded['resource_id'], self.resource.short_id)

    def test_visits_still_skip_heartbeat_and_unsuccessful_responses(self):
        middleware = Tracking(lambda request: HttpResponse())
        for path, status in [('/heartbeat/', 200), ('/resource/', 302), ('/resource/', 404)]:
            with self.subTest(path=path, status=status):
                request = self.factory.get(path)
                request.user = AnonymousUser()
                request.is_human = True
                response = HttpResponse(status=status)
                self.assertIs(middleware.process_response(request, response), response)
        self.session.record.assert_not_called()

    def test_visits_still_require_user_attribute(self):
        request = self.factory.get('/resource/')
        request.is_human = True
        response = HttpResponse()
        middleware = Tracking(lambda request: HttpResponse())
        self.assertIs(middleware.process_response(request, response), response)
        self.session.record.assert_not_called()

    def test_downloads_still_require_request(self):
        capture_download(resource=self.resource)
        capture_resource_download(resource=self.resource)
        self.session.record.assert_not_called()

    def test_visits_record_only_referrer_hostname(self):
        middleware = Tracking(lambda request: HttpResponse())
        cases = [
            ('https://ChatGPT.com/c/example?token=secret#section', 'chatgpt.com'),
            ('https://www.hydroshare.org:443/search/?q=water', 'www.hydroshare.org'),
            ('http://example.org/', 'example.org'),
            (None, 'None'),
            ('', 'None'),
        ]
        for referrer, expected in cases:
            with self.subTest(referrer=referrer):
                self.session.record.reset_mock()
                headers = {'HTTP_REFERER': referrer} if referrer is not None else {}
                request = self.factory.get('/search/', **headers)
                request.user = AnonymousUser()
                middleware.process_response(request, HttpResponse())
                self.session.record.assert_called_once()
                fields = self.recorded_fields()
                self.assertEqual(fields['referrer_host'], expected)
                self.assertNotIn('secret', self.session.record.call_args.kwargs['value'])

    def test_invalid_referrer_does_not_prevent_visit_tracking(self):
        middleware = Tracking(lambda request: HttpResponse())
        for referrer in ['https://[invalid/', '/relative/path', 'not a URL', 'file:///tmp/file']:
            with self.subTest(referrer=referrer):
                self.session.record.reset_mock()
                request = self.factory.get('/search/', HTTP_REFERER=referrer)
                request.user = AnonymousUser()
                with patch('hs_tracking.middleware.logger.warning') as warning:
                    middleware.process_response(request, HttpResponse())
                warning.assert_called_once()
                self.session.record.assert_called_once()
                self.assertEqual(self.recorded_fields()['referrer_host'], 'None')
