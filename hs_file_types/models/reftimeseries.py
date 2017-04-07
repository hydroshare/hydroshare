import os
import shutil
import json
import logging
from dateutil import parser
from urllib2 import Request, urlopen, URLError
import jsonschema

from django.utils import timezone
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.template import Template, Context

from dominate.tags import div, form, button, h4, p, textarea, legend, table, tbody, tr, \
    th, td

from hs_core.hydroshare.resource import delete_resource_file
from hs_core.hydroshare import utils

from base import AbstractFileMetaData, AbstractLogicalFile


class TimeSeries(object):
    """represents a one timeseries metadata"""
    def __init__(self, site_name, site_code, latitude, longitude, variable_name, variable_code,
                 url, service_type, reference_type, return_type, start_date, end_date):
        self.site_name = site_name
        self.site_code = site_code
        self.latitude = latitude
        self.longitude = longitude
        self.variable_name = variable_name
        self.variable_code = variable_code
        self.url = url
        self.service_type = service_type
        self.reference_type = reference_type
        self.return_type = return_type
        self.start_date = start_date
        self.end_date = end_date

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

        return root_div.render(pretty=True)


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
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesLayerResource']['title']

    @property
    def abstract(self):
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesLayerResource']['abstract']

    @property
    def key_words(self):
        # had to name this property as key_words since the parent class has a model field keywords
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesLayerResource']['keyWords']

    @property
    def serieses(self):
        json_data_dict = self._json_to_dict()
        return json_data_dict['timeSeriesLayerResource']['REFTS']

    @property
    def time_serieses(self):
        ts_serieses = []
        for series in self.serieses:
            st_date = parser.parse(series['beginDate'])
            st_date = st_date.strftime('%m-%d-%Y')
            end_date = parser.parse(series['endDate'])
            end_date = end_date.strftime('%m-%d-%Y')
            ts_series = TimeSeries(site_name=series['site'],
                                   site_code=series['siteCode'],
                                   latitude=series['location']['latitude'],
                                   longitude=series['location']['longitude'],
                                   variable_name=series['variable'],
                                   variable_code=series['variableCode'],
                                   url=series['url'],
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
        sites = []
        site_codes = []
        for series in self.serieses:
            if series['siteCode'] not in site_codes:
                site = Site(name=series['site'], code=series['siteCode'],
                            latitude=series['location']['latitude'],
                            longitude=series['location']['longitude']
                            )
                sites.append(site)
                site_codes.append(site.code)
        return sites

    @property
    def variables(self):
        variables = []
        variable_codes = []
        for series in self.serieses:
            if series['variableCode'] not in variable_codes:
                variable = Variable(name=series['variable'], code=series['variableCode'])
                variables.append(variable)
                variable_codes.append(variable.code)
        return variables

    @property
    def web_services(self):
        services = []
        urls = []
        for series in self.serieses:
            if series['url'] not in urls:
                service = RefWebService(url=series['url'], service_type=series['serviceType'],
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
            if self.temporal_coverage:
                html_string += self.temporal_coverage.get_html()

            if self.spatial_coverage:
                html_string += self.spatial_coverage.get_html()

        ts_legend = legend("Time Serieses", cls="pull-left", style="margin-top:20px;")
        html_string += ts_legend.render()
        for series in self.time_serieses:
            html_string += series.get_html()

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

    def get_html_forms(self, dataset_name_form=True):
        """overrides the base class function"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(RefTimeseriesFileMetaData, self).get_html_forms()
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

            legend("Time Serieses", cls="pull-left", style="margin-top:20px;")
            for series in self.time_serieses:
                series.get_html()

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
        json_file_content_div = div(style="clear: both", cls="col-xs-12")
        with json_file_content_div:
            legend("Reference Timeseries JSON File Content")
            p(json_res_file.full_path[33:])
            # header_info = json.dumps(self.json_file_content, indent=4, sort_keys=True,
            #                          separators=(',', ': '))
            header_info = self.json_file_content
            if isinstance(header_info, str):
                header_info = unicode(header_info, 'utf-8')

            textarea(header_info, readonly="", rows="15",
                     cls="input-xlarge", style="min-width: 100%")

        return json_file_content_div

    def get_series_html(self):
        """
        generate html code for displaying data about each time series - should be
        used for for view and edit mode
        :return:
        """

        for series in self.serieses:
            # TODO: generate html for the series
            pass

    def _json_to_dict(self):
        return json.loads(self.json_file_content)


class RefTimeseriesLogicalFile(AbstractLogicalFile):
    """ Each resource file is assigned an instance of this logical file type on upload to
    Composite Resource """
    metadata = models.OneToOneField(RefTimeseriesFileMetaData, related_name="logical_file")
    data_type = "Reference timeseries data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .json.refts file can be set to this logical file group"""
        return [".json.refts"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file type allowed in this logical file group is: .json.refts"""
        return [".json.refts"]

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

        # get the file from irods
        res_file = utils.get_resource_file_by_id(resource, file_id)

        if res_file is None:
            raise ValidationError("File not found.")

        if res_file.extension != '.refts':
            raise ValidationError("Not a Ref Timeseries file.")

        files_to_add_to_resource = []
        if res_file.has_generic_logical_file:
            # TODO: validate the temp_file (json file)
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
                    fed_file_full_path = ''
                    if resource.resource_federation_path:
                        fed_file_full_path = os.path.join(resource.root_path,
                                                          file_folder)

                    new_res_file = utils.add_file_to_resource(
                        resource, uploaded_file, folder=file_folder,
                        fed_res_file_name_or_path=fed_file_full_path
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
    sites = set([series['siteCode'] for series in logical_file.metadata.serieses])
    if len(sites) == 1:
        series = logical_file.metadata.serieses[0]
        value_dict = {'east': series['location']['longitude'],
                      'north': series['location']['latitude'],
                      'projection': 'Unknown',
                      'units': "Decimal degrees"}
        logical_file.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for series in logical_file.metadata.serieses:
            latitude = float(series['location']['latitude'])
            if bbox['northlimit'] < latitude:
                bbox['northlimit'] = latitude
            if bbox['southlimit'] > latitude:
                bbox['southlimit'] = latitude

            longitude = float(series['location']['longitude'])
            if bbox['eastlimit'] < longitude:
                bbox['eastlimit'] = longitude

            if bbox['westlimit'] > longitude:
                bbox['westlimit'] = longitude
        logical_file.metadata.create_element('coverage', type='box', value=bbox)


def _validate_json_file(res_json_file):
    json_file_content = res_json_file.resource_file.read()
    try:
        json_data = json.loads(json_file_content)
    except:
        raise Exception("Not a json file")
    try:
        # validate json_data based on the schema
        jsonschema.validate(json_data, TS_SCHEMA)
    except Exception:
        raise Exception("Not a valid reference time series json file")

    # test that there is no duplicate time series data
    ts_serieses = json_data['timeSeriesLayerResource']['REFTS']
    locations = []
    for item in ts_serieses:
        # remove the inner dictionary item with key of 'location'
        if 'location' in item.keys():
            locations.append(item.pop('location'))

    ts_unique_serieses = [dict(t) for t in set(tuple(d.items()) for d in ts_serieses)]
    if len(ts_serieses) != len(ts_unique_serieses):
        raise Exception("Duplicate time series found")
    if not locations:
        raise Exception("Not a valid reference time series json file")
    _validate_json_data(ts_serieses)
    return json_file_content


def _validate_json_data(series_data):
    # 1. here we need to test that the date values are actually date type data
    # the beginDate <= endDate
    # 2. the url is valid and live

    err_msg = "Invalid json file. {}"
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
        req = Request(series['url'])
        try:
            urlopen(req)
        except URLError:
            raise Exception(err_msg.format("Invalid URL found"))

TS_SCHEMA = {
    "type": "object",
    "properties": {
        "timeSeriesLayerResource": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "abstract": {"type": "string"},
                "fileVersion": {"type": "number"},
                "keyWords": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "symbol": {"type": "string"},
                "REFTS": {
                    "type": "array",
                    "properties": {
                        "beginDate": {"type": "string"},
                        "endDate": {"type": "string"},
                        "location": {
                            "type": "object",
                            "properties": {
                                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                            },
                        },
                        "netWorkName": {"type": "string"},
                        "refType": {"type": "string"},
                        "returnType": {"type": "string"},
                        "serviceType": {"type": "string"},
                        "site": {"type": "string"},
                        "siteCode": {"type": "string"},
                        "url": {"type": "string"},
                        "variable": {"type": "string"},
                        "variableCode": {"type": "string"}
                    },
                    "required": ["beginDate", "endDate", "location", "netWorkName", "refType",
                                 "returnType", "serviceType", "site", "siteCode", "url",
                                 "variable", "variableCode"]
                }
            },
            "required": ["title", "abstract", "fileVersion", "keyWords", "symbol", "REFTS"]
        }
    }
}
