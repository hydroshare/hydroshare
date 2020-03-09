from django.http import HttpResponse

# Create your views here.


def datatest(request):
    return HttpResponse("<h1>data test</h1>\n", 200)
