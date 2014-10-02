from __future__ import absolute_import
from hs_core.models import *
from resource_aggregation.models import *
from ga_resources.utils import json_or_jsonp
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from hs_core import hydroshare
import os
from mezzanine.pages.page_processors import processor_for


class CreateAggregationForm(forms.Form):
    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)
    resource_permalink = forms.CharField(required=False, min_length=0)
    resource_description = forms.CharField(required=False, min_length=0)
    more = forms.CharField(required=False, min_length=0)  # field used to know if user wishes to continue

@login_required
def create_resource_aggregation(request, *args, **kwargs):
    frm = CreateAggregationForm(request.POST)
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

        agg = hydroshare.create_resource(
            resource_type='ResourceAggregation',
            owner=request.user,
            title=frm.cleaned_data['title'],
            keywords=[k.strip() for k in frm.cleaned_data['keywords'].split(',')] if frm.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=frm.cleaned_data['abstract'] or frm.cleaned_data['title']
        )

        if frm.cleaned_data.get('resource_permalink'):
            hs_res_permalink = frm.cleaned_data.get('resource_permalink')
            trash, hs_res_shortkey = os.path.split(hs_res_permalink[:-1])
            hs_res = hydroshare.get_resource_by_shortkey(hs_res_shortkey)
            description = frm.cleaned_data.get('resource_description') or ''
            Resource.objects.create(resource_short_id=hs_res.short_id or hs_res_shortkey,
                                    resource_description=description,
                                    content_object=agg)

        if frm.cleaned_data.get('more'):
            data = {'agg_short_id': agg.short_id}
            return json_or_jsonp(request, data)

        return HttpResponseRedirect('/my-resources/')   # FIXME this will eventually need to change

@login_required
def add_resource_view(request, shortkey, *args, **kwargs):
    agg = hydroshare.get_resource_by_shortkey(shortkey)
    resources = Resource.objects.filter(object_id=agg.id)
    agg_resources = {}
    for agg_res in resources:
        res = hydroshare.get_resource_by_shortkey(agg_res.resource_short_id)
        if res:
            short_id = res.short_id
            if agg_res.resource_description:
                description = agg_res.resource_description
            else:
                description = "None"
            agg_resources[res.title] = [short_id, description]
    context = {'agg': agg,
               'agg_resources': agg_resources}
    return render(request, "pages/add-resource.html", context)


class AddResourceForm(forms.Form):
    resource_permalink = forms.CharField(required=False, min_length=0)
    resource_description = forms.CharField(required=False, min_length=0)
    more = forms.CharField(required=False, min_length=0)  # field used to know if user wishes to continue

@login_required
def add_resource(request, shortkey, *args, **kwargs):
    frm = AddResourceForm(request.POST)
    if frm.is_valid():
        agg = hydroshare.get_resource_by_shortkey(shortkey)

        if frm.cleaned_data.get('resource_permalink'):
            hs_res_permalink = frm.cleaned_data.get('resource_permalink')
            trash, new_short_id = os.path.split(hs_res_permalink[:-1])
            hs_res = hydroshare.get_resource_by_shortkey(new_short_id)
            description = frm.cleaned_data.get('resource_description') or ''
            for res in Resource.objects.filter(object_id=agg.id):
                if res.resource_short_id == new_short_id:
                    res.delete()
            Resource.objects.create(resource_short_id=hs_res.short_id or new_short_id,
                                          resource_description=description,
                                          content_object=agg)

        return HttpResponseRedirect('/my-resources/')

@processor_for(ResourceAggregation)
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

    resources = Resource.objects.filter(object_id=cm.id)
    agg_resources = {}
    for agg_res in resources:
        res = hydroshare.get_resource_by_shortkey(agg_res.resource_short_id)
        if res:
            short_id = res.short_id
            if agg_res.resource_description:
                description = agg_res.resource_description
            else:
                description = "None"
            agg_resources[res.title] = [short_id, description]

    return {
        'dublin_core': [t for t in cm.dublin_metadata.all().exclude(term='AB').exclude(term='DM').exclude(term='DC').exclude(term='DTS').exclude(term='T')],
        'abstract' : abstract,
        'short_id' : cm.short_id,
        'agg_resources': agg_resources,
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