import datetime
import re

from dateutil import tz

HS_DATE_PATT = "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
HS_DATE_PATT += "T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
HS_DATE_PATT += "T(?P<tz>\S+)$" # noqa
HS_DATE_RE = re.compile(HS_DATE_PATT)

HS_DATE_ISO_PATT = "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
HS_DATE_ISO_PATT += "[T\s](?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})(?P<microsecond>\.[0-9]+){0,1}" # noqa
HS_DATE_ISO_PATT += "(?P<tz>\S+)$" # noqa
HS_DATE_ISO_RE = re.compile(HS_DATE_ISO_PATT)

HS_DATE_NOTZ_PATT = "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
HS_DATE_NOTZ_PATT += "T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})$"
HS_DATE_NOTZ_RE = re.compile(HS_DATE_NOTZ_PATT)


def hs_date_to_datetime(datestr):
    """
    Parse HydroShare (HS) formatted date from a String to a datetime.datetime.
     Note: We use a weird TZ format, that does not appear to be ISO 8601
     compliant, e.g.: 2015-06-03T09:29:00T-00003
    :param datestr: String representing the date in HS format
    :return: datetime.datetime with timezone set to UTC
    """
    m = HS_DATE_RE.match(datestr)
    if m is None:
        msg = "Unable to parse date {0}.".format(datestr)
        raise HsDateException(msg)
    try:
        ret_date = datetime.datetime(year=int(m.group('year')),
                                     month=int(m.group('month')),
                                     day=int(m.group('day')),
                                     hour=int(m.group('hour')),
                                     minute=int(m.group('minute')),
                                     second=int(m.group('second')),
                                     tzinfo=tz.UTC)
    except Exception as e:
        msg = "Unable to parse date {0}, error {1}.".format(datestr,
                                                            str(e))
        raise HsDateException(msg)

    return ret_date


def hs_date_to_datetime_iso(datestr):
    """
    Parse the ISO 8601-formatted HydroShare (HS) date from a String to a datetime.datetime.
    :param datestr: String representing the date in HS format
    :return: datetime.datetime with timezone set to UTC
    """
    m = HS_DATE_ISO_RE.match(datestr)
    if m is None:
        msg = "Unable to parse date {0}.".format(datestr)
        raise HsDateException(msg)
    try:
        # Handle microseconds (if present)
        if m.group('microsecond'):
            us = float(m.group('microsecond'))
            # Convert from seconds to microseconds
            microsecond = int(1000 * 1000 * us)
        else:
            microsecond = 0

        ret_date = datetime.datetime(year=int(m.group('year')),
                                     month=int(m.group('month')),
                                     day=int(m.group('day')),
                                     hour=int(m.group('hour')),
                                     minute=int(m.group('minute')),
                                     second=int(m.group('second')),
                                     microsecond=microsecond,
                                     tzinfo=tz.UTC)
    except Exception as e:
        msg = "Unable to parse date {0}, error {1}.".format(datestr,
                                                            str(e))
        raise HsDateException(msg)

    return ret_date


def hs_date_to_datetime_notz(datestr):
    """
    Parse HydroShare (HS) formatted datetime (without timezone information) from a String
    to a datetime.datetime.
    :param datestr: String representing the date in HS format (without timezone information)
    :return: datetime.datetime with timezone set to UTC
    """
    m = HS_DATE_NOTZ_RE.match(datestr)
    if m is None:
        msg = "Unable to parse date {0}.".format(datestr)
        raise HsDateException(msg)
    try:
        ret_date = datetime.datetime(year=int(m.group('year')),
                                     month=int(m.group('month')),
                                     day=int(m.group('day')),
                                     hour=int(m.group('hour')),
                                     minute=int(m.group('minute')),
                                     second=int(m.group('second')),
                                     tzinfo=tz.UTC)
    except Exception as e:
        msg = "Unable to parse date {0}, error {1}.".format(datestr,
                                                            str(e))
        raise HsDateException(msg)

    return ret_date


class HsDateException(Exception):
    pass
