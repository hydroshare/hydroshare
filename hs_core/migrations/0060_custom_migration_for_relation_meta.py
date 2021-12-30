import logging
import os

from django.contrib.contenttypes.models import ContentType
from django.db import migrations

# from hs_core.models import BaseResource
# from hs_core.hydroshare.utils import set_dirty_bag_flag
from django_irods.storage import IrodsStorage
from hs_core.models import CoreMetaData, FedStorage


def get_resource_metadata_from_resource(resource):
    # metaclass = resource.get_metadata_class()
    return CoreMetaData.objects.get(id=resource.object_id)


def is_federated(resource):
    """Return existence of resource_federation_path."""
    return resource.resource_federation_path is not None and \
        resource.resource_federation_path != ''


def set_dirty_bag_flag(resource):
    if resource.resource_federation_path:
        istorage = FedStorage()
    else:
        istorage = IrodsStorage()

    if is_federated(resource):
        res_coll = os.path.join(resource.resource_federation_path, resource.short_id)
    else:
        res_coll = resource.short_id

    istorage.setAVU(res_coll, "bag_modified", "true")
    istorage.setAVU(res_coll, "metadata_dirty", "true")


def migrate_relation_meta(apps, schema_editor):
    """Migrates the Source metadata element to the Relation metadata element using
    relation type as 'source'. Migrates some old relation types to new types"""
    log = logging.getLogger()

    def migrate(app_name, resource_cls_name):
        Resource = apps.get_model(app_name, resource_cls_name)
        Relation = apps.get_model("hs_core", "Relation")
        Source = apps.get_model("hs_core", "Source")

        try:
            for res in Resource.objects.all().iterator():
                type_migrated = False
                # migrate relation types
                res_meta_obj = get_resource_metadata_from_resource(res)
                metadata_type = ContentType.objects.get_for_model(res_meta_obj)
                for rel in Relation.objects.filter(object_id=res_meta_obj.id, content_type__pk=metadata_type.id).all():
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
                for source in Source.objects.filter(object_id=res_meta_obj.id, content_type__pk=metadata_type.id).all():
                # for source in res.metadata.sources.all():
                    if not Relation.objects.filter(object_id=res_meta_obj.id, content_type__pk=metadata_type.id, type='source',
                                                   value=source.derived_from).exists():
                    # if not res.metadata.relations.filter(type='source', value=source.derived_from).exists():
                        Relation.objects.create(content_object=res_meta_obj, type='source', value=source.derived_from)
                        # res.metadata.create_element('relation', type='source', value=source.derived_from)
                        source_migrated = True

                if any([source_migrated, type_migrated, Relation.objects.filter(object_id=res_meta_obj.id,
                                                                                content_type__pk=metadata_type.id,
                                                                                type='isVersionOf').exists(),
                        Relation.objects.filter(object_id=res_meta_obj.id, content_type__pk=metadata_type.id,
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
                        Relation.objects.filter(object_id=res_meta_obj.id, content_type__pk=metadata_type.id,
                                                type='hasPart').all().delete()
                        # create new relation meta element of type 'hasPart' with value of citation of the resource that the
                        # collection contains
                        for res_in_collection in res.resources.all():
                            Relation.objects.create(content_object=res_meta_obj, type='hasPart',
                                                    value=res_in_collection.get_citation())
                            # res.metadata.create_element("relation", type='hasPart', value=res_in_collection.get_citation())
                            res_in_coll_meta_obj = get_resource_metadata_from_resource(res_in_collection)
                            res_in_col_metadata_type = ContentType.objects.get_for_model(res_in_coll_meta_obj)
                            Relation.objects.filter(object_id=res_in_coll_meta_obj.id,
                                                    content_type__pk=res_in_col_metadata_type.id).all().delete()
                            # res_in_collection.metadata.relations.filter(type='isPartOf').all().delete()
                            Relation.objects.create(content_object=res_in_coll_meta_obj, type='isPartOf',
                                                    value=res.get_citation())
                            # res_in_collection.metadata.create_element("relation", type='isPartOf', value=res.get_citation())
                            set_dirty_bag_flag(res_in_collection)
                        set_dirty_bag_flag(res)
                        log_msg = "Updated relation metadata of type 'hasPart' for  collection resource " \
                                  "with ID:{} and type:{}."
                        log_msg = log_msg.format(res.short_id, res.resource_type)
                        log.info(log_msg)
                        print(log_msg)
        except Exception as err:
            err_msg = "Custom migration of relation metadata failed. Error:{}".format(str(err))
            print(err_msg)
            log.error(err_msg)
            raise

    migrate(app_name="hs_composite_resource", resource_cls_name="CompositeResource")


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0059_auto_20211216_1427'),
    ]

    operations = [
        migrations.RunPython(code=migrate_relation_meta),
    ]
