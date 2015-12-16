from suds import MethodNotFound, WebFault
from suds.transport import TransportError
from suds.client import Client
from lxml import etree
from django.http import Http404
from xml.sax._exceptions import SAXParseException
from datetime import datetime
from matplotlib.pyplot import savefig
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateFormatter, AutoDateLocator
import operator
import requests
import csv
import collections
import os
from StringIO import StringIO
from hs_core import hydroshare

from ref_ts.owslib_revised.waterml.wml11 import WaterML_1_1 as wml11
from ref_ts.owslib_revised.waterml.wml10 import WaterML_1_0 as wml10

def wmlParse(response, ver=11):
    if ver == 11:
        return wml11(response).response
    elif ver == 10:
        return wml10(response).response
    else:
        raise

def wmlVersion(wsdl_url):
    ver = -1
    if "1_0.asmx?" in wsdl_url.lower():
        ver = 10
    elif "1_1.asmx?" in wsdl_url.lower():
        ver = 11
    return ver

def check_url_and_version(wsdl_url):
    if not wsdl_url.lower().endswith('.asmx?wsdl'):
        raise Http404("The correct url format ends in '.asmx?WSDL'.")
    return wmlVersion(wsdl_url)

def connect_wsdl_url(wsdl_url):
    try:
        client = Client(wsdl_url)
    except TransportError:
        raise Http404('Url not found')
    except ValueError:
        raise Http404('Invalid url')  # ought to be a 400, but no page implemented for that
    except SAXParseException:
        raise Http404("The correct url format ends in '.asmx?WSDL'.")
    except:
        raise Http404("Sorry, but we've encountered an unexpected error.")
    return client

def get_version(root):
    wml_version = None
    for element in root.iter():
        if '{http://www.opengis.net/waterml/2.0}Collection' in element.tag:
            wml_version = '2.0'
            break
        if '{http://www.cuahsi.org/waterML/1.1/}timeSeriesResponse' \
                or '{http://www.cuahsi.org/waterML/1.0/}timeSeriesResponse' in element.tag:
            wml_version = '1'
            break
    return wml_version

def sites_from_soap(wsdl_url, locations='[:]'):
    """
    Note: locations (a list) is given by CUAHSI WOF standard

    returns:
    a list of site names and codes at the given locations
    """
    wml_ver = check_url_and_version(wsdl_url)
    client = connect_wsdl_url(wsdl_url)

    try:
        if wml_ver == 11:
            response = client.service.GetSites(locations)
        elif wml_ver == 10:
            response = client.service.GetSitesXml(locations)
    except MethodNotFound:
        raise Http404("Method 'GetSites' not found")
    except WebFault:
        raise Http404('This service does not support an all sites search. \
        Please provide a list of locations')  # ought to be a 400, but no page implemented for that
    except:
        raise Http404("Sorry, but we've encountered an unexpected error. This is most likely\
         due to incorrect formatting in the web service response.")

    sites_list = []
    try:
        response = response.encode('utf-8')
        wml_sites = wmlParse(response, wml_ver)
        counter = 0
        for site in wml_sites.sites:
            siteName = site.name
            siteCode = site.codes[0]
            netWork = site.site_info.net_work
            counter += 1
            sites_list.append("%s. %s [%s:%s]" % (str(counter), siteName, netWork, siteCode))
    except:
        return "Parsing error: The Data in the WSDL Url '{0}' was not correctly formatted \
according to the WaterOneFlow standard given at 'http://his.cuahsi.org/wofws.html#waterml'.".format(wsdl_url)
    return sites_list

