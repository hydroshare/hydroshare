__author__ = 'tonycastronova'

from django.http import HttpResponse
from collections import OrderedDict
from hs_model_program.models import ModelProgramResource
import json

def get_model_metadata(request):

    # get the request data
    r = request.GET

    # get the resource id for looking up the resource object
    resource_id = r['resource_id']

    # get the model program resource
    obj = ModelProgramResource.objects.filter(short_id=resource_id).first()
    mpmeta = obj.metadata.mpmetadata.first()

    # build an output dictionary which will be returned as JSON
    metadata = {}
    if obj is not None:
        metadata = dict(
            description=obj.description,
            program_website=mpmeta.program_website,
            date_released=mpmeta.date_released,
            software_version=mpmeta.software_version,
            software_language=mpmeta.software_language,
            operating_sys=mpmeta.operating_sys,
            url = "http://"+request.get_host()+"/resource/"+resource_id+"/",
        )
    json_data = json.dumps(metadata)
    return HttpResponse(json_data, content_type="application/json")