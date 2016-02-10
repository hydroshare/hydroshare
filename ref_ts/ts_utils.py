import requests
import csv
import os
import logging
from dateutil import parser
from lxml import etree
from suds.transport import TransportError
from suds.client import Client
from xml.sax._exceptions import SAXParseException
import matplotlib.pyplot as plt

from hs_core import hydroshare
from owslib.waterml.wml11 import WaterML_1_1 as wml11
from owslib.waterml.wml10 import WaterML_1_0 as wml10

logger = logging.getLogger("django")

def wmlParse(response, ver=11):
    if ver == 11:
        return wml11(response).response
    elif ver == 10:
        return wml10(response).response
    else:
        raise Exception("This wml version is not supported by OWSLib")

def wmlVersionFromSoapURL(wsdl_url):
    ver = -1
    if "1_0." in wsdl_url.lower():
        ver = 10
    elif "1_1." in wsdl_url.lower():
        ver = 11
    elif "2_0." in wsdl_url.lower():
        ver = 20
    else:
        ver = -1
    return ver

def check_url_and_version(wsdl_url):
    if not wsdl_url.lower().endswith('.asmx?wsdl'):
        if not wsdl_url.lower().endswith('.php?wsdl'):
            raise Exception("invalid soap endpoint")
    return wmlVersionFromSoapURL(wsdl_url)

def connect_wsdl_url(wsdl_url):
    try:
        client = Client(wsdl_url)
    except TransportError:
        raise Exception('Url not found')
    except ValueError:
        raise Exception('Invalid url')  # ought to be a 400, but no page implemented for that
    except SAXParseException:
        raise Exception("The correct url format ends in '.asmx?WSDL'.")
    except:
        raise Exception("Unexpected error")
    return client

def get_wml_version_from_xml_tag(root):
    wml_version = -1
    for element in root.iter():
        if '{http://www.opengis.net/waterml/2.0}collection' in element.tag.lower():
            wml_version = 20
            break
        elif '{http://www.cuahsi.org/waterml/1.1/}timeseriesresponse' in element.tag.lower():
            wml_version = 11
            break
        elif '{http://www.cuahsi.org/waterml/1.0/}timeseriesresponse' in element.tag.lower():
            wml_version = 10
            break
    return wml_version

def sites_from_soap(wsdl_url, locations='[:]'):
    try:
        client = connect_wsdl_url(wsdl_url)
        wml_ver = check_url_and_version(wsdl_url)
        response = None
        if wml_ver == 11:
            response = client.service.GetSites(locations)
        elif wml_ver == 10:
            response = client.service.GetSitesXml(locations)
        response = response.encode('utf-8')
        wml_sites = wmlParse(response, wml_ver)
        counter = 0
        sites_list = []
        for site in wml_sites.sites:
            siteName = site.name
            siteCode = site.codes[0]
            # netWork = site.site_info.net_work
            counter += 1
            # sites_list.append("%s. %s [%s:%s]" % (str(counter), siteName, netWork, siteCode))
            sites_list.append("%s. %s [network:%s]" % (str(counter), siteName, siteCode))
    except Exception as e:
        logger.exception("sites_from_soap: %s" % (e.message))
        raise e
    return sites_list

# get variable name list
def site_info_from_soap(wsdl_url, **kwargs):
    try:
        site = kwargs['site']
        index = site.rfind(" [")
        site = site[index+2:len(site)-1]
        wml_ver = check_url_and_version(wsdl_url)
        client = connect_wsdl_url(wsdl_url)
        variables_list = []

        response = client.service.GetSiteInfo(site)
        response = response.encode('utf-8')
        wml_siteinfo = wmlParse(response, wml_ver)
        counter = 0
        for series in wml_siteinfo.sites[0].series_catalogs[0].series:
            wml_variable = series.variable
            variable_name = wml_variable.variable_name
            variable_code = wml_variable.variable_code
            method_id = series.method_id if series.method_id is not None else "Unknown"
            source_id = series.source_id if series.source_id is not None else "Unknown"
            value_count = series.value_count
            quality_control_level_id = series.quality_control_level_id if series.quality_control_level_id is not None else "Unknown"
            start_date = series.begin_date_time
            end_date = series.end_date_time
            counter += 1
            variables_list.append("%s. %s (Count:%s, ID:%s, methodCode:%s, sourceCode:%s, qualityControlLevelCode:%s)\
             [network:%s:methodCode=%s:sourceCode=%s:qualityControlLevelCode=%s]" %
                                 (str(counter), variable_name, str(value_count), variable_code, method_id, \
                                  source_id, quality_control_level_id, \
                                  variable_code, method_id, source_id, quality_control_level_id))

        return variables_list
    except Exception as e:
        logger.exception("site_info_from_soap: %s" % (e.message))
        raise e

