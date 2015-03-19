from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
#from django.common.decorators import render_to
from hs_core import hydroshare
from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import inlineformset_factory
from .models import *
from .models import HydroProgramResource
from django.utils.timezone import now
from ga_resources.utils import json_or_jsonp
import json
import os
from django.conf import settings
from .metadata import parser
import mmap

#
# class CreateNetcdfForm(forms.Form):
#     title = forms.CharField(required=True)
#     creators = forms.CharField(required=False, min_length=0)
#     contributors = forms.CharField(required=False, min_length=0)
#     abstract = forms.CharField(required=False, min_length=0)
#     keywords = forms.CharField(required=False, min_length=0)

# class CreateNetcdfVariableForm(forms.Form):
#     # Required Fields
#     defined_name = forms.CharField(max_length=50, null=False)
#     units = forms.CharField(verbose_name='Variable unit', max_length=50, null=False)
#     type = forms.CharField(verbose_name='Variable data type', max_length=50, null=False)
#     shape = forms.CharField(verbose_name='Variable shape', max_length=50, null=False)
#     # Optional Fields
#     description_name = forms.CharField()
#     method = forms.TextField(verbose_name='Variable method',)
#     missing_value = forms.CharField(verbose_name='Variable missing value', max_length=100)




@login_required
def create_netcdf(request, *args, **kwargs):

    NetcdfFormset = inlineformset_factory(NetcdfResource, NetcdfVariable, extra=1)

    if request.method == 'POST':
        formset = NetcdfFormset(request.POST)
        if formset.is_valid():

            res = hydroshare.create_resource(
                resource_type='NetcdfResource',
                owner=request.user,
                #dublin_metadata=dcterms
            )

            for form in formset:
                print(form.as_table())
            # TODO add netcdf variable instance. Need to know what is in the form
            #formset.save()

            return HttpResponseRedirect(res.get_absolute_url())
    else:
        formset = NetcdfFormset()

    return render_to_response("create-netcdf.html", { "formset": formset})