# get variable names list
def site_info_from_soap(wsdl_url, **kwargs):
    site = kwargs['site']
    index = site.rfind(" [")
    site = site[index+2:len(site)-1]
    network = (site.split(':'))[0]
    wml_ver = check_url_and_version(wsdl_url)
    client = connect_wsdl_url(wsdl_url)
    variables_list = []
    try:
        response = client.service.GetSiteInfo(site)
        response = response.encode('utf-8')
        wml_siteinfo = wmlParse(response, wml_ver)
        counter = 0
        for series in wml_siteinfo.sites[0].series_catalogs[0].series:
            wml_variable = series.variable
            variable_name = wml_variable.variable_name
            variable_code = wml_variable.variable_code
            method_id = series.method_id
            source_id = series.source_id
            value_count = series.value_count
            quality_control_level_id = series.quality_control_level_id
            start_date = series.begin_date_time
            end_date = series.end_date_time
            counter += 1
            variables_list.append("%s. %s (ID:%s, Count:%s) [%s:%s:methodCode=%s:sourceCode=%s:qualityControlLevelCode=%s]" %
                                 (str(counter), variable_name, variable_code, str(value_count), network, variable_code,
                                  method_id, source_id, quality_control_level_id))

        return variables_list
    except MethodNotFound:
        raise Http404("Method 'GetSiteInfo' not found")
    except:
        return "Parsing error: The Data in the WSDL Url '{0}' was not correctly formatted \
according to the WaterOneFlow standard given at 'http://his.cuahsi.org/wofws.html#waterml'.".format(wsdl_url)

def time_to_int(t):
    ''' if time format looks like '2014-07-22T10:45:00.000' '''
    try:
        ret = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S.%f').strftime('%s'))
    except ValueError:
        try:
            ret = int(datetime.strptime(unicode(t), '%Y-%m-%d').strftime('%s'))
        except ValueError:
            try:
                # if time format looks like '2014-07-22T10:45:00'

                ret = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S').strftime('%s'))
            except ValueError:
                try:
                    #if the time format looks like '2014-07-22 10:45:00'
                    ret = int(datetime.strptime(unicode(t), '%Y-%m-%d %H:%M:%S').strftime('%s'))
                except:
                # if time format looks like '2014-07-22T10:45:00.000-05:00'
                    offset_hrs = int(t[-6:-3])
                    offset_min = int(t[-6]+t[-2:])
                    t = t[:-6]
                    epoch_secs = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S').strftime('%s'))
                    ret = epoch_secs + offset_hrs*3600 + offset_min*60
    return ret

