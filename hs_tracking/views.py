import csv
from io import StringIO
import urllib.parse

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages

from . import models as hs_tracking
from .models import Session, Variable
from .utils import get_std_log_fields, authentic_redirect_url
from hs_tools_resource.utils import do_work_when_launching_app_as_needed, WebAppLaunchException, split_url


class AppLaunch(TemplateView):

    def get(self, request, **kwargs):
        # get the query parameters and remove the redirect url b/c
        # we don't need to log this.
        querydict = dict(request.GET)
        url = querydict.pop('url', [None])[0]

        if not authentic_redirect_url(url):
            return HttpResponseForbidden()
        # do work as needed when launching web app
        res_id = querydict.pop('res_id', [''])[0]
        tool_res_id = querydict.pop('tool_res_id', [''])[0]
        if res_id and tool_res_id:
            try:
                do_work_when_launching_app_as_needed(tool_res_id, res_id, request.user)
            except WebAppLaunchException as ex:
                messages.warning(request, str(ex))
                return HttpResponseRedirect(request.META['HTTP_REFERER'])

        # log app launch details if user is logged in
        if request.user.is_authenticated():
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
                          if type(v) == list))

            # format and save the log message
            msg = Variable.format_kwargs(**fields)
            session.record('app_launch', value=msg)

        # encode url before redirect
        path, query = split_url(url)
        path = urllib.parse.quote(path).replace('%3A', ':')
        if query:
            query = urllib.parse.quote(query, safe='')
            url = "{}?{}".format(path, query)
        else:
            url = path

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
