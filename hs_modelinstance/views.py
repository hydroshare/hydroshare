from django.http import HttpResponse
from hs_model_program.models import ModelProgramResource
import json
import datetime


def is_executed_by(request):
    return HttpResponse(json.dumps(dict(is_executed_by=True)), content_type="application/json")
