from django.shortcuts import render
#import models if necessary

def index(request):
    return render(request, 'index.html')

def resource_landing(request):
    return render(request, 'resource_landing.html')

def dashboard(request):
    return render(request, 'dashboard.html')
