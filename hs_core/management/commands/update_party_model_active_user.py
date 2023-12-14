from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Subquery

from hs_core.models import Contributor, Creator


class Command(BaseCommand):
    help = "Sets the is_active_user field of all creators and contributors"

    def handle(self, *args, **options):
        active_users = User.objects.filter(is_active=True)

        def update_party_active_flag(model_class):
            model_class_name = model_class.__name__
            update_rec_count = model_class.objects.exclude(hydroshare_user_id__isnull=True).filter(
                hydroshare_user_id__in=Subquery(active_users.values('id'))).update(is_active_user=True)
            msg = f"Updated {update_rec_count} {model_class_name} records with 'is_active_user' set to True'"
            print(msg, flush=True)

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
