# -*- coding: utf-8 -*-

"""
Clears out two-day-old zip files from iRODS storage
Meant to be run once a day via Jenkins
"""

from datetime import datetime, timedelta
import json

from django.conf import settings
from django.core.management.base import BaseCommand
import requests

import logging

from theme.models import UserProfile


class Command(BaseCommand):
    help = "Clears out two-day-old zip files from iRODS storage."

    def sync_mailchimp(self, active_subscribed, list_id):
        logger = logging.getLogger('django')

        session = requests.Session()
        url = "https://us3.api.mailchimp.com/3.0/lists/{list_id}/members"
        # get total members
        response = session.get(url.format(list_id=list_id), auth=requests.auth.HTTPBasicAuth(
            'hs-celery', settings.MAILCHIMP_PASSWORD))
        total_items = json.loads(response.content)["total_items"]
        # get list of all member ids
        response = session.get(
            (url + "?offset=0&count={total_items}").format(list_id=list_id,
                                                           total_items=total_items),
            auth=requests.auth.HTTPBasicAuth('hs-celery', settings.MAILCHIMP_PASSWORD))
        # clear the email list
        delete_count = 0
        for member in json.loads(response.content)["members"]:
            if member["status"] == "subscribed":
                session_response = session.delete(
                    (url + "/{id}").format(list_id=list_id, id=member["id"]),
                    auth=requests.auth.HTTPBasicAuth('hs-celery', settings.MAILCHIMP_PASSWORD))
                if session_response.status_code != 204:
                    logger.info("Expected 204 status, got " + str(session_response.status_code))
                    logger.debug(session_response.content)
                else:
                    delete_count += 1
        # add active subscribed users to mailchimp
        add_count = 0
        for subscriber in active_subscribed:
            json_data = {"email_address": subscriber.user.email, "status": "subscribed",
                         "merge_fields": {"FNAME": subscriber.user.first_name,
                                          "LNAME": subscriber.user.last_name}}
            session_response = session.post(
                url.format(list_id=list_id), json=json_data, auth=requests.auth.HTTPBasicAuth(
                    'hs-celery', settings.MAILCHIMP_PASSWORD))
            if session_response.status_code != 200:
                logger.info("Expected 200 status code, got " + str(session_response.status_code))
                logger.debug(session_response.content)
            else:
                add_count += 1
        if delete_count == active_subscribed.count():
            logger.info("successfully cleared mailchimp for list id " + list_id)
        else:
            logger.info(
                "cleared " + str(delete_count) + " out of " + str(
                    active_subscribed.count()) + " for list id " + list_id)

        if active_subscribed.count() == add_count:
            logger.info("successfully synced all subscriptions for list id " + list_id)
        else:
            logger.info("added " + str(add_count) + " out of " + str(
                active_subscribed.count()) + " for list id " + list_id)

    def handle(self, *args, **options):
        sixty_days = datetime.today() - timedelta(days=60)
        active_subscribed = UserProfile.objects.filter(email_opt_out=False,
                                                       user__last_login__gte=sixty_days,
                                                       user__is_active=True)
        self.sync_mailchimp(active_subscribed, settings.MAILCHIMP_ACTIVE_SUBSCRIBERS)
        subscribed = UserProfile.objects.filter(email_opt_out=False, user__is_active=True)
        self.sync_mailchimp(subscribed, settings.MAILCHIMP_SUBSCRIBERS)
