from json import dumps

from django.contrib.auth.models import User
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import redirect

from mezzanine.generic.views import initial_validation
from mezzanine.utils.views import render, set_cookie, is_spam
from mezzanine.utils.cache import add_cache_bypass

from hs_core.hydroshare import get_resource_types
from hs_core.models import BaseResource
from theme.forms import ThreadedCommentForm
from theme.forms import RatingForm

class UserProfileView(TemplateView):
    template_name='accounts/profile.html'

    def get_context_data(self, **kwargs):
        if 'user' in kwargs:
            try:
                u = User.objects.get(pk=int(kwargs['user']))
            except:
                u = User.objects.get(username=kwargs['user'])

        else:
            try:
                u = User.objects.get(pk=int(self.request.GET['user']))
            except:
                u = User.objects.get(username=self.request.GET['user'])

        res = BaseResource.objects.filter(user=u)

        return {
            'u': u,
            'resources': res,
        }

# added by Hong Yi to address issue #186 to customize Mezzanine-based commenting form and view
def comment(request, template="generic/comments.html"):
    """
    Handle a ``ThreadedCommentForm`` submission and redirect back to its
    related object.
    """
    response = initial_validation(request, "comment")
    if isinstance(response, HttpResponse):
        return response
    obj, post_data = response
    form = ThreadedCommentForm(request, obj, post_data)
    if form.is_valid():
        url = obj.get_absolute_url()
        if is_spam(request, form, url):
            return redirect(url)
        comment = form.save(request)
        response = redirect(add_cache_bypass(comment.get_absolute_url()))
        # Store commenter's details in a cookie for 90 days.
        # for field in ThreadedCommentForm.cookie_fields:
        #     cookie_name = ThreadedCommentForm.cookie_prefix + field
        #     cookie_value = post_data.get(field, "")
        #     set_cookie(response, cookie_name, cookie_value)
        return response
    elif request.is_ajax() and form.errors:
        return HttpResponse(dumps({"errors": form.errors}))
    # Show errors with stand-alone comment form.
    context = {"obj": obj, "posted_comment_form": form}
    response = render(request, template, context)
    return response

# added by Hong Yi to address issue #186 to customize Mezzanine-based rating form and view
def rating(request):
    """
    Handle a ``RatingForm`` submission and redirect back to its
    related object.
    """
    response = initial_validation(request, "rating")
    if isinstance(response, HttpResponse):
        return response
    obj, post_data = response
    url = add_cache_bypass(obj.get_absolute_url().split("#")[0])
    response = redirect(url + "#rating-%s" % obj.id)
    rating_form = RatingForm(request, obj, post_data)
    if rating_form.is_valid():
        rating_form.save()
        if request.is_ajax():
            # Reload the object and return the rating fields as json.
            obj = obj.__class__.objects.get(id=obj.id)
            rating_name = obj.get_ratingfield_name()
            json = {}
            for f in ("average", "count", "sum"):
                json["rating_" + f] = getattr(obj, "%s_%s" % (rating_name, f))
            response = HttpResponse(dumps(json))
        ratings = ",".join(rating_form.previous + [rating_form.current])
        set_cookie(response, "mezzanine-rating", ratings)
    return response


from mezzanine.conf import settings
from django.contrib.messages import info, error
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from mezzanine.utils.email import send_verification_mail, send_approve_mail
from mezzanine.utils.urls import login_redirect, next_url
from mezzanine.utils.views import render

from .forms import SignupForm

def signup(request, template="accounts/account_signup.html"):
    """
    Signup form.
    """
    form = SignupForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_user = form.save()
        if not new_user.is_active:
            if settings.ACCOUNTS_APPROVAL_REQUIRED:
                send_approve_mail(request, new_user)
                info(request, _("Thanks for signing up! You'll receive "
                                "an email when your account is activated."))
            else:
                send_verification_mail(request, new_user, "signup_verify")
                info(request, _("A verification email has been sent with "
                                "a link for activating your account."))
            return redirect(next_url(request) or "/")
        else:
            info(request, _("Successfully signed up"))
            auth_login(request, new_user)
            return login_redirect(request)
    context = {"form": form, "title": _("Sign up")}
    return render(request, template, context)
