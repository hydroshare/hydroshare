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
from .models import HydroProgramResource
from django.utils.timezone import now
from ga_resources.utils import json_or_jsonp
import json
import os
from django.conf import settings
from .metadata import parser
import mmap
from mezzanine.pages.page_processors import processor_for
from django.template import RequestContext
# from django.contrib import messages
from crispy_forms.helper import FormHelper


class DetailView(generic.DetailView):
    model = HydroProgramResource
    #template_name = 'hydromodel/detail.html'
    template_name = 'hs_hydroprogram/detail.html'


class CreateHydroProgramForm(forms.Form):
    #
    # def __init__(self, *args, **kwargs):
    #     super(CreateHydroProgramForm,self).__init(*args, **kwargs)
    #     self.helper= FormHelper()
    #     self.helper.html5_required = True

    title = forms.CharField(required=True)
    creators = forms.CharField(required=False, min_length=0)
    contributors = forms.CharField(required=False, min_length=0)
    abstract = forms.CharField(required=False, min_length=0)
    keywords = forms.CharField(required=False, min_length=0)
    # # rest_url = forms.URLField(required=False)
    # # wsdl_url = forms.URLField(required=False)
    # reference_type = forms.CharField(required=False, min_length=0)
    # # site = forms.CharField(required=False, min_length=0)
    # # variable = forms.CharField(required=False, min_length=0)
    # software_url = forms.CharField(required=False, min_length=0)

    software_version = forms.CharField(required=False,max_length=255)
    software_language = forms.CharField(required=False,max_length=100)
    operating_sys = forms.CharField(required=False,max_length=255)
    date_released = forms.DateTimeField(required=True)
    release_notes = forms.CharField(required=False)
    program_website = forms.CharField(required=True, max_length=255)
    software_repo = forms.CharField(required=True, max_length=255)
    user_manual = forms.FileField(required=False)
    theoretical_manual = forms.FileField(required=False)
    source_code = forms.FileField(required=False)
    exec_code = forms.FileField(required=False)
    build_notes = forms.CharField(required=False)




def file_upload(request):

    print 'Upload function'

    form_data = {'title':'My Title'}

    # return back some info
    #return render(request,'pages/create-hydro-program.html',form_data)
    return render_to_response('pages/create-hydro-program.html',form_data, context_instance=RequestContext(request))
    #return render_to_response('create-resource.html',{'form':form})
 #   return HttpResponse()


def mytest(request, *args, **kwargs):

    print 'TEST'


@login_required
def create_hydro_program(request, *args, **kwargs):

    print 'CREATE RESOURCE'

    form = CreateHydroProgramForm(request.POST)
    print request.POST['creators']
    #print frm
    #print request.FILES.getlist('files'),
    if form.is_valid():
        dcterms = [
            { 'term': 'T', 'content': form.cleaned_data['title']},
            { 'term': 'AB', 'content': form.cleaned_data['abstract'] or form.cleaned_data['title']},
            { 'term': 'DTS', 'content': now().isoformat()}
        ]

        for cn in form.cleaned_data['contributors'].split(','):
            cn = cn.strip()
            dcterms.append({'term' : 'CN', 'content' : cn})
        for cr in form.cleaned_data['creators'].split(','):
            cr = cr.strip()
            dcterms.append({'term' : 'CR', 'content' : cr})


        # get files
        file_map = form.cleaned_data['file_map']
        uploaded_files = {}
        for f in request.files:
            tag = file_map[f.name]
            upload_files[tag] = f

        res = hydroshare.create_resource(
            resource_type='HydroProgramResource',
            owner=request.user,
            title=form.cleaned_data['title'],
            keywords=[k.strip() for k in form.cleaned_data['keywords'].split(',')] if form.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=form.cleaned_data['abstract'] or form.cleaned_data['title'],
            ###########
            software_version = form.cleaned_data['sofware_version'],
            software_language = form.cleaned_data['software_language'],
            operating_sys = form.cleaned_data['operating_sys'],
            date_released = form.cleaned_data['date_released'],
            release_notes = form.cleaned_data['release_notes'],
            program_website =form.cleaned_data['program_website'],
            software_repo =form.cleaned_data['software_repo'],
            user_manual =form.cleaned_data[''],
            theoretical_manual =form.cleaned_data[''],
            source_code =form.cleaned_data[''],
            exec_code =form.cleaned_data[''],
            build_notes =form.cleaned_data[''],
        )
        return HttpResponseRedirect(res.get_absolute_url())
    else:
        # messages.error(request, "Error")
        #return render_to_response('pages/create-hydro-program.html',frm, context_instance=RequestContext(request))
        context = {'form': form,'test':'somevalue'}
        return render_to_response('pages/create-hydro-program.html', context ,context_instance=RequestContext(request))
        #return render(request, 'pages/create-hydro-program.html', {'form':frm})

