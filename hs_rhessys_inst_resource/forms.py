from django import forms

class InputForm(forms.Form):
    name = forms.CharField(label="Name", max_length=50, widget=forms.TextInput(attrs={'size':80}))
    model_desc = forms.CharField(label="Model description", max_length=500, widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    study_area_bbox = forms.CharField(label="Study area bounding box", max_length = 50, widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_repo = forms.URLField(label="git repository", max_length=500, widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_username = forms.CharField(label="git user name", max_length=50, required=False, widget=forms.TextInput(attrs={'size':80}))
    git_password = forms.CharField(label="git password", widget=forms.PasswordInput(attrs={'size':80}), required=False)
    commit_id = forms.CharField(label="git commit id", max_length=50, widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))
    git_branch = forms.CharField(label="git branch", max_length=50, widget=forms.TextInput(attrs={'size':80}))
    model_command_line_parameters = forms.CharField(label="model command line parameters", max_length=500, required=False, widget=forms.TextInput(attrs={'size':80}))
    project_name = forms.CharField(label="project name", max_length=100, widget=forms.TextInput(attrs={'size':80, 'readonly':'readonly'}))