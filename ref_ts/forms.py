from django import forms

class ReferencedSitesForm(forms.Form):
    url = forms.URLField()

class ReferencedVariablesForm(forms.Form):
    url = forms.URLField(required=True)
    site = forms.CharField(required=True)

class GetTSValuesForm(forms.Form):
    ref_type = forms.CharField(required=True)
    service_url = forms.CharField(required=True)
    site = forms.CharField(required=False)
    variable = forms.CharField( required=False)

class VerifyRestUrlForm(forms.Form):
    url = forms.URLField(required=True)

class CreateRefTimeSeriesForm(forms.Form):
    title = forms.CharField(required=False)