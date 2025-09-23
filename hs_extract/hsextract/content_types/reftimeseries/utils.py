import json
import ssl
from urllib.error import URLError
from urllib.request import Request, urlopen

import jsonschema
import pytz
from dateutil import parser
from hsextract import s3_client as s3


def extract_referenced_timeseries_metadata(res_json_file):
    json_data = _validate_json_file(res_json_file)
    metadata = {}
    metadata["title"] = json_data['timeSeriesReferenceFile']['title']
    metadata["abstract"] = json_data['timeSeriesReferenceFile']['abstract']
    metadata["subjects"] = json_data['timeSeriesReferenceFile']['keyWords']
    metadata["period_coverage"] = period_coverage(json_data)
    metadata["spatial_coverage"] = spatial_coverage(json_data)

    metadata["content_files"] = [res_json_file]

    return metadata


def _validate_json_file(res_json_file):
    with s3.open(res_json_file, 'r') as f:
        json_data = json.loads(f.read())

    try:
        # validate json_data based on the schema
        jsonschema.Draft4Validator(TS_SCHEMA).validate(json_data)
    except jsonschema.ValidationError as ex:
        msg = "Not a valid reference time series json file. {}".format(str(ex))
        raise Exception(msg)

    _validate_json_data(json_data)
    return json_data


def _validate_json_data(json_data):
    # Here we are validating the followings:
    # 1. date values are actually date type data and the beginDate <= endDate
    # 2. 'url' is valid and live if the url value is not none or 'unknown' (case insensitive)
    # 3. 'sampleMedium' is not empty string
    # 4. 'variableName' is not empty string
    # 5. 'title' is not empty string
    # 6. 'abstract' is not empty string
    # 7. 'fileVersion' is not empty string
    # 8. 'symbol' is not empty string
    # 9. 'siteName' is not empty string
    # 10. 'methodLink' is not empty string
    # 11. 'methodDescription' is not empty string

    err_msg = "Invalid json file. {}"
    # validate title
    _check_for_empty_string(
        json_data['timeSeriesReferenceFile']['title'], 'title')

    # validate abstract
    _check_for_empty_string(json_data['timeSeriesReferenceFile'][
                            'abstract'], 'abstract')

    # validate fileVersion
    _check_for_empty_string(json_data['timeSeriesReferenceFile'][
                            'fileVersion'], 'fileVersion')

    # validate symbol
    _check_for_empty_string(
        json_data['timeSeriesReferenceFile']['symbol'], 'symbol')

    series_data = json_data['timeSeriesReferenceFile']['referencedTimeSeries']
    urls = []
    for series in series_data:
        try:
            start_date = parser.parse(series['beginDate'])
            end_date = parser.parse(series['endDate'])
        except Exception:
            raise Exception(err_msg.format("Invalid date values"))

        if start_date.utcoffset() is not None:
            start_date = start_date.replace(tzinfo=None)
        if end_date.utcoffset() is not None:
            end_date = end_date.replace(tzinfo=None)
        if start_date > end_date:
            raise Exception(err_msg.format("Invalid date values"))

        # validate requestInfo object
        request_info = series["requestInfo"]

        # validate refType
        if request_info['refType'] not in ['WOF', "WPS", "DirectFile"]:
            raise ValueError("Invalid value for refType")

        # validate returnType
        if request_info['returnType'] not in ['WaterML 1.1', 'WaterML 2.0', 'TimeseriesML']:
            raise ValueError("Invalid value for returnType")

        # validate serviceType
        if request_info['serviceType'] not in ['SOAP', 'REST']:
            raise ValueError("Invalid value for serviceType")

        # check valueCount is not a negative number
        if series['valueCount'] is not None and series['valueCount'] < 0:
            raise ValueError("valueCount can't be a negative number")

        # check that sampleMedium
        _check_for_empty_string(series['sampleMedium'], 'sampleMedium')

        # validate siteName
        _check_for_empty_string(series['site']['siteName'], 'siteName')

        # validate variableName
        _check_for_empty_string(
            series['variable']['variableName'], 'variableName')

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        url = Request(request_info['url'])
        if url not in urls:
            urls.append(url)
            try:
                urlopen(url, context=ctx)
            except URLError:
                raise Exception(err_msg.format(
                    "Invalid web service URL found"))

        #  validate methodDescription for empty string
        _check_for_empty_string(
            series['method']['methodDescription'], 'methodDescription')

        # validate methodLink
        if series['method']['methodLink'] is not None:
            url = series['method']['methodLink'].strip()
            if not url:
                raise ValueError("methodLink has a value of empty string")
            if url.lower() != 'unknown':
                url = Request(url)
                if url not in urls:
                    urls.append(url)
                    try:
                        urlopen(url, context=ctx)
                    except URLError:
                        raise Exception(err_msg.format(
                            "Invalid method link found"))


