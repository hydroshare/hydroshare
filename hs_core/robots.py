import robot_detection
from django.http import HttpResponseForbidden
import logging
import logging.handlers
from django.conf import settings
import re

# todo: robot_detection needs to be updated periodically
# this might need to go in the Dockerfile
# todo:  (wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)

# Set up a specific logger with our desired output level
LOG_FILENAME = '/hydroshare/log/robots.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)
logger.addHandler(handler)

class CrawlerBlocker:
    def __init__(self):
        self.whitelist = getattr(settings, "BOT_WHITELIST", -1)

    def process_request(self, request):

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        request.is_crawler = 0
        request.is_whitelisted = 1

        # they are identified as a bot to exclude them from the use tracking
        if user_agent is '':
            # calls without a user agent generally reflect internal calls (e.g. testing).
            # whitelist these calls since they are not very common
            request.is_crawler = True
            request.is_whitelisted = 1
        else:
            # if user agent is a bot, tag it as a crawler (checks against robotstxt.org master list)
            # the webcrawler is also checjed against the whitelist defined in settings.py
            request.is_crawler = robot_detection.is_robot(user_agent)
            if self.whitelist != -1:
                if not re.match("(" + ")|(".join(self.whitelist) + ")", user_agent):
                    request.is_whitelisted = 0

        # return 403 if the request is not whitelisted
        if not request.is_whitelisted:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')

    def process_view(self, request, view_func, view_args, view_kwargs):
        # only return the view if the request is NOT identified as a crawler
       if not request.is_whitelisted:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')