def parse_1_0_and_1_1_owslib(wml_string, wml_ver):

    try:
        wml_str, variable_code, variable_name, net_work, site_name, site_code, elevation, vertical_datum,\
        longitude, latitude, projection, srs, noDataValue, unit_abbr, unit_code, unit_name, unit_type,\
        method_code, method_id, method_description, source_code, source_id, quality_control_level_code,\
        quality_control_level_definition, data, method_code_query, source_code_query,  \
        quality_control_level_code_query, start_date, end_date = \
        None, None, None, None, None, None, None, None,  None, None, None, None, None, None,\
        None, None, None, None, None, None, None, None, None, None,  None, None, None, None, None, None

        wmlValues = wmlParse(wml_string, wml_ver)

        variable_query = wmlValues.query_info.criteria.variable_param
        if variable_query is None:
            for p in wmlValues.query_info.criteria.parameters:
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
        variable_code = wmlValues.variable_codes[0]
        variable_name = wmlValues.variable_names[0]

        if hasattr(wmlValues.time_series[0], "source_info"):
            sourceInfo_obj = wmlValues.time_series[0].source_info
            if sourceInfo_obj:
                # net_work = sourceInfo_obj.net_work if hasattr(sourceInfo_obj, "net_work") else None
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
                    if projection_list and len(projection_list) > 0:
                       projection = projection_list[0]
                    srs_list = loc_obj.srs if hasattr(loc_obj, "srs") else None
                    if srs_list and len(srs_list) > 0:
                        srs = srs_list[0]

        variable_obj = wmlValues.time_series[0].variable if hasattr(wmlValues.time_series[0], "variable") else None
        noDataValue = variable_obj.no_data_value if hasattr(variable_obj, "no_data_value") else None
        unit_obj = variable_obj.unit if hasattr(variable_obj, "unit") else None
        if unit_obj:
            unit_abbr = unit_obj.abbreviation if hasattr(unit_obj, "abbreviation") else None
            unit_code = unit_obj.code if hasattr(unit_obj, "code") else None
            unit_name = unit_obj.name if hasattr(unit_obj, "name") else None
            unit_type = unit_obj.unit_type if hasattr(unit_obj, "unit_type") else None

        value_obj = wmlValues.time_series[0].values[0]
        value_list = value_obj.values if hasattr(value_obj, "values") else None
        x = []
        y = []
        data = {"x": x, "y": y}
        if value_list:
            for val in value_list:
                t = val.date_time
                t_str = t.isoformat() # convert to datetime string
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
            if type(method_description) is unicode:
                method_description = method_description.encode('ascii', 'ignore')
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
                'data': data,
                "start_date": start_date,
                "end_date": end_date
                }
    except Exception as e:
        logger.exception("parse_1_0_and_1_1_owslib: %s" % (e.message))
        raise e

def getAttributeValueFromElement(ele, a_name, exactmatch=False):
    for a in ele.attrib:
        if not exactmatch:
            if a_name in a:
               return ele.attrib.get(a, None)
        else:
             if a_name == a:
               return ele.attrib.get(a, None)
    return None

def parse_featureOfInterest(OM_Observation_element):
    site_name = None

    for featureOfInterest_element in OM_Observation_element.iter():
        if "featureOfInterest" in featureOfInterest_element.tag:
            site_name = getAttributeValueFromElement(featureOfInterest_element, "title")
    return {"site_name": site_name}

