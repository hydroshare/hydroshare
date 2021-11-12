import csv
from django.core.management.base import BaseCommand
from hs_core.models import Relation, BaseResource


class Command(BaseCommand):
    help = "Output versioning chain violation resources (e.g., #4028) for fixing and delete those relations " \
           "that point to non-existant resources"

    def handle(self, *args, **options):
        replace_by_qs = Relation.objects.filter(type='isReplacedBy')
        msg = f'There are currently {replace_by_qs.count()} isReplacedBy relations'
        print(msg, flush=True)

        replaced_by_dict = {}
        for obj in replace_by_qs:
            res_id = obj.value.split('/')[-1]
            if not BaseResource.objects.filter(short_id=res_id).exists():
                obj.delete()
                msg = '{res_id} does not exist, so delete the corresponding isReplacedBy relation metadata element'
                print(msg, flush=True)
                continue
            res_obj = BaseResource.objects.filter(object_id=obj.object_id).first()
            if not res_obj:
                obj.delete()
                msg = 'resource with {obj.object_id} object_id does not exist, so delete the corresponding ' \
                      'isReplacedBy relation metadata element'
                print(msg, flush=True)
                continue
            if res_obj.short_id in replaced_by_dict:
                replaced_by_dict[res_obj.short_id].append(res_id)
            else:
                replaced_by_dict[res_obj.short_id] = [res_id]

        version_of_dict = {}
        version_of_qs = Relation.objects.filter(type='isVersionOf')
        msg = f'There are currently {version_of_qs.count()} isVersionOf relations'
        print(msg, flush=True)

        for obj in version_of_qs:
            res_id = obj.value.split('/')[-1]
            if not BaseResource.objects.filter(short_id=res_id).exists():
                obj.delete()
                msg = '{res_id} does not exist, so delete the corresponding isVersionOf relation metadata element'
                print(msg, flush=True)
                continue
            res_obj = BaseResource.objects.filter(object_id=obj.object_id).first()
            if not res_obj:
                obj.delete()
                msg = 'resource with {obj.object_id} object_id does not exist, so delete the corresponding ' \
                      'isVersionOf relation metadata element'
                print(msg, flush=True)
                continue
            if res_obj.short_id in version_of_dict:
                version_of_dict[res_obj.short_id].append(res_id)
            else:
                version_of_dict[res_obj.short_id] = [res_id]

        # output resource list where one resource is replaced by more than one other resources
        with open('is_replaced_by_violations.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Resource', 'isReplacedBy'])
            for key, val_list in replaced_by_dict.items():
                if len(val_list) > 1:
                    # obsolesence chain violation
                    for val in val_list:
                        writer.writerow([key, val])

        # output resource list where one resource is valueOf more than one other resources
        with open('is_version_of_violations.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Resource', 'isVersionOf'])
            for key, val_list in version_of_dict.items():
                if len(val_list) > 1:
                    # obsolesence chain violation
                    for val in val_list:
                        writer.writerow([key, val])

        # output resource list where isReplacedBy and isVersionOf are not in pairs
        with open('replace_by_and_version_of_not_in_pairs.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Resource', 'isReplacedBy', 'isVersionOf'])
            for key, val_list in replaced_by_dict.items():
                for val in val_list:
                    if val not in version_of_dict:
                        writer.writerow([key, val, ''])
            for key, val_list in version_of_dict.items():
                for val in val_list:
                    if val not in replaced_by_dict:
                        writer.writerow([key, '', val])
