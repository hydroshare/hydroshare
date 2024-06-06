"""Add is_human attribute to request for filtering logs and other such things.

Note: robot_detection needs to be updated periodically (possible inside the Dockerfile)
(wget http://www.robotstxt.org/db/all.txt, python robot_detection.py all.txt)
"""

import robot_detection
from django.utils.deprecation import MiddlewareMixin


class RobotFilter(MiddlewareMixin):
    """Process request and apply is_human field if a robot is detected."""

    def process_request(self, request):
        """Add is_human field to the request object.

        This is used to filter non-human activity from the usage logs
        """
        user_agent = request.headers.get("user-agent", None)
        request.is_human = True

        if user_agent is None or robot_detection.is_robot(user_agent):
            request.is_human = False
