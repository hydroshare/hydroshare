import csv
from cStringIO import StringIO

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseRedirect

from . import models as hs_tracking
from .models import Session, Variable
from .utils import get_std_log_fields


class AppLaunch(TemplateView):

    def get(self, request, **kwargs):

        # get the url or hydroshare.org if one is not provided.
        url = request.GET.get('url', 'http://www.hydroshare.org')

        # log app launch details if user is logged in
        if hasattr(request, 'user'):

            # get user session and standard fields
            session = Session.objects.for_request(request, request.user)
            fields = get_std_log_fields(request, session)

            # get extra app related fields, e.g. params in the app redirect
            fields['name'] = request.GET.get('name', 'Not Provided')
            if '?' in url:
                app_args = url.split('?')[1]
                arg_dict = dict(item.split("=") for item in app_args.split("&"))
                fields.update(arg_dict)

            # format and save the log message
            msg = Variable.format_kwargs(**fields)
            session.record('app_launch', value=msg)

        return HttpResponseRedirect(url)


class UseTrackingView(TemplateView):
    template_name = 'hs_tracking/tracking.html'

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
        w.writerow(
            ['visitor', 'session', 'session start', 'timestamp', 'variable', 'type', 'value'])
        variables = hs_tracking.Variable.objects.all().order_by('timestamp')

        for v in variables:
            row = [v.session.visitor.id, v.session.id, v.session.begin, v.timestamp,
                   v.name, v.get_type_display(), v.value]
            w.writerow(row)
        f.seek(0)
        return HttpResponse(f.read(), content_type="text/csv")
