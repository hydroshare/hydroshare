from django import forms

class ValidateMetadataForm(forms.Form):
    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required = True)
    cellSizeYValue = forms.FloatField(required = True)
    cellSizeUnit = forms.CharField(max_length=50, required = True)
    cellDataType = forms.CharField(max_length=50, required=True)
    cellNoDataValue = forms.FloatField(required = False)
    bandCount =forms.IntegerField(required=True)
    bandName_1 = forms.CharField(max_length=50, required=True)
    variableName_1 = forms.CharField(max_length=50, required=True)
    variableUnit_1 = forms.CharField(max_length=50, required=True)
    method_1 = forms.CharField(max_length=50, required=False)
    comment_1 = forms.CharField(widget=forms.Textarea, required=False)