def parse_1_0_and_1_1_owslib(wml_string, wml_ver):

        wml_str, variable_code, variable_name, net_work, site_name, site_code, elevation, vertical_datum,\
        longitude, latitude, projection, srs, noDataValue, unit_abbr, unit_code, unit_name, unit_type,\
        method_code, method_id, method_description, source_code, source_id, quality_control_level_code,\
        quality_control_level_definition, for_graph, method_code_query, source_code_query,  \
        quality_control_level_code_query, start_date, end_date = None, None, None, None, None, None, None, None,\
                                                                 None, None, None, None, None, None,\
        None, None, None, None, None, None, None, None, None, None,  None, None, None, None, None, None

        wmlVaules = wmlParse(wml_string, wml_ver)

        variable_query = wmlVaules.query_info.criteria.variable_param
        if variable_query is None:
            for p in wmlVaules.query_info.criteria.parameters:
                if p[0].lower() == "variable":
                    variable_query = p[1]
        if variable_query is not None:
            params = variable_query.split(':')
            for param in params:
                if "methodcode" in param.lower():
                    method_code_query = (param.split('='))[1]
                elif "sourcecode" in param.lower():
                    source_code_query = (param.split('='))[1]
                elif "qualitycontrollevelcode" in param.lower():
                    quality_control_level_code_query = (param.split('='))[1]

        wml_str = wml_string
        variable_code = wmlVaules.variable_codes[0]
        variable_name = wmlVaules.variable_names[0]

        if hasattr(wmlVaules.time_series[0], "source_info"):
            sourceInfo_obj = wmlVaules.time_series[0].source_info
            if sourceInfo_obj:
                net_work = sourceInfo_obj.net_work if hasattr(sourceInfo_obj, "net_work") else None
                site_name = sourceInfo_obj.site_name if hasattr(sourceInfo_obj, "site_name") else None
                site_codes = sourceInfo_obj.site_codes if hasattr(sourceInfo_obj, "site_codes") else None
                if site_codes and len(site_codes) > 0:
                    site_code = site_codes[0]
                elevation = sourceInfo_obj.elevation if hasattr(sourceInfo_obj, "elevation") else None
                vertical_datum = sourceInfo_obj.vertical_datum if hasattr(sourceInfo_obj, "vertical_datum") else None
                loc_obj = sourceInfo_obj.location if hasattr(sourceInfo_obj, "location") else None
                if loc_obj:
                    geo_coords_tuple_list = loc_obj.geo_coords if hasattr(loc_obj, "geo_coords") else None
                    if geo_coords_tuple_list and len(geo_coords_tuple_list) > 0:
                        longitude = geo_coords_tuple_list[0][0]
                        latitude = geo_coords_tuple_list[0][1]

                    local_coords_tuple_list = loc_obj.local_sites if hasattr(loc_obj, "local_sites") else None
                    if local_coords_tuple_list and len(local_coords_tuple_list) > 0:
                        local_coords_x = local_coords_tuple_list[0][0]
                        local_coords_y = local_coords_tuple_list[0][1]
                    projection_list = loc_obj.projections if hasattr(loc_obj, "projections") else None
                    if projection_list and len(projection_list) >  0:
                       projection = projection_list[0]
                    srs_list = loc_obj.srs if hasattr(loc_obj, "srs") else None
                    if srs_list and len(srs_list) > 0:
                        srs = srs_list[0]

        variable_obj = wmlVaules.time_series[0].variable if hasattr(wmlVaules.time_series[0], "variable") else None
        noDataValue = variable_obj.no_data_value if hasattr(variable_obj, "no_data_value") else None
        unit_obj = variable_obj.unit if hasattr(variable_obj, "unit") else None
        if unit_obj:
            unit_abbr = unit_obj.abbreviation if hasattr(unit_obj, "abbreviation") else None
            unit_code = unit_obj.code if hasattr(unit_obj, "code") else None
            unit_name = unit_obj.name if hasattr(unit_obj, "name") else None
            unit_type = unit_obj.unit_type if hasattr(unit_obj, "unit_type") else None

        value_obj = wmlVaules.time_series[0].values[0]
        value_list = value_obj.values if hasattr(value_obj, "values") else None
        x = []
        y = []
        for_graph = {"x": x, "y": y}
        if value_list:
            for val in value_list:
                t = val.date_time
                t_str = t.isoformat()
                x.append(t_str)
                y.append(float(val.value))

        start_date = value_list[0].date_time.isoformat()
        end_date = value_list[len(value_list)-1].date_time.isoformat()
        method_list = value_obj.methods if hasattr(value_obj, "methods") else None
        if method_list and len(method_list) > 0:
            method_obj = method_list[0]
            method_code = method_obj.code if hasattr(method_obj, "code") else None
            method_id = method_obj.id if hasattr(method_obj, "id") else None
            method_description = method_obj.description if hasattr(method_obj, "description") else None
        if method_code is None:
            method_code = method_code_query

        source_list = value_obj.sources if hasattr(value_obj, "sources") else None
        if source_list and len(source_list) > 0:
            source_code = source_list[0].code if hasattr(source_list[0], "code") else None
            source_id = source_list[0].code if hasattr(source_list[0], "id") else None
        if source_code is None:
            source_code = source_code_query

        quality_control_level_list = value_obj.quality_control_levels if \
            hasattr(value_obj, "quality_control_levels") else None
        if quality_control_level_list and len(quality_control_level_list) > 0:
            quality_control_level_obj = quality_control_level_list[0]
            quality_control_level_code = quality_control_level_obj.code if \
                hasattr(quality_control_level_obj, "code") else None
            quality_control_level_definition = quality_control_level_obj.definition if \
                hasattr(quality_control_level_obj, "definition") else None

        if quality_control_level_code is None:
            quality_control_level_code = quality_control_level_code_query

        if quality_control_level_definition is None:
            if quality_control_level_code is None or quality_control_level_code == "0":
                quality_control_level_definition = "Raw Data"
            elif quality_control_level_code == "1":
                quality_control_level_definition = "Quality Controlled Data"
            elif quality_control_level_code == "2":
                quality_control_level_definition = "Derived Products"
            elif quality_control_level_code == "3":
                quality_control_level_definition = "Interpreted Products"
            elif quality_control_level_code == "4":
                quality_control_level_definition = "Knowledge Products"
            else:
                quality_control_level_definition = 'Unknown'


        return {'wml_str': wml_str,
                'variable_code': variable_code,
                'variable_name': variable_name,
                "net_work": net_work,
                'site_name': site_name,
                'site_code': site_code,
                'elevation': elevation,
                'vertical_datum': vertical_datum,
                'latitude': latitude,
                'longitude': longitude,
                'projection': projection,
                'srs': srs,
                'noDataValue': noDataValue,
                'unit_abbr': unit_abbr,
                'unit_code': unit_code,
                'unit_name': unit_name,
                'unit_type': unit_type,
                'method_code': method_code,
                'method_id': method_id,
                'method_description': method_description,
                'source_code': source_code,
                'source_id': source_id,
                'quality_control_level_code': quality_control_level_code,
                'quality_control_level_definition': quality_control_level_definition,
                'for_graph': for_graph,
                "start_date": start_date,
                "end_date": end_date
                }

