import logging

from django.contrib.contenttypes.models import ContentType
from django.db import migrations, transaction

# from hs_core.models import BaseResource
from hs_core.hydroshare.utils import set_dirty_bag_flag


def migrate_relation_meta(apps, schema_editor):
    """Migrates the Source metadata element to the Relation metadata element using
    relation type as 'source'. Migrates some old relation types to new types"""

    log = logging.getLogger()
    BaseResource = apps.get_model("hs_core", "BaseResource")
    Relation = apps.get_model("hs_core", "Relation")
    Source = apps.get_model("hs_core", "Source")
    transaction.set_autocommit(False)
    try:
        for res in BaseResource.objects.all().iterator():
            res = res.get_content_model()
            type_migrated = False
            # migrate relation types
            metadata_type = ContentType.objects.get_for_model(res.metadata)
            for rel in Relation.objects.filter(object_id=res.metadata.id, content_type__pk=metadata_type.id).all():
            # for rel in res.metadata.relations.all():
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
                    log.info(log_msg)
                    print(log_msg)
                    type_migrated = True
            # res.metadata.save()
            # res.save()
            # migrate source elements to relation elements
            source_migrated = False
            for source in Source.objects.filter(object_id=res.metadata.id, content_type__pk=metadata_type.id).all():
            # for source in res.metadata.sources.all():
                if not Relation.objects.filter(object_id=res.metadata.id, content_type__pk=metadata_type.id, type='source',
                                               value=source.derived_from).exists():
                # if not res.metadata.relations.filter(type='source', value=source.derived_from).exists():
                    Relation.objects.create(content_object=res.metadata, type='source', value=source.derived_from)
                    # res.metadata.create_element('relation', type='source', value=source.derived_from)
                    source_migrated = True

            if any([source_migrated, type_migrated, Relation.objects.filter(object_id=res.metadata.id,
                                                                            content_type__pk=metadata_type.id,
                                                                            type='isVersionOf').exists(),
                    Relation.objects.filter(object_id=res.metadata.id, content_type__pk=metadata_type.id,
                                            type='isReplacedBy').exists()]):

            # if any([source_migrated, type_migrated, res.metadata.relations.filter(type='isVersionOf').exists(),
            #        res.metadata.relations.filter(type='isReplacedBy').exists()]):
                # setting bag flag to dirty so that resource bag file will be regenerated on demand with updated
                # resource metadata xml file
                set_dirty_bag_flag(res)

            if source_migrated:
                log_msg = "Source metadata element was migrated to relation metadata element for resource " \
                          "with ID:{} and type:{}."
                log_msg = log_msg.format(res.short_id, res.resource_type)
                log.info(log_msg)
                print(log_msg)

            # collection resource relation (hasPart) update to citation of contained resource and add relation meta
            # of type 'isPartOf' to all resources that are part of the collection resource
            # relation
            if res.resource_type == "CollectionResource":
                if res.resources.count() > 0:
                    # first delete all relation type of 'hasPart' for the collection resource
                    # res.metadata.relations.filter(type='hasPart').all().delete()
                    Relation.objects.filter(object_id=res.metadata.id, content_type__pk=metadata_type.id,
                                            type='hasPart').all().delete()
                    # create new relation meta element of type 'hasPart' with value of citation of the resource that the
                    # collection contains
                    for res_in_collection in res.resources.all():
                        Relation.objects.create(content_object=res.metadata, type='hasPart',
                                                value=res_in_collection.get_citation())
                        # res.metadata.create_element("relation", type='hasPart', value=res_in_collection.get_citation())
                        res_in_col_metadata_type = ContentType.objects.get_for_model(res_in_collection.metadata)
                        Relation.objects.filter(object_id=res_in_collection.metadata.id,
                                                content_type__pk=res_in_col_metadata_type.id).all().delete()
                        # res_in_collection.metadata.relations.filter(type='isPartOf').all().delete()
                        Relation.objects.create(content_object=res_in_collection.metadata, type='isPartOf',
                                                value=res.get_citation())
                        # res_in_collection.metadata.create_element("relation", type='isPartOf', value=res.get_citation())
                        set_dirty_bag_flag(res_in_collection)
                    set_dirty_bag_flag(res)
                    log_msg = "Updated relation metadata of type 'hasPart' for  collection resource " \
                              "with ID:{} and type:{}."
                    log_msg = log_msg.format(res.short_id, res.resource_type)
                    log.info(log_msg)
                    print(log_msg)
            transaction.commit()
    except Exception as err:
        err_msg = "Custom migration of relation metadata failed. Error:{}".format(str(err))
        print(err_msg)
        log.error(err_msg)


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0059_auto_20211216_1427'),
    ]

    operations = [
        migrations.RunPython(code=migrate_relation_meta),
    ]
