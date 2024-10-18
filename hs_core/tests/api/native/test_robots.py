
from unittest import TestCase

from hs_core.robots import RobotFilter


class MockRequest(object):
    def __init__(self):
        self.data = {}
        self.META = {}

    def __get__(self, obj):
        return self.data[obj]

    def __set__(self, obj, value):
        self.data[obj] = value


class TestRobots(TestCase):

    def setUp(self):

        # define a set of webcrawler and browser user-agents
        self.agents = [
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

    def test_is_human(self):
        request = MockRequest()
        self.robot = RobotFilter(request)
        for agent, is_human in self.agents:
            request.headers = {'user-agent': agent}
            self.robot.process_request(request)
            self.assertTrue(request.is_human == is_human)
