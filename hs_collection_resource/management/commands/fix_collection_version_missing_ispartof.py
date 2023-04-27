from django.core.management.base import BaseCommand
from hs_core.enums import RelationTypes
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Add missing isPartOf relation to resources in a collection"

    # Get the hasPart relations for all collections
    # For each relation, get the resource that is part
    # Check that the resource has a reverse relation (that it isPartOf the collection)

    def handle(self, *args, **options):
        collections = BaseResource.objects.filter(resource_type="CollectionResource").all()
        for collection in collections:
            print(f"Checking collection: {collection.short_id}")
            for res in collection.resources.all():
                rel_values = [rel.value for rel in res.metadata.relations.filter(type=RelationTypes.isPartOf).all()]
                print(f"Relations: {rel_values}")
                if collection.get_citation() not in rel_values:
                    print("IsPartOf relation missing from resource {res}. Creating it...")
                    res.metadata.create_element('relation',
                                                type=RelationTypes.isPartOf,
                                                value=collection.get_citation())
        print("DONE")
