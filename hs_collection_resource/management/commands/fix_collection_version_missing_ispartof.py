from django.core.management.base import BaseCommand
from hs_core.enums import RelationTypes
from hs_core.models import BaseResource


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
        print("DONE")
