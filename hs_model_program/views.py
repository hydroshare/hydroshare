__author__ = 'tonycastronova'

from django.http import HttpResponse
from hs_model_program.models import ModelProgramResource
import json
import datetime

def get_model_metadata(request):

    # get the request data
    r = request.GET

    # get the resource id for looking up the resource object
    resource_id = r['resource_id']

    # get the model program resource
    obj = ModelProgramResource.objects.filter(short_id=resource_id).first()
    metadata = {}

    if obj is not None:
        mpmeta = obj.metadata.program

        # get the http protocol
        protocol = 'https' if request.is_secure() else 'http'

        if mpmeta.date_released:
            dt = datetime.datetime.strftime(mpmeta.date_released,'%m/%d/%Y')
        else:
            dt = ''

        # build an output dictionary which will be returned as JSON
        if obj is not None:
            metadata = dict(
                description=obj.description,
                program_website=mpmeta.program_website,
                date_released=dt,
                software_version=mpmeta.software_version,
                software_language=mpmeta.software_language,
                operating_sys=mpmeta.operating_sys,
                url = protocol+"://"+request.get_host()+"/resource/"+resource_id+"/",
            )

    json_data = json.dumps(metadata)
    return HttpResponse(json_data, content_type="application/json")