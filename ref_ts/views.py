from __future__ import absolute_import
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django import forms
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for
from ga_resources.utils import json_or_jsonp
from hs_core import hydroshare
from hs_core.hydroshare.hs_bagit import create_bag
from hs_core.models import ResourceFile
from . import ts_utils
from .models import RefTimeSeries
import requests
from suds.client import Client
import csv
import os
from lxml import etree
from StringIO import StringIO
import datetime
from django.utils.timezone import now

class ReferencedSitesForm(forms.Form):
    wsdl_url = forms.URLField()

def search_sites(request):
    f = ReferencedSitesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['wsdl_url']
        sites = ts_utils.sites_from_soap(url)

        return json_or_jsonp(request, sites)

class ReferencedVariablesForm(forms.Form):
    wsdl_url = forms.URLField()
    site = forms.CharField(min_length=0)

def search_variables(request):
    f = ReferencedVariablesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['wsdl_url']
        site = params['site']
        variables = ts_utils.site_info_from_soap(url, site=site)

        return json_or_jsonp(request, variables)


class GetTSValuesForm(forms.Form):
    ref_type = forms.CharField(min_length=0, required=True)
    service_url = forms.CharField(min_length=0, required=True)
    site = forms.CharField(min_length=0, required=False)
    variable = forms.CharField(min_length=0, required=False)

def time_series_from_service(request):
    f = GetTSValuesForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        ref_type = params['ref_type']
        url = params['service_url']
        site = params.get('site')
        variable = params.get('variable')
        if ref_type == 'rest':
            ts = ts_utils.time_series_from_service(url, ref_type)
        else:
            ts = ts_utils.time_series_from_service(url, ref_type, site_name_or_code=site, variable_code=variable)
        return json_or_jsonp(request, ts)


class VerifyRestUrlForm(forms.Form):
    rest_url = forms.URLField()

def verify_rest_url(request):
    f = VerifyRestUrlForm(request.GET)
    if f.is_valid():
        params = f.cleaned_data
        url = params['rest_url']
        try:
            ts = requests.get(url)
            ts_xml = etree.XML(ts.text.encode('utf-8'))
            if 'timeSeriesResponse' in ts_xml.tag:
                return json_or_jsonp(request, ts.status_code)
            elif 'Collection' in ts_xml.tag:
                return json_or_jsonp(request, ts.status_code)
            else:
                return json_or_jsonp(request, 400)
        except:
            return json_or_jsonp(request, 400)

class CreateRefTimeSeriesForm(forms.Form):
    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)
    rest_url = forms.URLField(required=False)
    wsdl_url = forms.URLField(required=False)
    reference_type = forms.CharField(required=False, min_length=0)
    site = forms.CharField(required=False, min_length=0)
    variable = forms.CharField(required=False, min_length=0)
    start_date = forms.CharField(required=True, min_length=0)

@login_required
def create_ref_time_series(request, *args, **kwargs):
    frm = CreateRefTimeSeriesForm(request.POST)
    if frm.is_valid():
        dcterms = [
            { 'term': 'T', 'content': frm.cleaned_data['title']},
            { 'term': 'AB', 'content': frm.cleaned_data['abstract'] or frm.cleaned_data['title']},
            { 'term': 'DTS', 'content': now().isoformat()}
        ]
        for cn in frm.cleaned_data['contributors'].split(','):
            cn = cn.strip()
            dcterms.append({'term' : 'CN', 'content' : cn})
        for cr in frm.cleaned_data['creators'].split(','):
            cr = cr.strip()
            dcterms.append({'term' : 'CR', 'content' : cr})

        if frm.cleaned_data['wsdl_url']:
            url = frm.cleaned_data['wsdl_url']
        elif frm.cleaned_data['rest_url']:
            url = frm.cleaned_data['rest_url']
        else:
            url = ''

        start_date_str = frm.cleaned_data["start_date"]
        start_date_int = ts_utils.time_to_int(start_date_str)
        start_date = datetime.datetime.fromtimestamp(start_date_int)
        site_name, site_code, variable_name, variable_code = None, None, None, None

        if frm.cleaned_data.get('site'):
            full_site = frm.cleaned_data['site'].replace(' ', '')
            n = full_site.index(':')
            site_name = full_site[:n]
            site_code = full_site[n+1:]

        if frm.cleaned_data.get('variable'):
            full_variable = frm.cleaned_data['variable'].replace(' ', '')
            n = full_variable.index(':')
            variable_name = full_variable[:n]
            variable_code = full_variable[n+1:]

        res = hydroshare.create_resource(
            resource_type='RefTimeSeries',
            owner=request.user,
            title=frm.cleaned_data['title'],
            keywords=[k.strip() for k in frm.cleaned_data['keywords'].split(',')] if frm.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=frm.cleaned_data['abstract'] or frm.cleaned_data['title'],
            reference_type=frm.cleaned_data['reference_type'],
            url=url,
            data_site_name=site_name,
            data_site_code=site_code,
            variable_name=variable_name,
            variable_code=variable_code,
            start_date=start_date,
            end_date=now()
        )
        return HttpResponseRedirect(res.get_absolute_url())

