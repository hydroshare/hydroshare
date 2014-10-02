from django.http import HttpResponse
from django.views.generic import View
from django import forms as f
from lxml import etree
import pprint
from ga_ows import utils
import json
import re

from ga_ows.utils import CaseInsensitiveDict, MultipleValueField

def get_filter_params(ciargs):
    """filters can either be specified as JSON or they can be specified as keyword args prefixed by a single underscore, _"""
    ret = {}
    for arg in filter(lambda x: x.startswith('_'), ciargs.keys()):
        ret[arg[1:]] = ciargs[arg]
    return ret

class OWSCompositeException(Exception):
    """Composite OWS Exception for raising more than one exception at once"""

    def __init__(self, *exceptions):
        super(OWSCompositeException, self).__init__()
        self.exceptions = exceptions

    def xml(self, extend=False):
        exn = etree.Element("ExceptionReport", nsmap={
            #    'xmlns' : "http://www.opengis.net/ows/1.1",
            #    'xsi' : "http://www.w3.org/2001/XMLSchema-instance",
        })
        exn.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = "http://www.opengis.net/ows/1.1owsExceptionReport.xsd"
        exn.attrib['version']="1.0.0"
        exn.attrib['lang'] = "en"
        exncode = etree.SubElement(exn, 'Exception')
        exncode.attrib['exceptionCode'] = self.__class__.__name__
        exncode.attrib['locator'] = self.locator
        if extend:
            exncode.text = self.__str__()
        return etree.tostring(exn, pretty_print=True)

    def __str__(self):
        return ''.join(["""<<<EXCEPTION_REPORT\n""",
        '---\n'.join(["""{doc}

        {args}

        {kwargs}
        """.format(
            doc=self.__doc__,
            args=pprint.pformat(e.vargs, indent=4),
            kwargs=pprint.pformat(e.kwargs, indent=4)
        ) for e in self.exceptions]),
        "\nEXCEPTION_REPORT;"])

class OWSException(Exception):
    """Base exception class for all OWS exceptions.  Supports XML rendering."""

    @classmethod
    def at(cls, loc, *args, **kwargs):
        """A factory method that fills in the "locator" property standard to OGC service exceptions"""
        self = cls(*args, **kwargs)
        self.locator = loc
        return self

    def __init__(self, *args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)
        self.vargs = args
        self.kwargs = kwargs
        self._locator = ""

    @property
    def locator(self):
        return self._locator

    @locator.setter
    def locator(self, l):
        self._locator = l

    def __str__(self):
        return """{doc}

        {args}

        {kwargs}
        """.format(
            doc=self.__doc__,
            args=pprint.pformat(self.vargs, indent=4),
            kwargs=pprint.pformat(self.kwargs, indent=4)
        )

    def xml(self, extend=False):
        """XML serialization for the exception using OGC standards with an optional extension to put the exception code
        in the Exception element's text
        """
        exn = etree.Element("ExceptionReport", nsmap={
        #    'xmlns' : "http://www.opengis.net/ows/1.1",
        #    'xsi' : "http://www.w3.org/2001/XMLSchema-instance",
        })
        exn.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = "http://www.opengis.net/ows/1.1owsExceptionReport.xsd"
        exn.attrib['version']="1.0.0"
        exn.attrib['lang'] = "en"
        exncode = etree.SubElement(exn, 'Exception')
        exncode.attrib['exceptionCode'] = self.__class__.__name__
        exncode.attrib['locator'] = self.locator
        if extend:
            exncode.text = self.__str__()
        return etree.tostring(exn, pretty_print=True)

class MissingParameterValue(OWSException):
    """ Operation request does not include a parameter value"""

class InvalidParameterValue(OWSException):
    """Operation request contains an invalid parameter value"""

class VersionNegotiationFailed(OWSException):
    """List of versions in 'AcceptVersions' parameter value, in GetCapabilities operation request, did not include any version supported by this server"""

class InvalidUpdateSequence(OWSException):
    """Value of (optional) updateSequence parameter, in GetCapabilities operation request, is greater than current value of service metadata updateSequence number"""

class NoApplicableCode(OWSException):
    """No other exceptionCode specified by this service and server applies to this exception"""

class RequestForm(f.Form):
    """
    Fun little class that gives a "create" classmethod to Form subclasses.  Create automatically calls
    from_request on every superclass in the MRO.  The point of this is to use forms as mixins where each form
    populates itself from a dictionary with possible default values.
    """
    @classmethod
    def create(cls, request):

        for c in cls.mro():
            if 'from_request' in c.__dict__:
                c.from_request(request)
        frm = cls(request)
        if not frm.is_valid():
            raise InvalidParameterValue.at(str(frm.errors))
        frm.all_parameters = request
        return frm