def parse_1_0_and_1_1(root):
        time_series_response_present = False
        if 'timeSeriesResponse' in root.tag:
            time_series_response_present = True
        elif 'timeSeriesResponse' in root.text[:19]:
            root = etree.fromstring(root.text)
            time_series_response_present = True
        if time_series_response_present:
            time_series = root[1]
            ts = etree.tostring(time_series)
            values = {}
            for_graph = []
            noDataValue, units, site_name, site_code, variable_name, \
            variable_code, latitude, longitude, methodCode, method, QCcode, \
            QClevel = None, None, None, None, None, None, None, None, None, None, None, None
            unit_is_set = False
            methodCode_set = False
            QCcode_set = False
            for element in root.iter():
                brack_lock = -1
                if '}' in element.tag:
                    brack_lock = element.tag.index('}')  #The namespace in the tag is enclosed in {}.
                tag = element.tag[brack_lock+1:]     #Takes only actual tag, no namespace
                if 'unitName' == tag:  # in the xml there is a unit for the value, then for time. just take the first
                    if not unit_is_set:
                        units = element.text
                        unit_is_set = True
                if 'value' == tag:
                    values[element.attrib['dateTime']] = element.text
                    if not methodCode_set:
                        for a in element.attrib:
                            if 'methodCode' in a:
                                methodCode = element.attrib[a]
                                methodCode_set = True
                            if 'qualityControlLevelCode' in a:
                                QCcode = element.attrib[a]
                                QCcode_set = True
                if 'siteName' == tag:
                    site_name = element.text
                if 'siteCode' == tag:
                    site_code = element.text
                if 'variableName' == tag:
                    variable_name = element.text
                if 'variableCode' == tag:
                    variable_code = element.text
                if 'latitude' == tag:
                    latitude = element.text
                if 'longitude' == tag:
                    longitude = element.text
                if 'noDataValue' == tag:
                    noDataValue = element.text

            if methodCode == 1:
                method = 'No method specified'
            else:
                method = 'Unknown method'

            if QCcode == 0:
                QClevel = "Raw Data"
            elif QCcode == "0":
                QClevel = "Raw Data"
            elif QCcode == 1:
                QClevel = "Quality Controlled Data"
            elif QCcode == "1":
                QClevel = "Quality Controlled Data"
            elif QCcode == 2:
                QClevel = "Derived Products"
            elif QCcode == "2":
                QClevel = "Derived Products"
            elif QCcode == 3:
                QClevel = "Interpreted Products"
            elif QCcode == "3":
                QClevel = "Interpreted Products"
            elif QCcode == 4:
                QClevel = "Knowledge Products"
            elif QCcode == "4":
                QClevel = "Knowledge Products"
            else:
                QClevel = 'Unknown'

            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            return {'time_series': ts,
                    'site_name': site_name,
                    'site_code': site_code,
                    'variable_name': variable_name,
                    'variable_code': variable_code,
                    'units': units,
                    'values': values,
                    'for_graph': for_graph,
                    'wml_version': '1',
                    'latitude': latitude,
                    'longitude': longitude,
                    'noDataValue': noDataValue,
                    'QClevel': QClevel,
                    'method': method}
        else:
            return "Parsing error: The waterml document doesn't appear to be a WaterML 1.0/1.1 time series"

