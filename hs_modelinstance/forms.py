__author__ = 'Mohamed'
from django.forms import ModelForm
from django import forms

from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users


class ModelOutputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        # for ModelOutput we have only one field includes_output
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('includes_output', css_class=field_width),
        )
        kwargs['element_name_label'] = 'Includes output files?'
        super(ModelOutputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, *args,
                                                    **kwargs)


class ModelOutputForm(ModelForm):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelOutputForm, self).__init__(*args, **kwargs)
        self.helper = ModelOutputFormHelper(allow_edit, res_short_id, element_id, element_name='ModelOutput')
        self.fields['includes_output'].widget.attrs['style'] = "width:auto;margin-top:-5px"

        # if len(self.initial) == 0:
        # self.initial['includes_output'] = False

    class Meta:
        model = ModelOutput
        fields = ['includes_output']
        exclude = ['content_object']


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
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('model_name', css_class=field_width),
        )

        kwargs['element_name_label'] = 'Model Program used for execution'
        super(ExecutedByFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, *args,
                                                   **kwargs)


class ExecutedByForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        # pop owner from kwargs so that it isn't passed into parent classes (below)
        owner = kwargs.pop('owner')

        super(ExecutedByForm, self).__init__(*args, **kwargs)
        self.helper = ExecutedByFormHelper(allow_edit, res_short_id, element_id, element_name='ExecutedBy')

        mp_resource = users.get_resource_list(user=owner, types=['ModelProgramResource'])

        # change above line to this once issue #262 is merged into develop
        # mp_resource = users.get_resource_list(types=['ModelProgramResource'])


        CHOICES = tuple([('Unknown', 'Unknown')] + [(r.short_id, r.title) for r in mp_resource.values()[0]])

        # Set the choice lists as the file names in the content model
        self.fields['model_name'].choices = CHOICES


    class Meta:
        model = ExecutedBy
        exclude = ['content_object', 'model_program_fk']


class ExecutedByValidationForm(forms.Form):
    model_name = forms.CharField(max_length=200)
    model_program_fk = forms