class CommonParameters(RequestForm):
    """A form specifying the parameters that are a common part of every request"""
    service = f.CharField()
    version = f.CharField()
    request = f.CharField()

    @classmethod
    def from_request(cls, request):
        if 'service' not in request:
            raise MissingParameterValue.at("service")
        elif 'version' not in request:
            raise MissingParameterValue.at('version')
        elif 'request' not in request:
            raise MissingParameterValue.at('request')

class GetCapabilitiesMixin(object):
    """Class-based view mixin for parsing GetCapabilitles requests"""

    #: A request object containing .service, .accepted_versions, .sections, .accepted_formats, and .update_sequence.  See the OWS standard document for more details

    class Parameters(RequestForm):
        service = f.CharField()
        accepted_versions = MultipleValueField()
        accepted_formats = MultipleValueField()
        sections = MultipleValueField(required=False)
        update_sequence = f.CharField(required=False)

        @classmethod
        def from_request(cls, request):
            request['service'] = request['service']
            request['accepted_versions'] = request.get('acceptversions','2.0.0').split(',')
            request['accepted_formats'] = request.get('acceptformats','text/xml').split(',')
            request['update_sequence'] = request.get('updatesequence')
            request['sections'] = request.getlist('sections')

    def get_capabilities_response(self, request, parameters):
        """Subclasses should implement this method.

        :param request: The actual request object.
        :param parameters: a GetCapabilities.Parameters object

        """
        raise NotImplemented("Implementor should define a way of handling a GetCapabilitiesRequest in the subclass")

    def GetCapabilities(self, request, kwargs):
        """Assumes a view that delegates service requests, such as ga_ows.views.wms.WMS.  This can just be dropped into that kind of service."""

        if 'xml' in kwargs:
            req = self._parse_xml_GetCapabilities(kwargs['xml'])
        else:
            req =  GetCapabilitiesMixin.Parameters.create(kwargs)

        return self.get_capabilities_response(request, req)

    def _parse_xml_GetCapabilities(self, root):
        """A document that should parse::

            <?xml version="1.0" encoding="UTF-8"?>
            <GetCapabilities xmlns="http://www.opengis.net/ows/1.1"
            xmlns:ows="http://www.opengis.net/ows/1.1"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.opengis.net/ows/1.1
            fragmentGetCapabilitiesRequest.xsd" service="WCS"
            updateSequence="XYZ123">
               <!-- Maximum example for WCS. Primary editor: Arliss Whiteside -->
               <AcceptVersions>
                  <Version>1.0.0</Version>
                  <Version>0.8.3</Version>
               </AcceptVersions>
               <Sections>
                  <Section>Contents</Section>
               </Sections>
               <AcceptFormats>
                  <OutputFormat>text/xml</OutputFormat>
               </AcceptFormats>
            </GetCapabilities>
        """
        service = root.attrib['service']
        updateSequence = None
        if 'updateSequence' in root.attrib:
            updateSequence = root.attrib['updateSequence']
        accepted_versions = []
        accepted_formats = []
        sections = []
        for child in root.iter(tag=etree.Element):
            if child.tag.endswith('Version'):
                accepted_versions.append(child.text)
            if child.tag.endswith('Section'):
                sections.append(child.text)
            if child.tag.endswith('Format'):
                accepted_formats.append(child.text)

        if not service:
            raise MissingParameterValue.at('service')
        else:
            return GetCapabilitiesMixin.Parameters.create(CaseInsensitiveDict({
                "service" : service,
                "acceptversions" : ','.join(accepted_versions),
                "sections" : ','.join(sections),
                "acceptformats" : ','.join(accepted_formats),
                "updatesequence" : updateSequence}.items()))


class OWSMixinBase(object):
    adapter = None

