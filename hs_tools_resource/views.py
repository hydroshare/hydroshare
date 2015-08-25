# from __future__ import absolute_import
# from django.contrib.auth.decorators import login_required
# from django import forms
# from django.shortcuts import redirect
# from hs_core import hydroshare
# import urllib
#
# class GoForToolsForm(forms.Form):
#     my_str = forms.CharField(required=False, min_length=0) # reserving this in case I need something
#
# @login_required
# def go_for_tools(request, shortkey, user, tooltype, *args, **kwargs):
#     frm = GoForToolsForm(request.POST)
#
#     if frm.is_valid():
#         my_string = frm.cleaned_data.get('my_str')
#         url_base = "http://www.example.com" # just in case the resource doesn't exist
#         res = hydroshare.get_resource_by_shortkey(shortkey)
#         if res:
#             if res.files.first():
#                 f_url = str(res.files.first().resource_file)
#                 f_name = f_url.split("/")[-1]  # choose the last part of the url for the file, which is it's name
#             else:
#                 f_name = "none-no-resource-file"
#             url_base = res.metadata.url_base.first() or "http://www.example.com" # if there isn't a url_base
#         else:
#             f_name = "none-no-resource-provided"
#
#
#         myParameters = { "res_id" : shortkey, "user" : user, "tool_type" : tooltype, "file_name": f_name }
#         myURL = "%s?%s" % (url_base, urllib.urlencode(myParameters))
#         return redirect(myURL)
