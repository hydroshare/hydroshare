# usage: python loadUsersFromJSON.py users.JSON
# Cannot get django migration for hs_access_control migrate_users() to run after loading
# existing users, so write this customized script to load existing users as well as
# creating related UserAccess data
# Author: Hong Yi
import os
import sys

os.environ.setdefault("PYTHONPATH", '/home/docker/hydroshare')
os.environ['DJANGO_SETTINGS_MODULE'] = 'hydroshare.settings'

import django
from django.core import serializers
from django.contrib.auth.models import User

django.setup()

with open(sys.argv[1]) as json_file:
    for user in serializers.deserialize("json", json_file):
        user.save()
    json_file.close()
from hs_access_control.models import UserAccess
UserAccess.objects.all().delete()
for u in User.objects.all():
    ua = UserAccess(user=u, admin=False)
    ua.save()