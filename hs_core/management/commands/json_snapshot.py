"""
This command converts all resource, aggregation and file metadata to json
"""
import os
import json

from django.core.management import BaseCommand

from hs_core.models import BaseResource
from django.contrib.contenttypes.fields import GenericRelation
from turfpy.measurement import bbox_polygon, bbox
from geojson import Point, Feature


def metadata_to_json(metadata):
    metadata_json_dict = {}
    generic_relations = list(filter(lambda f: isinstance(f, GenericRelation), type(metadata)._meta.virtual_fields))
    for generic_relation in generic_relations:
        if generic_relation.related_model not in metadata.ignored_generic_relations():
            gr_name = generic_relation.name
            gr = getattr(metadata, gr_name)
            for f in gr.all():
                gr_json = {}
                for field_term, field_value in f.get_field_terms_and_values():
                    gr_json[os.path.basename(field_term)] = str(field_value)
                gr_name_str = str(gr_name)
                if gr_name_str == "coverages":
                    coverage_value = json.loads(gr_json["_value"])
                    if gr_json["type"] == "box":
                        gr_name_str = "spatial_coverage"
                        bbox = [float(coverage_value["northliomit"]), float(coverage_value["southlimit"]), float(coverage_value["eastlimit"]), float(coverage_value["westlimit"])]
                        coverage_value = bbox_polygon(bbox)
                    elif gr_json["type"] == "point":
                        gr_name_str = "spatial_coverage"
                        point = Feature(geometry=Point([float(coverage_value["east"]), float(coverage_value["north"])]))
                        coverage_value = point
                    else:
                        gr_name_str = "period_coverage"
                    gr_json["_value"] = coverage_value
                if gr_name_str.startswith("_"):
                    metadata_json_dict[gr_name_str] = gr_json
                elif gr_name_str not in metadata_json_dict:
                    metadata_json_dict[gr_name_str.strip("_")] = [gr_json]
                else:
                    metadata_json_dict[gr_name_str.strip("_")].append(gr_json)
    return metadata_json_dict

def files_to_json(files):
    files_json_list = []
    for f in files:
        files_json_list.append({"path": str(f), "size": f.size})
    return files_json_list

def to_json(agg):
    json_dict = metadata_to_json(agg.metadata)
    json_dict["files"] = files_to_json(agg.files.all())
    return json_dict

def resource_to_json(resource):
    json_list = [{"https://hydroshare.org/resource/" + resource.short_id: to_json(resource)}]
    if resource.resource_type == "CompositeResource":
        for agg in resource.logical_files:
            json_list.append({agg.url: to_json(agg)})
    return json_list

class Command(BaseCommand):
    help = "Ingest a zipped bag archive into a resource"

    def handle(self, *args, **options):
        os.mkdir("mongo_dump")
        for res in BaseResource.objects.filter(raccess__public=True):
            json_dict = resource_to_json(res)
            with open("mongo_dump/" + res.short_id + ".json", "w") as file:
                file.write(json.dumps(json_dict, indent=2))
