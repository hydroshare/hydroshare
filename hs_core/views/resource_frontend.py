from hs_core.models import BaseResource, get_permissions_context
from hs_core.page_processors import resource_detail_context, PageMock
from django.shortcuts import get_object_or_404, render

def resource_detail(request, short_id):
    base_resource = get_object_or_404(BaseResource, short_id=short_id)
    context = {}
    context.update(resource_detail_context(request, base_resource))
    context.update(get_permissions_context(request, base_resource))
    context.update({
        'page': PageMock(base_resource),
        'cm': base_resource,
        'res': base_resource,
    })
    return render(request, template_name='nopages/genericresource.html', context=context)