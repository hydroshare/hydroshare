from django.contrib.auth.models import User
from django.views.generic import TemplateView


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
