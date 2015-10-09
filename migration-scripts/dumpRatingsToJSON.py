# This script dumps HydroShare Rating table into rating.json to be used to  
# ingest the rating data back into new system for manual migration purpose
# Author: Hong Yi
import os

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")

import django
from django.core import serializers
from mezzanine.generic.models import Rating

django.setup()
data = serializers.serialize("json", Rating.objects.all(), indent=4, use_natural_foreign_keys=True, use_natural_primary_keys=True)
out = open("rating.json", "w")

out.write(data)
out.close()