# #todo:  Copied from Ref Time Series.  Do I need this?
# @processor_for(HydroProgramResource)
# def add_dublin_core(request, page):
#     from dublincore import models as dc
#
#     class DCTerm(forms.ModelForm):
#         class Meta:
#             model = dc.QualifiedDublinCoreElement
#             fields = ['term', 'content']
#
#     cm = page.get_content_model()
#     try:
#         abstract = cm.dublin_metadata.filter(term='AB').first().content
#     except:
#         abstract = None
#
#     return {
#         'dublin_core': [t for t in cm.dublin_metadata.all().exclude(term='AB').exclude(term='DM').exclude(term='DC').exclude(term='DTS').exclude(term='T')],
#         'abstract' : abstract,
#         'short_id' : cm.short_id,
#         'resource_type': cm._meta.verbose_name,
#         'reference_type': cm.reference_type,
#         'url': cm.url,
#         'site_name': cm.data_site_name if cm.data_site_name else '',
#         'site_code' : cm.data_site_code if cm.data_site_code else '',
#         'variable_name': cm.variable_name if cm.variable_name else '',
#         'variable_code': cm.variable_code if cm.variable_code else '',
#         'files': cm.files.all(),
#         'dcterm_frm': DCTerm(),
#         'bag': cm.bags.first(),
#         'users': User.objects.all(),
#         'groups': Group.objects.all(),
#         'owners': set(cm.owners.all()),
#         'view_users': set(cm.view_users.all()),
#         'view_groups': set(cm.view_groups.all()),
#         'edit_users': set(cm.edit_users.all()),
#         'edit_groups': set(cm.edit_groups.all()),
#     }



def upload_files(request):


    print 'here!'

    files = request.POST.get('content', 'NONE')

    data = {'response': 'I received the file list on the server!'}


    #render_to_response('create_hydro_program.html', {'h': 'test'})

    return json_response(True,data)

def parse_metadata(request):

    name = request.POST.get('name','NONE')
    type = request.POST.get('type','NONE')
    size = request.POST.get('size','NONE')
    content = request.POST.get('content', 'NONE')
    parsed_metadata = {}


    if content != 'NONE':
        # todo: validate the metadata file
        #if parser.validate(content):

        # create a file object in memory
        fileObj = mmap.mmap(-1,len(content))
        fileObj.write(content)
        fileObj.seek(0)


        # parse the file object
        parsed_metadata = parser.get_metadata_dictionary(fileObj)


    data = {'name':name,
            'type':type,
            'size':size,
            'content':parsed_metadata}


    #render_to_response('create_hydro_program.html', {'h': 'test'})

    return json_response(True,data)




def get_eula(request):

    print 'IN: get_eula(request)'

    name = request.GET.get('name','NONE')
    response = {'eula':'Could not find a EULA for: '+name}

    formatted_name = name.lower().replace(' ','')

    try:
        path = os.path.join(settings.STATIC_ROOT, 'resources/eulas.json')
        txt = open(path,'r').readlines()[0]

        # todo: move th is to view load, so that it isn't constantly repeated
        # load the eula dictionary
        eula_dict = json.loads(txt)


        # set the response
        if formatted_name in eula_dict:
            response['eula'] = eula_dict[formatted_name]
        else:
            print formatted_name, 'not in dictionary!'

    except Exception, e:
        print e

    return HttpResponse(
        json.dumps(response), content_type='application/json'
    )
    #return json_response(True,response)



def json_response(result, data):
    response = json.dumps({"result" : result, "data" : data })
    return HttpResponse(response, mimetype="application/json")
