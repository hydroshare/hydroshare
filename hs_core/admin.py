from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import ugettext_lazy as _

from .models import *


class UserCreationFormExtended(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationFormExtended, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(label=_("E-mail"), max_length=75)

UserAdmin.add_form = UserCreationFormExtended
UserAdmin.add_fieldsets = (
    (None, {
        'classes': ('wide',),
        'fields': ('email', 'username', 'password1', 'password2',)
    }),
)
UserAdmin.list_display = [
    'username', 'email', 'first_name', 'last_name', 'is_staff',
    'is_active', 'date_joined', 'last_login'
]

class InlineResourceFiles(GenericTabularInline):
    model = ResourceFile

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
