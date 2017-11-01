import csv
from cStringIO import StringIO

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseRedirect

from . import models as hs_tracking
from .models import Session, Variable
from .utils import get_std_log_fields

import urlparse


class AppLaunch(TemplateView):

    def get(self, request, **kwargs):

        # get the query parameters and remove the redirect url b/c
        # we don't need to log this.
        querydict = dict(request.GET)
        url = querydict.pop('url')[0]

        # log app launch details if user is logged in
        if request.user.is_authenticated():

            # get user session and standard fields
            session = Session.objects.for_request(request, request.user)
            fields = get_std_log_fields(request, session)

            # parse the query and param portions of the url
            purl = urlparse.urlparse(url)

            # extract the app url args so they can be logged
            app_args = urlparse.parse_qs(purl.query)

            # update the log fields with the extracted request and url params
            fields.update(querydict)
            fields.update(app_args)

            # clean up the formatting of the query and app arg dicts
            # i.e. represent lists in csv format without brackets [ ]
            # so that the log records don't need to be cleaned later.
            fields.update(dict((k, ','.join(v)) for k, v in fields.iteritems()
                          if type(v) == list))

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