def parse_2_0(root):
        if 'Collection' in root.tag:
            ts = etree.tostring(root)
            keys = []
            vals = []
            for_graph = []
            QClevel, units, site_name, variable_name, latitude, longitude, method, site_code, variable_code, sample_medium = None, None, None, None, None, None, None, None, None, None
            name_is_set, site_code_set = False, False
            variable_name = root[1].text
            for element in root.iter():
                if 'MeasurementTVP' in element.tag:
                        for e in element:
                            if 'time' in e.tag:
                                keys.append(e.text)
                            if 'value' in e.tag:
                                vals.append(e.text)
                if 'uom' in element.tag:
                    units = element.attrib['code']
                if 'MonitoringPoint' in element.tag:
                    for e in element.iter():
                        if 'identifier' in e.tag and not site_code_set:
                            site_code = e.text
                            site_code_set = True
                        if 'name' in e.tag and not name_is_set:
                            site_name = e.text
                            name_is_set = True
                        if 'pos' in e.tag:
                            lat_long = e.text
                            lat_long = lat_long.split(' ')
                            latitude = lat_long[0]
                            longitude = lat_long[1]
                if 'observedProperty' in element.tag:
                    for a in element.attrib:
                        if 'title' in a:
                            variable_name = element.attrib[a]
                        if 'href' in a:
                            variable_code = element.attrib[a]
                            variable_code = variable_code.replace('#', '')
                if variable_name == 'Unmapped':
                    try:
                        if 'vocabulary' in element.attrib:
                            variable_name = element.text
                    except:
                        variable_name = 'Unmapped'
                if 'ObservationProcess' in element.tag:
                    for e in element.iter():
                        if 'processType' in e.tag:
                            for a in e.attrib:
                                if 'title' in a:
                                    method = e.attrib[a]
                if 'sampledMedium' in element.tag:
                    for a in element.attrib.iteritems():
                        if 'title' in a[0]:
                            sample_medium = a[1]
            values = dict(zip(keys, vals))
            if variable_name=='Unmapped':
                for element in root.iter():
                    if len(element.attrib.values())>0:
                        if 'vocabulary' in element.attrib.values()[0]:
                            variable_name = element.text
                        if 'qualityControlLevelCode' in element.attrib.values()[0] and 'name' in element.tag:
                            QClevel = element.text
            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            smallest_time = list(values.keys())[0]
            for t in list(values.keys()):
                if t < smallest_time:
                    smallest_time = t
            return {'time_series': ts,
                    'site_name': site_name,
                    'site_code': site_code,
                    'start_date': smallest_time,
                    'variable_name': variable_name,
                    'variable_code': variable_code,
                    'units': units,
                    'values': values,
                    'for_graph': for_graph,
                    'wml_version': '2.0',
                    'latitude': latitude,
                    'longitude': longitude,
                    'QClevel': QClevel,
                    'method': method,
                    'sample_medium': sample_medium}

def map_waterml(xml_doc):
    root = etree.XML(xml_doc)
    version = get_version(root)
    if version == '1':
        ts = parse_1_0_and_1_1(root)
        units = ts['units']
        values = ts['values']
    elif version == '2.0':
        ts = parse_2_0(root)
        units = ts['units']
        values = ts['values']
    elif not version:
        return False

# get values
def time_series_from_service(service_url, soap_or_rest, **kwargs):
    """ performs getValues call and returns (through parsing fxns) time series and parsed data from response
    called by view: create_ref_time_series
    keyword arguments are given by CAUHSI WOF standard :
    site_name_or_code = location
    variable
    startDate
    endDate
    authToken

    returns:
    a string containing a WaterML file with location metadata and data
    """
    # http://icewater.usu.edu/littlebearriver/cuahsi_1_1.asmx/GetValuesObject?location=LittleBearRiver:USU-LBR-SFLower&variable=LittleBearRiver:USU6:methodCode=2:sourceCode=2:qualityControlLevelCode=0&startDate=2007-07-26&endDate=2007-08-26&authToken=
    if soap_or_rest == 'soap':
        var = kwargs['variable_code']
        index = var.rfind(" [")
        var = var[index+2:len(var)-1]

        site = kwargs['site_code']
        index = site.rfind(" [")
        site = site[index+2:len(site)-1]

        s_d = kwargs.get('startDate', '')
        e_d = kwargs.get('endDate', '')
        a_t = kwargs.get('authToken', '')

        wml_ver = check_url_and_version(service_url)
        client = connect_wsdl_url(service_url)
        try:
            response = client.service.GetValues(site, var, s_d, e_d, a_t)
        except MethodNotFound:
            raise Http404("Method 'GetValues' not found")
        except WebFault:
            raise Http404('This service does not work properly.')
        except:
            raise Http404("Sorry, but we've encountered an unexpected error. This is most likely \
due to incorrect formatting in the web service format.")

    elif soap_or_rest == 'rest':
        r = requests.get(service_url)
        if r.status_code == 200:
            response = r.text.encode('utf-8')
    root = etree.XML(response)
    wml_version = get_version(root)
    if wml_version == '1':
        ts = parse_1_0_and_1_1_owslib(response, wml_ver)
    elif wml_version == '2.0':
        ts = parse_2_0(root)
    else:
        raise Http404()
    return ts


