"""
An implementation of OGC WFS 2.0.0 over the top of Django.  This module requires that OGR be installed and that you use
either the PostGIS or Spatialite backends to GeoDjango for the layers you are retrieving. The module provides a
generic view, :py:class:WFS that provides standard WFS requests and responses and :py:class:WFST that provides WFS +
Transactions.

This is an initial cut at WFS compatibility.  It is not perfect by any means, but it is a decent start.  To use WFS with
your application, you will either need to use a GeoDjango model or derive from :py:class:WFSAdapter and
wrap a model class with it. Most URL configs will look like this::

    url('r/wfs', WFS.as_view(model=myapp.models.MyGeoModel))

Models' Meta class can be modified to include attributes that can be picked up by the view as descriptive parameters
that will make it into the response of a GetCapabilities request.

The following features remain unimplemented:
    * Transactions
    * Creation and removal of stored queries
    * Resolution
    * The standard XML filter language (instead I intend to support OGR SQL and the Django filter language)
"""
from collections import namedtuple
from uuid import uuid4
from django.http import HttpResponse
from django.contrib.gis.db.models.query import GeoQuerySet
from django.contrib.gis.db.models import GeometryField
from django import forms as f
import json
from django.shortcuts import render_to_response
from ga_ows.views import common
from ga_ows.utils import MultipleValueField, BBoxField, CaseInsensitiveDict
from lxml import etree
from ga_ows.views.common import RequestForm, CommonParameters, GetCapabilitiesMixin
from osgeo import ogr
from django.conf import settings
from tempfile import gettempdir
from django.db import connections
import re
from lxml import etree
import os

#: Requests' Common Parameters
#: ===========================

class InputParameters(RequestForm):
    """

    """
    srs_name = f.CharField()
    input_format = f.CharField() # default should be "application/gml+xml; version=3.2"
    srs_format = f.CharField(required=False)

    @classmethod
    def from_request(cls, request):
        request['srs_name'] = request.get('srsname', 'EPSG:4326')
        request['input_format'] = request.get('inputformat', "application/gml+xml; version=3.2")

class PresentationParameters(RequestForm):
    count = f.IntegerField()
    start_index = f.IntegerField()
    max_features = f.IntegerField()
    output_format = f.CharField()

    @classmethod
    def from_request(cls, request):
        request['count'] = int(request.get('count', '1'))
        request['start_index'] = int(request.get('startindex','1'))
        request['max_features'] = int(request.get('maxfeatures', '1'))
        request['output_format'] = request.get('outputformat',"application/gml+xml; version=3.2")

class AdHocQueryParameters(RequestForm):
    type_names = MultipleValueField()
    aliases = MultipleValueField(required=False)
    filter = f.CharField(required=False)
    filter_language = f.CharField(required=False)
    resource_id = f.CharField(required=False)
    bbox = BBoxField()
    sort_by = f.CharField(required=False)

    @classmethod
    def from_request(cls, request):
        request['type_names'] = request.getlist('typenames')
        request['aliases'] = request.getlist('aliases')
        request['filter'] = request.get('filter')
        request['filter_language'] = request.get('filterlanguage')
        request['resource_id'] = request.get('resource_id')
        request['bbox'] = request.get('bbox')
        request['sort_by'] = request.get('sortby')

class StoredQueryParameters(RequestForm):
    stored_query_id = f.CharField(required=False)

    @classmethod
    def from_request(cls, request):
        request['stored_query_id'] = request.get('storedquery_id')

class GetFeatureByIdParameters(RequestForm):
    feature_id = f.CharField()

    @classmethod
    def from_request(cls, request):
        request['feature_id'] = request.get('id')

class ResolveParameters(RequestForm):
    resolve = f.CharField(required=False)
    resolve_depth = f.IntegerField()
    resolve_timeout = f.FloatField()

    @classmethod
    def from_request(cls, request):
        request['resolve'] = request.get('resolve')
        request['resolve_depth'] = int(request.get('resolve_depth','0'))
        request['resolve_timeout'] = float(request.get('resolve_timeout', '0'))


