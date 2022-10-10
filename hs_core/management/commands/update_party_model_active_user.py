from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from hs_core.models import Contributor, Creator


class Command(BaseCommand):
    help = "Sets the is_active_user field of all creators and contributors"

    def handle(self, *args, **options):

        def update_party_active_flag(model_class):
            record_count = 0
            model_class_name = model_class.__name__
            for party in model_class.objects.exclude(hydroshare_user_id__isnull=True).iterator():
                try:
                    user = User.objects.get(id=party.hydroshare_user_id)
                    party.is_active_user = user.is_active
                except ObjectDoesNotExist:
                    party.is_active_user = False
                    err_msg = f"No user was found for user id:{party.hydroshare_user_id} for " \
                              f"{model_class_name} record id:{party.id}"
                    print(err_msg, flush=True)

                party.save()
                record_count += 1
                print(f"{record_count}. Updated {model_class_name} record id:{party.id}", flush=True)

        msg = f"Total creators (as hydroshare user) " \
              f"found:{Creator.objects.exclude(hydroshare_user_id__isnull=True).count()}"
        print(msg)
        print()
        update_party_active_flag(Creator)
        print()
        msg = f"Total contributors (as hydroshare user) " \
              f"found:{Contributor.objects.exclude(hydroshare_user_id__isnull=True).count()}"
        print(msg)
        print()
        update_party_active_flag(Contributor)
