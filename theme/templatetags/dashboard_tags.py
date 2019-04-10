from __future__ import unicode_literals

from django import template

register = template.Library()


@register.filter(name='icon_name_lookup')
def lookup(dict_icon_type, index):
    if index in dict_icon_type:
        return dict_icon_type[index]
    return ''