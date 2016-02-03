from __future__ import absolute_import

import requests
import logging
from xml.etree import ElementTree

from django.conf import settings
from django.core.mail import send_mail

from celery.task import periodic_task
from celery.schedules import crontab

from hs_core.models import BaseResource
from hs_core.hydroshare.resource import get_activated_doi
#periodic_task(ignore_result=True, run_every=crontab(minute=0, hour=0)) execute daily at midnight

@periodic_task(ignore_result=True, run_every=crontab(minute='*/3'))
def check_doi_activation():
    msg_lst = []
    pending_resources = BaseResource.objects.filter(raccess__published=True, doi__contains='pending')

    for res in pending_resources:
        if res.metadata.dates.all().filter(type='published'):
            pub_date = res.metadata.dates.all().filter(type='published')[0]
            pub_date = pub_date.start_date.strftime('%m/%d/%Y')
            act_doi = get_activated_doi(res.doi)

            response = requests.get('https://test.crossref.org/servlet/submissionDownload?usr={USERNAME}&pwd={PASSWORD}&doi_batch_id={DOI_BATCH_ID}&type={TYPE}'.format(
                                USERNAME=settings.CROSSREF_LOGIN_ID, PASSWORD=settings.CROSSREF_LOGIN_PWD, DOI_BATCH_ID=res.short_id, TYPE='result'))
            root = ElementTree.fromstring(response.content)
            rec_cnt_elem = root.find('.//record_count')
            success_cnt_elem = root.find('.//success_count')
            success = False
            if rec_cnt_elem is not None and success_cnt_elem is not None:
                rec_cnt = rec_cnt_elem.text
                success_cnt = success_cnt_elem.text
                if rec_cnt == success_cnt:
                    res.doi = act_doi
                    res.save()
                    success = True
            if not success:
                msg_lst.append("Published resource DOI {res_doi} is not yet activated with request data deposited since {pub_date}.".format(res_doi=act_doi, pub_date=pub_date))
                msg_log = logging.getLogger('django')
                msg_log.debug(response.content)
        else:
           msg_lst.append("{res_id} does not have published date in its metadata.".format(res_id=res.short_id))

    if msg_lst:
        email_msg = '\n'.join(msg_lst)
        # send email for people monitoring and follow-up as needed
        send_mail('Notification of pending DOI activation of published resources', email_msg,
                   settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_SUPPORT_EMAIL])