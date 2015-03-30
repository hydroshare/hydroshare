from suds import MethodNotFound, WebFault
from suds.transport import TransportError
from suds.client import Client
from lxml import etree
from django.http import Http404
from .models import RefTimeSeries
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
from hs_core.hydroshare.hs_bagit import create_bag
from hs_core import hydroshare
from hs_core.models import ResourceFile


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
        raise Http404("Sorry, but we've encountered an unexpected error. This is most likely\
         due to incorrect formatting in the web service response.")
    try:
        sites = []
        root = etree.XML(response)
        wml_version = get_version(root)
        if wml_version == '1':
            for element in root:
                if 'site' in element.tag:
                    sites.append(element[0][0].text + " : " + element[0][1].text)
        elif wml_version == '2.0':
            pass   # FIXME I need to change this, obviously
        else:
            raise Http404()
    except:
        return "Parsing error: The Data in the WSDL Url '{0}' was not correctly formatted \
according to the WaterOneFlow standard given at 'http://his.cuahsi.org/wofws.html#waterml'.".format(wsdl_url)
    # ret = dict(zip(site_names, site_codes))
    sites = sorted(sites)
    return sites

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
        response = response.encode('utf-8')
        root = etree.XML(response)
        wml_version = get_version(root)
        variable_name = ''
        variable_code = ''
        variables = []
        if wml_version =='1':
            for element in root.iter():
                brack_lock = element.tag.index('}')  #The namespace in the tag is enclosed in {}.
                tag = element.tag[brack_lock+1:]     #Takes only actual tag, no namespace
                if 'variableCode' in tag:
                    variable_code = element.text
                if 'variableName' in tag:
                    variable_name = element.text
                    variables.append(variable_name + ' : ' + variable_code)
        elif wml_version == '2.0':
            pass  # FIXME add what to do here
        else:
            raise Http404()
        variables = sorted(variables)
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

def parse_1_0_and_1_1(root):
    # try:
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
            noDataValue, units, site_name, site_code, variable_name, variable_code, latitude, longitude, methodCode, method, QCcode, QClevel = None, None, None, None, None, None, None, None, None, None, None, None
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
    # except:
    #     return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."

def parse_2_0(root):
    #try:
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
    #         return "Parsing error: The waterml document doesn't appear to be a WaterML 2.0 time series"
    # except:
    #     return "Parsing error: The Data in the Url, or in the request, was not correctly formatted."

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

#performs getValues call and returns (through parsing fxns) time series and parsed data from response
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

#creates vis and returns open file
def create_vis(path, varcode, site_code, data, xlab, variable_name, units, noDataValue):
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
    vis_name = 'visualization-'+site_code+'-'+varcode+'.png'
    vis_path = path+vis_name
    savefig(vis_path, bbox_inches='tight')
    vis_file = open(vis_path, 'r')
    return vis_file

#gets time series, creates the metadata terms, creates the files and returns them
def make_files(shortkey, reference_type, url, data_site_code, variable_code, title):

    ts, csv_link, csv_size, xml_link, xml_size = {}, '', '', '', ''
    if reference_type == 'rest':

        ts = time_series_from_service(url, reference_type)

    else:
        ts = time_series_from_service(url,
                                      reference_type,
                                      site_name_or_code=data_site_code,
                                      variable_code=variable_code)

    #update/create metadata elements
    res = hydroshare.get_resource_by_shortkey(shortkey)
    s = res.metadata.sites.all()[0]
    hydroshare.resource.update_metadata_element(
        shortkey,
        'Site',
        s.id,
        latitude=ts['latitude'],
        longitude=ts['longitude'])
    v = res.metadata.variables.all()[0]
    hydroshare.resource.update_metadata_element(
        shortkey,
        'Variable',
        v.id,
        sample_medium=ts.get('sample_medium', 'unknown')
        )
    hydroshare.resource.create_metadata_element(
        shortkey,
        'QualityControlLevel',
        value=ts['QClevel'],
        )
    hydroshare.resource.create_metadata_element(
        shortkey,
        'Method',
        value=ts['method'],
        )



    vals = ts['values']
    for_graph = ts['for_graph']
    units = ts['units']
    variable_name = ts['variable_name']
    noDataValue = ts.get('noDataValue', None)
    vis_file = create_vis("", variable_code, data_site_code, for_graph, 'Date', variable_name, units, noDataValue)
    version = ts['wml_version']
    d = datetime.today()
    date = '{0}_{1}_{2}'.format(d.month, d.day, d.year)
    file_base = '{0}-{1}'.format(title.replace(" ", ""), date)
    csv_name = '{0}.{1}'.format(file_base, 'csv')
    if version == '1':
        xml_end = 'wml_1'
        xml_name = '{0}-{1}.wml'.format(file_base, xml_end)
    elif version == '2.0':
        xml_end = 'wml_2_0'
        xml_name = '{0}-{1}.wml'.format(file_base, xml_end)
    for_csv = []
    od_vals = collections.OrderedDict(sorted(vals.items()))
    for k, v in od_vals.items():
        t = (k, v)
        for_csv.append(t)
    with open(csv_name, 'wb') as csv_file:
        w = csv.writer(csv_file)
        w.writerow([title])
        var = '{0}({1})'.format(ts['variable_name'], ts['units'])
        w.writerow(['time', var])
        for r in for_csv:
            w.writerow(r)
    with open(xml_name, 'wb') as xml_file:
        xml_file.write(ts['time_series'])
    csv_file = open(csv_name, 'r')
    files = []
    if version == '1' or version == '1.0':
        wml1_file = open(xml_name, 'r')
        wml2_file = transform_file(reference_type, url, data_site_code, variable_code, title)
        files = [csv_file, wml1_file, wml2_file, vis_file]
        return files
    if version == '2' or version == '2.0':
        wml2_file = open(xml_name, 'r')
        files = [csv_file, wml2_file, vis_file]
        return files

#this fxn creates the calls the make files fxn and adds the files as resource files
def generate_files(shortkey):
    res = hydroshare.get_resource_by_shortkey(shortkey)
    files = make_files(res.short_id, res.metadata.referenceURLs.all()[0].type, res.metadata.referenceURLs.all()[0].value, res.metadata.sites.all()[0].code, res.metadata.variables.all()[0].code, res.title)
    for f in files:
        hydroshare.add_resource_files(res.short_id, f)
        os.remove(f.name)
    create_bag(res)

#transforms wml1.1 to wml2.0
def transform_file(reference_type, url, data_site_code, variable_code, title):
    if reference_type == 'soap':
        client = Client(url)
        response = client.service.GetValues(':'+data_site_code, ':'+variable_code, '', '', '')
    elif reference_type == 'rest':
        r = requests.get(url)
        response = str(r.text)
    waterml_1 = etree.XML(response)
    wml_string = etree.tostring(waterml_1)
    s = StringIO(wml_string)
    dom = etree.parse(s)
    module_dir = os.path.dirname(__file__)
    xsl_location = os.path.join(module_dir, "static/ref_ts/xslt/WaterML1_1_timeSeries_to_WaterML2.xsl")
    xslt = etree.parse(xsl_location)
    transform = etree.XSLT(xslt)
    newdom = transform(dom)
    d = datetime.today()
    date = '{0}_{1}_{2}'.format(d.month, d.day, d.year)
    xml_name = '{0}-{1}-{2}'.format(title.replace(" ", ""), date, 'wml_2_0.wml')
    with open(xml_name, 'wb') as f:
        f.write(newdom)
    xml_file = open(xml_name, 'r')
    return xml_file


