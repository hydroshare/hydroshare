
import requests

from django.test import TestCase


class TestRobots(TestCase):

    def setUp(self):

        self.url = 'http://localhost:8000'
        self.headers = requests.utils.default_headers()

    def test_whitelisted_agents(self):

        agents = [
            'Mozilla/5.0 (compatible; bingbot/2.0; '
            '+http://www.bing.com/bingbot.htm)',
            'Googlebot/2.1 (+http://www.googlebot.com/bot.html)',
            'Mozilla/5.0 (compatible; Yahoo! Slurp; '
            'http://help.yahoo.com/help/us/ysearch/slurp)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) '
            'AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:21.0) Gecko/20100101 Firefox/21.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586'
        ]

        for agent in agents:
            self.headers.update({'User-Agent': agent})
            response = requests.get(self.url, headers=self.headers)
            self.assertTrue(response.status_code != 403,
                            msg='User-Agent:%s --> %d == 403' % (agent, response.status_code))

    def test_blacklisted_agents(self):

        agents = ['Mozilla/5.0 (compatible; BLEXBot/1.0; +http://webmeup-crawler.com/)',
                  'SiteLockSpider [en] (WinNT; I ;Nav)',
                  'Mozilla/5.0 (compatible; MJ12bot/v1.4.5; http://www.majestic12.co.uk/bot.php?+)',
                  'Araneo/0.7 (araneo@esperantisto.net; http://esperantisto.net)',
                  'BSpider/1.0 libwww-perl/0.40',
                  'WOLP/1.0 mda/1.0'
                  ]

        for agent in agents:
            self.headers.update({'User-Agent': agent})
            response = requests.get(self.url, headers=self.headers)
            self.assertTrue(response.status_code == 403,
                            msg='User-Agent:%s --> %d != 403' % (agent, response.status_code))
