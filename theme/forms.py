import requests

from django import forms
from django.utils.translation import gettext, ugettext, ugettext_lazy as _
from django_comments.signals import comment_was_posted
from django_comments.forms import CommentSecurityForm
from django_comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_text
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

# from mezzanine.core.forms import Html5Mixin
from mezzanine.generic.models import ThreadedComment, Rating
from mezzanine.utils.views import ip_for_request
from mezzanine.utils.email import split_addresses, send_mail_template
from mezzanine.utils.cache import add_cache_bypass
from mezzanine.conf import settings

from .models import UserProfile, ProfileNotConfigured
# from .utils import unique_slug
from hs_core.hydroshare.users import create_account
from hs_core.templatetags.hydroshare_tags import best_name
from hs_core.models import Party

from hydroshare import settings as hydroshare_settings

COMMENT_MAX_LENGTH = getattr(settings, 'COMMENT_MAX_LENGTH', 3000)

_exclude_fields = tuple(getattr(settings,
                                "ACCOUNTS_PROFILE_FORM_EXCLUDE_FIELDS", ()))

if hydroshare_settings.ACCOUNTS_NO_USERNAME:
    # _exclude_fields += ("username",)
    username_label = _("Email address")
else:
    username_label = _("Username or email address")

# This form.py is added by Hong Yi for customizing comments in HydroShare
# as part of effort to address issue https://github.com/hydroshare/hydroshare/issues/186
# In particular, we want to remove name, email, and url fields and
# want to link comments to user profile


class Html5Mixin(object):
    """
    Mixin for form classes. Adds HTML5 features to forms for client
    side validation by the browser, like a "required" attribute and
    "email" and "url" input types.
    """

    def __init__(self, *args, **kwargs):
        super(Html5Mixin, self).__init__(*args, **kwargs)
        if hasattr(self, "fields"):
            first_field = None

            for name, field in self.fields.items():
                # Autofocus first non-hidden field
                if not first_field and not field.widget.is_hidden:
                    first_field = field
                    first_field.widget.attrs["autofocus"] = ""
                if settings.FORMS_USE_HTML5:
                    if isinstance(field, forms.EmailField):
                        self.fields[name].widget.input_type = "email"
                    elif isinstance(field, forms.URLField):
                        self.fields[name].widget.input_type = "url"
                if field.required:
                    self.fields[name].widget.attrs["required"] = ""

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


class LoginForm(Html5Mixin, forms.Form):
    """
    Fields for login.
    """
    username = forms.CharField(label=username_label)
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(render_value=False))

    def clean(self):
        """
        Authenticate the given username/email and password. If the fields
        are valid, store the authenticated user for returning via save().
        """
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        self._user = authenticate(username=username, password=password)
        if self._user is None:
            raise forms.ValidationError(
                             ugettext("Invalid username/email and password"))
        elif not self._user.is_active:
            raise forms.ValidationError(ugettext("Your account is inactive"))
        return self.cleaned_data

    def save(self):
        """
        Just return the authenticated user - used for logging in.
        """
        return getattr(self, "_user", None)


class SignupForm(forms.ModelForm):
    class Meta:
        model = User
        exclude = ['last_login', 'date_joined', 'password']

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput())
    organization = forms.CharField(required=True)
    user_type = forms.CharField(required=True)
    country = forms.CharField(label='Country', required=True)
    state = forms.CharField(label='State/Province', required=True)

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

    def clean_user_type(self):
        data = self.cleaned_data['user_type']
        if len(data.strip()) == 0:
            raise forms.ValidationError("User type is a required field.")
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
            user_type=data['user_type'],
            country=data['country'],
            state=data['state'],
            active=False,
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def clean_first_name(self):
        data = self.cleaned_data['first_name']
        return data.strip()

    def clean_last_name(self):
        data = self.cleaned_data['last_name']
        return data.strip()

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
        if data is None or len(data.strip()) == 0:
            raise forms.ValidationError("Organization is a required field.")
        return data

    def clean_country(self):
        data = self.cleaned_data['country']
        if data is None or len(data.strip()) == 0:
            raise forms.ValidationError("Country is a required field.")
        return data

    def clean_state(self):
        data = self.cleaned_data['state']
        if data is None or len(data.strip()) == 0:
            raise forms.ValidationError("State is a required field.")
        return data

    def clean_identifiers(self):
        data = self.cleaned_data['identifiers']
        return Party.validate_identifiers(data)


try:
    class ProfileFieldsForm(forms.ModelForm):
        class Meta:
            model = UserProfile
            exclude = ('user',) + _exclude_fields
except ProfileNotConfigured:
    pass


