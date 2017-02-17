import re

import robot_detection
from django.conf import settings
from django.http import HttpResponseForbidden


# note: robot_detection needs to be updated periodically (possible inside the Dockerfile)
# (wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)

class CrawlerBlocker:
    def __init__(self):
        self.whitelist = getattr(settings, "BOT_WHITELIST", [])

    def process_request(self, request):

        user_agent = request.META.get('HTTP_USER_AGENT', None)
        request.is_crawler = False
        request.is_whitelisted = True

        if user_agent is None:
            # calls without a user agent generally reflect internal calls (e.g. testing).
            # whitelist these calls since they are not very common and not doing so will
            # break unittests
            request.is_crawler = True
            request.is_whitelisted = True
        else:
            # if user agent is a bot, tag it as a crawler (checks against
            # robotstxt.org master list). Webcrawlers are also checked against
            # the whitelist defined in settings.py to determine if
            # site access will be granted
            request.is_crawler = robot_detection.is_robot(user_agent)
            if len(self.whitelist) > 0 and request.is_crawler:
                if not re.match("(" + ")|(".join(self.whitelist) + ")", user_agent):
                    request.is_whitelisted = False

        # return 403 if the request is not whitelisted
        if not request.is_whitelisted:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')

    def process_view(self, request, view_func, view_args, view_kwargs):

        # only return the view if the request is NOT identified as a whitelisted crawler or human
        if not request.is_whitelisted:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')
