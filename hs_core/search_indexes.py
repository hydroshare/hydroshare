"""Define search indexes for hs_core module."""

# NOTE: this has been optimized for the current and future discovery pages.
# Features that are not used have been commented out temporarily

import re

import probablepeople

from django.conf import settings
from nameparser import HumanName


# # SOLR extension needs to be installed for the following to work
# from haystack.utils.geo import Point


adjacent_caps = re.compile("[A-Z][A-Z]")


def normalize_name(name):
    """
    Normalize a name for sorting and indexing.

    This uses two powerful python libraries for differing reasons.

    `probablepeople` contains a discriminator between company and person names.
    This is used to determine whether to parse into last, first, middle or to
    leave the name alone.

    However, the actual name parser in `probablepeople` is unnecessarily complex,
    so that strings that it determines to be human names are parsed instead by
    the simpler `nameparser`.

    """
    sname = name.strip()  # remove leading and trailing spaces

    # Recognizer tends to mistake concatenated initials for Corporation name.
    # Pad potential initials with spaces before running recognizer
    # For any character A-Z followed by "." and another character A-Z, add a space after the first.
    # (?=[A-Z]) means to find A-Z after the match string but not match it.
    nname = re.sub("(?P<thing>[A-Z]\\.)(?=[A-Z])", "\\g<thing> ", sname)

    try:
        # probablepeople doesn't understand utf-8 encoding. Hand it pure unicode.
        _, type = probablepeople.tag(nname)  # discard parser result
    except probablepeople.RepeatedLabelError:  # if it can't understand the name, it's foreign
        type = 'Unknown'

    if type == 'Corporation':
        return sname  # do not parse and reorder company names

    # special case for capitalization: flag as corporation
    if (adjacent_caps.match(sname)):
        return sname

    # treat anything else as a human name
    nameparts = HumanName(nname)
    normalized = ""
    if nameparts.last:
        normalized = nameparts.last

    if nameparts.suffix:
        if not normalized:
            normalized = nameparts.suffix
        else:
            normalized = normalized + ' ' + nameparts.suffix

    if normalized:
        normalized = normalized + ','

    if nameparts.title:
        if not normalized:
            normalized = nameparts.title
        else:
            normalized = normalized + ' ' + nameparts.title

    if nameparts.first:
        if not normalized:
            normalized = nameparts.first
        else:
            normalized = normalized + ' ' + nameparts.first

    if nameparts.middle:
        if not normalized:
            normalized = nameparts.middle
        else:
            normalized = ' ' + normalized + ' ' + nameparts.middle

    return normalized.strip()


def get_content_types(res):
    """ return a set of content types matching extensions in a resource.
        These include content types of logical files, as well as the generic
        content types 'Document', 'Spreadsheet', 'Presentation'.

        This is only meaningful for Composite resources.
    """

    resource = res.get_content_model()  # enable full logical file interface

    types = {res.discovery_content_type}  # accumulate high-level content types.
    missing_exts = set()  # track unmapped file extensions
    all_exts = set()  # track all file extensions

    # categorize logical files by type, and files without a logical file by extension.
    for f in resource.files.all():
        # collect extensions of files
        path = f.short_path
        path = path.split(".")  # determine last extension
        if len(path) > 1:
            ext = path[len(path) - 1]
            if len(ext) <= 5:  # skip obviously non-MIME extensions
                all_exts.add(ext.lower())
            else:
                ext = None
        else:
            ext = None

        if f.has_logical_file:
            candidate_type = type(f.logical_file).get_discovery_content_type()
            types.add(candidate_type)
        else:
            if ext is not None:
                missing_exts.add(ext.lower())

    # categorize common extensions that are not part of logical files.
    for ext_type in settings.DISCOVERY_EXTENSION_CONTENT_TYPES:
        if missing_exts & settings.DISCOVERY_EXTENSION_CONTENT_TYPES[ext_type]:
            types.add(ext_type)
            missing_exts -= settings.DISCOVERY_EXTENSION_CONTENT_TYPES[ext_type]

    if missing_exts:  # if there is anything left over, then mark as Generic
        types.add('Generic Data')

    return types, missing_exts, all_exts
