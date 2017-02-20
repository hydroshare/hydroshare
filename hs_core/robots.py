import re

import robot_detection
from django.conf import settings
from django.http import HttpResponseForbidden


# note: robot_detection needs to be updated periodically (possible inside the Dockerfile)
# (wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)

class RobotFilter:

    def process_request(self, request):
        """Adds is_human field to the request object.  This is used to filter non-human
           activity from the usage logs"""

        user_agent = request.META.get('HTTP_USER_AGENT', None)
        request.is_human = True

        if user_agent is None or robot_detection.is_robot(user_agent):
            request.is_human = False