#: Exceptions
#: ==========

class CannotLockAllFeatures(common.OWSException):
    """A locking request with a lockAction of ALL failed to lock all the requested features."""

class DuplicateStoredQueryIdValue(common.OWSException):
    """The identifier specified for a stored query expression is a duplicate."""

class DuplicateStoredQueryParameterName(common.OWSException):
    """This specified name for a stored query parameter is already being used within the same stored query definition."""

class FeaturesNotLocked(common.OWSException):
    """For servers that do not support automatic data locking (see 15.2.3.1), this exception indicates that a transaction operation is modifying features that have not previously been locked using a LockFeature (see Clause 12) or GetFeatureWithLock (see Clause 13) operation."""

class InvalidLockId(common.OWSException):
    """The value of the lockId parameter on a Transaction operation is invalid because it was not generated by the server."""

class InvalidValue(common.OWSException):
    """A Transaction (see Clause 15) has attempted to insert or change the value of a data component in a way that violates the schema of the feature."""

class LockHasExpired(common.OWSException):
    """The specified lock identifier on a Transaction or LockFeature operation has expired and is no longer valid."""

class OperationParsingFailed(common.OWSException):
    """The request is badly formed and failed to be parsed by the server."""

class OperationProcessingFailed(common.OWSException):
    """An error was encountered while processing the operation."""

class ResponseCacheExpired(common.OWSException):
    """The response cache used to support paging has expired and the results are no longer available."""

class OperationNotSupported(common.OWSException):
    """The operation is not yet implemented"""

########################################################################################################################
# Adapter class
########################################################################################################################

#: Class for describing features.  A named tuple containing:
#:      * name : str - the feature type name.  this is what goes in the featureTypes parameter on a GetFeature request.
#:      * title : str - the human readable name for this feature type
#:      * abstract : str - a short description of this feature type, if necessary
#:      * keywords : list(str) - keywords associated with this feature_type
#:      * srs : str - the sptial reference system that is default for this feature type
#:      * bbox : (minx, miny, maxx, maxy) - the boundinb box for this feature type.  must be present and filled in WGS84
#:
FeatureDescription = namedtuple('FeatureDescription', ('ns', 'ns_name', 'name','title','abstract','keywords','srs','bbox', 'schema'))

#: A description of a stored-query parameter. A named tuple containing:
#:      * type : str - the parameter type
#:      * name : str - the parameter name (computer-readable)
#:      * title : str - the parameter name (human-readable)
#:      * abstract : str - a short description of the parameter
#:      * query_expression : :py:class:StoredQueryExpression
#:
StoredQueryParameter = namedtuple("StoredQueryParameter", ('type','name', 'title','abstract', 'query_expression'))

#: A description of how a stored query parameter should be filled in.  A named tuple containing:
#:      * text : str - template text for a query
#:      * language : str - the language the query is expressed in.
#:      * private : boolean - whether or not the query is private
#:      * return_feature_types : the comma-separated computer-readable names of the feature types that are returned
StoredQueryExpression = namedtuple("StoredQueryExpression", ('text', 'language', 'private', 'return_feature_types'))

#: A description of a stored query. A named tuple containing:
#:      * name : str - the computer-readable name of the stored query
#:      * title : str - the human-readable name of the stored query
#:      * feature_types : str - the comma-separated computer-readable names of the feature types that are returned
StoredQueryDescription = namedtuple("StoredQueryDescription", ('name', 'feature_types', 'title', 'parameters'))

class WFSAdapter(object):
    """
    This adapter should be defined by any class that needs to expose WFS services on its interface.  The adapter will
    be called with an object as its working object and will encapsulate all the functionality needed to expose that
    object via WFS using the ga_ows.WFSView class.
    """
    def get_feature_descriptions(self, request, *types):
        raise OperationNotSupported.at('GetFeatureDescription', 'Implementor should return list of FeatureDescriptions')

    def list_stored_queries(self, request):
        """Subclasses of this class may implement extra stored queries by creating methods
        matching the pattern::

            def SQ_{QueryName}(self, request, parms):
                pass

        where request and parms are the Django HTTPRequest object and parms are
        GetFeature parameters
        """
        queries = dict([(q[3:],[]) for q in filter(lambda x: x.startswith("SQ_"),
            reduce(
                list.__add__,
                [c.__dict__.keys() for c in self.__class__.mro()]
            )
        )])
        return queries

    def get_features(self, request, parms):
        raise OperationNotSupported.at('GetFeature', "Implementor is given a GetFeatures.Parameters object and should return an OGR dataset or a GeoDjango QuerySet")

    def supports_feature_versioning(self):
        return False

