from django.contrib.auth.models import User, Group
from django.shortcuts import render
from hs_core.models import BaseResource
from hs_tracking.models import Variable
from hs_core.hydroshare.utils import get_resource_by_shortkey
import datetime
import re
from django.utils import timezone
from matplotlib import pylab
from pylab import *
import PIL, StringIO
import math
from django.db.models import Q
from django.http import HttpResponse

import logging

test_offset = 60
days_to_report = 50
logger = logging.getLogger('hydroshare')

def index(request):
        return render(request, 'index.html')

def user_stats(request, username):
        start_date =datetime.datetime.now() - datetime.timedelta(days = test_offset + days_to_report)
        end_date = datetime.datetime.now() - datetime.timedelta(days = test_offset)

        query = (Q(name="app_launch") | Q(name="visit") | Q(name="download")) \
                 & Q(timestamp__range=[start_date, end_date])

        user = User.objects.get(username__iexact=username)
        re_compiler = {"visit": re.compile('/resource/([^/]+)/'), \
                       "download": re.compile('\|resource_guid=([^|]+)\|'),\
                       "app_launch": re.compile('\|resourceid=([^|]+)\|')}

        map_resources = {}
        num_resources = 0

        for v in Variable.objects.filter(query).order_by("-timestamp"):
            value = v.get_value()
            m = re_compiler[v.name].search(value)
            if(m and m.group(1)):
                resource_id = m.group(1)
                if(resource_id is not None):
                        res_query = Q(short_id=resource_id) & (Q(r2urp__user=user)| \
                                Q(r2grp__group__gaccess__active=True, r2grp__group__g2ugp__user=user)| \
                                Q(r2url__user=user) | Q(r2urf__user=user))
                        if(BaseResource.objects.filter(res_query).exists()):
                                res = None
                                try:
                                        res = get_resource_by_shortkey(resource_id, or_404=False)
                                except BaseResource.DoesNotExist:
                                        res = None

                                if(res is not None):
                                        num_resources += 1
                                        if (resource_id in map_resources.keys()):
                                                map_resources[resource_id]["count"] += 1
                                                map_resources[resource_id]["first_accessed"] = v.timestamp
                                        else:
                                                caption = ""
                                                if(v.name == "visit"):
                                                        if (re.search("/[0-9a-z-]{32}/.*add", value)):
                                                                caption = "You added this resource"
                                                        elif(re.search("/[0-9a-z-]{32}/.*update", value)):
                                                                caption = "You updated the resource"
                                                        elif(re.search("/[0-9a-z-]{32}/share.*$", value)):
                                                                caption = "You shared the resource"
                                                        else:
                                                                caption = "You visited the resource"
                                                elif(v.name == "download"):
                                                        caption = "You downloaded the resource"
                                                else:
                                                        caption = "You app launched the resource"
                                                url = "https://dev-hs-3.cuahsi.org/resource/" + resource_id + "/"

                                                map_resources[resource_id] = {
                                                    "count": 1,
                                                    "name": v.name,
                                                    "url": url,
                                                    "value": caption,
                                                    "title": res.title,
                                                    "resource_type": res.resource_type,
                                                    "first_accessed": v.timestamp,
                                                    "last_accessed": v.timestamp}
        for resource_id in map_resources.keys():
            resource = map_resources[resource_id]
            current_time = timezone.now()
            last_time = resource["last_accessed"]
            time_difference = (current_time - last_time).days
            months = int(time_difference / 30)
            weeks = int(time_difference / 7)
            if months != 0:
                map_resources[resource_id]["access_time"] = str(months) + "months ago"
            elif weeks != 0:
                map_resources[resource_id]["access_time"] = str(weeks) + "weeks ago"
            else:
                map_resources[resource_id]["access_time"] = str(time_difference) + "days ago"

        return render(request, 'user_stats.html',
                      context = {"total_count": num_resources,
                                 "username": username,
                                 "resources": map_resources.values()})

def showHistogram(request):
        t = arange(0.0, 2.0, 0.01)
        s = sin(2*pi*t)
        plot(t, s, linewidth=1.0)
        grid(True)
        buffer = StringIO.StringIO()
        canvas = pylab.get_current_fig_manager().canvas
        canvas.draw()
        pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
        pilImage.save(buffer, "PNG")
        pylab.close()
        return HttpResponse(buffer.getvalue(), content_type="image/png")

