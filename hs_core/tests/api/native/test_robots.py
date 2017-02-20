
import datetime

from django.test import Client, TestCase
from django.utils import timezone

from django.core.urlresolvers import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
import requests
from hs_core.tests.api.rest.base import HSRESTTestCase
from cStringIO import StringIO
from hs_tracking import models as hs_tracking
from django.test.client import RequestFactory
import csv
from django.contrib.auth.models import User
from mock import patch, Mock
from dateutil.parser import parse

class TestRobots(HSRESTTestCase):

    def test_robot_filter(self):

        agents = [
            ('Mozilla/5.0 (compatible; bingbot/2.0; '
            '+http://www.bing.com/bingbot.htm)', 0),
            ('Googlebot/2.1 (+http://www.googlebot.com/bot.html)', 0),
             ('Mozilla/5.0 (compatible; Yahoo! Slurp; '
            'http://help.yahoo.com/help/us/ysearch/slurp)', 0),
              ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36', 1),
               ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) '
            'AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27', 1),
                ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0', 1),
                 ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586', 1)
        ]
        
        # make a request to hydroshare with each useragent and check
        # if the activity has been recorded
        for agent, expected_visits in agents:

            start_dt = timezone.now()
            headers = requests.utils.default_headers()
            headers.update({'User-Agent': agent})

            site_url = 'http://%s' % Site.objects.get_current().domain
            requests.get(site_url, headers=headers)

            history_response = requests.get('%s%s' % (site_url, '/tracking/reports/history/'))
            reader = csv.reader(StringIO(history_response.content))

            visits = list(filter(lambda c: parse(c[3]) >= start_dt,
                                     filter(lambda c: 'visit' == c[4], reader)))

            self.assertTrue(len(visits) == expected_visits)