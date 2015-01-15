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
from django.contrib.auth.models import User, Group
from collections import OrderedDict
from hs_core.hydroshare.hs_bagit import create_bag

# class DetailView(generic.DetailView):
#     model = HydroProgramResource
#     #template_name = 'hydromodel/detail.html'
#     template_name = 'hydroprogramresource.html'


class CreateHydroProgramForm(forms.Form):
    #
    # def __init__(self, *args, **kwargs):
    #     super(CreateHydroProgramForm,self).__init(*args, **kwargs)
    #     self.helper= FormHelper()
    #     self.helper.html5_required = True

    title = forms.CharField(required=False)
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
    date_released = forms.DateTimeField(required=False)
    release_notes = forms.CharField(required=False)
    program_website = forms.CharField(required=False, max_length=255)
    software_repo = forms.CharField(required=False, max_length=255)
    user_manual = forms.FileField(required=False)
    theoretical_manual = forms.FileField(required=False)
    source_code = forms.FileField(required=False)
    exec_code = forms.FileField(required=False)
    build_notes = forms.CharField(required=False)
    software_rights = forms.CharField(required=False)



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


        terms = ['source','theoretical','user','notes']
        # get files
        file_map = json.loads(form.data['file_map'])
        upload_files = {}
        for f in request.FILES.itervalues():
            tag = file_map[f.name]
            for term in terms:
                if term in tag.lower():
                    upload_files[term] = f




        res = hydroshare.create_resource(
            resource_type='HydroProgramResource',
            owner=request.user,
            title=form.cleaned_data['title'],
            keywords=[k.strip() for k in form.cleaned_data['keywords'].split(',')] if form.cleaned_data['keywords'] else None,
            dublin_metadata=dcterms,
            content=form.cleaned_data['abstract'] or form.cleaned_data['title'],
            files = upload_files.values(),
            ###########
            software_version = form.cleaned_data['software_version'],
            software_language = form.cleaned_data['software_language'],
            operating_sys = form.cleaned_data['operating_sys'],
            date_released = form.cleaned_data['date_released'],
            release_notes = form.cleaned_data['release_notes'],
            program_website =form.cleaned_data['program_website'],
            software_repo =form.cleaned_data['software_repo'],
            # user_manual = upload_files['user'] if 'user' in upload_files else None,
            # theoretical_manual = upload_files['theoretical'] if 'theoretical' in upload_files else None,
            # source_code =upload_files['source'] if 'source' in upload_files else None,
            # exec_code = '',
            # build_notes =upload_files['notes'] if 'notes' in upload_files else None,
            user_manual = 'undefined',
            theoretical_manual = 'undefined',
            source_code ='undefined',
            software_rights = form.data['eula']
        )

        updated_kwargs = {}
        # get the file links from the content model (this should be done during create_resource)
        files = res.files.all()
        for f in files:
            # get the file url and name
            url = f.resource_file.url
            fname = url.split('/')[-1]

            # get the term associated with this file
            term = file_map[fname].lower()
            if 'theoretical' in term : res.theoretical_manual = url
            elif 'user' in term : res.user_manual = url
            elif 'source' in term : res.source_code= url
            elif 'notes' in term :res.build_notes = url

        if len(files) > 0:
            res.save()

        #save_files(res.short_id, upload_files)
        return HttpResponseRedirect(res.get_absolute_url())

    else:
        # messages.error(request, "Error")
        #return render_to_response('pages/create-hydro-program.html',frm, context_instance=RequestContext(request))
        context = {'form': form,'test':'somevalue'}
        return render_to_response('pages/create-hydro-program.html', context ,context_instance=RequestContext(request))
        #return render(request, 'pages/create-hydro-program.html', {'form':frm})

@processor_for(HydroProgramResource)
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
    coverages = cm.metadata.coverages.all()

    # get the current resource
    res = hydroshare.get_resource_by_shortkey(cm.short_id)

    # build an ordered dictionary to store model program metadata
    program_metadata = OrderedDict([
                        ('Date Released', cm.date_released),
                        ('Program Website', cm.program_website),
                        ('Version', cm.software_version),
                        ('Language', cm.software_language),
                        ('Operating System', cm.operating_sys),
                        ('Code Repository', cm.software_repo),
                        ('Software Rights', cm.software_rights)
                    ])
    program_files = OrderedDict([
                        ('User Manual', res.user_manual),
                        ('Theoretical Manual', res.theoretical_manual),
                        ('Source Code', res.source_code),
                        ('Release Notes', cm.release_notes),
                    ])

    return {
        'dublin_core': [t for t in cm.dublin_metadata.all().exclude(term='AB').exclude(term='DM').exclude(term='DC').exclude(term='DTS').exclude(term='T')],
        'abstract': abstract,
        'short_id': cm.short_id,
        'resource_type': cm._meta.verbose_name,
        'coverages': coverages,
        'cm' : cm,
        #'spatial_coverage': cm.spatial_coverage,
        #'temporal_coverage': cm.temporal_coverage,
        #'includes_output': cm.includes_output,
        #'executed_by' : cm.executed_by,
        #'files': cm.files.all(),
        'dcterm_frm': DCTerm(),
        'bag': cm.bags.first(),
        'users': User.objects.all(),
        'groups': Group.objects.all(),
        'owners': set(cm.owners.all()),
        'view_users': set(cm.view_users.all()),
        'view_groups': set(cm.view_groups.all()),
        'edit_users': set(cm.edit_users.all()),
        'edit_groups': set(cm.edit_groups.all()),
        ##################
        'program_metadata' : program_metadata,
        'program_files' : program_files,

        # 'software_version' : cm.software_version,
        # 'software_language' : cm.software_language,
        # 'operating_sys' : cm.operating_sys,
        # 'date_released' : cm.date_released,
        # 'release_notes' : cm.release_notes,
        # 'program_website' : cm.program_website,
        # 'software_repo' : cm.software_repo,
        # 'user_manual'  : cm.user_manual,
        # 'theoretical_manual' : cm.theoretical_manual,
        # 'source_code' : cm.source_code,
        # 'exec_code' :cm.exec_code,
        # 'build_notes' : cm.build_notes,
        # 'software_rights': cm.software_rights
    }

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
