from __future__ import unicode_literals

from django import template
import timeago
from django.utils import timezone as django_timezone
register = template.Library()


@register.filter(name='icon_name_lookup')
def lookup(dict_icon_type, index):
    if index in dict_icon_type:
        return dict_icon_type[index]
    return ''


@register.filter(name='new_date')
def lookup(datetime_obj):
    return ''


@register.filter(name='just_in_time')
def date_time_pac(in_datetime):
    now_what = django_timezone.now()
    return timeago.format(in_datetime, now_what)


@register.simple_tag(name='resource_link_builder')
def build_resource_link(title, short_id):
    link = "/resource/" + short_id + "/"
    return "<strong> <a href=\"" + link + "\">" + title + "</a> </strong>"


@register.simple_tag(name='build_privacy_status')
def build_privacy_status(is_published, is_public, is_discoverable):
    if is_published:
        return "Published"
    elif is_public:
        return "Public"
    elif is_discoverable:
        return "Discoverable"
    else:
        return "Private"


@register.filter(name='resource_img_urlize')
def resource_img_urlize(index):
    if index in ResourceNameDBToUIMap.dict:
        url_pre = "/{{STATIC_URL}}/img/resource-icons/"
        url_post = "48x48.png"
        return url_pre + ResourceNameDBToUIMap.dict[index] + url_post
    return ''


@register.simple_tag(name='resource_img_url_builder')
def resource_img_url_builder(static_url, rsc_type):
    if rsc_type in ResourceNameDBToUIMap.dict:
        url_pre = "<img " + "src=\"" + static_url + "/img/resource-icons/"
        url_post = "48x48.png\">"
        return url_pre + ResourceNameDBToUIMap.dict[rsc_type] + url_post
    return ''


class ResourceNameDBToUIMap:
    dict = {
        'CompositeResource': 'composite',
        'RasterResource': 'geographicraster',
        'RefTimeSeriesResource': 'his',
        'ScriptResource': 'script',
        'ModelProgramResource': 'modelprogram',
        'ModelInstanceResource': 'modelinstance',
        'SWATModelInstanceResource': 'swat',
        'NetcdfResource': 'multidimensional',
        'Time Series': 'timeseries',
        'GeographicFeatureResouce': 'geographicfeature',
        'ToolResource': 'webapp',
        'CollectionResource': 'collection',
        'MODFLOWModelInstanceResource': 'modflow',
        'GenericResource': 'generic'
    }
