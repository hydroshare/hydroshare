import os
import shutil
import json
import logging
from dateutil import parser
from urllib2 import Request, urlopen, URLError
import jsonschema
from lxml import etree

from django.utils import timezone
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.template import Template, Context

from dominate.tags import div, form, button, h4, p, textarea, legend, table, tbody, tr, \
    th, td, a

from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData

from base import AbstractFileMetaData, AbstractLogicalFile


class TimeSeries(object):
    """represents a one timeseries metadata"""
    def __init__(self, network_name, site_name, site_code, latitude, longitude, variable_name,
                 variable_code, method_description, method_link, sample_medium, url, service_type,
                 reference_type, return_type, start_date, end_date, value_count):
        self.network_name = network_name
        self.site_name = site_name
        self.site_code = site_code
        self.latitude = latitude
        self.longitude = longitude
        self.variable_name = variable_name
        self.variable_code = variable_code
        self.method_description = method_description
        self.method_link = method_link
        self.sample_medium = sample_medium
        self.url = url
        self.service_type = service_type
        self.reference_type = reference_type
        self.return_type = return_type
        self.start_date = start_date
        self.end_date = end_date
        self.value_count = value_count

    def get_html(self, site_number):
        """generates html code for viewing site related data"""

        root_div = div(cls="col-xs-12 pull-left", style="margin-top:10px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well panel panel-default"):
                with div(cls="panel-heading"):
                    with h4(cls="panel-title"):
                        a(self.site_name, data_toggle="collapse", data_parent="#accordion",
                          href="#collapse{}".format(site_number))
                with div(id="collapse{}".format(site_number), cls="panel-collapse collapse"):
                    with div(cls="panel-body"):
                        with table(cls='custom-table'):
                            with tbody():
                                with tr():
                                    get_th('Network Name')
                                    td(self.network_name)
                                with tr():
                                    get_th('Service Type')
                                    td(self.service_type)
                                with tr():
                                    get_th('Return Type')
                                    td(self.return_type)
                                with tr():
                                    get_th('Reference Type')
                                    td(self.reference_type)
                                with tr():
                                    get_th('URL')
                                    with td():
                                        a(self.url, href=self.url, target="_blank")
                                with tr():
                                    get_th('Site Name')
                                    td(self.site_name)
                                with tr():
                                    get_th('Site Code')
                                    td(self.site_code)
                                with tr():
                                    get_th('Latitude')
                                    td(self.latitude)
                                with tr():
                                    get_th('Longitude')
                                    td(self.longitude)
                                with tr():
                                    get_th('Variable Name')
                                    td(self.variable_name)
                                with tr():
                                    get_th('Variable Code')
                                    td(self.variable_code)
                                with tr():
                                    get_th('Method Description')
                                    td(self.method_description)
                                with tr():
                                    get_th('Method Link')
                                    with td():
                                        a(self.method_link, href=self.method_link, target="_blank")
                                with tr():
                                    get_th('Sample Medium')
                                    td(self.sample_medium)
                                with tr():
                                    get_th('Value Count')
                                    td(self.value_count)
                                with tr():
                                    get_th('Begin Date')
                                    td(self.start_date)
                                with tr():
                                    get_th('End Date')
                                    td(self.end_date)

        return root_div

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of the metadata element"""

        NAMESPACES = CoreMetaData.NAMESPACES
        ref_ts_result = etree.SubElement(container, '{%s}referencedTimeSeriesResult'
                                         % NAMESPACES['hsterms'])
        rdf_description = etree.SubElement(ref_ts_result, '{%s}Description' % NAMESPACES['rdf'])

        # encode request info data
        hs_request_info = etree.SubElement(rdf_description, '{%s}requestInfo'
                                           % NAMESPACES['hsterms'])
        hs_request_info_desc = etree.SubElement(hs_request_info, '{%s}Description'
                                                % NAMESPACES['rdf'])
        hs_network_name = etree.SubElement(hs_request_info_desc, '{%s}networkName'
                                           % NAMESPACES['hsterms'])
        hs_network_name.text = self.network_name
        hs_ref_type = etree.SubElement(hs_request_info_desc, '{%s}refType' % NAMESPACES['hsterms'])
        hs_ref_type.text = self.reference_type
        hs_retrun_type = etree.SubElement(hs_request_info_desc, '{%s}returnType'
                                          % NAMESPACES['hsterms'])
        hs_retrun_type.text = self.return_type
        hs_service_type = etree.SubElement(hs_request_info_desc, '{%s}serviceType'
                                           % NAMESPACES['hsterms'])
        hs_service_type.text = self.reference_type
        hs_wsdl_url = etree.SubElement(hs_request_info_desc, '{%s}url' % NAMESPACES['hsterms'])
        hs_wsdl_url.text = self.url

        # encode date (duration) data
        hs_begin_date = etree.SubElement(rdf_description, '{%s}beginDate' % NAMESPACES['hsterms'])
        st_date = parser.parse(self.start_date)
        hs_begin_date.text = st_date.isoformat()
        hs_end_date = etree.SubElement(rdf_description, '{%s}endDate' % NAMESPACES['hsterms'])
        end_date = parser.parse(self.end_date)
        hs_end_date.text = end_date.isoformat()

        # encode sample medium
        hs_sample_medium = etree.SubElement(rdf_description, '{%s}sampleMedium'
                                            % NAMESPACES['hsterms'])
        hs_sample_medium.text = self.sample_medium

        # encode value count
        hs_value_count = etree.SubElement(rdf_description, '{%s}valueCount' % NAMESPACES['hsterms'])
        hs_value_count.text = str(self.value_count)

        # encode site data
        hs_site = etree.SubElement(rdf_description, '{%s}site' % NAMESPACES['hsterms'])
        hs_site_desc = etree.SubElement(hs_site, '{%s}Description' % NAMESPACES['rdf'])
        hs_site_code = etree.SubElement(hs_site_desc, '{%s}siteCode' % NAMESPACES['hsterms'])
        hs_site_code.text = self.site_code
        hs_site_name = etree.SubElement(hs_site_desc, '{%s}siteName' % NAMESPACES['hsterms'])
        hs_site_name.text = self.site_name
        hs_site_lat = etree.SubElement(hs_site_desc, '{%s}Latitude' % NAMESPACES['hsterms'])
        hs_site_lat.text = str(self.latitude)
        hs_site_lon = etree.SubElement(hs_site_desc, '{%s}Longitude' % NAMESPACES['hsterms'])
        hs_site_lon.text = str(self.longitude)

        # encode variable data
        hs_variable = etree.SubElement(rdf_description, '{%s}variable' % NAMESPACES['hsterms'])
        hs_variable_desc = etree.SubElement(hs_variable, '{%s}Description' % NAMESPACES['rdf'])
        hs_variable_code = etree.SubElement(hs_variable_desc, '{%s}variableCode'
                                            % NAMESPACES['hsterms'])
        hs_variable_code.text = self.variable_code
        hs_variable_name = etree.SubElement(hs_variable_desc, '{%s}variableName'
                                            % NAMESPACES['hsterms'])
        hs_variable_name.text = self.variable_name

        # encode method data
        hs_method = etree.SubElement(rdf_description, '{%s}method' % NAMESPACES['hsterms'])
        hs_rdf_method_desc = etree.SubElement(hs_method, '{%s}Description' % NAMESPACES['rdf'])
        hs_method_desc = etree.SubElement(hs_rdf_method_desc, '{%s}methodDescription'
                                          % NAMESPACES['hsterms'])
        hs_method_desc.text = self.method_description
        hs_method_link = etree.SubElement(hs_rdf_method_desc, '{%s}methodLink'
                                          % NAMESPACES['hsterms'])
        hs_method_link.text = self.method_link


class Site(object):
    """represents a site for timeseries data"""
    def __init__(self, name, code, latitude, longitude):
        self.name = name
        self.code = code
        self.latitude = latitude
        self.longitude = longitude

    def get_html(self):
        """generates html code for viewing site related data"""

        root_div = div(cls="col-xs-12 pull-left", style="margin-top:10px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                # strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Name')
                            td(self.name)
                        with tr():
                            get_th('Code')
                            td(self.code)
                        with tr():
                            get_th('Latitude')
                            td(self.latitude)
                        with tr():
                            get_th('Longitude')
                            td(self.longitude)

        return root_div.render(pretty=True)


class Variable(object):
    """represents a variable for timeseries data"""
    def __init__(self, name, code):
        self.name = name
        self.code = code

    def get_html(self):
        """generates html code for viewing variable related data"""

        root_div = div(cls="col-xs-12 pull-left", style="margin-top:10px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                # strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Name')
                            td(self.name)
                        with tr():
                            get_th('Code')
                            td(self.code)

        return root_div.render(pretty=True)


class Method(object):
    """represents a method for timeseries data"""
    def __init__(self, description, link):
        self.description = description
        self.link = link


class RefWebService(object):
    """represents a web service for timeseries data"""
    def __init__(self, url, service_type, reference_type, return_type):
        self.url = url
        self.service_type = service_type
        self.reference_type = reference_type
        self.return_type = return_type

    def get_html(self):
        """generates html code for viewing web service related data"""

        root_div = div(cls="col-xs-12 pull-left", style="margin-top:10px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            with div(cls="custom-well"):
                # strong(self.name)
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('URL')
                            td(self.url)
                        with tr():
                            get_th('Service Type')
                            td(self.service_type)
                        with tr():
                            get_th('Return Type')
                            td(self.return_type)
                        with tr():
                            get_th('Reference Type')
                            td(self.reference_type)

        return root_div.render(pretty=True)


class RefTimeseriesFileMetaData(AbstractFileMetaData):
    # the metadata element models are from the hs_core app
    model_app_label = 'hs_core'
    # field to store the content of the json file (the file that is part
    # of the RefTimeseriesLogicalFile type
    json_file_content = models.TextField()
    # this is to store abstract
    abstract = models.TextField(null=True, blank=True)

    @property
    def has_title_in_json(self):
        """checks if title is in the uploaded json file"""
        json_data_dict = self._json_to_dict()
        return 'title' in json_data_dict['timeSeriesReferenceFile']

    def get_title_from_json(self):
        """gets the title associated with this ref time series from the json file"""
        json_data_dict = self._json_to_dict()
        if 'title' in json_data_dict['timeSeriesReferenceFile']:
            return json_data_dict['timeSeriesReferenceFile']['title']
        return ''

    @property
    def has_abstract_in_json(self):
        """checks if abstract is in the uploaded json file"""
        json_data_dict = self._json_to_dict()
        return 'abstract' in json_data_dict['timeSeriesReferenceFile']

    def get_abstract_from_json(self):
        """get the abstract associated with this ref time series from the json file"""
        json_data_dict = self._json_to_dict()
        if 'abstract' in json_data_dict['timeSeriesReferenceFile']:
            return json_data_dict['timeSeriesReferenceFile']['abstract']
        return ''

    @property
    def file_version(self):
        """get the file version associated with this ref time series from the json file"""
        json_data_dict = self._json_to_dict()
        if 'fileVersion' in json_data_dict['timeSeriesReferenceFile']:
            return json_data_dict['timeSeriesReferenceFile']['fileVersion']
        return ''

    @property
    def symbol(self):
        """get the symbol associated with this ref time series from the json file"""
        json_data_dict = self._json_to_dict()
        if 'symbol' in json_data_dict['timeSeriesReferenceFile']:
            return json_data_dict['timeSeriesReferenceFile']['symbol']
        return ''

    @property
    def has_keywords_in_json(self):
        """checks if keywords exists in the uploaded json file"""

        json_data_dict = self._json_to_dict()
        return 'keyWords' in json_data_dict['timeSeriesReferenceFile']

    def get_keywords_from_json(self):
        """get a list of all keywords associated with this ref time series from json file"""
        json_data_dict = self._json_to_dict()
        if 'keyWords' in json_data_dict['timeSeriesReferenceFile']:
            return json_data_dict['timeSeriesReferenceFile']['keyWords']
        return []

    @property
    def sample_mediums(self):
        """get a list of all sample mediums associated with this ref time series"""
        sample_mediums = []
        for series in self.series_list:
            if "sampleMedium" in series:
                if series['sampleMedium'] not in sample_mediums:
                    sample_mediums.append(series['sampleMedium'])
        return sample_mediums

    @property
    def value_counts(self):
        """get a list of all value counts associated with this ref time series"""
        value_counts = []
        for series in self.series_list:
            if "valueCount" in series:
                if series['valueCount'] not in value_counts:
                    value_counts.append(series['valueCount'])
        return value_counts

    @property
    def series_list(self):
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesReferenceFile']['referencedTimeSeries']

    @property
    def time_series_list(self):
        """get a list of all time series associated with this ref time series"""
        ts_serieses = []
        for series in self.series_list:
            st_date = parser.parse(series['beginDate'])
            st_date = st_date.strftime('%m-%d-%Y')
            end_date = parser.parse(series['endDate'])
            end_date = end_date.strftime('%m-%d-%Y')
            method_des = ''
            method_link = ''
            if 'method' in series:
                method_des = series['method']['methodDescription']
                method_link = series['method']['methodLink']

            request_info = series['requestInfo']
            ts_series = TimeSeries(network_name=request_info['networkName'],
                                   site_name=series['site']['siteName'],
                                   site_code=series['site']['siteCode'],
                                   latitude=series['site']['latitude'],
                                   longitude=series['site']['longitude'],
                                   variable_name=series['variable']['variableName'],
                                   variable_code=series['variable']['variableCode'],
                                   method_description=method_des,
                                   method_link=method_link,
                                   sample_medium=series['sampleMedium'],
                                   url=request_info['url'],
                                   service_type=request_info['serviceType'],
                                   reference_type=request_info['refType'],
                                   return_type=request_info['returnType'],
                                   start_date=st_date,
                                   end_date=end_date,
                                   value_count=series['valueCount']
                                   )
            ts_serieses.append(ts_series)
        return ts_serieses

    @property
    def sites(self):
        """get a list of all sites associated with this ref time series"""
        sites = []
        site_codes = []
        for series in self.series_list:
            site_dict = series['site']
            if site_dict['siteCode'] not in site_codes:
                site = Site(name=site_dict['siteName'], code=site_dict['siteCode'],
                            latitude=site_dict['latitude'],
                            longitude=site_dict['longitude']
                            )
                sites.append(site)
                site_codes.append(site.code)
        return sites

    @property
    def variables(self):
        """get a list of all variables associated with this ref time series"""
        variables = []
        variable_codes = []
        for series in self.series_list:
            variable_dict = series['variable']
            if variable_dict['variableCode'] not in variable_codes:
                variable = Variable(name=variable_dict['variableName'],
                                    code=variable_dict['variableCode'])
                variables.append(variable)
                variable_codes.append(variable.code)
        return variables

    @property
    def methods(self):
        """get a list of all methods associated with this ref time series"""
        methods = []
        for series in self.series_list:
            if 'method' in series:
                method_dict = series['method']
                method = Method(description=method_dict['methodDescription'],
                                link=method_dict['methodLink'])
                methods.append(method)
        return methods

    @property
    def web_services(self):
        """get a list of all web services associated with this ref time series"""
        services = []
        urls = []
        for series in self.series_list:
            request_info = series['requestInfo']
            if request_info['url'] not in urls:
                service = RefWebService(url=request_info['url'],
                                        service_type=request_info['serviceType'],
                                        reference_type=request_info['refType'],
                                        return_type=request_info['returnType'])
                services.append(service)
                urls.append(service.url)
        return services

    def get_html(self):
        """overrides the base class function"""

        html_string = super(RefTimeseriesFileMetaData, self).get_html()
        if not self.has_metadata:
            root_div = div(cls="alert alert-warning alert-dismissible", role="alert")
            with root_div:
                h4("No file level metadata exists for the selected file.")
            html_string = root_div.render()
        else:
            if self.abstract:
                abstract_div = div(cls="col-xs-12 content-block")
                with abstract_div:
                    legend("Abstract")
                    p(self.abstract)

                html_string += abstract_div.render()
            if self.file_version:
                file_ver_div = div(cls="col-xs-12 content-block")
                with file_ver_div:
                    legend("File Version")
                    p(self.file_version)
                html_string += file_ver_div.render()
            if self.symbol:
                symbol_div = div(cls="col-xs-12 content-block")
                with symbol_div:
                    legend("Symbol")
                    if self.symbol.startswith('http'):
                        with p():
                            a(self.symbol, href=self.symbol, target="_blank")
                    else:
                        p(self.symbol)
                html_string += symbol_div.render()
            if self.temporal_coverage:
                html_string += self.temporal_coverage.get_html()

            if self.spatial_coverage:
                html_string += self.spatial_coverage.get_html()

        html_string += self.get_ts_series_html().render()
        html_string += self.get_json_file_data_html().render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_ts_series_html(self):
        """Generates html for all time series """

        root_div = div(cls="col-xs-12")
        with root_div:
            legend("Reference Time Series", cls="pull-left", style="margin-top:20px;")
            panel_group_div = div(cls="panel-group", id="accordion")
            panel_group_div.add(p("Note: Time series are listed below by site name. "
                                  "Click on a site name to see details.", cls="col-xs-12"))
            for index, series in enumerate(self.time_series_list):
                panel_group_div.add(series.get_html(index + 1))

        return root_div

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True):
        """overrides the base class function"""

        root_div = div()
        with root_div:
            div("{% load crispy_forms_tags %}")
            if self.has_title_in_json:
                self.get_dataset_name_html()
            else:
                self.get_dataset_name_form()
            if self.has_keywords_in_json:
                self.get_keywords_html()
            else:
                self.get_keywords_html_form()

            self.get_extra_metadata_html_form()
            abstract_div = div(cls="col-xs-12 content-block")
            with abstract_div:
                if self.has_abstract_in_json:
                    legend("Abstract")
                    p(self.abstract)
                else:
                    self.get_abstract_form()
            if self.file_version:
                file_ver_div = div(cls="col-xs-12 content-block")
                with file_ver_div:
                    legend("File Version")
                    p(self.file_version)

            if self.symbol:
                symbol_div = div(cls="col-xs-12 content-block")
                with symbol_div:
                    legend("Symbol")
                    if self.symbol.startswith('http'):
                        with p():
                            a(self.symbol, href=self.symbol, target="_blank")
                    else:
                        p(self.symbol)

            self.get_temporal_coverage_html_form()
            with div(cls="col-lg-6 col-xs-12"):
                with form(id="id-coverage-spatial-filetype", action="{{ spatial_form.action }}",
                          method="post", enctype="multipart/form-data"):
                    div("{% crispy spatial_form %}")
                    with div(cls="row", style="margin-top:10px;"):
                        with div(cls="col-md-offset-10 col-xs-offset-6 "
                                     "col-md-2 col-xs-6"):
                            button("Save changes", type="button",
                                   cls="btn btn-primary pull-right",
                                   style="display: none;",
                                   onclick="metadata_update_ajax_submit("
                                           "'id-coverage-spatial-filetype');")

            self.get_ts_series_html()
            self.get_json_file_data_html()

        template = Template(root_div.render())
        context_dict = dict()
        temp_cov_form = self.get_temporal_coverage_form(allow_edit=False)
        spatial_cov_form = self.get_spatial_coverage_form()

        context_dict["temp_form"] = temp_cov_form
        context_dict["spatial_form"] = spatial_cov_form
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_abstract_form(self):
        form_action = "/hsapi/_internal/{}/update-reftimeseries-abstract/"
        form_action = form_action.format(self.logical_file.id)
        root_div = div(cls="col-xs-12")

        # if json file contains abstract then we don't need this form since abstract can't be
        # edited in that case
        if self.has_abstract_in_json:
            return

        with root_div:
            with form(action=form_action, id="filetype-abstract",
                      method="post", enctype="multipart/form-data"):
                div("{% csrf_token %}")
                with div(cls="form-group"):
                    with div(cls="control-group"):
                        legend('Abstract')
                        with div(cls="controls"):
                            textarea(self.abstract,
                                     cls="form-control input-sm textinput textInput",
                                     id="file_abstract", cols=40, rows=5,
                                     name="abstract")
                with div(cls="row", style="margin-top:10px;"):
                    with div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                               style="display: none;", type="button")
        return root_div

    def get_json_file_data_html(self):
        """
        Generates html code to display the contents of the json file. The generated html
        is used for ref timeseries file type metadata in the view and edit modes.
        :return:
        """

        json_res_file = self.logical_file.files.first()
        json_file_content_div = div(style="clear:both;", cls="col-xs-12 content-block")
        with json_file_content_div:
            legend("Reference Time Series JSON File Content", style="margin-top:20px;")
            p(json_res_file.full_path[33:])
            header_info = self.json_file_content
            if isinstance(header_info, str):
                header_info = unicode(header_info, 'utf-8')

            textarea(header_info, readonly="", rows="15",
                     cls="input-xlarge", style="min-width: 100%")

        return json_file_content_div

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(RefTimeseriesFileMetaData, self)._get_xml_containers()
        NAMESPACES = CoreMetaData.NAMESPACES
        if self.abstract:
            dc_description = etree.SubElement(container_to_add_to,
                                              '{%s}description' % NAMESPACES['dc'])
            dc_des_rdf_Desciption = etree.SubElement(dc_description,
                                                     '{%s}Description' % NAMESPACES['rdf'])
            dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption,
                                                '{%s}abstract' % NAMESPACES['dcterms'])
            dcterms_abstract.text = self.abstract
        if self.file_version:
            hsterms_file_version = etree.SubElement(container_to_add_to,
                                                    '{%s}fileVersion' % NAMESPACES['hsterms'])
            hsterms_file_version.text = self.file_version

        if self.symbol:
            hsterms_symbol = etree.SubElement(container_to_add_to,
                                              '{%s}symbol' % NAMESPACES['hsterms'])
            hsterms_symbol.text = self.symbol

        for series in self.time_series_list:
            series.add_to_xml_container(container_to_add_to)

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def _json_to_dict(self):
        return json.loads(self.json_file_content)


class RefTimeseriesLogicalFile(AbstractLogicalFile):
    """ Each resource file is assigned an instance of this logical file type on upload to
    Composite Resource """
    metadata = models.OneToOneField(RefTimeseriesFileMetaData, related_name="logical_file")
    data_type = "referenceTimeseriesData"
    verbose_content_type = "Reference to Time Series"  # used during discovery

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .json file can be set to this logical file group"""
        return [".json"]

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".json"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file type allowed in this logical file group is: .json"""
        return [".json"]

    @classmethod
    def get_allowed_ref_types(cls):
        """returns a list of refType controlled vocabulary terms"""
        return ['WOF', "WPS", "DirectFile"]

    @classmethod
    def get_allowed_return_types(cls):
        """returns a list of returnType controlled vocabulary terms"""
        return ['WaterML 1.1', 'WaterML 2.0', 'TimeseriesML']

    @classmethod
    def get_allowed_service_types(cls):
        """returns a list of serviceType controlled vocabulary terms"""
        return ['SOAP', 'REST']

    @staticmethod
    def get_aggregation_display_name():
        return 'Referenced Time Series Content: A reference to one or more time series served ' \
               'from HydroServers outside of HydroShare in WaterML format'

    @staticmethod
    def get_aggregation_type_name():
        return "ReferencedTimeSeriesAggregation"

    @property
    def is_single_file_aggregation(self):
        """This aggregation supports only one file"""
        return True

    @classmethod
    def create(cls):
        # this custom method MUST be used to create an instance of this class
        rf_ts_metadata = RefTimeseriesFileMetaData.objects.create(json_file_content="No data")
        return cls.objects.create(metadata=rf_ts_metadata)

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """ Creates a RefTimeseriesLogicalFile (aggregation) from a json resource file (.refts.json)
        """

        log = logging.getLogger()
        if file_id is None:
            raise ValueError("Must specify id of the file to be set as an aggregation type")

        # get the the selected resource file object
        res_file = utils.get_resource_file_by_id(resource, file_id)

        if res_file is None:
            raise ValidationError("File not found.")

        if not res_file.file_name.lower().endswith('.refts.json'):
            raise ValidationError("Selected file '{}' is not a Ref Time Series file.".format(
                res_file.file_name))

        if res_file.has_logical_file:
            raise ValidationError("Selected file '{}' is already part of an aggregation".format(
                res_file.file_name))

        try:
            json_file_content = _validate_json_file(res_file)
        except Exception as ex:
            raise ValidationError(ex.message)

        # get the file from irods to temp dir
        temp_file = utils.get_file_from_irods(res_file)
        temp_dir = os.path.dirname(temp_file)

        with transaction.atomic():
            # create a reftiemseries logical file object to be associated with
            # resource files
            logical_file = cls.create()
            logical_file.metadata.json_file_content = json_file_content
            logical_file.metadata.save()

            try:
                # make the json file part of the aggregation
                logical_file.add_resource_file(res_file)
                logical_file.dataset_name = logical_file.metadata.get_title_from_json()
                logical_file.save()
                # extract metadata
                _extract_metadata(resource, logical_file)
                log.info("RefTimeseries aggregation type - json file was added to the resource.")
                logical_file._finalize(user, resource, folder_created=False,
                                       res_files_to_delete=[])

                log.info("RefTimeseries aggregation type was created.")
            except Exception as ex:
                msg = "RefTimeseries aggregation type. Error when setting aggregation " \
                      "type. Error:{}"
                msg = msg.format(ex.message)
                log.exception(msg)
                raise ValidationError(msg)
            finally:
                # remove temp dir
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)

    def get_copy(self):
        """Overrides the base class method"""

        copy_of_logical_file = super(RefTimeseriesLogicalFile, self).get_copy()
        copy_of_logical_file.metadata.json_file_content = self.metadata.json_file_content
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.save()
        return copy_of_logical_file

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(RefTimeseriesLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()


def _extract_metadata(resource, logical_file):
    # add resource level title if necessary
    if resource.metadata.title.value.lower() == 'untitled resource' \
            and logical_file.metadata.has_title_in_json:
        resource.metadata.update_element('title', resource.metadata.title.id,
                                         value=logical_file.dataset_name)

    # add resource level abstract if necessary
    logical_file_abstract = logical_file.metadata.get_abstract_from_json()
    if resource.metadata.description is None and logical_file.metadata.has_abstract_in_json:
        resource.metadata.create_element('description',
                                         abstract=logical_file_abstract)
    # add resource level keywords
    logical_file_keywords = logical_file.metadata.get_keywords_from_json()
    if logical_file.metadata.has_keywords_in_json:
        resource_keywords = [kw.value.lower() for kw in resource.metadata.subjects.all()]
        for kw in logical_file_keywords:
            if kw.lower() not in resource_keywords:
                resource.metadata.create_element('subject', value=kw)

    # add to the file level metadata
    logical_file.metadata.keywords = logical_file_keywords
    logical_file.metadata.abstract = logical_file_abstract
    logical_file.metadata.save()

    # add file level temporal coverage
    start_date = min([parser.parse(series['beginDate']) for series in
                      logical_file.metadata.series_list])
    end_date = max([parser.parse(series['endDate']) for series in
                    logical_file.metadata.series_list])
    if timezone.is_aware(start_date):
        start_date = timezone.make_naive(start_date)
    if timezone.is_aware(end_date):
        end_date = timezone.make_naive(end_date)
    value_dict = {'start': start_date.isoformat(), 'end': end_date.isoformat()}
    logical_file.metadata.create_element('coverage', type='period', value=value_dict)

    # add file level spatial coverage
    # check if we have single site or multiple sites
    sites = set([series['site']['siteCode'] for series in logical_file.metadata.series_list])
    if len(sites) == 1:
        series = logical_file.metadata.series_list[0]
        value_dict = {'east': series['site']['longitude'],
                      'north': series['site']['latitude'],
                      'projection': 'Unknown',
                      'units': "Decimal degrees"}
        logical_file.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for series in logical_file.metadata.series_list:
            latitude = float(series['site']['latitude'])
            if bbox['northlimit'] < latitude:
                bbox['northlimit'] = latitude
            if bbox['southlimit'] > latitude:
                bbox['southlimit'] = latitude

            longitude = float(series['site']['longitude'])
            if bbox['eastlimit'] < longitude:
                bbox['eastlimit'] = longitude

            if bbox['westlimit'] > longitude:
                bbox['westlimit'] = longitude
        logical_file.metadata.create_element('coverage', type='box', value=bbox)


def _validate_json_file(res_json_file):
    if res_json_file.resource_file:
        json_file_content = res_json_file.resource_file.read()
    else:
        json_file_content = res_json_file.fed_resource_file.read()
    try:
        json_data = json.loads(json_file_content)
    except:
        raise Exception("Not a json file")
    try:
        # validate json_data based on the schema
        jsonschema.Draft4Validator(TS_SCHEMA).validate(json_data)
    except jsonschema.ValidationError as ex:
        msg = "Not a valid reference time series json file. {}".format(ex.message)
        raise Exception(msg)

    ts_series_list = json_data['timeSeriesReferenceFile']['referencedTimeSeries']
    _validate_json_data(ts_series_list)
    return json_file_content


def _validate_json_data(series_data):
    # 1. here we need to test that the date values are actually date type data
    # the beginDate <= endDate
    # 2. the url is valid and live
    # 3. 'sampleMedium' key is present in each series
    # 4. 'valueCount' key is present in each series

    err_msg = "Invalid json file. {}"
    urls = []
    for series in series_data:
        try:
            start_date = parser.parse(series['beginDate'])
            end_date = parser.parse(series['endDate'])
        except Exception:
            raise Exception(err_msg.format("Invalid date values"))

        if timezone.is_aware(start_date):
            start_date = timezone.make_naive(start_date)
        if timezone.is_aware(end_date):
            end_date = timezone.make_naive(end_date)
        if start_date > end_date:
            raise Exception(err_msg.format("Invalid date values"))

        # validate requestInfo object
        request_info = series["requestInfo"]
        # validate refType
        if request_info['refType'] not in RefTimeseriesLogicalFile.get_allowed_ref_types():
            raise ValidationError("Invalid value for refType")
        # validate returnType
        if request_info['returnType'] not in RefTimeseriesLogicalFile.get_allowed_return_types():
            raise ValidationError("Invalid value for returnType")
        # validate serviceType
        if request_info['serviceType'] not in RefTimeseriesLogicalFile.get_allowed_service_types():
            raise ValidationError("Invalid value for serviceType")

        # chek that sampleMedium key is there
        if 'sampleMedium' not in series:
            raise ValidationError("sampleMedium is missing")
        # check  that valueCount key is there
        if 'valueCount' not in series:
            raise ValidationError("valueCount is missing")

        url = Request(request_info['url'])
        if url not in urls:
            urls.append(url)
            try:
                urlopen(url)
            except URLError:
                raise Exception(err_msg.format("Invalid web service URL found"))

        if 'method' in series:
            url = Request(series['method']['methodLink'])
            if url not in urls:
                urls.append(url)
                try:
                    urlopen(url)
                except URLError:
                    raise Exception(err_msg.format("Invalid method link found"))


TS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timeSeriesReferenceFile": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "abstract": {"type": "string"},
                "fileVersion": {"type": "string"},
                "keyWords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True
                },
                "symbol": {"type": "string"},
                "referencedTimeSeries": {
                    "type": "array",
                    "properties": {
                        "beginDate": {"type": "string"},
                        "endDate": {"type": "string"},
                        "site": {
                            "type": "object",
                            "properties": {
                                "siteCode": {"type": "string"},
                                "siteName": {"type": "string"},
                                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                "longitude": {"type": "number", "minimum": -180, "maximum": 180}
                            },
                            "required": ["siteCode", "siteName", "latitude", "longitude"],
                            "additionalProperties": False
                        },
                        "variable": {
                            "type": "object",
                            "properties": {
                                "variableCode": {"type": "string"},
                                "variableName": {"type": "string"}
                            },
                            "required": ["variableCode", "variableName"],
                            "additionalProperties": False
                        },
                        "method": {
                            "type": "object",
                            "properties": {
                                "methodDescription": {"type": "string"},
                                "methodLink": {"type": "string"}
                            },
                            "required": ["methodDescription", "methodLink"],
                            "additionalProperties": False
                        },
                        "requestInfo": {
                            "type": "object",
                            "properties": {
                                "netWorkName": {"type": "string"},
                                "refType": {"enum": ["WOF", "WPS", "DirectFile"]},
                                "returnType": {"enum": ["WaterML 1.1", "WaterML 2.0",
                                                        "TimeseriesML"]},
                                "serviceType": {"enum": ["SOAP", "REST"]},
                                "url": {"type": "string"}
                            },
                            "required": ["networkName", "refType", "returnType", "serviceType",
                                         "url"],
                            "additionalProperties": False
                        },
                        "sampleMedium": {"type": "string"},
                        "valueCount": {"type": "number"}
                    },
                    "required": ["beginDate", "endDate", "requestInfo",
                                 "site", "sampleMedium", "valueCount", "variable"],
                    "additionalProperties": False
                }
            },
            "required": ["fileVersion", "symbol", "referencedTimeSeries"],
            "additionalProperties": False
        }
    },
    "required": ["timeSeriesReferenceFile"],
    "additionalProperties": False
}
