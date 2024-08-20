from django.conf.urls import url
from django_irods.views import rest_check_task_status

urlpatterns = [
    # for REST API poll
    url(r'^rest_check_task_status/(?P<task_id>[A-z0-9\-]+)$',
        rest_check_task_status,
        name='rest_check_task_status'),
]