def _check_for_empty_string(item_to_chk, item_name):
    if item_to_chk is not None and not item_to_chk.strip():
        raise ValueError("{} has a value of empty string".format(item_name))


TS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "timeSeriesReferenceFile": {
            "type": "object",
            "properties": {
                "title": {"type": ["string", "null"]},
                "abstract": {"type": ["string", "null"]},
                "fileVersion": {"type": ["string", "null"]},
                "keyWords": {"type": ["array", "null"], "items": {"type": "string"}, "uniqueItems": True},
                "symbol": {"type": ["string", "null"]},
                "referencedTimeSeries": {
                    "type": "array",
                    "properties": {
                        "beginDate": {"type": "string"},
                        "endDate": {"type": "string"},
                        "site": {
                            "type": "object",
                            "properties": {
                                "siteCode": {"type": "string"},
                                "siteName": {"type": ["string", "null"]},
                                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                            },
                            "required": ["siteCode", "siteName", "latitude", "longitude"],
                            "additionalProperties": False,
                        },
                        "variable": {
                            "type": "object",
                            "properties": {
                                "variableCode": {"type": "string"},
                                "variableName": {"type": ["string", "null"]},
                            },
                            "required": ["variableCode", "variableName"],
                            "additionalProperties": False,
                        },
                        "method": {
                            "type": "object",
                            "properties": {
                                "methodDescription": {"type": ["string", "null"]},
                                "methodLink": {"type": ["string", "null"]},
                            },
                            "required": ["methodDescription", "methodLink"],
                            "additionalProperties": False,
                        },
                        "requestInfo": {
                            "type": "object",
                            "properties": {
                                "netWorkName": {"type": "string"},
                                "refType": {"enum": ["WOF", "WPS", "DirectFile"]},
                                "returnType": {"enum": ["WaterML 1.1", "WaterML 2.0", "TimeseriesML"]},
                                "serviceType": {"enum": ["SOAP", "REST"]},
                                "url": {"type": "string"},
                            },
                            "required": ["networkName", "refType", "returnType", "serviceType", "url"],
                            "additionalProperties": False,
                        },
                        "sampleMedium": {"type": ["string", "null"]},
                        "valueCount": {"type": ["number", "null"]},
                    },
                    "required": [
                        "beginDate",
                        "endDate",
                        "requestInfo",
                        "site",
                        "sampleMedium",
                        "valueCount",
                        "variable",
                        "method",
                    ],
                    "additionalProperties": False,
                },
            },
            "required": ["title", "abstract", "fileVersion", "keyWords", "symbol", "referencedTimeSeries"],
            "additionalProperties": False,
        }
    },
    "required": ["timeSeriesReferenceFile"],
    "additionalProperties": False,
}


def is_aware(value):
    return value.utcoffset() is not None


def make_naive(value, timezone=pytz.utc):
    """
    Makes an aware datetime.datetime naive in a given time zone.
    """
    # Emulate the behavior of astimezone() on Python < 3.6.
    if not is_aware(value):
        raise ValueError("make_naive() cannot be applied to a naive datetime")
    value = value.astimezone(timezone)
    if hasattr(timezone, 'normalize'):
        # This method is available for pytz time zones.
        value = timezone.normalize(value)
    return value.replace(tzinfo=None)


def period_coverage(json_data):
    # add file level temporal coverage
    start_date = min(
        [parser.parse(series['beginDate']) for series in json_data[
            'timeSeriesReferenceFile']['referencedTimeSeries']]
    )
    end_date = max(
        [parser.parse(series['endDate']) for series in json_data[
            'timeSeriesReferenceFile']['referencedTimeSeries']]
    )
    if is_aware(start_date):
        start_date = make_naive(start_date)
    if is_aware(end_date):
        end_date = make_naive(end_date)
    return {'start': start_date.isoformat(), 'end': end_date.isoformat()}


def spatial_coverage(json_data):
    # add file level spatial coverage
    # check if we have single site or multiple sites
    sites = set([series['site']['siteCode'] for series in json_data[
                'timeSeriesReferenceFile']['referencedTimeSeries']])
    if len(sites) == 1:
        series = json_data['timeSeriesReferenceFile'][
            'referencedTimeSeries'][0]
        value_dict = {
            'east': series['site']['longitude'],
            'north': series['site']['latitude'],
            'projection': 'Unknown',
            'units': "Decimal degrees",
        }
        return {'type': 'point', **value_dict}
    else:
        bbox = {
            'northlimit': -90,
            'southlimit': 90,
            'eastlimit': -180,
            'westlimit': 180,
            'projection': 'Unknown',
            'units': "Decimal degrees",
        }
        for series in json_data['timeSeriesReferenceFile']['referencedTimeSeries']:
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
        return {'type': 'box', **bbox}
