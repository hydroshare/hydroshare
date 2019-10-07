from django import forms


class ModelProgramMetadataValidationForm(forms.Form):
    version = forms.CharField(required=False, max_length=250)
    release_date = forms.DateField(required=False)
    website = forms.URLField(required=False, max_length=255)
    code_repository = forms.URLField(required=False, max_length=255)
    programming_languages = forms.CharField(required=False)
    operating_systems = forms.CharField(required=False)

    def clean_version(self):
        version = self.cleaned_data['version'].strip()
        return version

    def clean_programming_languages(self):
        langauge_string = self.cleaned_data['programming_languages']
        if langauge_string:
            # generate a list of strings
            languages = langauge_string.split(',')
            return languages
        return langauge_string

    def clean_operating_systems(self):
        os_string = self.cleaned_data['operating_systems']
        if os_string:
            # generate a list of strings
            op_systems = os_string.split(',')
            return op_systems
        return []

