from django.shortcuts import render
from django.views.generic import TemplateView


class AtlasSearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        target_origin = request.scheme + "://" + request.get_host()
        iframe_src = target_origin + "/discover/"
        if request.META.get('QUERY_STRING'):
            iframe_src += "?" + request.META['QUERY_STRING']
        context = {"targetOrigin": target_origin, "iframeSrc": iframe_src}
        return render(request, 'pages/search.html', context)