@processor_for(RefTimeSeries)
def add_dublin_core(request, page):
    from dublincore import models as dc

    class DCTerm(forms.ModelForm):
        class Meta:
            model = dc.QualifiedDublinCoreElement
            fields = ['term', 'content']

    cm = page.get_content_model()
    try:
        abstract = cm.dublin_metadata.filter(term='AB').first().content
    except:
        abstract = None

    return {
        'dublin_core': [t for t in cm.dublin_metadata.all().exclude(term='AB').exclude(term='DM').exclude(term='DC').exclude(term='DTS').exclude(term='T')],
        'abstract' : abstract,
        'short_id' : cm.short_id,
        'resource_type': cm._meta.verbose_name,
        'reference_type': cm.reference_type,
        'url': cm.url,
        'site_name': cm.data_site_name if cm.data_site_name else '',
        'site_code' : cm.data_site_code if cm.data_site_code else '',
        'variable_name': cm.variable_name if cm.variable_name else '',
        'variable_code': cm.variable_code if cm.variable_code else '',
        'files': cm.files.all(),
        'dcterm_frm': DCTerm(),
        'bag': cm.bags.first(),
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'owners': set(cm.owners.all()),
        'view_users': set(cm.view_users.all()),
        'view_groups': set(cm.view_groups.all()),
        'edit_users': set(cm.edit_users.all()),
        'edit_groups': set(cm.edit_groups.all()),
    }

