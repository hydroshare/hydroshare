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
import tempfile
from django.core.files.uploadedfile import UploadedFile
import shutil

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
                    if variable_name + ' : ' + variable_code not in variables:
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
        ts = parse_1_0_and_1_1(root)
    elif wml_version == '2.0':
        ts = parse_2_0(root)
    else:
        raise Http404()
    ts['root'] = root #add root to ts
    return ts


def create_vis(path, site_name, data, xlab, variable_name, units, noDataValue):
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
    vis_name = 'visualization-'+site_name+'-'+variable_name+'.png'
    vis_name.replace(" ","")
    vis_path = path + "/" + vis_name
    savefig(vis_path, bbox_inches='tight')
    vis_file = open(vis_path, 'rb')
    #vis_file = UploadedFile(file=vis_file,name=vis_name)
    return {"fname":vis_name,"fhandle":vis_file}

def make_files(res, tempdir, ts):
    '''gets time series, creates the metadata terms, creates the files and returns them
    called by generate_files
    '''
    site_name = res.metadata.sites.all()[0].name
    var_name = res.metadata.variables.all()[0].name
    title = res.title

    vals = ts['values']
    for_graph = ts['for_graph']
    units = ts['units']
    noDataValue = ts.get('noDataValue', None)
    vis_file = create_vis(tempdir, site_name, for_graph, 'Date', var_name, units, noDataValue)
    version = ts['wml_version']
    file_base = title.replace(" ", "")
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
    #csv_file = UploadedFile(file=csv_file,name=csv_name)

    xml_name_full_path = tempdir + "/" + xml_name
    with open(xml_name_full_path, 'wb') as xml_file:
        xml_file.write(ts['time_series'])

    if version == '1' or version == '1.0':
        wml1_file = {"fname": xml_name, "fhandle":open(xml_name_full_path, 'r')}
        #wml1_file = UploadedFile(file=wml1_file,name=xml_name)
        wml2_file = transform_file(ts, title, tempdir)
        files = [csv_file, wml1_file, wml2_file, vis_file]
        return files
    if version == '2' or version == '2.0':
        wml2_file = {"fname":xml_name, "fhandle":open(xml_name_full_path, 'r')}
        #wml2_file = UploadedFile(file=wml2_file,name=xml_name)
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
        ts = time_series_from_service(res.metadata.referenceURLs.all()[0].value,
                                  res.metadata.referenceURLs.all()[0].type,
                                  site_name_or_code=res.metadata.sites.all()[0].code,
                                  variable_code=res.metadata.variables.all()[0].code)

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
    xml_name = '{0}-{1}'.format(title.replace(" ", ""), 'wml_2_0.xml')
    xml_2_full_path = tempdir + "/" + xml_name

    with open(xml_2_full_path, 'wb') as f:
        f.write(newdom)

    xml_file = open(xml_2_full_path, 'r')
    #xml_file = UploadedFile(file=xml_file, name=xml_name)

    return {"fname":xml_name, "fhandle": xml_file}


