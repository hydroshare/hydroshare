# This script dumps HydroShare Comment table into comments.json to be used to  
# ingest the comment data back into new system for manual migration purpose
# Author: Hong Yi
import os

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")

import django
from django.core import serializers
from django.contrib.comments.models import Comment

django.setup()
data = serializers.serialize("json", Comment.objects.all(), indent=4, use_natural_foreign_keys=True, use_natural_primary_keys=True)
out = open("comments.json", "w")

out.write(data)
out.close()