def create_vis_2(path, site_name, data, xlab, variable_name, units, noDataValue, predefined_name=None):
    '''creates vis and returns open file'''
    x_list = data["x"]
    y_list = data["y"]
    x_list_draw = []
    y_list_draw = []

    for i in range(len(x_list)):
        if noDataValue is not None and (y_list[i]) != int(noDataValue):
            x_list_draw.append(datetime.strptime(x_list[i], "%Y-%m-%dT%H:%M:%S"))
            y_list_draw.append(y_list[i])

    fig, ax = plt.subplots()
    ax.plot_date(x_list_draw, y_list_draw, 'b-', color='g')
    ax.set_xlabel(xlab)
    ax.xaxis_date()
    ax.set_ylabel(variable_name + "(" + units + ")")
    ax.grid(True)
    fig.autofmt_xdate()

    if predefined_name is None:
        vis_name = 'visualization-'+site_name+'-'+variable_name+'.png'
        vis_name = vis_name.replace(" ", "_")
    else:
        vis_name = predefined_name
    vis_path = path + "/" + vis_name
    savefig(vis_path, bbox_inches='tight')
    vis_file = open(vis_path, 'rb')
    return {"fname": vis_name, "fhandle": vis_file}

def create_vis(path, site_name, data, xlab, variable_name, units, noDataValue, predefined_name=None):
    '''creates vis and returns open file'''
    loc = AutoDateLocator()
    fmt = AutoDateFormatter(loc)
    fmt.scaled[365.0] = '%y'
    fmt.scaled[30.] = '%b %y'
    fmt.scaled[1.0] = '%b %d %y'

    x = []
    y = []
    x1 =[]
    y1 =[]
    for d in data:
        if str(int(d['y'])) != str(noDataValue):
            x1.append(d['x'])
            y1.append(d['y'])
    vals_dict = dict(zip(x1, y1))
    sorted_vals = sorted(vals_dict.items(), key=operator.itemgetter(0))
    for d in sorted_vals:
        t = (d[0])
        t = datetime.fromtimestamp(t)
        x.append(t)
        y.append(d[1])
    fig, ax = plt.subplots()
    ax.plot_date(x, y, '-')
    # ax.set_aspect(10)
    ax.set_xlabel(xlab)
    if 'NoneType' in str(type(units)):
        units = 'unknown'
    ax.set_ylabel(variable_name + "(" + units + ")")
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(fmt)
    #ax.xaxis.set_minor_locator(days)
    ax.autoscale_view()

    ax.grid(True)
    if predefined_name is None:
        vis_name = 'visualization-'+site_name+'-'+variable_name+'.png'
        vis_name = vis_name.replace(" ","_")
    else:
        vis_name = predefined_name
    vis_path = path + "/" + vis_name
    savefig(vis_path, bbox_inches='tight')
    vis_file = open(vis_path, 'rb')
    return {"fname": vis_name, "fhandle": vis_file}

