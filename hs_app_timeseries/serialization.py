
import rdflib

from hs_core.serialization import GenericResourceMeta


class TimeSeriesResourceMeta(GenericResourceMeta):
    """
    Lightweight class for representing metadata of TimeSeriesResource instances.
    """
    def __init__(self):
        super(TimeSeriesResourceMeta, self).__init__()

        self.site = None
        self.variable = None
        self.method = None
        self.processing_level = None
        self.time_series_result = None

    def _read_resource_metadata(self):
        super(TimeSeriesResourceMeta, self)._read_resource_metadata()

        print("--- TimeSeriesResourceMeta ---")

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')

        # Get site
        for s, p, o in self._rmeta_graph.triples((None, hsterms.site, None)):
            self.site = TimeSeriesResourceMeta.Site()
            # Get SiteCode
            site_code_lit = self._rmeta_graph.value(o, hsterms.SiteCode)
            if site_code_lit is None:
                msg = "SiteCode for site was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.site.siteCode = str(site_code_lit)
            # Get SiteName
            site_name_lit = self._rmeta_graph.value(o, hsterms.SiteName)
            if site_name_lit is None:
                msg = "SiteName for site was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.site.siteName = str(site_name_lit)

            print("\t\t{0}".format(self.site))

    def write_metadata_to_resource(self, resource):
        super(TimeSeriesResourceMeta, self).write_metadata_to_resource(resource)

    class Site(object):

        def __init__(self):
            self.siteCode = None
            self.siteName = None
            self.elevation_m = None  # Optional
            self.elevationDatum = None  # Optional
            self.siteType = None  # Optional

        def __str__(self):
            msg = "Site siteCode: {siteCode}, siteName: {siteName}, "
            msg += "elevation_m: {elevation_m}, elevationDatum: {elevationDatum}, "
            msg += "siteType: {siteType}"
            msg = msg.format(siteCode=self.siteCode, siteName=self.siteName,
                             elevation_m=self.elevation_m,
                             elevationDatum=self.elevationDatum,
                             siteType=self.siteType)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class Variable(object):

        def __init__(self):
            self.variableCode = None
            self.variableName = None
            self.variableType = None
            self.noDataValue = None
            self.variableDefinition = None  # Optional
            self.speciation = None  # Optional

        def __str__(self):
            msg = "Variable variableCode: {variableCode}, variableName: {variableName}, "
            msg += "variableType: {variableType}, noDataValue: {noDataValue}, "
            msg += "variableDefinition: {variableDefinition}, speciation: {speciation}"
            msg = msg.format(variableCode=self.variableCode, variableName=self.variableName,
                             variableType=self.variableType, noDataValue=self.noDataValue,
                             variableDefinition=self.variableDefinition, speciation=self.speciation)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class Method(object):

        def __init__(self):
            self.methodCode = None
            self.methodName = None
            self.methodType = None
            self.methodDescription = None  # Optional
            self.methodLink = None  # Optional

        def __str__(self):
            msg = "Method methodCode: {methodCode}, methodName: {methodName}, "
            msg += "methodType: {methodType}, methodDescription: {methodDescription}, "
            msg += "methodLink: {methodLink}"
            msg = msg.format(methodCode=self.methodCode, methodName=self.methodName,
                             methodType=self.methodType,
                             methodDescription=self.methodDescription,
                             methodLink=self.methodLink)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ProcessingLevel(object):

        def __init__(self):
            self.processingLevelCode = None
            self.definition = None  # Optional
            self.explanation = None  # Optional

        def __str__(self):
            msg = "ProcessingLevel processingLevelCode: {processingLevelCode}, "
            msg += "definition: {definition}, explanation: {explanation}"
            msg = msg.format(processingLevelCode=self.processingLevelCode,
                             definition=self.definition,
                             explanation=self.explanation)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class TimeSeriesResult(object):

        def __init__(self):
            self.unitsType = None
            self.unitsName = None
            self.unitsAbbreviation = None
            self.status = None
            self.sampleMedium = None
            self.valueCount = None
            self.aggregationStatistics = None

        def __str__(self):
            msg = "TimeSeriesResult unitsType: {unitsType}, unitsName: {unitsName}, "
            msg += "unitsAbbreviation: {unitsAbbreviation}, status: {status}, "
            msg += "sampleMedium: {sampleMedium}, valueCount: {valueCount}, "
            msg += "aggregationStatistics: {aggregationStatistics}"
            msg = msg.format(unitsType=self.unitsType, unitsName=self.unitsName,
                             unitsAbbreviation=self.unitsAbbreviation,
                             status=self.status, sampleMedium=self.sampleMedium,
                             valueCount=self.valueCount,
                             aggregationStatistics=self.aggregationStatistics)
            return msg

        def __unicode__(self):
            return unicode(str(self))