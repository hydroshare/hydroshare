from django.shortcuts import render
from django.db.models import Q

from hs_core.hydroshare.utils import get_resource_types


def sitemap(request):
    resource_types = (
        (rt.__name__, {
            "resources": rt.objects.filter(Q(raccess__public=True) | Q(raccess__discoverable=True)),
        })
        for rt in get_resource_types()
    )
    return render(request, "sitemap.html", {
        "resource_types": resource_types,
    })
