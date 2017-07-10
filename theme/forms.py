import requests

from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils import timezone
from django.contrib.auth.models import User

from mezzanine.core.forms import Html5Mixin
from mezzanine.generic.models import Rating
from django_comments.forms import CommentSecurityForm
from mezzanine.utils.views import ip_for_request
from mezzanine.utils.email import split_addresses, send_mail_template
from mezzanine.utils.cache import add_cache_bypass
from mezzanine.conf import settings

from .models import UserProfile
from hs_core.hydroshare.users import create_account
from hs_core.templatetags.hydroshare_tags import best_name


class RatingForm(CommentSecurityForm):
    """
    Form for a rating. Subclasses ``CommentSecurityForm`` to make use
    of its easy setup for generic relations.
    """
    value = 1

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(RatingForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        Check unauthenticated user's cookie as a light check to
        prevent duplicate votes.
        """
        bits = (self.data["content_type"], self.data["object_pk"])
        self.current = "%s.%s" % bits
        request = self.request
        self.previous = request.COOKIES.get("mezzanine-rating", "").split(",")
        already_rated = self.current in self.previous
        if already_rated and not self.request.user.is_authenticated():
            raise forms.ValidationError(ugettext("Already rated."))
        return 1

    def save(self):
        """
        Saves a new rating - authenticated users can update the
        value if they've previously rated.
        """
        user = self.request.user
        rating_value = 1
        rating_name = self.target_object.get_ratingfield_name()
        rating_manager = getattr(self.target_object, rating_name)
        if user.is_authenticated():
            try:
                rating_instance = rating_manager.get(user=user)
            except Rating.DoesNotExist:
                rating_instance = Rating(user=user, value=rating_value)
                rating_manager.add(rating_instance)
            else:
                if rating_instance.value != int(rating_value):
                    rating_instance.value = rating_value
                    rating_instance.save()
                else:
                    # User submitted the same rating as previously,
                    # which we treat as undoing the rating (like a toggle).
                    rating_instance.delete()
        else:
            rating_instance = Rating(value=rating_value)
            rating_manager.add(rating_instance)
        return rating_instance


class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ['last_login', 'date_joined', 'password']

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput())
    Captcha = forms.CharField(required=False)
    challenge = forms.CharField()
    response = forms.CharField()

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SignupForm, self).__init__(*args, **kwargs)

    def verify_captcha(self):
        params = dict(self.cleaned_data)
        params['privatekey'] = getattr(settings, 'RECAPTCHA_PRIVATE_KEY',
                                       "6LdNC_USAAAAADNdzytMK2-qmDCzJcgybFkw8Z5x")
        params['remoteip'] = self.request.META['REMOTE_ADDR']
        resp = requests.post('https://www.google.com/recaptcha/api/verify', params=params)
        lines = resp.text.split('\n')
        if not lines[0].startswith('false'):
            return True
        return False

    def clean(self):
        if not self.verify_captcha():
            self.add_error('Captcha', "You did not complete the CAPTCHA correctly. "
                                      "Please try again.")

    def clean_password2(self):
        data = self.cleaned_data
        if data["password1"] == data["password2"]:
            data["password"] = data["password1"]
            return data
        else:
            raise forms.ValidationError("Password must be confirmed")

    def save(self, *args, **kwargs):
        data = self.cleaned_data
        return create_account(
            email=data['email'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            superuser=False,
            password=data['password'],
            active=False,
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_first_name(self):
        data = self.cleaned_data['first_name']
        if len(data.strip()) == 0:
            raise forms.ValidationError("First name is a required field.")
        return data

    def clean_last_name(self):
        data = self.cleaned_data['last_name']
        if len(data.strip()) == 0:
            raise forms.ValidationError("Last name is a required field.")
        return data

    def clean_email(self):
        data = self.cleaned_data['email']
        if len(data.strip()) == 0:
            raise forms.ValidationError("Email is a required field.")
        return data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user', 'public', 'create_irods_user_account']

    def clean_organization(self):
        data = self.cleaned_data['organization']
        if len(data.strip()) == 0:
            raise forms.ValidationError("Organization is a required field.")
        return data

    def clean_country(self):
        data = self.cleaned_data['country']
        if len(data.strip()) == 0:
            raise forms.ValidationError("Country is a required field.")
        return data

    def clean_state(self):
        data = self.cleaned_data['state']
        if len(data.strip()) == 0:
            raise forms.ValidationError("State is a required field.")
        return data
