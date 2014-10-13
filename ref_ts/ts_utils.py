from suds import MethodNotFound, WebFault
from suds.transport import TransportError
from suds.client import Client
from lxml import etree
from django.http import Http404
from .models import RefTimeSeries
from xml.sax._exceptions import SAXParseException
from datetime import datetime
import requests


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

def sites_from_soap(wsdl_url, locations=[':']):
    """
    Note: locations (a list) is given by CUAHSI WOF standard

    returns:
    a list of site names and codes at the given locations
    """

    if not wsdl_url.endswith('.asmx?WSDL') and not wsdl_url.endswith('.asmx?wsdl'):
        raise Http404("The correct url format ends in '.asmx?WSDL'.")
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
    try:
        response = client.service.GetSites(locations)
    except MethodNotFound:
        raise Http404("Method 'GetSites' not found")
    except WebFault:
        raise Http404('This service does not support an all sites search. \
Please provide a list of locations')  # ought to be a 400, but no page implemented for that
    except:
        raise Http404("Sorry, but we've encountered an unexpected error. This is most likely \
due to incorrect formatting in the web service response.")
    try:
        site_names = []
        site_codes = []
        root = etree.XML(response)
        wml_version = get_version(root)
        if wml_version == '1':
            for element in root:
                if 'site' in element.tag:
                    site_names.append(element[0][0].text)
                    site_codes.append(element[0][1].text)
        elif wml_version == '2.0':
            pass   # FIXME I need to change this, obviously
        else:
            raise Http404()
    except:
        return "Parsing error: The Data in the WSDL Url '{0}' was not correctly formatted \
according to the WaterOneFlow standard given at 'http://his.cuahsi.org/wofws.html#waterml'.".format(wsdl_url)
    ret = dict(zip(site_names, site_codes))
    return ret

def site_info_from_soap(wsdl_url, **kwargs):
    site = ':' + kwargs['site']

    if not wsdl_url.endswith('.asmx?WSDL') and not wsdl_url.endswith('.asmx?wsdl'):
        raise Http404("The correct url format ends in '.asmx?WSDL'.")
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
    try:
        response = client.service.GetSiteInfo(site)
    except MethodNotFound:
        raise Http404("Method 'GetValues' not found")

    try:
        response = client.service.GetSiteInfo(site)
        root = etree.XML(response)
        wml_version = get_version(root)
        variable_names = []
        variable_codes = []
        if wml_version =='1':
            for element in root.iter():
                brack_lock = element.tag.index('}')  #The namespace in the tag is enclosed in {}.
                tag = element.tag[brack_lock+1:]     #Takes only actual tag, no namespace
                if 'variableName' in tag:
                    variable_names.append(element.text)
            for element in root.iter():
                brack_lock = element.tag.index('}')  #The namespace in the tag is enclosed in {}.
                tag = element.tag[brack_lock+1:]     #Takes only actual tag, no namespace
                if 'variableCode' in tag:
                    variable_codes.append(element.text)
        elif wml_version == '2.0':
            pass  # FIXME add what to do here
        else:
            raise Http404()
        variables = dict(zip(variable_names, variable_codes))
        return variables
    except:
        return "Parsing error: The Data in the WSDL Url '{0}' was not correctly formatted \
according to the WaterOneFlow standard given at 'http://his.cuahsi.org/wofws.html#waterml'.".format(wsdl_url)

def time_to_int(t):
    # if time format looks like '2014-07-22T10:45:00.000'
    try:
        ret = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S.%f').strftime('%s'))
    except ValueError:
        try:
            # if time format looks like '2014-07-22T10:45:00.000-05:00'
            offset_hrs = int(t[-6:-3])
            offset_min = int(t[-6]+t[-2:])
            t = t[:-6]
            epoch_secs = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S.%f').strftime('%s'))
            ret = epoch_secs + offset_hrs*3600 + offset_min*60
        except ValueError:
            try:
                # if time format looks like '2014-07-22T10:45:00'
                ret = int(datetime.strptime(unicode(t), '%Y-%m-%dT%H:%M:%S').strftime('%s'))
            except ValueError:
                #if the time format looks like '2014-07-22 10:45:00'
                ret = int(datetime.strptime(unicode(t), '%Y-%m-%d %H:%M:%S').strftime('%s'))
    return ret

