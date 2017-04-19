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
from django.core.files.uploadedfile import UploadedFile
from django.template import Template, Context

from dominate.tags import div, form, button, h4, p, textarea, legend, table, tbody, tr, \
    th, td, a

from hs_core.hydroshare.resource import delete_resource_file
from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData

from base import AbstractFileMetaData, AbstractLogicalFile


class TimeSeries(object):
    """represents a one timeseries metadata"""
    def __init__(self, network_name, site_name, site_code, latitude, longitude, variable_name,
                 variable_code, method_description, method_link, sample_medium, url, service_type,
                 reference_type, return_type, start_date, end_date):
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

        # encode web service data
        hs_network_name = etree.SubElement(rdf_description, '{%s}networkName'
                                           % NAMESPACES['hsterms'])
        hs_network_name.text = self.network_name
        hs_ref_type = etree.SubElement(rdf_description, '{%s}refType' % NAMESPACES['hsterms'])
        hs_ref_type.text = self.reference_type
        hs_retrun_type = etree.SubElement(rdf_description, '{%s}returnType' % NAMESPACES['hsterms'])
        hs_retrun_type.text = self.return_type
        hs_service_type = etree.SubElement(rdf_description, '{%s}serviceType'
                                           % NAMESPACES['hsterms'])
        hs_service_type.text = self.reference_type
        hs_wsdl_url = etree.SubElement(rdf_description, '{%s}wsdlURL' % NAMESPACES['hsterms'])
        hs_wsdl_url.text = self.url

        # encode date (duration) data
        hs_begin_date = etree.SubElement(rdf_description, '{%s}beginDate' % NAMESPACES['hsterms'])
        st_date = parser.parse(self.start_date)
        hs_begin_date.text = st_date.isoformat()
        hs_end_date = etree.SubElement(rdf_description, '{%s}endDate' % NAMESPACES['hsterms'])
        end_date = parser.parse(self.end_date)
        hs_end_date.text = end_date.isoformat()

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

    @property
    def title(self):
        """get the title associated with this ref time series"""
        json_data_dict = self._json_to_dict()
        if 'title' in json_data_dict['timeSeriesLayerResource']:
            return json_data_dict['timeSeriesLayerResource']['title']
        return ''

    @property
    def abstract(self):
        """get the abstract associated with this ref time series"""
        json_data_dict = self._json_to_dict()
        if 'abstract' in json_data_dict['timeSeriesLayerResource']:
            return json_data_dict['timeSeriesLayerResource']['abstract']
        return ''

    @property
    def key_words(self):
        """get a list of all keywords associated with this ref time series"""
        # had to name this property as key_words since the parent class has a model field keywords
        json_data_dict = self._json_to_dict()
        if 'keyWords' in json_data_dict['timeSeriesLayerResource']:
            return json_data_dict['timeSeriesLayerResource']['keyWords']
        return []

    @property
    def serieses(self):
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesLayerResource']['referencedTimeSeries']

    @property
    def time_serieses(self):
        """get a list of all time series associated with this ref time series"""
        ts_serieses = []
        for series in self.serieses:
            st_date = parser.parse(series['beginDate'])
            st_date = st_date.strftime('%m-%d-%Y')
            end_date = parser.parse(series['endDate'])
            end_date = end_date.strftime('%m-%d-%Y')
            method_des = ''
            method_link = ''
            if 'method' in series:
                method_des = series['method']['methodDescription']
                method_link = series['method']['methodLink']

            sample_medium = series.get('sampleMedium', "")

            ts_series = TimeSeries(network_name=series['networkName'],
                                   site_name=series['site']['siteName'],
                                   site_code=series['site']['siteCode'],
                                   latitude=series['site']['latitude'],
                                   longitude=series['site']['longitude'],
                                   variable_name=series['variable']['variableName'],
                                   variable_code=series['variable']['variableCode'],
                                   method_description=method_des,
                                   method_link=method_link,
                                   sample_medium=sample_medium,
                                   url=series['wsdlURL'],
                                   service_type=series['serviceType'],
                                   reference_type=series['refType'],
                                   return_type=series['returnType'],
                                   start_date=st_date,
                                   end_date=end_date
                                   )
            ts_serieses.append(ts_series)
        return ts_serieses

    @property
    def sites(self):
        """get a list of all sites associated with this ref time series"""
        sites = []
        site_codes = []
        for series in self.serieses:
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
        for series in self.serieses:
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
        for series in self.serieses:
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
        for series in self.serieses:
            if series['wsdlURL'] not in urls:
                service = RefWebService(url=series['wsdlURL'], service_type=series['serviceType'],
                                        reference_type=series['refType'],
                                        return_type=series['returnType'])
                services.append(service)
                urls.append(service.url)
        return services

    # TODO: other properties to go here

    def get_html(self):
        """overrides the base class function"""

        html_string = super(RefTimeseriesFileMetaData, self).get_html()
        if not self.has_metadata:
            root_div = div(cls="alert alert-warning alert-dismissible", role="alert")
            with root_div:
                h4("No file level metadata exists for the selected file.")
            html_string = root_div.render()
        else:
            abstract_div = div(cls="col-xs-12 content-block")
            with abstract_div:
                legend("Abstract")
                p(self.abstract)

            html_string += abstract_div.render()
            if self.temporal_coverage:
                html_string += self.temporal_coverage.get_html()

            if self.spatial_coverage:
                html_string += self.spatial_coverage.get_html()

        html_string += self.get_ts_series_html().render()

        # TODO: delete these commented code
        # site_legend = legend("Sites", cls="pull-left", style="margin-top:20px;")
        # html_string += site_legend.render()
        # for site in self.sites:
        #     html_string += site.get_html()
        #
        # variable_legend = legend("Variables", cls="pull-left", style="margin-top:20px;")
        # html_string += variable_legend.render()
        # for variable in self.variables:
        #     html_string += variable.get_html()
        #
        # service_legend = legend("Web Services", cls="pull-left", style="margin-top:20px;")
        # html_string += service_legend.render()
        # for service in self.web_services:
        #     html_string += service.get_html()

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
            for index, series in enumerate(self.time_serieses):
                panel_group_div.add(series.get_html(index + 1))

        return root_div

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True):
        """overrides the base class function"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(RefTimeseriesFileMetaData, self).get_html_forms(temporal_coverage=False)
            abstract_div = div(cls="col-xs-12 content-block")
            with abstract_div:
                legend("Abstract")
                p(self.abstract)
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

            # TODO: delete these commented code
            # legend("Sites", cls="pull-left", style="margin-top:20px;")
            # for site in self.sites:
            #     site.get_html()
            #
            # legend("Variables", cls="pull-left", style="margin-top:20px;")
            # for variable in self.variables:
            #     variable.get_html()
            #
            # legend("Web Services", cls="pull-left", style="margin-top:20px;")
            # for service in self.web_services:
            #     service.get_html()

            self.get_json_file_data_html()

        template = Template(root_div.render())
        context_dict = dict()
        temp_cov_form = self.get_temporal_coverage_form()
        spatial_cov_form = self.get_spatial_coverage_form()

        context_dict["temp_form"] = temp_cov_form
        context_dict["spatial_form"] = spatial_cov_form
        context = Context(context_dict)
        rendered_html = template.render(context)
        return rendered_html

    def get_json_file_data_html(self):
        """
        Generates html code to display the contents of the json file file. The generated html
        is used for ref timeseries file type metadata view and edit modes.
        :return:
        """

        json_res_file = self.logical_file.files.first()
        json_file_content_div = div(style="clear:both;", cls="col-xs-12 content-block")
        with json_file_content_div:
            legend("Reference Time Series JSON File Content", style="margin-top:20px;")
            p(json_res_file.full_path[33:])
            # header_info = json.dumps(self.json_file_content, indent=4, sort_keys=True,
            #                          separators=(',', ': '))
            header_info = self.json_file_content
            if isinstance(header_info, str):
                header_info = unicode(header_info, 'utf-8')

            textarea(header_info, readonly="", rows="15",
                     cls="input-xlarge", style="min-width: 100%")

        return json_file_content_div

    def add_to_xml_container(self, container):
        """Generates xml+rdf representation of all metadata elements associated with this
        logical file type instance"""

        container_to_add_to = super(RefTimeseriesFileMetaData, self).add_to_xml_container(container)
        for series in self.time_serieses:
            series.add_to_xml_container(container_to_add_to)

    def _json_to_dict(self):
        return json.loads(self.json_file_content)


class RefTimeseriesLogicalFile(AbstractLogicalFile):
    """ Each resource file is assigned an instance of this logical file type on upload to
    Composite Resource """
    metadata = models.OneToOneField(RefTimeseriesFileMetaData, related_name="logical_file")
    data_type = "referenceTimeseriesData"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .refts file can be set to this logical file group"""
        return [".refts"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file type allowed in this logical file group is: .refts"""
        return [".refts"]

    @classmethod
    def get_allowed_ref_types(cls):
        """returns a list of refType controlled vocabulary terms"""
        return ['WOF']

    @classmethod
    def get_allowed_return_types(cls):
        """returns a list of returnType controlled vocabulary terms"""
        return ['WaterML 1.1']

    @classmethod
    def get_allowed_service_types(cls):
        """returns a list of serviceType controlled vocabulary terms"""
        return ['SOAP']

    @classmethod
    def create(cls):
        # this custom method MUST be used to create an instance of this class
        rf_ts_metadata = RefTimeseriesFileMetaData.objects.create(json_file_content="No data")
        return cls.objects.create(metadata=rf_ts_metadata)

    @classmethod
    def set_file_type(cls, resource, file_id, user):
        """
            Sets a json resource file to RefTimeseriesFile type
            :param resource: an instance of resource type CompositeResource
            :param file_id: id of the resource file to be set as RefTimeSeriesFile type
            :param user: user who is setting the file type
            :return:
            """

        log = logging.getLogger()

        # get the the selected resource file object
        res_file = utils.get_resource_file_by_id(resource, file_id)

        if res_file is None:
            raise ValidationError("File not found.")

        if res_file.extension != '.refts':
            raise ValidationError("Not a Ref Time Series file.")

        files_to_add_to_resource = []
        if res_file.has_generic_logical_file:
            try:
                json_file_content = _validate_json_file(res_file)
            except Exception as ex:
                raise ValidationError(ex.message)

            # get the file from irods to temp dir
            temp_file = utils.get_file_from_irods(res_file)
            temp_dir = os.path.dirname(temp_file)
            files_to_add_to_resource.append(temp_file)
            file_folder = res_file.file_folder
            with transaction.atomic():
                # first delete the json file that we retrieved from irods
                # for setting it to reftimeseries file type
                delete_resource_file(resource.short_id, res_file.id, user)

                # create a reftiemseries logical file object to be associated with
                # resource files
                logical_file = cls.create()

                logical_file.metadata.json_file_content = json_file_content
                logical_file.metadata.save()

                try:
                    # add the json file back to the resource
                    uploaded_file = UploadedFile(file=open(temp_file, 'rb'),
                                                 name=os.path.basename(temp_file))

                    new_res_file = utils.add_file_to_resource(
                        resource, uploaded_file, folder=file_folder
                    )
                    # make the resource file we added as part of the logical file
                    logical_file.add_resource_file(new_res_file)
                    logical_file.metadata.save()
                    logical_file.dataset_name = logical_file.metadata.title
                    logical_file.save()
                    # extract metadata
                    _extract_metadata(resource, logical_file)
                    log.info("RefTimeseries file type - json file was added to the resource.")
                except Exception as ex:
                    msg = "RefTimeseries file type. Error when setting file type. Error:{}"
                    msg = msg.format(ex.message)
                    log.exception(msg)
                    # TODO: in case of any error put the original file back and
                    # delete the folder that was created
                    raise ValidationError(msg)
                finally:
                    # remove temp dir
                    if os.path.isdir(temp_dir):
                        shutil.rmtree(temp_dir)

                log.info("RefTimeseries file type was created.")

        else:
            err_msg = "Selected file is not part of a GenericLogical file."
            log.error(err_msg)
            raise ValidationError(err_msg)

    def get_copy(self):
        """Overrides the base class method"""

        copy_of_logical_file = super(RefTimeseriesLogicalFile, self).get_copy()
        copy_of_logical_file.metadata.json_file_content = self.metadata.json_file_content
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.save()
        return copy_of_logical_file


def _extract_metadata(resource, logical_file):
    # add resource level title if necessary
    if resource.metadata.title.value == 'Untitled resource':
        resource.metadata.update_element('title', resource.metadata.title.id,
                                         value=logical_file.metadata.title)

    # add resource level abstract id necessary
    if resource.metadata.description is None:
        resource.metadata.create_element('description', abstract=logical_file.metadata.abstract)
    # add resource level keywords
    resource_keywords = [kw.value.lower() for kw in resource.metadata.subjects.all()]
    for kw in logical_file.metadata.key_words:
        if kw.lower() not in resource_keywords:
            resource.metadata.create_element('subject', value=kw)

    # add to the file level metadata
    logical_file.metadata.keywords = logical_file.metadata.key_words
    logical_file.metadata.save()

    # add file level temporal coverage
    start_date = min([parser.parse(series['beginDate']) for series in
                     logical_file.metadata.serieses])
    end_date = max([parser.parse(series['endDate']) for series in
                    logical_file.metadata.serieses])
    if timezone.is_aware(start_date):
        start_date = timezone.make_naive(start_date)
    if timezone.is_aware(end_date):
        end_date = timezone.make_naive(end_date)
    value_dict = {'start': start_date.isoformat(), 'end': end_date.isoformat()}
    logical_file.metadata.create_element('coverage', type='period', value=value_dict)

    # add file level spatial coverage
    # check if we have single site or multiple sites
    sites = set([series['site']['siteCode'] for series in logical_file.metadata.serieses])
    if len(sites) == 1:
        series = logical_file.metadata.serieses[0]
        value_dict = {'east': series['site']['longitude'],
                      'north': series['site']['latitude'],
                      'projection': 'Unknown',
                      'units': "Decimal degrees"}
        logical_file.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for series in logical_file.metadata.serieses:
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
        jsonschema.validate(json_data, TS_SCHEMA)
    except Exception:
        raise Exception("Not a valid reference time series json file")

    # TODO: validate that there are no duplicate time series
    # test that there is no duplicate time series data
    ts_serieses = json_data['timeSeriesReferenceFile']['referencedTimeSeries']
    # locations = []
    # for item in ts_serieses:
    #     # remove the inner dictionary item with key of 'location'
    #     if 'location' in item.keys():
    #         locations.append(item.pop('location'))
    #
    # ts_unique_serieses = [dict(t) for t in set(tuple(d.items()) for d in ts_serieses)]
    # if len(ts_serieses) != len(ts_unique_serieses):
    #     raise Exception("Duplicate time series found")
    # if not locations:
    #     raise Exception("Not a valid reference time series json file")
    _validate_json_data(ts_serieses)
    return json_file_content


def _validate_json_data(series_data):
    # 1. here we need to test that the date values are actually date type data
    # the beginDate <= endDate
    # 2. the url is valid and live

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

        # validate refType
        if series['refType'] not in RefTimeseriesLogicalFile.get_allowed_ref_types():
            raise ValidationError("Invalid value for refType")
        # validate returnType
        if series['returnType'] not in RefTimeseriesLogicalFile.get_allowed_return_types():
            raise ValidationError("Invalid value for returnType")
        # validate serviceType
        if series['serviceType'] not in RefTimeseriesLogicalFile.get_allowed_service_types():
            raise ValidationError("Invalid value for serviceType")

        url = Request(series['wsdlURL'])
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
                    "items": {"type": "string"}
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
                                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                            },
                        },
                        "variable": {
                            "type": "object",
                            "properties": {
                                "variableCode": {"type": "string"},
                                "variableName": {"type": "string"},
                            },
                        },
                        "method": {
                            "type": "object",
                            "properties": {
                                "methodDescription": {"type": "string"},
                                "methodLink": {"type": "string"},
                            },
                        },
                        "netWorkName": {"type": "string"},
                        "refType": {"type": "string"},
                        "returnType": {"type": "string"},
                        "serviceType": {"type": "string"},
                        "wsdlURL": {"type": "string"},
                        "sampleMedium": {"type": "string"},
                    },
                    "required": ["beginDate", "endDate", "netWorkName", "refType",
                                 "returnType", "serviceType", "site", "siteCode", "wsdlURL",
                                 "variable"]
                }
            },
            "required": ["fileVersion", "referencedTimeSeries"]
        }
    }
}