class GeoDjangoWFSAdapter(WFSAdapter):
    def __init__(self, models):
        self.models = {}
        self.srids = {}
        # NOTE this assumes that there will be only one geometry field per model.  This is of course not necessarily the case, but it works 95% of the time.
        self.geometries = {}
        for model in models:
            self.models[model._meta.app_label + ":" + model._meta.object_name] = model
            for field in model._meta.fields:
                if isinstance(field, GeometryField):
                    self.geometries[model._meta.app_label + ":" + model._meta.object_name] = field
                    self.srids[model._meta.app_label + ":" + model._meta.object_name] = field.srid

    def list_stored_queries(self, request):
        sq = super(GeoDjangoWFSAdapter, self).list_stored_queries(request)
        fts = list(self.models.keys())
        for k in sq.keys():
            sq[k] = StoredQueryDescription(name=k, feature_types=fts, title=k, parameters=[])
        return sq

    def get_feature_descriptions(self, request, *types):
        namespace = request.build_absolute_uri().split('?')[0] + "/schema" # todo: include https://bitbucket.org/eegg/django-model-schemas/wiki/Home

        for model in self.models.values():
            if model.objects.count() > 0:
                extent = model.objects.extent()
            else:
                extent = (0,0,0,0)

            yield FeatureDescription(
                ns=namespace,
                ns_name=model._meta.app_label,
                name=model._meta.object_name,
                abstract=model.__doc__,
                title=model._meta.verbose_name,
                keywords=[],
                srs=self.srids[model._meta.app_label + ":" + model._meta.object_name],
                bbox=extent,
                schema=namespace
            )

    def get_features(self, request, parms):
        if parms.cleaned_data['stored_query_id']:
            squid = "SQ_" + parms.cleaned_data['stored_query_id']
            try: 
                return self.__getattribute__(squid)(request, parms)
            except AttributeError:
                raise OperationNotSupported.at('GetFeatures', 'stored_query_id={squid}'.format(squid=squid))
        else:
            #try:
                return self.AdHocQuery(request, parms)
            #except KeyError as k:
            #    raise OperationProcessingFailed.at("GetFeatures", str(k))
            #except ValueError as v:
            #    raise OperationParsingFailed.at("GetFeatures", "filter language not supported or invalid JSON")

    def AdHocQuery(self, request, parms):
        type_names = parms.cleaned_data['type_names'] # only support one type-name at a time (model) for now
        #aliases = parms.cleaned_data['aliases'] # ignored for now
        flt = parms.cleaned_data['filter'] # filter should be in JSON 
        flt_lang = parms.cleaned_data['filter_language'] # only support JSON now
        #res_id = parms.cleaned_data['resource_id'] # ignored
        bbox = parms.cleaned_data['bbox'] 
        sort_by = parms.cleaned_data['sort_by']
        count = parms.cleaned_data['count']
        if not count:
            count = parms.cleaned_data['max_features']
        start_index = parms.cleaned_data['start_index']
        srs_name = parms.cleaned_data['srs_name'] # assume bbox is in this
        srs_format = parms.cleaned_data['srs_format'] # this can be proj, None (srid), srid, or wkt.
        
        model = self.models[type_names[0]] # support only the first type-name for now.
        geometry_field = self.geometries[type_names[0]]
        query_set = model.objects.all()

        if bbox:
            mnx, mny, mxx, mxy = bbox
            query_set.filter(**{ geometry_field.name + "__bboverlaps" :
                "POLYGON(({mnx} {mny}, {mxx} {mny}, {mxx} {mxy}, {mnx} {mxy}, {mnx} {mny}))".format(
                    mnx=mnx, 
                    mny=mny, 
                    mxx=mxx, 
                    mxy=mxy)
            })

        if flt:
            flt = json.loads(flt)
            query_set = query_set.filter(**flt)

        if sort_by and ',' in sort_by:
            sort_by = sort_by.split(',')
            query_set = query_set.order_by(*sort_by)
        elif sort_by:
            query_set = query_set.order_by(sort_by)

        if start_index and count:
            query_set = query_set[start_index:start_index+count]
        elif start_index:
            query_set = query_set[start_index:]
        elif count:
            query_set = query_set[:count]

        if srs_name:
            if (not srs_format or srs_format == 'srid') and srs_name != geometry_field.srid:
                if srs_name.lower().startswith('epsg:'):
                    srs_name = srs_name[5:]
                query_set.transform(int(srs_name))

        # TODO support proj and WKT formats by manually transforming geometries.
        # First create a list() from the queryset, then create SpatialReference objects for 
        # the source and dest.  Then import them from their corresponding SRS definitions
        # then loop over the list and transform each model instance's geometry record

        return query_set

    def SQ_GetFeatureById(self, request, parms):
        my_parms = GetFeatureByIdParameters.create(request.REQUEST)
        typename, pk =  my_parms.cleaned_data['feature_id'].split('.')
        return self.models[typename].objects.filter(pk=int(pk))



