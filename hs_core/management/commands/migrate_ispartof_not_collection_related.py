import logging

from django.core.management.base import BaseCommand

from hs_core.enums import RelationTypes
from hs_core.hydroshare.utils import set_dirty_bag_flag
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Migrate 'isPartOf' relation type (which are not related to collection) to 'isReferencedBy' relation type."

    def handle(self, *args, **options):
        log = logging.getLogger()
        res_count = BaseResource.objects.count()
        log_msg = "Total resources to process:{}".format(res_count)
        print(log_msg)
        updated_res_count = 0
        for res in BaseResource.objects.all().iterator():
            res = res.get_content_model()
            if res.metadata is None:
                log_msg = "Resource with ID:{} missing metadata object. Skipping this resource".format(res.short_id)
                print(log_msg)
                log.warning(log_msg)
                continue

            if res.collections:
                res.update_relation_meta()
            rel_type_updated = False
            for rel in res.metadata.relations.filter(type=RelationTypes.isPartOf).all():
                for col_res in res.collections.all():
                    if rel.value == col_res.get_citation():
                        break
                else:
                    # isPartOf relation is not related to collection - so update the relation type
                    rel.type = RelationTypes.isReferencedBy
                    rel.save()
                    rel_type_updated = True
            if rel_type_updated:
                updated_res_count += 1
                set_dirty_bag_flag(res)
                log_msg = "Relation type:{} migrated to type:{} for resource with ID:{} and type:{}."
                log_msg = log_msg.format(RelationTypes.isPartOf.value, RelationTypes.isReferencedBy.value,
                                         res.short_id, res.resource_type)
                print(log_msg)
                log.info(log_msg)

        log_msg = "{} resource(s) updated for migrating relation type (isPartOf).".format(updated_res_count)
        print(log_msg)
        log.info(log_msg)
