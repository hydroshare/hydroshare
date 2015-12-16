from __future__ import absolute_import, division, unicode_literals
from future.builtins import int, open, str

from hashlib import md5
from json import loads
import os
#from dublincore.models import AbstractQualifiedDublinCoreTerm
import re

try:
    from urllib.request import urlopen
    from urllib.parse import urlencode, quote, unquote
except ImportError:
    from urllib import urlopen, urlencode, quote, unquote

from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse, resolve, NoReverseMatch
from django.db.models import Model, get_model
from django.template import (Context, Node, TextNode, Template,
    TemplateSyntaxError, TOKEN_TEXT, TOKEN_VAR, TOKEN_COMMENT, TOKEN_BLOCK)
from django.template.defaultfilters import escape
from django.template.loader import get_template
from django.utils import translation
from django.utils.html import strip_tags
from django.utils.text import capfirst

# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image, ImageFile, ImageOps
except ImportError:
    import Image
    import ImageFile
    import ImageOps

from mezzanine.conf import settings
from mezzanine.core.fields import RichTextField
from mezzanine.core.forms import get_edit_form
from mezzanine.utils.cache import nevercache_token, cache_installed
from mezzanine.utils.html import decode_entities
from mezzanine.utils.importing import import_dotted_path
from mezzanine.utils.sites import current_site_id, has_site_permission
from mezzanine.utils.urls import admin_url
from mezzanine.utils.views import is_editable
from mezzanine import template


register = template.Library()


@register.filter
def resource_type(content):
    return content.get_content_model()._meta.verbose_name

@register.filter
def contact(content):
    """
    Takes a value edited via the WYSIWYG editor, and passes it through
    each of the functions specified by the RICHTEXT_FILTERS setting.
    """
    if not content:
        return ''

    if not content.is_authenticated():
        content = "Anonymous"
    elif content.first_name:
        content = """<a href='/user/{uid}/'>{fn} {ln}<a>""".format(fn=content.first_name, ln=content.last_name, uid=content.pk)
    else:
        content = """<a href='/user/{uid}/'>{un}<a>""".format(uid=content.pk, un=content.username)

    return content

@register.filter
def best_name(content):
    """
    Takes a value edited via the WYSIWYG editor, and passes it through
    each of the functions specified by the RICHTEXT_FILTERS setting.
    """

    if not content.is_authenticated():
        content = "Anonymous"
    elif content.first_name:
        content = """{fn} {ln}""".format(fn=content.first_name, ln=content.last_name, un=content.username)
    else:
        content = content.username

    return content