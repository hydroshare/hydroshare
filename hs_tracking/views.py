import csv
import urllib.parse
from io import StringIO

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from . import models as hs_tracking
from .models import Session, Variable
from .utils import authentic_redirect_url, get_std_log_fields


class AppLaunch(TemplateView):

    def get(self, request, **kwargs):
        # get the query parameters and remove the redirect url b/c
        # we don't need to log this.
        querydict = dict(request.GET)
        url = querydict.pop('url', [None])[0]

        if not authentic_redirect_url(url):
            return HttpResponseForbidden()

        # encode url placeholder values received from the front-end
        url_placeholders = ["HS_JS_AGG_KEY", "HS_JS_MAIN_FILE_KEY", "HS_JS_FILE_KEY"]
        for placeholder in url_placeholders:
            placeholder_value = querydict.pop(placeholder, [''])[0]
            if placeholder in url:
                encoded_value = urllib.parse.quote(placeholder_value)
                url = url.replace(placeholder, encoded_value)

        # log app launch details if user is logged in
        if request.user.is_authenticated:
            # get user session and standard fields
            session = Session.objects.for_request(request, request.user)
            fields = get_std_log_fields(request, session)

            # parse the query and param portions of the url
            purl = urllib.parse.urlparse(url)

            # extract the app url args so they can be logged
            app_args = urllib.parse.parse_qs(purl.query)

            # update the log fields with the extracted request and url params
            fields.update(querydict)
            fields.update(app_args)

            # clean up the formatting of the query and app arg dicts
            # i.e. represent lists in csv format without brackets [ ]
            # so that the log records don't need to be cleaned later.
            fields.update(dict((k, ','.join(v)) for k, v in list(fields.items())
                          if type(v) is list))

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
