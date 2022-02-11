from django.core.management.base import BaseCommand
from hs_core.models import Relation, BaseResource


class Command(BaseCommand):
    help = "Cleanup broken/dangling resources resulting from versioning issues, e.g., #3276 and #4028"

    def handle(self, *args, **options):
        replace_by_qs = Relation.objects.filter(type='isReplacedBy')
        msg = f'Before cleanup, there are currently {replace_by_qs.count()} isReplacedBy relations'
        print(msg, flush=True)

        for obj in replace_by_qs:
            res_id = obj.value.split('/')[-1]
            if not BaseResource.objects.filter(short_id=res_id).exists():
                obj.delete()

        replace_by_qs = Relation.objects.filter(type='isReplacedBy')
        msg = f'After cleanup, there are currently {replace_by_qs.count()} isReplacedBy relations'
        print(msg, flush=True)

        version_of_qs = Relation.objects.filter(type='isVersionOf')
        msg = f'Before cleanup, there are currently {version_of_qs.count()} isVersionOf relations'
        print(msg, flush=True)

        for obj in version_of_qs:
            res_id = obj.value.split('/')[-1]
            if not BaseResource.objects.filter(short_id=res_id).exists():
                obj.delete()

        version_of_qs = Relation.objects.filter(type='isVersionOf')
        msg = f'After cleanup, there are currently {version_of_qs.count()} isVersionOf relations'
        print(msg, flush=True)
