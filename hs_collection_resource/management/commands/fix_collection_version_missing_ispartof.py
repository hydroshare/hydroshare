from django.core.management.base import BaseCommand
from hs_core.enums import RelationTypes
from hs_core.models import BaseResource
from hs_core.hydroshare import current_site_url


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
        current_site = current_site_url()
        collections = BaseResource.objects.filter(resource_type="CollectionResource").all()
        for collection in collections:
            print(f"Checking collection: {collection} {current_site}/resource/{collection.short_id}")
            for res in collection.resources.all():
                rel_values = [rel.value for rel in res.metadata.relations.filter(type=RelationTypes.isPartOf).all()]
                print(f"Relations: {rel_values}")
                if collection.get_citation() not in rel_values:
                    print(f"IsPartOf relation missing from {res}, {current_site}/resource/{res.short_id}")
                    if dry_run:
                        print("SKIPPING creating IsPartOf relation because dry_run")
                    else:
                        print("Creating IsPartOf relation...")
                        res.metadata.create_element('relation',
                                                    type=RelationTypes.isPartOf,
                                                    value=collection.get_citation())
        print('-' * 100)
        print("check that all collections include hasPart metadata for contained resources")
        for res in BaseResource.object.all():
            print(f"Checking resource {res}, {current_site}/resource/{res.short_id}")
            rels = res.metadata.relations.filter(type=RelationTypes.isPartOf).all()
            if not rels:
                print("Skipping resource, no isPartOf relations")
                continue
            for rel in rels:
                col = rel.metadata.resource
                haspart_relations = col.metadata.relations.filter(type=RelationTypes.hasPart).all()
                citation = res.get_citation()
                if citation not in haspart_relations:
                    print(f"{res}, {current_site}/resource/{res.short_id} has isPart meta.")
                    print(f"Collection {col}, {current_site}/resource/{col.short_id} is missing hasPart.")
                    if dry_run:
                        print("SKIPPING creating hasPart relation because dry_run")
                    else:
                        print("Creating hasPart relation...")
                        col.metadata.create_element('relation',
                                                    type=RelationTypes.hasPart,
                                                    value=citation)

        print("DONE")
