from django.shortcuts import render


def init_explore(request):
    return render(request, 'recommendations.html', {})
