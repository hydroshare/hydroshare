from __future__ import annotations

from datetime import date, datetime

from django import template
from django.utils.dateparse import parse_date, parse_datetime


register = template.Library()


@register.filter
def format_discovery_date(value):
    if not value:
        return ""

    parsed_value = None
    if isinstance(value, datetime):
        parsed_value = value.date()
    elif isinstance(value, date):
        parsed_value = value
    elif isinstance(value, str):
        text = value.strip()
        dt_value = parse_datetime(text)
        if dt_value is None and text.endswith("Z"):
            dt_value = parse_datetime(text.replace("Z", "+00:00"))
        if dt_value is not None:
            parsed_value = dt_value.date()
        else:
            parsed_value = parse_date(text)

    if parsed_value is None:
        return value

    return f"{parsed_value.month}/{parsed_value.day:02d}/{parsed_value.year}"