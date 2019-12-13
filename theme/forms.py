import requests

from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django_comments.signals import comment_was_posted
from django_comments.forms import CommentSecurityForm
from django_comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils import timezone
from django.contrib.auth.models import User

from mezzanine.core.forms import Html5Mixin
from mezzanine.generic.models import ThreadedComment, Rating
from mezzanine.utils.views import ip_for_request
from mezzanine.utils.email import split_addresses, send_mail_template
from mezzanine.utils.cache import add_cache_bypass
from mezzanine.conf import settings

from .models import UserProfile
from hs_core.hydroshare.users import create_account
from hs_core.templatetags.hydroshare_tags import best_name
from hs_core.models import Party

from hydroshare import settings as hydroshare_settings

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)


# This form.py is added by Hong Yi for customizing comments in HydroShare
# as part of effort to address issue https://github.com/hydroshare/hydroshare/issues/186
# In particular, we want to remove name, email, and url fields and
# want to link comments to user profile
class CommentDetailsForm(CommentSecurityForm):
    """
    Handles the specific details of the comment (name, comment, etc.).
    """
    comment = forms.CharField(label=_('Comment'), widget=forms.Textarea,
                              max_length=COMMENT_MAX_LENGTH)

    def get_comment_object(self):
        """
        Return a new (unsaved) comment object based on the information in this
        form. Assumes that the form is already validated and will throw a
        ValueError if not.

        Does not set any of the fields that would come from a Request object
        (i.e. ``user`` or ``ip_address``).
        """
        if not self.is_valid():
            raise ValueError("get_comment_object may only be called on valid forms")

        CommentModel = self.get_comment_model()
        new = CommentModel(**self.get_comment_create_data())
        new = self.check_for_duplicate_comment(new)

        return new

    def get_comment_model(self):
        """
        Get the comment model to create with this form. Subclasses in custom
        comment apps should override this, get_comment_create_data, and perhaps
        check_for_duplicate_comment to provide custom comment models.
        """
        return Comment

    def get_comment_create_data(self):
        """
        Returns the dict of data to be used to create a comment. Subclasses in
        custom comment apps that override get_comment_model can override this
        method to add extra fields onto a custom comment model.
        """
        return dict(
            content_type=ContentType.objects.get_for_model(self.target_object),
            object_pk=force_text(self.target_object._get_pk_val()),
            comment=self.cleaned_data["comment"],
            submit_date=timezone.now(),
            site_id=settings.SITE_ID,
            is_public=True,
            is_removed=False,
        )

    def check_for_duplicate_comment(self, new):
        """
        Check that a submitted comment isn't a duplicate. This might be caused
        by someone posting a comment twice. If it is a dup, silently return the *previous* comment.
        """
        possible_duplicates = self.get_comment_model()._default_manager.using(
            self.target_object._state.db
        ).filter(
            content_type=new.content_type,
            object_pk=new.object_pk,
            user_name=new.user_name,
            user_email=new.user_email,
            user_url=new.user_url,
        )
        for old in possible_duplicates:
            if old.submit_date.date() == new.submit_date.date() and old.comment == new.comment:
                return old

        return new


class CommentForm(CommentDetailsForm):
    honeypot = forms.CharField(required=False,
                               label=_('If you enter anything in this field '
                                       'your comment will be treated as spam'))

    def clean_honeypot(self):
        """Check that nothing's been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]
        if value:
            raise forms.ValidationError(self.fields["honeypot"].label)
        return value


# added by Hong Yi for customizing THreadedCommentForm
class ThreadedCommentForm(CommentForm, Html5Mixin):

    def __init__(self, request, *args, **kwargs):
        """
        Set some initial field values from cookies or the logged in
        user, and apply some HTML5 attributes to the fields if the
        ``FORMS_USE_HTML5`` setting is ``True``.
        """
        kwargs.setdefault("initial", {})
        super(ThreadedCommentForm, self).__init__(*args, **kwargs)

    def get_comment_model(self):
        """
        Use the custom comment model instead of the built-in one.
        """
        return ThreadedComment

    def save(self, request):
        """
        Saves a new comment and sends any notification emails.
        """
        comment = self.get_comment_object()
        obj = comment.content_object
        if request.user.is_authenticated():
            comment.user = request.user
            comment.user_name = best_name(comment.user)

        comment.by_author = request.user == getattr(obj, "user", None)
        comment.ip_address = ip_for_request(request)
        comment.replied_to_id = self.data.get("replied_to")
        comment.save()
        comment_was_posted.send(sender=comment.__class__, comment=comment,
                                request=request)
        notify_emails = split_addresses(settings.COMMENTS_NOTIFICATION_EMAILS)
        notify_emails.append(obj.user.email)
        reply_to_comment = comment.replied_to
        if reply_to_comment is not None:
            notify_emails.append(reply_to_comment.user.email)
        if notify_emails:
            subject = "[HydroShare Support] New comment by {c_name} for: {res_obj}".format(
                c_name=comment.user_name, res_obj=str(obj))
            context = {
                "comment": comment,
                "comment_url": add_cache_bypass(comment.get_absolute_url()),
                "request": request,
                "obj": obj,
            }
            send_mail_template(subject, "email/comment_notification",
                               settings.DEFAULT_FROM_EMAIL, notify_emails,
                               context)

        return comment


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
                rating_manager.add(rating_instance, bulk=False)
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
            rating_manager.add(rating_instance, bulk=False)
        return rating_instance


class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ['last_login', 'date_joined', 'password']

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput())
    organization = forms.CharField(required=True)

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(SignupForm, self).__init__(*args, **kwargs)

    def verify_captcha(self):
        url = hydroshare_settings.RECAPTCHA_VERIFY_URL
        values = {
            'secret': hydroshare_settings.RECAPTCHA_SECRET_KEY,
            'response': self.request.POST.get('g-recaptcha-response')
        }
        response = requests.post(url, values)
        result = response.json()
        if(result["success"]):
            return (True, [])

        return (False, result["error-codes"])

    def clean(self):
        success, error_codes = self.verify_captcha()

        if not success:
            self.add_error(None, " ".join(error_codes))

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
            organization=data['organization'],
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
    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['identifiers'].required = False

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

    def clean_identifiers(self):
        data = self.cleaned_data['identifiers']
        return Party.validate_identifiers(data)