def make_files(res, tempdir, ts):
    '''gets time series, creates the metadata terms, creates the files and returns them
    called by generate_files
    '''
    site_name = res.metadata.sites.all()[0].name
    var_name = res.metadata.variables.all()[0].name
    title = res.metadata.title.value

    vals = ts['values']
    for_graph = ts['for_graph']
    units = ts['units']
    noDataValue = ts.get('noDataValue', None)
    vis_file = create_vis(tempdir, site_name, for_graph, 'Date', var_name, units, noDataValue)
    version = ts['wml_version']
    file_base = title.replace(" ", "_")
    csv_name = '{0}.{1}'.format(file_base, 'csv')
    if version == '1':
        xml_end = 'wml_1'
        xml_name = '{0}-{1}.xml'.format(file_base, xml_end)
    elif version == '2.0':
        xml_end = 'wml_2_0'
        xml_name = '{0}-{1}.xml'.format(file_base, xml_end)
    for_csv = []
    od_vals = collections.OrderedDict(sorted(vals.items()))
    for k, v in od_vals.items():
        t = (k, v)
        for_csv.append(t)
    csv_name_full_path = tempdir + "/" + csv_name
    with open(csv_name_full_path, 'wb') as csv_file:
        w = csv.writer(csv_file)
        w.writerow([title])
        var = '{0}({1})'.format(ts['variable_name'], ts['units'])
        w.writerow(['time', var])
        for r in for_csv:
            w.writerow(r)
    csv_file = {"fname":csv_name, "fhandle":open(csv_name_full_path, 'r')}
    xml_name_full_path = tempdir + "/" + xml_name
    with open(xml_name_full_path, 'wb') as xml_file:
        xml_file.write(ts['time_series'])

    if version == '1' or version == '1.0':
        wml1_file = {"fname": xml_name, "fhandle":open(xml_name_full_path, 'r')}
        wml2_file = transform_file(ts, title, tempdir)
        files = [csv_file, wml1_file, wml2_file, vis_file]
        return files
    if version == '2' or version == '2.0':
        wml2_file = {"fname":xml_name, "fhandle":open(xml_name_full_path, 'r')}
        files = [csv_file, wml2_file, vis_file]
        return files

def generate_files(shortkey, ts, tempdir):
    ''' creates the calls the make files fxn and adds the files as resource files

    called by view: create_ref_time_series, update_files
    :param shortkey: res shortkey
    :param ts: parsed time series dict
    '''
    res = hydroshare.get_resource_by_shortkey(shortkey)

    if res.metadata.referenceURLs.all()[0].type == 'rest':
        ts = time_series_from_service(res.metadata.referenceURLs.all()[0].value, res.metadata.referenceURLs.all()[0].type)
    else:
        site_code = res.metadata.sites.all()[0].code
        net_work = res.metadata.sites.all()[0].net_work
        variable_code = res.metadata.variables.all()[0].code
        method_code = res.metadata.methods.all()[0].code
        source_code = res.metadata.datasources.all()[0].code
        quality_control_level_code = res.metadata.quality_levels.all()[0].code

        site_code_query = "[%s:%s]" % (net_work, site_code)
        variable_code_query = "[%s:%s:methodCode=%s:sourceCode=%s:qualityControlLevelCode=%s]" % \
        (net_work, variable_code, method_code, source_code, quality_control_level_code)

        ts = time_series_from_service(res.metadata.referenceURLs.all()[0].value,
                                  res.metadata.referenceURLs.all()[0].type,
                                  site_code=site_code_query,
                                  variable_code=variable_code_query)

    files = make_files(res, tempdir, ts)
    return files


#
def transform_file(ts, title, tempdir):
    ''' transforms wml1.1 to wml2.0 '''
    waterml_1 = ts['root']
    wml_string = etree.tostring(waterml_1)
    s = StringIO(wml_string)
    dom = etree.parse(s)
    module_dir = os.path.dirname(__file__)
    xsl_location = os.path.join(module_dir, "static/ref_ts/xslt/WaterML1_1_timeSeries_to_WaterML2.xsl")
    xslt = etree.parse(xsl_location)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)
    xml_name = '{0}-{1}'.format(title.replace(" ", "_"), 'wml_2_0.xml')
    xml_2_full_path = tempdir + "/" + xml_name

    with open(xml_2_full_path, 'wb') as f:
        f.write(newdom)

    xml_file = open(xml_2_full_path, 'r')

    return {"fname":xml_name, "fhandle": xml_file}