# WFS itself.  All the individual classes are defined as mixins for the sake of modularity and ease of debugging.

class WFSBase(object):
    """The base class for WFS mixins.  Makes sure that all mixins assume an adapter"""
    adapter = None

class DescribeFeatureTypeMixin(WFSBase):
    """
    Defines the DescribeFeatureType operation found in section 9 of the WFS standard
    """
    class Parameters(
        CommonParameters
    ):
        type_names = MultipleValueField()
        output_format = f.CharField()

        @classmethod
        def from_request(cls, request):
            request['type_names'] = request.getlist('typename') + request.getlist('typenames')
            request['output_format'] = request.get('outputformat', "application/gml+xml; version=3.2")


    def _parse_xml_DescribeFeatureType(self, request):
        """See section 9.4.2 of the OGC spec.  Note that the spec is unclear how to encode the typeNames parameter.  Its
        example says one thing and the standard says another, so I've done both here.

        Returns a named tuple:
            * type_names: 'all' or list.  all should return all feature types.  list should return the named feature types.
        """
        def add_ns(it, ns):
            x = it.split(':')
            if len(x) > 1:
                return ns[x[0]], x[1]
            else:
                return '',x

        root = etree.fromstring(request)
        xmlns = root.get('xmlns')
        output_format = root.get('outputFormat', 'application/gml+xml; version=3.2')

        if xmlns is not None:
            xmlns = "{" + xmlns + "}"
        else:
            xmlns = ""

        namespaces = {}
        for name, value in root.attrib.items():
            if name.startswith(xmlns):
                namespaces[value] = name[len(xmlns):]

        type_names = root.get('typeNames')
        if type_names is not None:
            type_names = [add_ns(n, namespaces) for n in type_names.split(',')]
        else:
            type_names = []
            for elt in root:
                if elt.tag.endswith("TypeName"):
                    namespace, name = elt.text.split(":")
                    namespace = namespaces[namespace]
                    type_names.append((namespace, name))

        if not len(type_names):
            type_names = 'all'

        return DescribeFeatureTypeMixin.Parameters.create(CaseInsensitiveDict({"typenames" : type_names, "outputformat" : output_format}))

    def _response_xml_DescribeFeatureType(self, response):
        return render_to_response("ga_ows/WFS_DescribeFeature.template.xml", { "feature_types" : list(response) })

    def _response_json_DescribeFeatureType(self, response, callback=None):
        rsp = []
        for feature_type in response:
            rsp.append({
                "schema" : feature_type.schema,
                "name" : feature_type.name,
                "abstract" : feature_type.abstract,
                "title" : feature_type.title,
                "ns_name" : feature_type.ns_name
            })

        if callback is not None:
            return HttpResponse(callback + "("  + json.dumps(rsp) + ")", mimetype='text/javascript')
        else:
            return HttpResponse(json.dumps(rsp), mimetype='application/json')

    def DescribeFeatureType(self, request, kwargs):
        """See section 9 of the OGC WFS standards document."""
        if 'xml' in kwargs:
            parms = self._parse_xml_DescribeFeatureType(kwargs['xml'])
        else:
            parms = DescribeFeatureTypeMixin.Parameters.create(kwargs)

        response = self.adapter.get_feature_descriptions(request, *parms.cleaned_data['type_names'])

        if parms.cleaned_data['output_format'].endswith('json'):
            if 'callback' in kwargs:
                return self._response_json_DescribeFeatureType(response, callback=kwargs['callback'])
            elif 'jsonp' in kwargs:
                return self._response_json_DescribeFeatureType(response, callback=kwargs['jsonp'])
            else:
                return self._response_json_DescribeFeatureType(response)
        else:
            return self._response_xml_DescribeFeatureType(response)

