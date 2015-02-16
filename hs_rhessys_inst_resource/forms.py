from django import forms

class InputForm(forms.Form):
    name = forms.CharField(label="Name", max_length=50, widget=forms.TextInput(attrs={'size':80}))
    model_desc = forms.CharField(label="Model description", max_length=500, 
                                 widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    study_area_bbox = forms.CharField(label="Study area bounding box", 
                                      max_length = 50, 
                                      widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_repo = forms.URLField(label="git repository", max_length=500, 
                              widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_username = forms.CharField(label="git user name", max_length=50, required=False, 
                                   widget=forms.TextInput(attrs={'size':80}))
    git_password = forms.CharField(label="git password", 
                                   widget=forms.PasswordInput(attrs={'size':80}), required=False)
    commit_id = forms.CharField(label="git commit id", max_length=50, 
                                widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_branch = forms.CharField(label="git branch", max_length=50, required=False,
                                 widget=forms.TextInput(attrs={'size':80}))
    model_command_line_parameters = forms.CharField(label="model command line parameters", 
                                                    max_length=500, required=False, 
                                                    widget=forms.TextInput(attrs={'size':80}))
    project_name = forms.CharField(label="project name", max_length=100, 
                                   widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))

class RunModelForm(forms.Form):
    title = forms.CharField(label="Title", max_length=64, required=True,
                            widget=forms.TextInput(attrs={'size':80}))
    description = forms.CharField(label="Description", max_length=1024, required=False,
                                  widget=forms.TextInput(attrs={'size':80, 'rows':1}))
    model_command_line_parameters = forms.CharField(label="Model command line parameters", 
                                                    max_length=1024, required=True, 
                                                    widget=forms.Textarea(attrs={'cols':80, 'rows':4}))
    tec_file = forms.CharField(label="TEC file",
                               max_length=1024, required=False,
                               widget=forms.Textarea(attrs={'cols':80, 'rows':4}))
    climate_station = forms.ChoiceField(label="Climate station", choices=(('','')), required=False)

    
