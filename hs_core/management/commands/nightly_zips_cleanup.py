# -*- coding: utf-8 -*-

"""
Clears out two-day-old zip files from iRODS storage
Meant to be run once a day via Jenkins
"""

from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage

import logging


class Command(BaseCommand):
    help = "Clears out two-day-old zip files from iRODS storage."

    def handle(self, *args, **options):
        logger = logging.getLogger('django')

        # delete 2 days ago
        date_folder = (date.today() - timedelta(2)).strftime('%Y-%m-%d')
        zips_daily_date = "zips/{daily_date}".format(daily_date=date_folder)

        logger.log("Deleting logs from {}".format(date_folder))
        istorage = IrodsStorage()
        if istorage.exists(zips_daily_date):
            istorage.delete(zips_daily_date)
            logger.log("Deleted.")