class GetFeatureMixin(WFSBase):
    """
    Defines the GetFeature operation in section 11 of the WFS standard.
    """
    class Parameters(
        CommonParameters,
        InputParameters,
        PresentationParameters,
        AdHocQueryParameters,
        StoredQueryParameters
    ):
        pass

    def _parse_xml_GetFeature(self, request):
        """
        """
        raise OperationNotSupported.at("GetFeature", "XML encoded POST for WFS.GetFeature needs implemented")
        #TODO implement this method.

    def GetFeature(self, request, kwargs):
        """
        """
        mimetypes = {
            'GeoJSON' : 'application/json'
        }

        if 'xml' in kwargs:
            parms = self._parse_xml_GetFeature(kwargs['xml'])
        else:
            parms = GetFeatureMixin.Parameters.create(kwargs)

        # must be an OGR dataset or a QuerySet containing one layer
        response = self.adapter.get_features(request, parms)
        if isinstance(response, GeoQuerySet):
            layer = None
            db_params = settings.DATABASES[response.db]
            if db_params['ENGINE'].endswith('postgis'):
                # Then we take the raw SQL from thr QuerySet and pass it through OGR instead.  This causes the SQL to be
                # executed twice, but it's also the most expedient way to create our output. This could be done better,
                # but it gets it out the door for now.

                # Create the query from the QuerySet
                # adapt() prevents SQL injection attacks
                from psycopg2.extensions import adapt
                query, parameters = response.query.get_compiler(response.db).as_sql()
                parameters = tuple([adapt(p) for p in parameters])
                query = query % parameters

                # Connect to PostGIS with OGR.
                drv = ogr.GetDriverByName("PostgreSQL")
                connection_string = "PG:dbname='{db}'".format(db=db_params['NAME'])
                if 'HOST' in db_params and db_params['HOST']:
                    connection_string += " host='{host}'".format(host=db_params['HOST'])
                if 'PORT' in db_params and db_params['PORT']:
                    connection_string += " port='{port}'".format(port=db_params['PORT'])
                if 'USER' in db_params and db_params['USER']:
                    connection_string += " user='{user}'".format(user=db_params['USER'])
                if 'PASSWORD' in db_params and db_params['PASSWORD']:
                    connection_string += " password='{password}'".format(password=db_params['PASSWORD'])
                conn = drv.Open(connection_string)

                # Put the QuerySet into a layer the hard way.
                layer = conn.ExecuteSQL(query)
            elif db_params['ENGINE'].endswith('spatialite'):
                # This works the same way as the if-statement above.
                # todo replace this with the sqlite version of the same thing for preventing SQL injection attacks
                from psycopg2.extensions import adapt
                query, parameters = response.query.get_compiler(response.db).as_sql()
                parameters = tuple([adapt(p) for p in parameters])
                query = query % parameters

                drv = ogr.GetDriverByName("Spatialite")
                conn = drv.Open(db_params['NAME'])
                layer = conn.ExecuteSQL(query)
        else:
            layer = response.GetLayerByIndex(0)

        drivers = dict([(ogr.GetDriver(drv).GetName(), ogr.GetDriver(drv)) for drv in range(ogr.GetDriverCount()) if ogr.GetDriver(drv).TestCapability(ogr.ODrCCreateDataSource)])
        output_format = parms.cleaned_data['output_format'].decode('ascii')
        if 'gml' in output_format or 'xml' in output_format:
            tmpname = "{tmpdir}{sep}{uuid}.{output_format}".format(tmpdir=gettempdir(), uuid=uuid4(), output_format='gml', sep=os.path.sep)
            drv = ogr.GetDriverByName("GML")
            ds = drv.CreateDataSource(tmpname)
            l2 = ds.CopyLayer(layer, 'WFS_result')
            l2.SyncToDisk()
            del ds
            responsef = open(tmpname)
            rdata = responsef.read()
            responsef.close()
            os.unlink(tmpname)
            return HttpResponse(rdata, mimetype=output_format)
        elif output_format in drivers:
            tmpname = "{tmpdir}{sep}{uuid}.{output_format}".format(tmpdir=gettempdir(), uuid=uuid4(), output_format=output_format, sep=os.path.sep)
            drv = drivers[output_format]
            ds = drv.CreateDataSource(tmpname)
            l2 = ds.CopyLayer(layer, 'WFS_result')
            l2.SyncToDisk()
            del ds
            responsef = open(tmpname)
            rdata = responsef.read()
            responsef.close()
            os.unlink(tmpname)
            return HttpResponse(rdata, mimetype=mimetypes.get(output_format,'text/plain'))
        else:
            raise OperationProcessingFailed.at('GetFeature', 'outputFormat {of} not supported ({formats})'.format(of=output_format, formats=drivers.keys()))