def addFrequency(map_resources):
        for resource_id in map_resources.keys():
                resource = map_resources[resource_id]
                start_time = resource["first_accessed"]
                end_time = resource["last_accessed"]
                total_access = resource["total_access"]
                num_days = (end_time - start_time).days
                if (num_days == 0):
                        num_days = 1
                map_resources[resource_id]["frequency"] = math.ceil(total_access / num_days)
                map_resources[resource_id]["number_days"] = num_days

def resource_landing(request):
        start_date = datetime.datetime.now() - datetime.timedelta(days=test_offset+days_to_report)
        end_date = datetime.datetime.now() - datetime.timedelta(days=test_offset)

        total_downloads = Variable.objects.filter(
                 (Q(name="download") |
                  Q(name="app_launch")) &
                 Q(timestamp__range=[start_date, end_date])).count()

        total_views = Variable.objects.filter(
                 Q(name="visit") &
                 Q(timestamp__range=[start_date, end_date])).count()

        query = (Q(name="app_launch") | Q(name="visit") | Q(name="download")) & \
                Q(timestamp__range=[start_date, end_date])

        re_compiler ={"visit": re.compile('/resource/([^/]+)/'),
                      "download": re.compile('\|resource_guid=([^|]+)\|'),
                      "app_launch": re.compile('\|resourceid=([^|]+)\|')}
        map_resources = {}
        for v in Variable.objects.filter(query).order_by("-timestamp"):
            value = v.get_value()
            m = re_compiler[v.name].search(value)

            if (m and m.group(1)):
                resource_id = m.group(1)
                if resource_id is not None:
                    try:
                        resource = get_resource_by_shortkey(resource_id, or_404=False)
                    except BaseResource.DoesNotExist:
                        resource = None
                    if resource is not None:
                        if (resource_id in map_resources.keys()):
                                map_resources[resource_id]["first_accessed"] = v.timestamp
                                map_resources[resource_id]["total_access"] += 1
                        else:
                                shared_user = User.objects.filter(
                                        Q(u2urp__resource=resource)).count()
                                shared_group = Group.objects.filter(
                                        Q(g2grp__resource=resource)).count()
                                url = "https://dev-hs-3.cuahsi.org/resource/" + resource_id + "/"
                                map_resources[resource_id] = {
                                    "title": resource.title,
                                    "url": url,
                                    "shared_user": shared_user,
                                    "shared_group": shared_group,
                                    "total_access": 1,
                                    "first_accessed": v.timestamp,
                                    "last_accessed": v.timestamp
                               }
                else:
                    logger.error("resource_id={} does not exist".format(resource_id))
        addFrequency(map_resources)
        resource_values = sorted(map_resources.values(), key=lambda d: d['total_access'], reverse=True)
        return render(request, 'resource_landing.html', context={"resources": resource_values, "total_views": total_views, "total_downloads": total_downloads})


def dashboard(request):
        users = []
        user_count = User.objects.all().count()
        variable_count = Variable.objects.all().count()
        # develop a list of users with activity in the range
        users_list = Variable.objects\
            .filter(
                Q(timestamp__date__gte=
                    datetime.datetime.now()-datetime.timedelta(days=test_offset+days_to_report),
                  timestamp__date__lt=
                    datetime.datetime.now()-datetime.timedelta(days=test_offset),
                  name='download') |
                Q(timestamp__date__gte=
                    datetime.datetime.now()-datetime.timedelta(days=test_offset+days_to_report),
                  timestamp__date__lt=
                    datetime.datetime.now()-datetime.timedelta(days=test_offset),
                  name='app_launch'))\
            .distinct()\
            .values_list('session__visitor__user', flat=True)
        for user_id in users_list:
            try:
                user = User.objects.get(id=user_id)
                users.append({"first_name": user.first_name,
                              "username": user.username,
                              "last_name":  user.last_name})

            except User.DoesNotExist:
                pass
        return render(request, "dashboard.html", context={"variable_count": variable_count, "user_count": user_count, "users": users})
