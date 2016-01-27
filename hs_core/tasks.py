from __future__ import absolute_import
from celery import shared_task

@shared_task
def check_doi_activation(doi):
    return True