class ListStoredQueriesMixin(WFSBase):
    """
    Defines the ListStoredQueries operation in section 14.3 of the standard
    """
    def ListStoredQueries(self, request, kwargs):
        """
        """
        queries = self.adapter.list_stored_queries(request)
        response = etree.Element("ListStoredQueriesResponse")
        for query, description in queries.items():
            sub = etree.SubElement(response, "StoredQuery")
            etree.SubElement(sub, "Title").text = query
            for feature_type in description.feature_types:
                etree.SubElement(sub, 'ReturnFeatureType').text = feature_type
        return HttpResponse(etree.tostring(response, pretty_print=True), mimetype='text/xml')


class DescribeStoredQueriesMixin(WFSBase):
    class Parameters(CommonParameters):
        stored_query_id = MultipleValueField()

        @classmethod
        def from_request(cls, request):
            request['stored_query_id'] = request.getlist('storedqueryid')

    def DescribeStoredQueries(self, request, kwargs):
        parms = DescribeStoredQueriesMixin.Parameters.create(kwargs)
        inspected_queries = parms.cleaned_data['stored_query_id']
        response = etree.Element('DescribeStoredQueriesResponse')
        for query, description in filter(lambda (x,y): x in inspected_queries, self.adapter.list_stored_queries(request).items()):
            desc = etree.SubElement(response, "StoredQueryDescription")
            etree.SubElement(desc, 'Title').text = query
            for parameter in description.parameters:
                p = etree.SubElement(desc, "Parameter", attrib={"name" : parameter.name, "type" : parameter.type})
                etree.SubElement(p, 'Title').text = parameter.title
                etree.SubElement(p, 'Abstract').text = parameter.abstractS
                if parameter.query_expression:
                    etree.SubElement(p, "QueryExpressionText", attrib={
                        "isPrivate" : parameter.query_expression.private == True,
                        "language" : parameter.query_expression.language,
                        "returnFeatureTypes" : ' '.join(parameter.query_expression.return_feature_types)
                    }).text = parameter.query_expression.text
        return HttpResponse(etree.tostring(response, pretty_print=True), mimetype='text/xml')