def parse_observedProperty(OM_Observation_element):
    variable_name = None
    for observedProperty_element in OM_Observation_element.iter():
        if "observedProperty" in observedProperty_element.tag:
            variable_name = getAttributeValueFromElement(observedProperty_element, "title")
            if variable_name.lower() == "unmapped":
                variable_name = getAttributeValueFromElement(observedProperty_element, "href")
                if "#" in variable_name:
                    variable_name = variable_name.replace("#", "")
    return {"variable_name": variable_name}

def parse_uom(OM_Observation_element):
    unit_name = None

    for uom_element in OM_Observation_element.iter():
        if "uom" in uom_element.tag:
            unit_name = getAttributeValueFromElement(uom_element, "title")
            if unit_name is None:
               unit_name = getAttributeValueFromElement(uom_element, "code")
               if unit_name is None:
                    unit_name = getAttributeValueFromElement(uom_element, "uom")
    return {"unit_name": unit_name}

def parse_qualifier(OM_Observation_element):
    qualifier_name = None
    qualifier_value = None
    for qualifier_element in OM_Observation_element.iter():
        if "qualifier" in qualifier_element.tag:
            qualifier_name = getAttributeValueFromElement(qualifier_element, "title")
            if qualifier_name is None:
                for ele in qualifier_element.iter():
                    if "text" in ele.tag.lower():
                        qualifier_name = getAttributeValueFromElement(ele, "definition")
                    if "value" in ele.tag.lower():
                        qualifier_value = ele.text
    return {"qualifier_name": qualifier_name, "qualifier_value": qualifier_value}

def parse_value(OM_Observation_element):
    x = []
    y = []
    for point_element in OM_Observation_element.iter():
        if "MeasurementTVP" in point_element.tag:
            for ele in point_element.iter():
                if "time" in ele.tag:
                    x.append(ele.text)
                elif "value" in ele.tag:
                    y.append(ele.text)
    return {"x": x, "y": y}

def parse_2_0(wml_string):

    wml_str, variable_code, variable_name, net_work, site_name, site_code, elevation, vertical_datum,\
    longitude, latitude, projection, srs, noDataValue, unit_abbr, unit_code, unit_name, unit_type,\
    method_code, method_id, method_description, source_code, source_id, quality_control_level_code,\
    quality_control_level_definition, data, method_code_query, source_code_query,  \
    quality_control_level_code_query, start_date, end_date = \
    None, None, None, None, None, None, None, None,  None, None, None, None, None, None,\
    None, None, None, None, None, None, None, None, None, None,  None, None, None, None, None, None

    wml_str = wml_string
    data = {"x": [], "y": []}
    root = etree.XML(wml_string)

    try:
        for ele in root.iter():
            if "OM_Observation" in ele.tag:
                ele_OM_Observation = ele
                site_name = parse_featureOfInterest(ele_OM_Observation)["site_name"]
                variable_name = parse_observedProperty(ele_OM_Observation)["variable_name"]
                unit_name = parse_uom(ele_OM_Observation)["unit_name"]
                qualifier = parse_qualifier(ele_OM_Observation)
                quality_control_level_code = qualifier["qualifier_name"]
                quality_control_level_definition = qualifier["qualifier_value"]

                x_y_dict = parse_value(ele)
                x = x_y_dict['x']
                y = x_y_dict['y']
                data['x'] = x
                data['y'] = y

            elif "localDictionary" in ele.tag:
                pass
            elif "samplingFeatureMember" in ele.tag:
                ele_samplingFeatureMember =ele
                for ele2 in ele_samplingFeatureMember.iter():
                    if "pos" in ele2.tag:
                        lat_lon_array = ele2.text.split(" ")
                        latitude = lat_lon_array[0]
                        longitude = lat_lon_array[1]
            elif "ObservationProcess" in ele.tag:
                ele_ObservationProcess = ele
                for ele2 in ele_ObservationProcess.iter():
                    if "NamedValue" in ele2.tag:
                        ele_NamedValue = ele2
                        if getAttributeValueFromElement(ele_NamedValue.getchildren()[0], "title") == "noDataValue":
                            noDataValue = ele_NamedValue.getchildren()[1].text

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
                        'data': data,
                        "start_date": start_date,
                        "end_date": end_date
                        }
    except Exception as ex:
        logger.error(ex.message)
        raise Exception("parse 2.0 error")

