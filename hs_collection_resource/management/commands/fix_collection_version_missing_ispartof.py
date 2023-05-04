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
        errors = []
        current_site = current_site_url()
        collections = BaseResource.objects.filter(resource_type="CollectionResource").all()
        print('-' * 100)
        print("1. Checking Collection's metadata...")
        col_count = collections.count()
        print(f"{col_count} collections to check")
        n = 0
        fixed = 0
        for collection in collections:
            n = n + 1
            col_citation = collection.get_citation()
            for res in collection.resources.all():
                rel_values = [rel.value for rel in res.metadata.relations.filter(type=RelationTypes.isPartOf).all()]
                if col_citation not in rel_values:
                    print(f"{n}/{col_count}:For collection:{collection}, {current_site}/resource/{collection.short_id}")
                    print(f"IsPartOf relation missing from {res}, {current_site}/resource/{res.short_id}")
                    if dry_run:
                        print("SKIPPING creating IsPartOf relation because dry_run")
                    else:
                        print("Creating IsPartOf relation...")
                        res.metadata.create_element('relation',
                                                    type=RelationTypes.isPartOf,
                                                    value=col_citation)
                    fixed = fixed + 1
                res_citation = res.get_citation()
                if not collection.metadata.relations.filter(type=RelationTypes.hasPart, value=res_citation).exists():
                    print(f"hasPart relation missing from collection: "
                          f"{collection}, {current_site}/resource/{collection.short_id}")
                    if dry_run:
                        print("SKIPPING creating hasPart relation because dry_run")
                    else:
                        collection.metadata.create_element('relation',
                                                           type=RelationTypes.hasPart,
                                                           value=res_citation)
                    fixed = fixed + 1
        print(f"{fixed} metadata relations were missing")

        print('-' * 100)
        print("2. Remove dangling isPart metadata from resources that are not included in collections")
        resources = BaseResource.objects.all()
        res_count = resources.count()
        print(f"{res_count} resources to check")
        i = 0
        fixed = 0
        for res in resources:
            i = i + 1
            isPartOf_relations = None
            if res.metadata:
                isPartOf_relations = res.metadata.relations.filter(type=RelationTypes.isPartOf).all()
            if not isPartOf_relations:
                continue
            res_citation = res.get_citation()
            for rel in isPartOf_relations:
                # get the collection object from the relation...
                try:
                    citation = rel.value
                    if "doi.org" in citation:
                        id = rel.value.split("/hs.")[1][:32]
                    else:
                        id = rel.value.split("/resource/")[1][:32]
                    col = BaseResource.objects.get(short_id=id)
                except Exception as e:
                    message = f"Unable to parse id from citation: {rel.value}, {e}"
                    print(message)
                    errors.append(message)
                    continue
                haspart_relations = col.metadata.relations.filter(type=RelationTypes.hasPart).all()
                if res_citation not in [rel.value for rel in haspart_relations]:
                    print(f"{i}/{res_count}:{res}, {current_site}/resource/{res.short_id} has isPart meta.")
                    print(f"Collection {col}, {current_site}/resource/{col.short_id} is missing hasPart.")
                    if dry_run:
                        print("SKIPPING delete of isPartOf relation because dry_run")
                    else:
                        print("Removing dangling isPartOf relation...")
                        res.metadata.delete_element('relation', rel.id)
                    fixed = fixed + 1
        print(f"{fixed} isPart relations found dangling")
        if errors:
            print("Errors:")
            for error in errors:
                print(error)
        print("DONE")
