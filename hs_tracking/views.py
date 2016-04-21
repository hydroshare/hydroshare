import csv
from cStringIO import StringIO

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse

from . import models as hs_tracking


class UseTrackingView(TemplateView):
    template_name='hs_tracking/tracking.html'

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(UseTrackingView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        return {}


class VisitorProfileReport(TemplateView):

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(VisitorProfileReport, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        """Download a CSV report of use tracking data."""

        f = StringIO()
        w = csv.writer(f)
        w.writerow(hs_tracking.VISITOR_FIELDS)
        visitors = hs_tracking.Visitor.objects.all()

        for v in visitors:
            info = v.export_visitor_information()
            row = [info[field] for field in hs_tracking.VISITOR_FIELDS]
            w.writerow(row)
        f.seek(0)
        return HttpResponse(f.read(), content_type="text/csv")


class HistoryReport(TemplateView):

    # @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        return super(HistoryReport, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        """Download a CSV report of use tracking data."""

        f = StringIO()
        w = csv.writer(f)
        w.writerow(['visitor', 'session', 'session start', 'timestamp', 'variable', 'type', 'value'])
        variables = hs_tracking.Variable.objects.all().order_by('timestamp')

        for v in variables:
            row = [v.session.visitor.id, v.session.id, v.session.begin, v.timestamp, v.name, v.get_type_display(), v.value]
            w.writerow(row)
        f.seek(0)
        return HttpResponse(f.read(), content_type="text/csv")
