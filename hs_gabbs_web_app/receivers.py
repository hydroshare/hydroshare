from django.dispatch import receiver
from django.conf import settings

from hs_tracking.signals import post_tracking_web_app_launch_url

from .utils import push_res_to_geohub


@receiver(post_tracking_web_app_launch_url)
def webapp_launch_url_processing(sender, **kwargs):
    request = kwargs['request']
    url = kwargs['url']

    if settings.GEOHUB_HOMEPAGE_URL in url:
        # for MyGeoHub MultiSpec GABBs tool launch, only authorized users can launch the tool.
        if request.user.is_authenticated():
            # for authorized users, the resource files will be pushed to mygeohub iRODS server
            # ready for the tool to load
            base_url = settings.GEOHUB_HOMEPAGE_URL + request.user.username + '/'
            start = url.find(base_url)
            if start > 0:
                start = start + len(base_url)
                end = start + url[start:].find('/')
                res_id = url[start:end]
                url = push_res_to_geohub(url, request.user, res_id)
                request.session['web_app_url'] = url
                if not url:
                    request.session['web_app_warning_message'] = "No valid file is included in " \
                                                                 "the resource to launch the " \
                                                                 "tool - Please include a valid " \
                                                                 "file."
        else:
            request.session['web_app_warning_message'] = "Only authorized users can launch " \
                                                         "MultiSpec tool - Please sign in first."