def time_str_to_datetime(t):
    try:
        t_datetime=parser.parse(t)
        return t_datetime
    except ValueError:
        logger.exception("time_str_to_datetime error: " + t)
        raise Exception("time_str_to_datetime error: " + t)

# get values
def QueryHydroServerGetParsedWML(service_url, soap_or_rest, site_code=None, variable_code=None, start_date='', end_date='', auth_token=''):
    # http://icewater.usu.edu/littlebearriver/cuahsi_1_1.asmx/GetValuesObject?
    # location=LittleBearRiver:USU-LBR-SFLower&
    # variable=LittleBearRiver:USU6:methodCode=2:sourceCode=2:qualityControlLevelCode=0&
    # startDate=2007-07-26&
    # endDate=2007-08-26&
    # authToken=

    try:
        if soap_or_rest == 'soap':
            client = connect_wsdl_url(service_url)
            response = client.service.GetValues(site_code, variable_code, start_date, end_date, auth_token)
        elif soap_or_rest == 'rest':
            r = requests.get(service_url)
            if r.status_code != 200:
                raise Exception("Query REST endpoint failed")
            response = r.text.encode('utf-8')
        root = etree.XML(response)
        wml_version_xml_tag = get_wml_version_from_xml_tag(root)
        if wml_version_xml_tag == 10 or wml_version_xml_tag == 11:
            ts = parse_1_0_and_1_1_owslib(response, wml_version_xml_tag)
        elif wml_version_xml_tag == 20:
            ts = parse_2_0(response)
         # some hydrosevers may return wml without having version info in tags (http://worldwater.byu.edu/interactive/gill_lab/services/index.php/cuahsi_1_1.asmx?WSDL)
        else:
            raise Exception("no version info found in wml")
        ts["wml_version"] = wml_version_xml_tag
        return ts
    except Exception as e:
        logger.exception("QueryHydroServerGetParsedWML: %s" % (e.message))
        raise e

def create_vis_2(path, site_name, data, xlabel, variable_name, units, noDataValue, predefined_name=None):
    try:
        x_list = data["x"]
        y_list = data["y"]
        x_list_draw = []
        y_list_draw = []

        for i in range(len(x_list)):
            if noDataValue is not None and (y_list[i]) == float(noDataValue):
               continue # skip nodatavalue
            x_list_draw.append(time_str_to_datetime(x_list[i]))
            y_list_draw.append(y_list[i])

        fig, ax = plt.subplots()
        ax.plot_date(x_list_draw, y_list_draw, 'b-', color='g')
        ax.set_xlabel(xlabel)
        ax.xaxis_date()
        ax.set_ylabel(variable_name + "(" + units + ")")
        ax.grid(True)
        fig.autofmt_xdate()

        if predefined_name is None:
            vis_name = 'preview.png'
        else:
            vis_name = predefined_name
        vis_path = path + "/" + vis_name
        plt.savefig(vis_path, bbox_inches='tight')
        return {"fname": vis_name, "fullpath": vis_path}
    except Exception as e:
        logger.exception("create_vis_2: %s" % (e.message))
        raise e

def generate_resource_files(shortkey, tempdir):

    res = hydroshare.get_resource_by_shortkey(shortkey)

    if res.metadata.referenceURLs.all()[0].type == 'rest':
        ts = QueryHydroServerGetParsedWML(res.metadata.referenceURLs.all()[0].value,
                                          res.metadata.referenceURLs.all()[0].type)
    else:
        site_code = res.metadata.sites.all()[0].code
        # net_work = res.metadata.sites.all()[0].net_work
        variable_code = res.metadata.variables.all()[0].code
        method_code = res.metadata.methods.all()[0].code
        source_code = res.metadata.datasources.all()[0].code
        quality_control_level_code = res.metadata.quality_levels.all()[0].code

        site_code_query = "%s:%s" % ("network", site_code)
        variable_code_query = "%s:%s:methodCode=%s:sourceCode=%s:qualityControlLevelCode=%s" % \
        ("network", variable_code, method_code, source_code, quality_control_level_code)

        ts = QueryHydroServerGetParsedWML(service_url=res.metadata.referenceURLs.all()[0].value,
                                  soap_or_rest=res.metadata.referenceURLs.all()[0].type,
                                  site_code=site_code_query,
                                  variable_code=variable_code_query)

    files = save_ts_to_files(res, tempdir, ts)
    return files

