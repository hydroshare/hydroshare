from django.urls import path

from .views import DiscoverySearchMoreView, DiscoverySearchPageView, DiscoverySearchResultsView

app_name = "discovery"

urlpatterns = [
    path("search-v2/", DiscoverySearchPageView.as_view(), name="page"),
    path("search-v2/results/", DiscoverySearchResultsView.as_view(), name="results"),
    path("search-v2/more/", DiscoverySearchMoreView.as_view(), name="more"),
]
