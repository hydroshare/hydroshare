import robot_detection
from django.http import HttpResponseForbidden


class CrawlerBlocker:
    def process_request(self, request):

        # get the user agent and assume nothing is a bot
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        request.is_crawler = False

        # return 403 if no user agent is provided
        if not user_agent:
            return HttpResponseForbidden('Request could not be processed, user agent could not be resolved.')

        # todo: robot_detection needs to be updated periodically
        # todo:     this might need to go in the Dockerfile
        # todo:     (wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)

        # if user agent is a bot, tag it as a crawler (checks against robotstxt.org master list)
        if robot_detection.is_robot(user_agent):
            request.is_crawler = True

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.is_crawler:
            return HttpResponseForbidden('Request could not be processed, see robots.txt')

# test urls
# http://192.168.56.101:8000/hsapi/_internal/create-resource/
# http://192.168.56.101:8000/resource/9cba40af259945cf986ce221ba03f5b9/
# http://192.168.56.101:8000/django_irods/download/bags/9cba40af259945cf986ce221ba03f5b9.zip





