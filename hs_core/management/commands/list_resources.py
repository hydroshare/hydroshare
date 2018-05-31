# -*- coding: utf-8 -*-

"""
Generate metadata and bag for a resource from Django

"""

from hs_core.models import BaseResource
from hs_core.hydroshare import user_from_id
from django.db.models import Q
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "list resources owned or accessible by a user."

    def add_arguments(self, parser):

        # a list of user id's
        parser.add_argument('user_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['user_ids']) > 0:  # an array of login names to check
            for rid in options['user_ids']:
                print("USER {}".format(rid))
                u = user_from_id(rid)
                if u is not None:
                    resources = BaseResource.objects.filter(
                        Q(r2urp__user=u) |
                        Q(r2grp__group__g2ugp__user=u) |
                        Q(r2url__user=u)).distinct()
                    for r in resources:
                        print("{} {}".format(r.short_id,str(r)))
                else:
                    print("no such user {}".format(rid))

        else:
            print("no users specified")
