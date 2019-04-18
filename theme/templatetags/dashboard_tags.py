from __future__ import unicode_literals

from django import template
import timeago
from django.utils import timezone as django_timezone
register = template.Library()


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


@register.simple_tag(name='resource_img_url_builder')
def resource_img_url_builder(static_url, rsc_type):
    if rsc_type in ResourceNameDBToUIMap.dict:
        url_pre = "<img " + "src=\"" + static_url + "/img/resource-icons/"
        url_post = "48x48.png\">"
        return url_pre + ResourceNameDBToUIMap.dict[rsc_type] + url_post
    return ''


@register.simple_tag(name='resource_verbose_name_builder')
def resource_verbose_name_builder(rsc_type):
    if rsc_type in ResourceNameDBToUIMap.dict:
        return ResourceNameDBToUIMap.dict_verbose_name[rsc_type]
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
    dict_verbose_name = {
        'CompositeResource': 'Composite',
        'RasterResource': 'Geographic Raster',
        'RefTimeSeriesResource': 'HIS Referenced Time Series',
        'ScriptResource': 'Script',
        'ModelProgramResource': 'Model Program',
        'ModelInstanceResource': 'Model Instance',
        'SWATModelInstanceResource': 'SWAT Model Instance',
        'NetcdfResource': 'Multidimensional (NetCDF)',
        'Time Series': 'Time Series',
        'GeographicFeatureResouce': 'Geographic Feature',
        'ToolResource': 'Web App',
        'CollectionResource': 'Collection',
        'MODFLOWModelInstanceResource': 'MODFLOW Model Instance',
        'GenericResource': 'Generic'
    }
