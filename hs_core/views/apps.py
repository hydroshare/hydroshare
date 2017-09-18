from django.views.generic import TemplateView

from hs_tools_resource.models import ToolResource

APPROVED_APPLICATIONS = [694]

class AppsView(TemplateView):
    template_name = "pages/apps.html"

    def get_context_data(self, **kwargs):
        context = super(AppsView, self).get_context_data(**kwargs)
        webapp_resources = ToolResource.objects.all()

        final_resource_list = []
        for resource in webapp_resources:
            if resource.metadata.app_icon and resource.metadata.app_home_page_url: # \
                # and resource.id in APPROVED_APPLICATIONS:
                    final_resource_list.append(resource)

        context['webapp_resources'] = final_resource_list
        return context