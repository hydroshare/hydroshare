import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from hs_core.hydroshare import utils
from hs_core.hydroshare.utils import set_dirty_bag_flag
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Migrate source metadata to relation metadata, and update relation types and values of all resources."

    def handle(self, *args, **options):
        log = logging.getLogger()
        res_count = BaseResource.objects.count()
        log_msg = "Total resources:{}".format(res_count)
        print(log_msg)
        res_count = 0
        for res in BaseResource.objects.all().iterator():
            res = res.get_content_model()
            type_migrated = False
            # migrate relation types
            if res.metadata is None:
                log_msg = "Resource with ID:{} missing metadata object. Skipping this resource".format(res.short_id)
                print(log_msg)
                log.warning(log_msg)
                continue
            res_count += 1
            for rel in res.metadata.relations.all():
                if rel.type in ('cites', 'isHostedBy', 'isDataFor', 'isCopiedFrom'):
                    old_type = rel.type
                    if rel.type == 'cites':
                        rel.type = 'references'
                    elif rel.type == 'isDataFor':
                        rel.type = 'isReferencedBy'
                    elif rel.type in ('isCopiedFrom', 'isHostedBy'):
                        rel.type = 'source'
                    rel.save()
                    log_msg = "Relation type:{} migrated to type:{} for resource with ID:{} and type:{}."
                    log_msg = log_msg.format(old_type, rel.type, res.short_id, res.resource_type)
                    print(log_msg)
                    log.info(log_msg)
                    type_migrated = True

            # migrate source elements to relation elements
            source_migrated = False
            if hasattr(res.metadata, 'sources'):
                for source in res.metadata.sources.all():
                    if not res.metadata.relations.filter(type='source', value=source.derived_from).exists():
                        res.metadata.create_element('relation', type='source', value=source.derived_from)
                        source_migrated = True
                res.metadata.sources.all().delete()

            # update relation type 'isVersionOf' and 'isReplacedBy' with resource citation
            for rel in res.metadata.relations.filter(Q(type='isVersionOf') | Q(type='isReplacedBy')).all():
                res_url_parts = rel.value.split('/resource/')
                if len(res_url_parts) == 2:
                    res_id = res_url_parts[1]
                    try:
                        res_to_link = utils.get_resource_by_shortkey(shortkey=res_id, or_404=False)
                        rel.value = res_to_link.get_citation()
                        rel.save()
                        log_msg = "Updated relation type '{}' with citation of resource (ID:{}) for resource (ID:{})'"
                        log_msg = log_msg.format(rel.type, res_id, res.short_id)
                        print(log_msg)
                        log.info(log_msg)
                    except BaseResource.DoesNotExist:
                        log_msg = "Resource doesn't exist for ID:{}. Failed to update relation type '{}' " \
                                  "with resource citation for resource with ID:{}"
                        log_msg = log_msg.format(res_id, rel.type, res.short_id)
                        print(log_msg)
                        log.warning(log_msg)
                else:
                    log_msg = "Invalid value ({}) for relation type '{}' for resource with ID:{}. " \
                              "Failed to update relation type '{}' value with citation for this resource"
                    log_msg = log_msg.format(rel.value, rel.type, res.short_id, rel.type)
                    print(log_msg)
                    log.warning(log_msg)

            if any([source_migrated, type_migrated, res.metadata.relations.filter(type='isVersionOf').exists(),
                    res.metadata.relations.filter(type='isReplacedBy').exists()]):
                set_dirty_bag_flag(res)

            if source_migrated:
                log_msg = "Source metadata element was migrated to relation metadata element for resource " \
                          "with ID:{} and type:{}."
                log_msg = log_msg.format(res.short_id, res.resource_type)
                print(log_msg)
                log.info(log_msg)

            # collection resource relation (hasPart) update to citation of contained resource and add relation meta
            # of type 'isPartOf' to all resources that are part of the collection resource
            # relation
            if res.resource_type == "CollectionResource":
                if res.resources.count() > 0:
                    res.metadata.relations.filter(type='hasPart').all().delete()
                    for res_in_collection in res.resources.all():
                        # add relation type 'hasPart' to collection resource
                        res.metadata.create_element("relation", type='hasPart', value=res_in_collection.get_citation())
                        res_in_collection.metadata.relations.filter(type='isPartOf').all().delete()

                        # add relation type 'isPartOf' to the resource that is part of the collection resource
                        res_in_collection.metadata.create_element("relation", type='isPartOf', value=res.get_citation())
                        log_msg = "Added 'isPartOf relation to resource with ID:{} and type:{} that is part of the" \
                                  "collection resource ID:{}"
                        log_msg = log_msg.format(res_in_collection.short_id, res_in_collection.resource_type,
                                                 res.short_id)
                        print(log_msg)
                        log.info(log_msg)
                        set_dirty_bag_flag(res_in_collection)
                    set_dirty_bag_flag(res)
                    log_msg = "Updated relation metadata of type 'hasPart' to citation of the contained resource " \
                              "for collection resource with ID:{} and type:{}."
                    log_msg = log_msg.format(res.short_id, res.resource_type)
                    print(log_msg)
                    log.info(log_msg)
        log_msg = "Total resources processed for migrating relation types:{}".format(res_count)
        print(log_msg)
        log.info(log_msg)
