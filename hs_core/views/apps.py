from django.views.generic import TemplateView

from hs_tools_resource.models import ToolResource


class AppsView(TemplateView):
    template_name = "pages/apps.html"

    def get_context_data(self, **kwargs):
        context = super(AppsView, self).get_context_data(**kwargs)

        context['webapp_resources'] = ToolResource.get_approved_apps()
        return context
