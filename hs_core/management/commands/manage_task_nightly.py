# -*- coding: utf-8 -*-

"""
Clears out two-day-old zip files from iRODS storage
Meant to be run once a day via Jenkins
"""

from xml.etree import ElementTree

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from rest_framework import status
import requests

from hs_core.hydroshare.resource import get_activated_doi, get_resource_doi, \
    get_crossref_url, deposit_res_metadata_with_crossref
from hs_core.models import BaseResource
from theme.models import UserQuota, QuotaMessage, User
from theme.utils import get_quota_message

import logging


class Command(BaseCommand):
    help = "Clears out two-day-old zip files from iRODS storage."

    def handle(self, *args, **options):
        # The nightly running task do DOI activation check and over-quota check

        logger = logging.getLogger('django')

        # Check DOI activation on failed and pending resources and send email.
        msg_lst = []
        # retrieve all published resources with failed metadata deposition with CrossRef if any and
        # retry metadata deposition
        failed_resources = BaseResource.objects.filter(raccess__published=True,
                                                       doi__contains='failure')
        for res in failed_resources:
            if res.metadata.dates.all().filter(type='published'):
                pub_date = res.metadata.dates.all().filter(type='published')[0]
                pub_date = pub_date.start_date.strftime('%m/%d/%Y')
                act_doi = get_activated_doi(res.doi)
                response = deposit_res_metadata_with_crossref(res)
                if response.status_code == status.HTTP_200_OK:
                    # retry of metadata deposition succeeds, change resource flag from failure
                    # to pending
                    res.doi = get_resource_doi(act_doi, 'pending')
                    res.save()
                else:
                    # retry of metadata deposition failed again, notify admin
                    msg_lst.append("Metadata deposition with CrossRef for the published resource "
                                   "DOI {doi} failed again after retry with first metadata "
                                   "deposition requested since {date}.".format(doi=act_doi,
                                                                               date=pub_date))
                    logger.debug(response.content)
            else:
                msg_lst.append("{res_id} does not have published date in its metadata.".format(
                    res_id=res.short_id))

        pending_resources = BaseResource.objects.filter(raccess__published=True,
                                                        doi__contains='pending')
        for res in pending_resources:
            if res.metadata.dates.all().filter(type='published'):
                pub_date = res.metadata.dates.all().filter(type='published')[0]
                pub_date = pub_date.start_date.strftime('%m/%d/%Y')
                act_doi = get_activated_doi(res.doi)
                main_url = get_crossref_url()
                req_str = '{MAIN_URL}servlet/submissionDownload?usr={USERNAME}&pwd=' \
                          '{PASSWORD}&doi_batch_id={DOI_BATCH_ID}&type={TYPE}'
                response = requests.get(req_str.format(MAIN_URL=main_url,
                                                       USERNAME=settings.CROSSREF_LOGIN_ID,
                                                       PASSWORD=settings.CROSSREF_LOGIN_PWD,
                                                       DOI_BATCH_ID=res.short_id,
                                                       TYPE='result'))
                root = ElementTree.fromstring(response.content)
                rec_cnt_elem = root.find('.//record_count')
                failure_cnt_elem = root.find('.//failure_count')
                success = False
                if rec_cnt_elem is not None and failure_cnt_elem is not None:
                    rec_cnt = int(rec_cnt_elem.text)
                    failure_cnt = int(failure_cnt_elem.text)
                    if rec_cnt > 0 and failure_cnt == 0:
                        res.doi = act_doi
                        res.save()
                        success = True
                if not success:
                    msg_lst.append("Published resource DOI {doi} is not yet activated with request "
                                   "data deposited since {date}.".format(doi=act_doi,
                                                                         date=pub_date))
                    logger.debug(response.content)
            else:
                msg_lst.append("{res_id} does not have published date in its metadata.".format(
                    res_id=res.short_id))

        if msg_lst:
            email_msg = '\n'.join(msg_lst)
            subject = 'Notification of pending DOI deposition/activation of published resources'
            # send email for people monitoring and follow-up as needed
            send_mail(subject, email_msg, settings.DEFAULT_FROM_EMAIL,
                      [settings.DEFAULT_SUPPORT_EMAIL])

        # check over quota cases and send quota warning emails as needed
        hs_internal_zone = "hydroshare"
        if not QuotaMessage.objects.exists():
            QuotaMessage.objects.create()
        qmsg = QuotaMessage.objects.first()
        users = User.objects.filter(is_active=True).all()
        for u in users:
            uq = UserQuota.objects.filter(user__username=u.username, zone=hs_internal_zone).first()
            used_percent = uq.used_percent
            if used_percent >= qmsg.soft_limit_percent:
                if used_percent >= 100 and used_percent < qmsg.hard_limit_percent:
                    if uq.remaining_grace_period < 0:
                        # triggers grace period counting
                        uq.remaining_grace_period = qmsg.grace_period
                    elif uq.remaining_grace_period > 0:
                        # reduce remaining_grace_period by one day
                        uq.remaining_grace_period -= 1
                elif used_percent >= qmsg.hard_limit_percent:
                    # set grace period to 0 when user quota exceeds hard limit
                    uq.remaining_grace_period = 0
                uq.save()

                if u.first_name and u.last_name:
                    sal_name = '{} {}'.format(u.first_name, u.last_name)
                elif u.first_name:
                    sal_name = u.first_name
                elif u.last_name:
                    sal_name = u.last_name
                else:
                    sal_name = u.username

                msg_str = 'Dear ' + sal_name + ':\n\n'

                ori_qm = get_quota_message(u)
                # make embedded settings.DEFAULT_SUPPORT_EMAIL clickable with subject auto-filled
                replace_substr = "<a href='mailto:{0}?subject=Request more quota'>{0}</a>".format(
                    settings.DEFAULT_SUPPORT_EMAIL)
                new_qm = ori_qm.replace(settings.DEFAULT_SUPPORT_EMAIL, replace_substr)
                msg_str += new_qm

                msg_str += '\n\nHydroShare Support'
                subject = 'Quota warning'
                # send email for people monitoring and follow-up as needed
                send_mail(subject, '', settings.DEFAULT_FROM_EMAIL,
                          [u.email, settings.DEFAULT_SUPPORT_EMAIL],
                          html_message=msg_str)
            else:
                if uq.remaining_grace_period >= 0:
                    # turn grace period off now that the user is below quota soft limit
                    uq.remaining_grace_period = -1
                    uq.save()
