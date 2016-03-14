__author__ = 'tonycastronova'

from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from hs_model_program.models import MpMetadata
from hs_core.forms import BaseFormHelper
from django.utils.html import escape
class mp_form_helper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):

        files = kwargs.pop('files')
        file_data = {}
        for f in files.all():
            short_url = escape(f.resource_file.name)
            name = short_url.split('/')[-1]
            file_data[name] = short_url

        options = '\n'.join(['<option value=%s>%s</option>'%(value, key) for key, value in file_data.iteritems() ])

        multiselect_elements = ['modelSoftware', 'modelDocumentation', 'modelReleaseNotes', 'modelEngine']
        multiselect = {}
        for elem in multiselect_elements:
            # build select list and selection table
            multiselect[elem] = HTML(
                            '<div class="div-multi-select" id="mp-div-multiselect" parent_metadata="'+elem+'">'
                                ' <select class="multi-select" id="mp-multi-select" multiple="multiple">'
                                        + options +
                                '</select>'
                            '</div><br>')


        # Order of the Fields below determines their layout on the edit page
        # For consistency, make sure this ordering matches models.py->get_xml()
        field_width = 'form-control input-sm'
        css_multichar = field_width + ' multichar'
        layout = Layout(
            HTML('<legend>Data</legend>'),
            HTML('<div class="col-sm-6 col-xs-12">'),
            Field('modelEngine', css_class=css_multichar, style="display:none"),
            multiselect['modelEngine'],
            Field('modelSoftware', css_class=css_multichar, style="display:none"),
            multiselect['modelSoftware'],
            Field('modelDocumentation', css_class=css_multichar, style="display:none"),
            multiselect['modelDocumentation'],
            Field('modelReleaseNotes', css_class=css_multichar, style="display:none"),
            multiselect['modelReleaseNotes'],
            HTML('<hr style="border:0">'),
            HTML('</div>'),
            HTML('<legend>General</legend>'),
            HTML('<div class="col-sm-6 col-xs-12">'),
            Field('modelReleaseDate', css_class=field_width, style="display:none"),
            HTML('<input type="text" class="'+field_width+'" id="modelReleaseDate_picker">'),
            Field('modelVersion', css_class=field_width),
            HTML('<br>'),
            HTML('<hr style="border:0">'),
            HTML('</div>'),
            HTML('<legend>Software</legend>'),
            HTML('<div class="col-sm-6 col-xs-12">'),
            Field('modelWebsite', css_class=field_width),
            Field('modelProgramLanguage', css_class=field_width),
            Field('modelOperatingSystem', css_class=field_width),
            Field('modelCodeRepository', css_class=field_width),
            HTML('</div>'),
        )
        super(mp_form_helper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='  ',  *args, **kwargs)


class mp_form(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        # pop files from kwargs, else metadata will fail to load in edit mode
        files = kwargs.pop('files')
        super(mp_form, self).__init__(*args, **kwargs)
        self.helper = mp_form_helper(allow_edit, res_short_id, element_id, element_name='MpMetadata', files=files)

        # hide the field help text
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None


    class Meta:
        model = MpMetadata

        fields = [  'modelVersion',
                    'modelProgramLanguage',
                    'modelOperatingSystem',
                    'modelReleaseDate',
                    'modelWebsite',
                    'modelCodeRepository',
                    'modelReleaseNotes',
                    'modelDocumentation',
                    'modelSoftware',
                    'modelEngine']
        exclude = ['content_object']


class mp_form_validation(forms.Form):
    modelVersion = forms.CharField(required=False)
    modelProgramLanguage = forms.CharField(required=False)
    modelOperatingSystem = forms.CharField(required=False)
    modelReleaseDate = forms.DateTimeField(required=False)
    modelWebsite = forms.CharField(required=False)
    modelCodeRepository = forms.CharField(required=False)
    modelReleaseNotes = forms.CharField(required=False)
    modelDocumentation = forms.CharField(required=False)
    modelSoftware = forms.CharField(required=False)
    modelEngine = forms.CharField(required=False)