class ProfileForm(Html5Mixin, forms.ModelForm):
    """
    ModelForm for auth.User - used for signup and profile update.
    If a Profile model is defined via ``ACCOUNTS_PROFILE_MODEL``, its
    fields are injected into the form.
    """

    password1 = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label=_("Password (again)"), widget=forms.PasswordInput(render_value=False)
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username")
        exclude = _exclude_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signup = self.instance.id is None
        user_fields = {f.name for f in User._meta.get_fields()}
        try:
            self.fields["username"].help_text = gettext(
                "Only letters, numbers, dashes or underscores please"
            )
        except KeyError:
            pass
        for field in self.fields:
            # Make user fields required.
            if field in user_fields:
                self.fields[field].required = True
            # Disable auto-complete for password fields.
            # Password isn't required for profile update.
            if field.startswith("password"):
                self.fields[field].widget.attrs["autocomplete"] = "off"
                self.fields[field].widget.attrs.pop("required", "")
                if not self._signup:
                    self.fields[field].required = False
                    if field == "password1":
                        self.fields[field].help_text = gettext(
                            "Leave blank unless you want " "to change your password"
                        )

        # Add any profile fields to the form.
        try:
            profile_fields_form = self.get_profile_fields_form()
            profile_fields = profile_fields_form().fields
            self.fields.update(profile_fields)
            # if not self._signup:
            #     user_profile = get_profile_for_user(self.instance)
            #     for field in profile_fields:
            #         value = getattr(user_profile, field)
            #         # Check for multiple initial values, i.e. a m2m field
            #         if isinstance(value, Manager):
            #             value = value.all()
            #         self.initial[field] = value
        except ProfileNotConfigured:
            pass

    # def clean_username(self):
    #     """
    #     Ensure the username doesn't exist or contain invalid chars.
    #     We limit it to slugifiable chars since it's used as the slug
    #     for the user's profile view.
    #     """
    #     username = self.cleaned_data.get("username")
    #     if username.lower() != slugify(username).lower():
    #         raise forms.ValidationError(
    #             gettext(
    #                 "Username can only contain letters, numbers, dashes "
    #                 "or underscores."
    #             )
    #         )
    #     lookup = {"username__iexact": username}
    #     try:
    #         User.objects.exclude(id=self.instance.id).get(**lookup)
    #     except User.DoesNotExist:
    #         return username
    #     raise forms.ValidationError(gettext("This username is already registered"))
    #
    # def clean_password2(self):
    #     """
    #     Ensure the password fields are equal, and match the minimum
    #     length defined by ``ACCOUNTS_MIN_PASSWORD_LENGTH``.
    #     """
    #     password1 = self.cleaned_data.get("password1")
    #     password2 = self.cleaned_data.get("password2")
    #
    #     if password1:
    #         errors = []
    #         if password1 != password2:
    #             errors.append(gettext("Passwords do not match"))
    #         if len(password1) < settings.ACCOUNTS_MIN_PASSWORD_LENGTH:
    #             errors.append(
    #                 gettext("Password must be at least %s characters")
    #                 % settings.ACCOUNTS_MIN_PASSWORD_LENGTH
    #             )
    #         if errors:
    #             self._errors["password1"] = self.error_class(errors)
    #     return password2
    #
    # def clean_email(self):
    #     """
    #     Ensure the email address is not already registered.
    #     """
    #     email = self.cleaned_data.get("email")
    #     qs = User.objects.exclude(id=self.instance.id).filter(email=email)
    #     if len(qs) == 0:
    #         return email
    #     raise forms.ValidationError(gettext("This email is already registered"))
    #
    # def save(self, *args, **kwargs):
    #     """
    #     Create the new user. If no username is supplied (may be hidden
    #     via ``ACCOUNTS_PROFILE_FORM_EXCLUDE_FIELDS`` or
    #     ``ACCOUNTS_NO_USERNAME``), we generate a unique username, so
    #     that if profile pages are enabled, we still have something to
    #     use as the profile's slug.
    #     """
    #
    #     kwargs["commit"] = False
    #     user = super().save(*args, **kwargs)
    #     try:
    #         self.cleaned_data["username"]
    #     except KeyError:
    #         if not self.instance.username:
    #             try:
    #                 username = (
    #                     "%(first_name)s %(last_name)s" % self.cleaned_data
    #                 ).strip()
    #             except KeyError:
    #                 username = ""
    #             if not username:
    #                 username = self.cleaned_data["email"].split("@")[0]
    #             qs = User.objects.exclude(id=self.instance.id)
    #             user.username = unique_slug(qs, "username", slugify(username))
    #     password = self.cleaned_data.get("password1")
    #     if password:
    #         user.set_password(password)
    #     elif self._signup:
    #         try:
    #             user.set_unusable_password()
    #         except AttributeError:
    #             # This could happen if using a custom user model that
    #             # doesn't inherit from Django's AbstractBaseUser.
    #             pass
    #     user.save()
    #
    #     try:
    #         profile = get_profile_for_user(user)
    #         profile_form = self.get_profile_fields_form()
    #         profile_form(self.data, self.files, instance=profile).save()
    #     except ProfileNotConfigured:
    #         pass
    #
    #     if self._signup:
    #         if (
    #             settings.ACCOUNTS_VERIFICATION_REQUIRED
    #             or settings.ACCOUNTS_APPROVAL_REQUIRED
    #         ):
    #             user.is_active = False
    #             user.save()
    #         else:
    #             token = default_token_generator.make_token(user)
    #             user = authenticate(
    #                 uidb36=int_to_base36(user.id), token=token, is_active=True
    #             )
    #     return user

    def get_profile_fields_form(self):
        try:
            return ProfileFieldsForm
        except NameError:
            raise ProfileNotConfigured