class GetValidTimesMixin(OWSMixinBase):
    class Parameters(CommonParameters):
        callback = f.CharField(required=False)
        layers = utils.MultipleValueField()

        @classmethod
        def from_request(cls, request):
            request['layers'] = request.get('layers', '').split(',')
            request['callback'] = request.get('callback', None)
            if not request['callback']:
                request['callback'] = request.get('jsonp', None)


    def GetValidTimes(self, r, kwargs):
        """Vendor extension that returns valid timestamps in json format"""
        parms = GetValidTimesMixin.Parameters.create(kwargs)
        if 'filter' in kwargs:
            parms.cleaned_data['filter'] = json.loads(kwargs['filter'])
        else:
            parms.cleaned_data['filter'] = get_filter_params(kwargs)

        if 'callback' in parms.cleaned_data and parms.cleaned_data['callback']:
            return HttpResponse("{callback}({js})".format(
                callback=kwargs['callback'],
                js=json.dumps([t.strftime('%Y.%m.%d-%H:%M:%S.%f') for t in self.adapter.get_valid_times(**parms.cleaned_data)]), mimetype='test/jsonp'
            ))
        else:
            return HttpResponse(json.dumps([t.strftime('%Y.%m.%d-%H:%M:%S.%f') for t in self.adapter.get_valid_times(**parms.cleaned_data)]), mimetype='application/json')

class GetValidVersionsMixin(OWSMixinBase):
    class Parameters(CommonParameters):
        callback = f.CharField(required=False)
        layers = utils.MultipleValueField()

        @classmethod
        def from_request(cls, request):
            request['layers'] = request.get('layers', '').split(',')
            request['callback'] = request.get('callback', None)
            if not request['callback']:
                request['callback'] = request.get('jsonp', None)

    def GetValidVersions(self, r, kwargs):
        """Vendor extension that returns valid version bands in json format"""
        parms = GetValidTimesMixin.Parameters.create(kwargs)
        if 'filter' in kwargs:
            parms.cleaned_data['filter'] = json.loads(kwargs['filter'])
        else:
            parms.cleaned_data['filter'] = get_filter_params(kwargs)

        if 'callback' in parms.cleaned_data and parms.cleaned_data['callback']:
            return HttpResponse("{callback}({js})".format(
                callback=kwargs['callback'],
                js=json.dumps([t for t in self.adapter.get_valid_versions(**parms.cleaned_data)]), mimetype='test/jsonp'
            ))
        else:
            return HttpResponse(json.dumps([t for t in self.adapter.get_valid_versions(**parms.cleaned_data)]), mimetype='application/json')

class GetValidElevationsMixin(OWSMixinBase):
    class Parameters(CommonParameters):
        callback = f.CharField(required=False)
        layers = utils.MultipleValueField()

        @classmethod
        def from_request(cls, request):
            request['layers'] = request.get('layers', '').split(',')
            request['callback'] = request.get('callback', None)
            if not request['callback']:
                request['callback'] = request.get('jsonp', None)

    def GetValidElevations(self, r, kwargs):
        """Vendor extension that returns valid elevation bands in json format"""
        parms = GetValidTimesMixin.Parameters.create(kwargs)
        if 'filter' in kwargs:
            parms.cleaned_data['filter'] = json.loads(kwargs['filter'])
        else:
            parms.cleaned_data['filter'] = get_filter_params(kwargs)

        if 'callback' in parms.cleaned_data:
            return HttpResponse("{callback}({js})".format(
                callback=kwargs['callback'],
                js=json.dumps([t for t in self.adapter.get_valid_elevations(**parms.cleaned_data)]), mimetype='test/jsonp'
            ))
        else:
            return HttpResponse(json.dumps([t for t in self.adapter.get_valid_elevations(**parms.cleaned_data)]), mimetype='application/json')


class OWSView(View, GetCapabilitiesMixin):
    """A generic view for an OWS webservice.  Includes the GetCapabilities mixin."""

    #: whether or not the Exception tag in the exception xml should contain a pretty-printed version of the exception.
    #: defaults to true, but should be set to false if you anticipate standards-strict clients.  In practice, though
    #: you almost never get these
    extended_exceptions = True

    def _parse_xml_Request(self, raw_post_data):
        root = etree.fromstring(raw_post_data)
        request = re.sub('{[^}]}', '', root.tag)
        return request, root

    def dispatch(self, request, *args, **kwargs):
        ciargs = CaseInsensitiveDict(request.REQUEST.items())

        try:
            if 'request' not in ciargs:
                if request.method == 'POST':
                    try:
                        action, xml = self._parse_xml_Request(request.raw_post_data)
                        return self.__getattribute__(action)(request, xml=xml)
                    except Exception:
                        raise MissingParameterValue.at('request')
                else:
                    raise MissingParameterValue.at('request')
            else:
                return self.__getattribute__(ciargs['request'])(request, ciargs)
        except OWSException as ex:
            return HttpResponse(ex.xml(extend=self.extended_exceptions), mimetype='text/xml')