def generate_files(request, shortkey, *args, **kwargs):
    res = hydroshare.get_resource_by_shortkey(shortkey)
    ts, csv_link, csv_size, xml_link, xml_size = {}, '', '', '', ''
    try:
        if res.reference_type == 'rest':
            ts = ts_utils.time_series_from_service(res.url, res.reference_type)
        else:
            ts = ts_utils.time_series_from_service(res.url,
                                               res.reference_type,
                                               site_name_or_code=res.data_site_code,
                                               variable_code=res.variable_code)

        vals = ts['values']
        version = ts['wml_version']
        d = datetime.date.today()
        date = '{0}_{1}_{2}'.format(d.month, d.day, d.year)
        file_base = '{0}-{1}'.format(res.title.replace(" ", ""), date)
        csv_name = '{0}.{1}'.format(file_base, 'csv')
        if version == '1':
            xml_end = 'wml_1'
            xml_name = '{0}-{1}.xml'.format(file_base, xml_end)
        elif version == '2.0':
            xml_end = 'wml_2_0'
            xml_name = '{0}-{1}.xml'.format(file_base, xml_end)
        for_csv = []
        for k, v in vals.items():
            t = (k, v)
            for_csv.append(t)
        ResourceFile.objects.filter(object_id=res.pk).delete()
        with open(csv_name, 'wb') as csv_file:
            w = csv.writer(csv_file)
            w.writerow([res.title])
            var = '{0}({1})'.format(ts['variable_name'], ts['units'])
            w.writerow(['time', var])
            for r in for_csv:
                w.writerow(r)
        with open(xml_name, 'wb') as xml_file:
            xml_file.write(ts['time_series'])
        csv_file = open(csv_name, 'r')
        xml_file = open(xml_name, 'r')
        files = [csv_file, xml_file]
        hydroshare.add_resource_files(res.short_id, csv_file, xml_file)
        create_bag(res)
        os.remove(csv_name)
        os.remove(xml_name)
        files = ResourceFile.objects.filter(object_id=res.pk)
        for f in files:
            if str(f.resource_file).endswith('.csv'):
                csv_link = f.resource_file.url
                csv_size = f.resource_file.size
            if xml_end in str(f.resource_file):
                xml_link = f.resource_file.url
                xml_size = f.resource_file.size
        status_code = 200
        data = {'for_graph': ts.get('for_graph'),
            'units': ts.get('units'),
            'site_name': ts.get('site_name'),
            'variable_name': ts.get('variable_name'),
            'status_code': status_code,
            'csv_name': csv_name,
            'xml_name': xml_name,
            'csv_link': csv_link,
            'csv_size': csv_size,
            'xml_link': xml_link,
            'xml_size': xml_size}
        return json_or_jsonp(request, data)  # successfully generated new files
    except Exception:  # most likely because the server is unreachable
        files = ResourceFile.objects.filter(object_id=res.pk)
        xml_file = None
        for f in files:
            if str(f.resource_file).endswith('.csv'):
                csv_link = f.resource_file.url
                csv_size = f.resource_file.size
            if str(f.resource_file).endswith('.xml'):
                xml_link = f.resource_file.url
                xml_size = f.resource_file.size
                xml_file = f.resource_file
        if xml_file is None:
            status_code = 404
            data = {'for_graph': ts.get('for_graph'),
                    'units': ts.get('units'),
                    'site_name': ts.get('site_name'),
                    'variable_name': ts.get('variable_name'),
                    'status_code': status_code,
                    'csv_link': csv_link,
                    'csv_size': csv_size,
                    'xml_link': xml_link,
                    'xml_size': xml_size}
            return json_or_jsonp(request, data)  # did not generate new files, did not find old ones
        xml_doc = open(str(xml_file), 'r').read()
        root = etree.XML(xml_doc)
        os.remove(str(xml_file))
        version = ts_utils.get_version(root)
        if version == '1':
            ts = ts_utils.parse_1_0_and_1_1(root)
            status_code = 200
        elif version =='2.0':
            ts = ts_utils.parse_2_0(root)
            status_code = 200
        else:
            status_code = 503
        data = {'for_graph': ts.get('for_graph'),
                    'units': ts.get('units'),
                    'site_name': ts.get('site_name'),
                    'variable_name': ts.get('variable_name'),
                    'status_code': status_code,
                    'csv_link': csv_link,
                    'csv_size': csv_size,
                    'xml_link': xml_link,
                    'xml_size': xml_size}
        return json_or_jsonp(request, data) # did not generate new files, return old ones

def transform_file(request, shortkey, *args, **kwargs):
    res = hydroshare.get_resource_by_shortkey(shortkey)
    if res.reference_type == 'soap':
        client = Client(res.url)
        response = client.service.GetValues(':'+res.data_site_code, ':'+res.variable_code, '', '', '')
    elif res.reference_type == 'rest':
        r = requests.get(res.url)
        response = str(r.text)
    waterml_1 = etree.XML(response)
    wml_string = etree.tostring(waterml_1)
    s = StringIO(wml_string)
    dom = etree.parse(s)
    module_dir = os.path.dirname(__file__)
    xsl_location = os.path.join(module_dir, "static/ref_ts/xslt/WaterML1_1_timeSeries_to_WaterML2.xsl")
    xslt = etree.parse(xsl_location)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)
    d = datetime.date.today()
    date = '{0}_{1}_{2}'.format(d.month, d.day, d.year)
    xml_name = '{0}-{1}-{2}'.format(res.title.replace(" ", ""), date, 'wml_2_0.xml')
    with open(xml_name, 'wb') as f:
        f.write(newdom)
    xml_file = open(xml_name, 'r')
    ResourceFile.objects.filter(object_id=res.pk, resource_file__contains='wml_2_0').delete()
    hydroshare.add_resource_files(res.short_id, xml_file)
    f = ResourceFile.objects.filter(object_id=res.pk, resource_file__contains='wml_2_0')[0].resource_file
    data = {
        'status_code': 200,
        'xml_name': xml_name,
        'xml_size': f.size,
        'xml_link': f.url
    }
    os.remove(xml_name)
    # print(etree.tostring(newdom, pretty_print=True))
    return json_or_jsonp(request, data)

