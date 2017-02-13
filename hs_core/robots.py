import robot_detection
from django.http import HttpResponseForbidden

# todo: robot_detection needs to be updated periodically
# this might need to go in the Dockerfile
# todo:  (wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)


class CrawlerBlocker:
    def process_request(self, request):

        # get the user agent and assume nothing is a bot
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        request.is_crawler = False

        # return 403 if no user agent is provided
        if not user_agent:
            return HttpResponseForbidden('Request could not be processed, '
                                         'user agent could not be resolved.')

        # if user agent is a bot, tag it as a crawler (checks against robotstxt.org master list)
        if robot_detection.is_robot(user_agent):
            request.is_crawler = True

    def process_view(self, request, view_func, view_args, view_kwargs):
        # only return the view if the request is NOT identified as a crawler
        if request.is_crawler:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')
