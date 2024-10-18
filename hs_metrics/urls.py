from django.urls import path

from hs_metrics import views

urlpatterns = [
    # users API

    path('metrics/', views.HydroshareSiteMetrics.as_view()),

]
