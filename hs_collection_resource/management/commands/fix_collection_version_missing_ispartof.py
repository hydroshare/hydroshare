from django.core.management.base import BaseCommand
from hs_core.enums import RelationTypes
from hs_core.models import BaseResource, Relation


class Command(BaseCommand):
    help = "Add missing isPartOf relation to resources in a collection"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Show what options would be edited without committing changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dryrun']
        collections = BaseResource.objects.filter(resource_type="CollectionResource").all()
        print('-' * 100)
        print("1. Check that all resources in collections have isPartOf metadata")
        for collection in collections:
            print(f"Checking collection: {collection.short_id}")
            for res in collection.resources.all():
                rel_values = [rel.value for rel in res.metadata.relations.filter(type=RelationTypes.isPartOf).all()]
                print(f"Relations: {rel_values}")
                if collection.get_citation() not in rel_values:
                    print("IsPartOf relation missing from resource {res}.")
                    if dry_run:
                        print("SKIPPING creating IsPartOf relation because dry_run")
                    else:
                        print("Creating IsPartOf relation...")
                        res.metadata.create_element('relation',
                                                    type=RelationTypes.isPartOf,
                                                    value=collection.get_citation())
        print('-' * 100)
        print("check that all collections include hasPart metadata for contained resources")
        # for rel in Relation.objects.filter(type=RelationTypes.isPartOf).all():
        #     col = rel.metadata.resource
        #     print(f"Checking collection {col}, https://beta.hydroshare.org/resource/{col.short_id}")
        #     print("This collection is pointed to by a res with isPartOf metadata. Checking that col contains hasPart metadata")
        #     haspart_relations = col.metadata.relations.filter(type=RelationTypes.hasPart).all()
        #     print(haspart_relations)
        #     # Need a way to check that hasPart relations contains the resources with isPart metadata

        for res in BaseResource.object.all():
            print(f"Checking resource {res}, https://beta.hydroshare.org/resource/{res.short_id}")
            rels = res.metadata.relations.filter(type=RelationTypes.isPartOf).all()
            if not rels:
                print("Skipping resource, no isPartOf relations")
                continue
            for rel in rels:
                col = rel.metadata.resource
                haspart_relations = col.metadata.relations.filter(type=RelationTypes.hasPart).all()
                citation = res.get_citation()
                if citation not in haspart_relations:
                    print(f"{res}, https://beta.hydroshare.org/resource/{res.short_id} has isPart meta.")
                    print(f"Collection {col}, https://beta.hydroshare.org/resource/{col.short_id} is missing hasPart.")
                    if dry_run:
                        print("SKIPPING creating hasPart relation because dry_run")
                    else:
                        print("Creating hasPart relation...")
                        col.metadata.create_element('relation',
                                                    type=RelationTypes.hasPart,
                                                    value=citation)

        print("DONE")
