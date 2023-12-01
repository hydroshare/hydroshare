from django import forms
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.auth.forms import UserCreationForm
from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _

from .models import ResourceFile, User, BaseResource, Creator


class UserAdmin(DjangoUserAdmin):
    actions = ['delete_selected']

    def delete_model(self, request, obj):
        # prevent user delete if user is an owner/author on a published resource
        try:
            c = Creator.objects.get(hydroshare_user_id=obj.id)
            published_resources = BaseResource.objects.filter(object_id=c.content_object.id, raccess__published=True)
        except Creator.DoesNotExist:
            published_resources = None
        if published_resources:
            res_ids = ", ".join(str(res.short_id) for res in published_resources)
            message = f"Can't delete user. They are a creator of published resource(s): {res_ids}"
            self.message_user(request, message, messages.ERROR)
            # https://github.com/django/django/blob/3.2/django/contrib/admin/actions.py#L46-L48C27
            return False
        else:
            return super(UserAdmin, self).delete_model(request, obj)

    def delete_selected(self, request, queryset):
        # prevent user delete if user is an owner/author on a published resource
        user_no_del = []
        for user in queryset:
            try:
                c = Creator.objects.get(hydroshare_user_id=user.id)
                published_resources = BaseResource.objects.filter(
                    object_id=c.content_object.id, raccess__published=True)
                if published_resources:
                    user_no_del.append(user)
                    queryset = queryset.exclude(id=user.id)
            except Creator.DoesNotExist:
                continue
        if user_no_del:
            usernames = ", ".join(str(u.username) for u in user_no_del)
            message = f"Can't delete user(s):{usernames}. They are creator(s) of published resources."
            self.message_user(request, message, messages.ERROR)
        if queryset.count():
            return django_delete_selected(self, request, queryset)
    delete_selected.short_description = django_delete_selected.short_description


class UserCreationFormExtended(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationFormExtended, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField(label=_("E-mail"), max_length=75)


UserAdmin.add_form = UserCreationFormExtended
UserAdmin.readonly_fields = ('username',)
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
