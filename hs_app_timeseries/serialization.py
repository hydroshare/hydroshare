
import rdflib

from django.db import transaction

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

        hsterms = rdflib.namespace.Namespace('https://www.hydroshare.org/terms/')

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
            # Get Elevation_m
            site_elevation_lit = self._rmeta_graph.value(o, hsterms.Elevation_m)
            if site_elevation_lit is not None:
                self.site.elevation_m = float(str(site_elevation_lit))
            # Get ElevationDatum
            site_elevation_datum_lit = self._rmeta_graph.value(o, hsterms.ElevationDatum)
            if site_elevation_datum_lit is not None:
                self.site.elevationDatum = str(site_elevation_datum_lit)
            # Get SiteType
            site_type_lit = self._rmeta_graph.value(o, hsterms.SiteType)
            if site_type_lit is not None:
                self.site.siteType = str(site_type_lit)
            print("\t\t{0}".format(self.site))

        # Get variable
        for s, p, o in self._rmeta_graph.triples((None, hsterms.variable, None)):
            self.variable = TimeSeriesResourceMeta.Variable()
            # Get VariableCode
            var_code_lit = self._rmeta_graph.value(o, hsterms.VariableCode)
            if var_code_lit is None:
                msg = "VariableCode for variable was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.variable.variableCode = str(var_code_lit)
            # Get VariableName
            var_name_lit = self._rmeta_graph.value(o, hsterms.VariableName)
            if var_name_lit is None:
                msg = "VariableName for variable was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.variable.variableName = str(var_name_lit)
            # Get VariableType
            var_type_lit = self._rmeta_graph.value(o, hsterms.VariableType)
            if var_type_lit is None:
                msg = "VariableType for variable was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.variable.variableType = str(var_type_lit)
            # Get NoDataValue
            var_nd_lit = self._rmeta_graph.value(o, hsterms.NoDataValue)
            if var_nd_lit is None:
                msg = "NoDataValue for variable was not found for resource {0}".format(self.root_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.variable.noDataValue = str(var_nd_lit)
            # Get VariableDefinition
            var_def_lit = self._rmeta_graph.value(o, hsterms.VariableDefinition)
            if var_def_lit is not None:
                self.variable.variableDefinition = str(var_def_lit)
            # Get Speciation
            var_spec_lit = self._rmeta_graph.value(o, hsterms.Speciation)
            if var_spec_lit is not None:
                self.variable.speciation = str(var_spec_lit)
            print("\t\t{0}".format(self.variable))

            # Get method
            for s, p, o in self._rmeta_graph.triples((None, hsterms.method, None)):
                self.method = TimeSeriesResourceMeta.Method()
                # Get MethodCode
                method_code_lit = self._rmeta_graph.value(o, hsterms.MethodCode)
                if method_code_lit is None:
                    msg = "MethodCode for method was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.method.methodCode = str(method_code_lit)
                # Get MethodName
                method_name_lit = self._rmeta_graph.value(o, hsterms.MethodName)
                if method_name_lit is None:
                    msg = "MethodName for method was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.method.methodName = str(method_name_lit)
                # Get MethodType
                method_type_lit = self._rmeta_graph.value(o, hsterms.MethodType)
                if method_type_lit is None:
                    msg = "MethodType for method was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.method.methodType = str(method_type_lit)
                # Get MethodDescription
                method_desc_lit = self._rmeta_graph.value(o, hsterms.MethodDescription)
                if method_desc_lit is not None:
                    self.method.methodDescription = str(method_desc_lit)
                # Get MethodLink
                method_link_lit = self._rmeta_graph.value(o, hsterms.MethodLink)
                if method_link_lit is not None:
                    self.method.methodLink = str(method_link_lit)
                print("\t\t{0}".format(self.method))

            # Get processingLevel
            for s, p, o in self._rmeta_graph.triples((None, hsterms.processingLevel, None)):
                self.processing_level = TimeSeriesResourceMeta.ProcessingLevel()
                # Get ProcessingLevelCode
                proc_code_lit = self._rmeta_graph.value(o, hsterms.ProcessingLevelCode)
                if proc_code_lit is None:
                    msg = "ProcessingLevelCode for ProcessingLevel was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.processing_level.processingLevelCode = str(proc_code_lit)
                # Get Definition
                method_def_lit = self._rmeta_graph.value(o, hsterms.Definition)
                if method_def_lit is not None:
                    self.processing_level.definition = str(method_def_lit)
                # Get Explanation
                method_explan_lit = self._rmeta_graph.value(o, hsterms.Explanation)
                if method_explan_lit is not None:
                    self.processing_level.explanation = str(method_explan_lit)
                print("\t\t{0}".format(self.processing_level))

            # Get timeSeriesResult
            for s, p, o in self._rmeta_graph.triples((None, hsterms.timeSeriesResult, None)):
                self.time_series_result = TimeSeriesResourceMeta.TimeSeriesResult()
                # Get units
                for s1, p1, o1 in self._rmeta_graph.triples((o, hsterms.units, None)):
                    # Get UnitsType
                    unit_type_lit = self._rmeta_graph.value(o1, hsterms.UnitsType)
                    if unit_type_lit is None:
                        msg = "UnitsType for TimeSeriesResult:units was not found for resource {0}".format(self.root_uri)
                        raise GenericResourceMeta.ResourceMetaException(msg)
                    self.time_series_result.unitsType = str(unit_type_lit)
                    # Get UnitsName
                    unit_name_lit = self._rmeta_graph.value(o1, hsterms.UnitsName)
                    if unit_name_lit is None:
                        msg = "UnitsName for TimeSeriesResult:units was not found for resource {0}".format(self.root_uri)
                        raise GenericResourceMeta.ResourceMetaException(msg)
                    self.time_series_result.unitsName = str(unit_name_lit)
                    # Get UnitsAbbreviation
                    unit_abbrev_lit = self._rmeta_graph.value(o1, hsterms.UnitsAbbreviation)
                    if unit_abbrev_lit is None:
                        msg = "UnitsAbbreviation for TimeSeriesResult:units was not found for resource {0}".format(self.root_uri)
                        raise GenericResourceMeta.ResourceMetaException(msg)
                    self.time_series_result.unitsAbbreviation = str(unit_abbrev_lit)
                # Get Status
                res_status_lit = self._rmeta_graph.value(o, hsterms.Status)
                if res_status_lit is None:
                    msg = "Status for TimeSeriesResult was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.time_series_result.status = str(res_status_lit)
                # Get SampleMedium
                res_sampmed_lit = self._rmeta_graph.value(o, hsterms.SampleMedium)
                if res_sampmed_lit is None:
                    msg = "SampleMedium for TimeSeriesResult was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.time_series_result.sampleMedium = str(res_sampmed_lit)
                # Get ValueCount
                res_valcount_lit = self._rmeta_graph.value(o, hsterms.ValueCount)
                if res_valcount_lit is None:
                    msg = "ValueCount for TimeSeriesResult was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.time_series_result.valueCount = int(str(res_valcount_lit))
                # Get AggregationStatistic
                res_aggstat_lit = self._rmeta_graph.value(o, hsterms.AggregationStatistic)
                if res_aggstat_lit is None:
                    msg = "AggregationStatistic for TimeSeriesResult was not found for resource {0}".format(self.root_uri)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                self.time_series_result.aggregationStatistics = str(res_aggstat_lit)
                print("\t\t{0}".format(self.time_series_result))

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: TimeSeriesResource instance
        """
        super(TimeSeriesResourceMeta, self).write_metadata_to_resource(resource)

        if self.site:
            site = resource.metadata.site
            if site:
                site.delete()
            resource.metadata.create_element('site', site_code=self.site.siteCode,
                                             site_name=self.site.siteName,
                                             elevation_m=self.site.elevation_m,
                                             elevation_datum=self.site.elevationDatum,
                                             site_type=self.site.siteType)
        if self.variable:
            variable = resource.metadata.variable
            if variable:
                variable.delete()
            resource.metadata.create_element('variable', variable_code=self.variable.variableCode,
                                             variable_name=self.variable.variableName,
                                             variable_type=self.variable.variableType,
                                             no_data_value=self.variable.noDataValue,
                                             variable_definition=self.variable.variableDefinition,
                                             speciation=self.variable.speciation)
        if self.method:
            method = resource.metadata.method
            if method:
                method.delete()
            resource.metadata.create_element('method', method_code=self.method.methodCode,
                                             method_name=self.method.methodName,
                                             method_type=self.method.methodType,
                                             method_description=self.method.methodDescription,
                                             method_link=self.method.methodLink)
        if self.processing_level:
            processing_level = resource.metadata.processing_level
            if processing_level:
                processing_level.delete()
            resource.metadata.create_element('ProcessingLevel',
                                             processing_level_code=self.processing_level.processingLevelCode,
                                             definition=self.processing_level.definition,
                                             explanation=self.processing_level.explanation)
        if self.time_series_result:
            time_series_result = resource.metadata.time_series_result
            if time_series_result:
                time_series_result.delete()
            resource.metadata.create_element('TimeSeriesResult',
                                             units_type=self.time_series_result.unitsType,
                                             units_name=self.time_series_result.unitsName,
                                             units_abbreviation=self.time_series_result.unitsAbbreviation,
                                             status=self.time_series_result.status,
                                             sample_medium=self.time_series_result.sampleMedium,
                                             value_count=self.time_series_result.valueCount,
                                             aggregation_statistics=self.time_series_result.aggregationStatistics)

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
            return str(self)

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
            return str(self)

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
            return str(self)

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
            return str(self)

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
            return str(self)