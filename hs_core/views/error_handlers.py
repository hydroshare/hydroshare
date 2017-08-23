from django.shortcuts import render
from hs_core.page_processors import PageMock

def bad_request(request):
    return render(request, template_name='400.html', context={'page': PageMock()})

def page_not_found(request):
    return render(request, template_name='404.html', context={'page': PageMock()})

def permission_denied(request):
    return render(request, template_name='403.html', context={'page': PageMock()})

def server_error(request):
    return render(request, template_name='500.html', context={'page': PageMock()})