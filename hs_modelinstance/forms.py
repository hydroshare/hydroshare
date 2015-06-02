__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms
from crispy_forms import *
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from hs_modelinstance.models import *
from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users

class MetadataField(layout.Field):
          def __init__(self, *args, **kwargs):
              kwargs['css_class'] = 'form-control input-sm'
              super(MetadataField, self).__init__(*args, **kwargs)

class ModelOutputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        # for ModelOutput we have only one field includes_output
        layout = Layout(
            MetadataField('includes_output'),
        )
        kwargs['element_name_label'] = 'Includes output files?'
        super(ModelOutputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, *args,
                                                    **kwargs)


class ModelOutputForm(ModelForm):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect(attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelOutputForm, self).__init__(*args, **kwargs)
        self.helper = ModelOutputFormHelper(allow_edit, res_short_id, element_id, element_name='ModelOutput')

    class Meta:
        model = ModelOutput
        fields = ('includes_output',)        

class ModelOutputValidationForm(forms.Form):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))

    def clean_includes_output(self):
        data = self.cleaned_data['includes_output']
        if data == u'False':
            return False
        else:
            return True


# ExecutedBy element forms
class ExecutedByFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
            MetadataField('model_name'),
            HTML("""
            <div id=progam_details_div style="display:none">
                <table id="program_details_table" class="modelprogram">
                <tr><td>Description: </td><td></td></tr>
                <tr><td>Release Date: </td><td></td></tr>
                <tr><td>Version: </td><td></td></tr>
                <tr><td>Language: </td><td></td></tr>
                <tr><td>Operating System: </td><td></td></tr>
                <tr><td>Url: </td><td></td></tr>
            </table>
            </div>
            """),
        )

        kwargs['element_name_label'] = 'Model Program used for execution'
        super(ExecutedByFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, *args,
                                                   **kwargs)


class ExecutedByForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ExecutedByForm, self).__init__(*args, **kwargs)
        self.helper = ExecutedByFormHelper(allow_edit, res_short_id, element_id, element_name='ExecutedBy')

        # get all model program resources
        mp_resource = users.get_resource_list(type=['ModelProgramResource'])

        # set model programs resources in choice list
        CHOICES = (('Unknown', 'Unknown'),) + tuple((r.short_id, r.title) for r in mp_resource.values()[0])

        # Set the choice lists as the file names in the content model
        self.fields['model_name'].choices = CHOICES

    class Meta:
        model = ExecutedBy
        exclude = ('content_object', 'model_program_fk',)


class ExecutedByValidationForm(forms.Form):
    model_name = forms.CharField(max_length=200)
    model_program_fk = forms

