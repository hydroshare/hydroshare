from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import Layout, HTML, Field
from hs_script_resource.models import ScriptSpecificMetadata
from hs_core.forms import BaseFormHelper


class ScriptFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):

        # Order of the Fields below determines their layout on the edit page
        # For consistency, make sure this ordering matches models.py->get_xml()
        field_width = 'form-control input-sm'
        layout = Layout(
            HTML('<legend>General</legend>'),
            HTML('<div class="col-sm-6 col-xs-12">'),
            Field('languageVersion', css_class=field_width),
            Field('scriptVersion', css_class=field_width),
            Field('scriptDependencies', css_class=field_width),
            Field('scriptReleaseDate', css_class=field_width, style="display:none"),
            HTML('<input type="text" class="' + field_width + '" id="scriptReleaseDate_picker">'),
            Field('scriptCodeRepository', css_class=field_width),
            HTML('</div>')
        )
        super(ScriptFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                               layout, element_name_label='  ', *args, **kwargs)


class ScriptForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ScriptForm, self).__init__(*args, **kwargs)
        self.helper = ScriptFormHelper(allow_edit, res_short_id, element_id, element_name='ScriptSpecificMetadata')

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class': 'has-popover',
                                                        'data-content': help_text,
                                                        'data-placement': 'right',
                                                        'data-container': 'body'})

    class Meta:
        model = ScriptSpecificMetadata

        fields = ['languageVersion',
                  'scriptVersion',
                  'scriptDependencies',
                  'scriptReleaseDate',
                  'scriptCodeRepository']
        exclude = ['content_object']


class ScriptFormValidation(forms.Form):
    languageVersion = forms.CharField(required=False)
    scriptVersion = forms.CharField(required=False)
    scriptDependencies = forms.CharField(required=False)
    scriptReleaseDate = forms.DateTimeField(required=False)
    scriptCodeRepository = forms.CharField(required=False)
