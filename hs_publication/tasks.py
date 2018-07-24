import logging

from celery.task import periodic_task
from celery.schedules import crontab

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from django.core.mail import send_mail

from hs_publication.models import PublicationQueue


# Pass 'django' into getLogger instead of __name__
# for celery tasks (as this seems to be the
# only way to successfully log in code executed
# by celery, despite our catch-all handler).
logger = logging.getLogger('django')


# Runs every day at midnight
@periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0))
def send_notification_email():
    pending_queue_items = PublicationQueue.objects.filter(status="pending")
    current_site = Site.objects.first()

    for member in User.objects.filter(groups__name='Publication Review'):
        send_mail(
            '%s Publication Queue Items Need Review' % len(pending_queue_items),
            'Please visit https://%s/admin/hs_publication/publicationqueue/ to review.' % current_site.domain,
            'publication@cuahsi.org',
            [member.email],
            fail_silently=False,
        )


@periodic_task(ignore_result=True, run_every=crontab(hour="*"))
def formally_publish_approved_resources():
    #TODO Publish approved resources every hour.
    pass