def save_ts_to_files(res, tempdir, ts):
    res_file_info_array = []

    site_name = res.metadata.sites.all()[0].name
    title = res.metadata.title.value

    # save preview figure
    data = ts['data']
    units = ts['unit_abbr']
    if units is None:
        units = ts['unit_name']
        if units is None:
            units = "Unknown"
    variable_name = ts['variable_name']
    noDataValue = ts['noDataValue']

    preview_file_info = create_vis_2(path=tempdir, site_name=site_name, data=data, xlabel='Date',
                                      variable_name=variable_name, units=units, noDataValue=noDataValue)
    res_file_info_array.append(preview_file_info)

    # csv wml1 wml2 file name base
    # file_name_base = title.replace(" ", "_")
    file_name_base = "res_" + str(res.short_id)
    # save csv file
    csv_name = '{0}.{1}'.format(file_name_base, 'csv')
    csv_name_full_path = tempdir + "/" + csv_name
    with open(csv_name_full_path, 'w') as csv_file:
        w = csv.writer(csv_file)
        x_data = ts['data']['x']
        y_data = ts['data']['y']
        for i in range(len(x_data)):
            row_str = [x_data[i], y_data[i]]
            w.writerow(row_str)
    res_file_info_array.append({"fname": csv_name, "fullpath": csv_name_full_path})

    wml_1_0_name = '{0}_wml_1_0.xml'.format(file_name_base)
    wml_1_0_full_path = tempdir + "/" + wml_1_0_name

    wml_1_1_name = '{0}_wml_1_1.xml'.format(file_name_base)
    wml_1_1_full_path = tempdir + "/" + wml_1_1_name

    wml_2_0_name = '{0}_wml_2_0.xml'.format(file_name_base)
    wml_2_0_full_path = tempdir + "/" + wml_2_0_name

    if ts["wml_version"] == 10 or ts["wml_version"] == 11:
        module_dir = os.path.dirname(__file__)
        if ts["wml_version"] == 11:
            xml_1011_name = wml_1_1_name
            xml_1011_full_path = wml_1_1_full_path
            xsl_location = os.path.join(module_dir, "static/ref_ts/xslt/WaterML1_1_timeSeries_to_WaterML2.xsl")
        else: # 1.0
            xml_1011_name = wml_1_0_name
            xml_1011_full_path = wml_1_0_full_path
            xsl_location = os.path.join(module_dir, "static/ref_ts/xslt/WaterML1_timeSeries_to_WaterML2.xsl")

        root_wml_1 = etree.fromstring(ts['wml_str'])
        with open(xml_1011_full_path, 'w') as xml_1_file:
            xml_1_file.write(etree.tostring(root_wml_1, pretty_print=True))
        res_file_info_array.append({"fname": xml_1011_name, "fullpath": xml_1011_full_path})

        try:
            # convert to wml 2
            xslt = etree.parse(xsl_location)
            transform =etree.XSLT(xslt)
            tree_wml_2 = transform(root_wml_1)

            tree_wml_2.write(wml_2_0_full_path, pretty_print=True)
            res_file_info_array.append({"fname": wml_2_0_name, "fullpath": wml_2_0_full_path})
        except Exception as e:
            logger.exception("convert to wml2 error: %s".format(e.message))

    elif ts["wml_version"] == 20:
        with open(wml_2_0_full_path, 'w') as xml_2_file:
            xml_2_file.write(ts['wml_str'])
        res_file_info_array.append({"fname": wml_2_0_name, "fullpath": wml_2_0_full_path})

    return res_file_info_array