# TODO implement stored queries
class CreateStoredQuery(WFSBase):
   def CreateStoredQuery(self, request, kwargs):
        raise OperationNotSupported.at("CreateStoredQuery")

class DropStoredQuery(WFSBase):
    def DropStoredQuery(self, request, kwargs):
        raise OperationNotSupported.at("DropStoredQuery")


# TODO implement transactions
class TransactionMixin(WFSBase):
    def Transaction(self, request, kwargs):
        """
        """
        raise OperationNotSupported.at('Transaction')

class GetFeatureWithLockMixin(WFSBase):
    def GetFeatureWithLock(self, request,  kwargs):
        raise OperationNotSupported.at("GetFeatureWithLock")

class LockFeatureMixin(WFSBase):
    def LockFeature(self, request, kwargs):
        raise OperationNotSupported.at('LockFeature')

class GetPropertyValueMixin(WFSBase):
    class Parameters(StoredQueryParameters, AdHocQueryParameters):
        value_reference = f.CharField()
        resolve_path = f.CharField(required=False)

        def from_request(cls, request):
            request['value_reference'] = request['valuereference']
            request['resolve_path'] = request['resolvepath']

    def GetPropertyValue(self, request, kwargs):
        raise OperationNotSupported.at('GetPropertyValue')

class WFS(
    common.OWSView,
    GetCapabilitiesMixin,
    DescribeFeatureTypeMixin,
    DescribeStoredQueriesMixin,
    GetFeatureMixin,
    ListStoredQueriesMixin,
    GetPropertyValueMixin
):
    """ A generic view supporting the WFS 2.0.0 standard from the OGC"""
    adapter = None
    models = None
    title = None
    keywords = []
    fees = None
    access_constraints = None
    provider_name = None
    addr_street = None
    addr_city = None
    addr_admin_area = None
    addr_postcode = None
    addr_country = None
    addr_email = None

    def __init__(self, **kwargs):
        common.OWSView.__init__(self, **kwargs)
        if self.models:
            self.adapter = GeoDjangoWFSAdapter(self.models)

    def get_capabilities_response(self, request, params):
        return render_to_response('ga_ows/WFS_GetCapabilities.template.xml', {
            "title" : self.title,
            "keywords" : self.keywords,
            "fees" : self.fees,
            "access_constraints" : self.access_constraints,
            "endpoint" : request.build_absolute_uri().split('?')[0],
            "output_formats" : [ogr.GetDriver(drv).GetName() for drv in range(ogr.GetDriverCount()) if ogr.GetDriver(drv).TestCapability(ogr.ODrCCreateDataSource)],
            "addr_street" : self.addr_street,
            "addr_city" : self.addr_city,
            "addr_admin_area" : self.addr_admin_area,
            "addr_postcode" : self.addr_postcode,
            "addr_country" : self.addr_country,
            "feature_versioning" : False,
            "transactional" : False,
            'feature_types' : self.adapter.get_feature_descriptions(request)
        })



class WFST(WFS,TransactionMixin,GetFeatureWithLockMixin, LockFeatureMixin):
    """ A generic view supporting the WFS 2.0.0 standard from the OGC including transactions"""
    def get_capabilities_response(self, request, params):
        return render_to_response('ga_ows/WFS_GetCapabilities.template.xml', {
            "title" : self.title,
            "keywords" : self.keywords,
            "fees" : self.fees,
            "access_constraints" : self.access_constraints,
            "endpoint" : request.build_absolute_uri().split('?')[0],
            "output_formats" : [ogr.GetDriver(drv).GetName() for drv in range(ogr.GetDriverCount()) if ogr.GetDriver(drv).TestCapability(ogr.ODrCCreateDataSource)],
            "addr_street" : self.addr_street,
            "addr_city" : self.addr_city,
            "addr_admin_area" : self.addr_admin_area,
            "addr_postcode" : self.addr_postcode,
            "addr_country" : self.addr_country,
            "feature_versioning" : self.adapter.supports_feature_versioning(),
            "transactional" : True,
            'feature_types' : self.adapter.get_feature_descriptions(request)
        })
