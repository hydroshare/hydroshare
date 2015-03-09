# Create your views here.
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from hs_core.hydroshare import get_resource_types
from mezzanine.generic.views import initial_validation
from django.http import HttpResponse
from .forms import ThreadedCommentForm
from mezzanine.utils.views import render, set_cookie, is_spam
from django.shortcuts import redirect
from mezzanine.utils.cache import add_cache_bypass
from json import dumps

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

        resource_types = get_resource_types()
        res = []
        for Resource in resource_types:
            res.extend([r for r in Resource.objects.filter(user=u)])

        return {
            'u' : u,
            'resources' :  res
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