def parse_1_0_and_1_1(root):
    try:
        if 'timeSeriesResponse' in root.tag:
            time_series = root[1]
            ts = etree.tostring(time_series)
            values = {}
            for_graph = []
            units, site_name, variable_name = None, None, None
            unit_is_set = False
            for element in root.iter():
                brack_lock = element.tag.index('}')  #The namespace in the tag is enclosed in {}.
                tag = element.tag[brack_lock+1:]     #Takes only actual tag, no namespace
                if 'unitName' == tag:  # in the xml there is a unit for the value, then for time. just take the first
                    if not unit_is_set:
                        units = element.text
                        unit_is_set = True
                if 'value' == tag:
                    values[element.attrib['dateTime']] = element.text
                if 'siteName' == tag:
                    site_name = element.text
                if 'variableName' == tag:
                    variable_name = element.text
            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            smallest_time = list(values.keys())[0]
            for t in list(values.keys()):
                if t < smallest_time:
                    smallest_time = t
            return {'time_series': ts,
                    'site_name': site_name,
                    'start_date': smallest_time,
                    'variable_name': variable_name,
                    'units': units,
                    'values': values,
                    'for_graph': for_graph,
                    'wml_version': '1'}
        else:
            return "Parsing error: The waterml document doesn't appear to be a WaterML 1.0/1.1 time series"
    except:
        return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."

def parse_2_0(root):
    try:
        if 'Collection' in root.tag:
            ts = etree.tostring(root)
            keys = []
            vals = []
            for_graph = []
            units, site_name, variable_name = None, None, None
            name_is_set = False
            variable_name = root[1].text
            for element in root.iter():
                if 'MeasurementTVP' in element.tag:
                        for e in element:
                            if 'time' in e.tag:
                                keys.append(e.text)
                            if 'value' in e.tag:
                                vals.append(e.text)
                if 'uom' in element.tag:
                    units = element.text
                if 'MonitoringPoint' in element.tag:
                    for e in element.iter():
                        if 'name' in e.tag and not name_is_set:
                            site_name = e.text
                            name_is_set = True
                if 'observedProperty' in element.tag:
                    for a in element.attrib:
                        if 'title' in a:
                            variable_name = element.attrib[a]
            values = dict(zip(keys, vals))
            for k, v in values.items():
                t = time_to_int(k)
                for_graph.append({'x': t, 'y': float(v)})
            smallest_time = list(values.keys())[0]
            for t in list(values.keys()):
                if t < smallest_time:
                    smallest_time = t
            return {'time_series': ts,
                    'site_name': site_name,
                    'start_date': smallest_time,
                    'variable_name': variable_name,
                    'units': units,
                    'values': values,
                    'for_graph': for_graph,
                    'wml_version': '2.0'}
        else:
            return "Parsing error: The waterml document doesn't appear to be a WaterML 2.0 time series"
    except:
        return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."

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

def time_series_from_service(service_url, soap_or_rest, **kwargs):
    """
    keyword arguments are given by CAUHSI WOF standard :
    site_name_or_code = location
    variable
    startDate
    endDate
    authToken

    returns:
    a string containing a WaterML file with location metadata and data
    """
    if soap_or_rest == 'soap':
        var = ':' + kwargs['variable_code']
        s_d = kwargs.get('startDate', '')
        e_d = kwargs.get('endDate', '')
        a_t = kwargs.get('authToken', '')

        try:
            client = Client(service_url)
        except TransportError:
            raise Http404('Url not found')
        except ValueError:
            raise Http404('Invalid url')  # ought to be a 400, but no page implemented for that
        try:
            location = ':' + kwargs['site_name_or_code'] # maybe the user provided a site code
            response = client.service.GetValues(location, var, s_d, e_d, a_t)
        except MethodNotFound:
            raise Http404("Method 'GetValues' not found")
        except WebFault:
                    #maybe the user provided a site name
            try:
                all_sites = sites_from_soap(service_url)
                location = ':' + all_sites[kwargs['site_name_or_code']]
                response = client.service.GetValues(location, var, s_d, e_d, a_t)
            except KeyError:
                Http404('Invalid site name')
            except WebFault:
                raise Http404('One or more of your parameters may be incorrect. \
Location and Variable are not optional, and case sensitive')
            except:
                raise Http404("Sorry, but we've encountered an unexpected error")
        except:
            raise Http404("Sorry, but we've encountered an unexpected error. This is most likely \
due to incorrect formatting in the web service format.")

    elif soap_or_rest == 'rest':
        r = requests.get(service_url)
        if r.status_code == 200:
            response = r.text.encode('utf-8')
    else:
        raise Http404()

    root = etree.XML(response)
    wml_version = get_version(root)
    if wml_version == '1':
        return parse_1_0_and_1_1(root)
    elif wml_version == '2.0':
        return parse_2_0(root)
    else:
        raise Http404()
