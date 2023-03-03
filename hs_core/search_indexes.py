"""Define search indexes for hs_core module."""

# NOTE: this has been optimized for the current and future discovery pages.
# Features that are not used have been commented out temporarily

import logging
import re

import probablepeople

from dateutil import parser
from django.conf import settings
from haystack import fields
from haystack import indexes
from nameparser import HumanName

from hs_core.models import BaseResource

# # SOLR extension needs to be installed for the following to work
# from haystack.utils.geo import Point


adjacent_caps = re.compile("[A-Z][A-Z]")


def remove_whitespace(thing):
    intab = ""
    outtab = ""
    trantab = str.maketrans(intab, outtab, " \t\r\n")
    return str(thing).translate(trantab)


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


def discoverable(thing):
    """ return True if the string given is discoverable information, False if not """
    if thing is not None and thing.strip() != "Unknown" and thing.strip() != "":
        return True
    return False


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    """Define base class for resource indexes."""

    text = indexes.CharField(document=True, use_template=True, stored=False)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True, stored=False)
    author = indexes.FacetCharField()  # normalized to last, first, middle
    author_lower = indexes.FacetCharField()  # normalized to last, first, middle in lower case
    author_url = indexes.CharField(indexed=False, null=True)
    title = indexes.FacetCharField()  # so that sorting isn't tokenized
    title_lower = indexes.FacetCharField()  # so that sorting isn't tokenized
    abstract = indexes.CharField()
    creator = fields.FacetMultiValueField()
    contributor = fields.FacetMultiValueField()
    subject = fields.FacetMultiValueField()
    availability = fields.FacetMultiValueField()
    shareable = indexes.BooleanField()
    # TODO: We might need more information than a bool in the future
    replaced = indexes.BooleanField(stored=False)
    created = indexes.DateTimeField(model_attr='created')
    modified = indexes.DateTimeField(model_attr='last_updated')
    organization = indexes.MultiValueField(stored=False)
    publisher = indexes.CharField(stored=False)
    coverage = indexes.MultiValueField(indexed=False)
    coverage_type = indexes.MultiValueField()
    # TODO: these are duplicated in the coverage field.
    east = indexes.FloatField(null=True)
    north = indexes.FloatField(null=True)
    northlimit = indexes.FloatField(null=True)
    eastlimit = indexes.FloatField(null=True)
    southlimit = indexes.FloatField(null=True)
    westlimit = indexes.FloatField(null=True)
    start_date = indexes.DateField(null=True)
    end_date = indexes.DateField(null=True)
    storage_type = indexes.CharField(stored=False)

    # TODO: SOLR extension needs to be installed for these to work
    # coverage_point = indexes.LocationField(null=True)
    # coverage_southwest = indexes.LocationField(null=True)
    # coverage_northeast = indexes.LocationField(null=True)

    format = indexes.MultiValueField(stored=False)
    identifier = indexes.MultiValueField(stored=False)
    language = indexes.CharField(stored=False)
    relation = indexes.MultiValueField(stored=False)
    geospatialrelations = indexes.MultiValueField(stored=False)
    resource_type = indexes.FacetCharField()
    content_type = fields.FacetMultiValueField()
    content_exts = fields.FacetMultiValueField()
    comment = indexes.MultiValueField(stored=False)
    owner_login = indexes.MultiValueField(stored=False)
    owner = fields.FacetMultiValueField()
    person = indexes.MultiValueField(stored=False)

    # non-core metadata
    geometry_type = indexes.CharField(stored=False)
    field_name = indexes.CharField(stored=False)
    field_type = indexes.CharField(stored=False)
    field_type_code = indexes.CharField(stored=False)
    variable = indexes.MultiValueField(stored=False)
    variable_type = indexes.MultiValueField(stored=False)
    variable_shape = indexes.MultiValueField(stored=False)
    variable_descriptive_name = indexes.MultiValueField(stored=False)
    variable_speciation = indexes.MultiValueField(stored=False)
    site = indexes.MultiValueField(stored=False)
    method = indexes.MultiValueField(stored=False)
    quality_level = indexes.MultiValueField(stored=False)
    data_source = indexes.MultiValueField(stored=False)
    sample_medium = indexes.MultiValueField(stored=False)
    units = indexes.MultiValueField(stored=False)
    units_type = indexes.MultiValueField(stored=False)
    absolute_url = indexes.CharField(indexed=False)

    # extra metadata
    extra = indexes.MultiValueField(stored=False)

    def _cache_queryset(self, obj, attribute_name, qs_to_cache):
        # Here is the link why we are setting a cached_attribute on obj (resource) to minimize DB queries
        # https://docs.djangoproject.com/en/1.11/topics/db/queries/#caching-and-querysets
        if not hasattr(obj, attribute_name):
            setattr(obj, attribute_name, qs_to_cache)

    def _has_metadata(self, obj):
        return hasattr(obj, 'metadata') and obj.metadata is not None

    def _get_coverage_bounding_box_value(self, obj, box_direction):
        """Gets the coverage value for the box limit
        :param  obj: an instance of resource
        :param  box_direction: One of these: northlimit, westlimit, southlimit, or eastlimit
        """
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.cached_coverages:
                if coverage.type == 'box':
                    return coverage.value[box_direction]

        return None

    def get_model(self):
        """Return BaseResource model."""
        return BaseResource

    def index_queryset(self, using=None):
        """Return queryset including discoverable (and public) resources."""
        candidates = self.get_model().objects.filter(raccess__discoverable=True).select_related('raccess')
        show = [x.short_id for x in candidates if x.show_in_discover]
        # this must return a queryset; this inefficient method is the best I can do
        discoverable_resources = self.get_model().objects.filter(short_id__in=show)
        discoverable_resources = discoverable_resources.select_related('raccess')
        return discoverable_resources

    def prepare_created(self, obj):
        return obj.created.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_modified(self, obj):
        return obj.last_updated.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_title(self, obj):
        """Return metadata title if exists, otherwise return 'none'."""

        if self._has_metadata(obj):
            if not hasattr(obj, 'cached_title'):
                self._cache_queryset(obj, 'cached_title', obj.metadata.title)
            title = obj.cached_title
            if title is not None and title.value is not None:
                return title.value.lstrip()
        else:
            return 'none'

    def prepare_title_lower(self, obj):
        result = self.prepare_title(obj)
        return result.lower()

    def prepare_abstract(self, obj):
        """Return metadata abstract if exists, otherwise return None."""

        if self._has_metadata(obj):
            description = obj.metadata.description
            if description is not None and description.abstract is not None:
                return description.abstract.lstrip()

        return None

    # TODO: it is confusing that the "author" is the first "creator"
    def prepare_author(self, obj):
        """
        Return first creator if exists, otherwise return empty list.

        This must be represented as a single-value field to enable sorting.
        """

        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_creators', obj.metadata.creators.all())
            first_creator = None
            for cr in obj.cached_creators:
                if cr.order == 1:
                    first_creator = cr
                    break
            if first_creator is None:
                return 'none'
            elif first_creator.name:
                normalized = normalize_name(first_creator.name)
                return normalized
            elif first_creator.organization:
                return first_creator.organization.strip()
            else:
                return 'none'
        return 'none'

    def prepare_author_lower(self, obj):
        result = self.prepare_author(obj)
        return result.lower()

    def prepare_author_url(self, obj):
        """
        Return metadata author description url if exists, otherwise return None.

        This field is stored but not indexed, to avoid hitting the Django database during response.
        """
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_creators', obj.metadata.creators.all())
            first_creator = None
            for cr in obj.cached_creators:
                if cr.order == 1:
                    first_creator = cr
                    break
            if first_creator is not None and first_creator.relative_uri is not None:
                return first_creator.relative_uri
            else:
                return None
        return None

    def prepare_creator(self, obj):
        """
        Return metadata creators if they exist, otherwise return empty array.

        This field can have multiple values
        """
        normalized_names = []
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_creators', obj.metadata.creators.all())
            for creator in obj.cached_creators:
                if creator.name is None or creator.name == '':
                    continue
                normalized_names.append(normalize_name(creator.name))

        return normalized_names

    def prepare_contributor(self, obj):
        """
        Return metadata contributors if they exist, otherwise return empty array.

        This field can have multiple values. Contributors include creators.
        """
        normalized_names = []
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_contributors', obj.metadata.contributors.all())
            for contributor in obj.cached_contributors:
                if contributor.name is None or contributor.name == '':
                    continue
                normalized_names.append(normalize_name(contributor.name))

        return list(set(normalized_names))  # remove duplicates

    def prepare_subject(self, obj):
        """
        Return metadata subjects if they exist, otherwise return empty array.

        This field can have multiple values.
        """
        subjects = []
        if self._has_metadata(obj):
            for subject in obj.metadata.subjects.all():
                if subject.value is None:
                    continue
                subjects.append(subject.value.strip())

        return subjects

    def prepare_organization(self, obj):
        """
        Return metadata organization if it exists, otherwise return empty array.
        """
        organizations = []
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_creators', obj.metadata.creators.all())
            for creator in obj.cached_creators:
                if creator.organization is None:
                    continue
                organizations.append(creator.organization.strip())

        return organizations

    def prepare_publisher(self, obj):
        """
        Return metadata publisher if it exists; otherwise return empty array.
        """
        if self._has_metadata(obj):
            publisher = obj.metadata.publisher
            if publisher is not None:
                return str(publisher).lstrip()
            else:
                return None
        else:
            return None

    def prepare_availability(self, obj):
        """
        availability is published, public, or discoverable

        To make faceting work properly, all flags that are True are represented.
        """
        options = []
        if hasattr(obj, 'raccess'):
            if obj.raccess.published:
                options.append('published')
            elif obj.raccess.public:
                options.append('public')
            elif obj.raccess.discoverable:
                options.append('discoverable')
            else:
                options.append('private')
        else:
            options.append('private')
        return options

    def prepare_shareable(self, obj):
        """ used in depicting results """
        return obj.raccess.shareable

    def prepare_replaced(self, obj):
        """Return True if 'isReplacedBy' attribute exists, otherwise return False."""
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_relations', obj.metadata.relations.all())
            for relation in obj.cached_relations:
                if relation.type == 'isReplacedBy':
                    return True
        return False

    def prepare_coverage(self, obj):
        """Return resource coverage if exists, otherwise return empty array."""
        # TODO: reject empty coverages
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            return [coverage._value.strip() for coverage in obj.cached_coverages]
        return []

    def prepare_coverage_type(self, obj):
        """
        Return resource coverage types if exists, otherwise return empty array.

        This field can have multiple values.
        """
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            return [coverage.type.strip() for coverage in obj.cached_coverages]
        return []

    # TODO: THIS IS SIMPLY THE WRONG WAY TO DO THINGS.
    # Should use geopy Point and Haystack LocationField throughout,
    # instead of encoding limits literally.
    # See http://django-haystack.readthedocs.io/en/v2.6.0/spatial.html

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_east(self, obj):
        """Return resource coverage east bound if exists, otherwise return None."""

        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            for coverage in obj.cached_coverages:
                if coverage.type == 'point':
                    return float(coverage.value["east"])
                # TODO: this returns the box center, not the extent
                # TODO: probably better to call this something different.
                elif coverage.type == 'box':
                    return (float(coverage.value["eastlimit"])
                            + float(coverage.value["westlimit"])) / 2
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_north(self, obj):
        """Return resource coverage north bound if exists, otherwise return None."""
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            for coverage in obj.cached_coverages:
                if coverage.type == 'point':
                    return float(coverage.value["north"])
                # TODO: This returns the box center, not the extent
                elif coverage.type == 'box':
                    return (float(coverage.value["northlimit"])
                            + float(coverage.value["southlimit"])) / 2
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_northlimit(self, obj):
        """Return resource coverage north limit if exists, otherwise return None."""

        return self._get_coverage_bounding_box_value(obj, "northlimit")

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_eastlimit(self, obj):
        """Return resource coverage east limit if exists, otherwise return None."""

        return self._get_coverage_bounding_box_value(obj, "eastlimit")

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_southlimit(self, obj):
        """Return resource coverage south limit if exists, otherwise return None."""

        return self._get_coverage_bounding_box_value(obj, "southlimit")

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_westlimit(self, obj):
        """Return resource coverage west limit if exists, otherwise return None."""

        return self._get_coverage_bounding_box_value(obj, "westlimit")

    # TODO: time coverages do not specify timezone, and timezone support is active.
    # TODO: Why aren't time coverages specified as Django DateTime objects?
    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_start_date(self, obj):
        """Return resource coverage start date if exists, otherwise return None."""

        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            for coverage in obj.cached_coverages:
                if coverage.type == 'period' and 'start' in coverage.value:
                    start_date = coverage.value["start"]
                    try:
                        start_date = parser.parse(start_date).date()
                        return start_date
                    except ValueError:
                        logger = logging.getLogger(__name__)
                        logger.error("invalid start date {} in resource {} {}"
                                     .format(start_date, obj.short_id, str(obj)))
                        return None
        return None

    # TODO: time coverages do not specify timezone, and timezone support is active.
    # TODO: Why aren't time coverages specified as Django DateTime objects?
    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_end_date(self, obj):
        """Return resource coverage end date if exists, otherwise return None."""

        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_coverages', obj.metadata.coverages.all())
            for coverage in obj.cached_coverages:
                if coverage.type == 'period' and 'end' in coverage.value:
                    end_date = coverage.value["end"]
                    try:
                        end_date = parser.parse(end_date).date()
                        return end_date
                    except ValueError:
                        logger = logging.getLogger(__name__)
                        logger.error("invalid end date {} in resource {} {}"
                                     .format(end_date, obj.short_id, str(obj)))
                        return None
        return None

    def prepare_storage_type(self, obj):
        return obj.storage_type

    def prepare_format(self, obj):
        """Return metadata formats if metadata exists, otherwise return empty array."""
        if self._has_metadata(obj):
            return [frmt.value.strip() for frmt in obj.metadata.formats.all()]
        return []

    def prepare_identifier(self, obj):
        """Return metadata identifiers if metadata exists, otherwise return empty array."""
        if self._has_metadata(obj):
            return [identifier.name.strip() for identifier in obj.metadata.identifiers.all()]
        return []

    def prepare_language(self, obj):
        """Return resource language if exists, otherwise return None."""
        if self._has_metadata(obj):
            language = obj.metadata.language
            if language is not None and language.code is None:
                return obj.metadata.language.code.strip()
        return None

    def prepare_relation(self, obj):
        """Return resource relations if exists, otherwise return empty array."""
        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_relations', obj.metadata.relations.all())
            return [relation.value.strip() for relation in obj.cached_relations]

        return []

    def prepare_geospatialrelation(self, obj):
        """Return resource geospatialrelations if exists, otherwise return empty array."""
        if self._has_metadata(obj):
            return [relation.text.strip() for relation in obj.metadata.geospatialrelations.all()]

        return []

    def prepare_resource_type(self, obj):
        """Resource type is display_name attribute of obj argument."""
        content_model = obj.get_content_model()
        return content_model.display_name

    def prepare_content_type(self, obj):
        """ register content types for both logical files and some MIME types """

        self._cache_queryset(obj, 'content_types', get_content_types(obj))

        if obj.resource_type == 'CompositeResource':
            output = obj.content_types[0]
            return list(output)
        else:
            return [obj.discovery_content_type]

    def prepare_content_exts(self, obj):
        """ index by file extension """

        self._cache_queryset(obj, 'content_types', get_content_types(obj))
        output = obj.content_types[2]
        return output

    def prepare_comment(self, obj):
        """Return list of all comments on resource."""
        return [comment.comment.strip() for comment in obj.comments.all()]

    def prepare_owner_login(self, obj):
        """Return list of usernames that have ownership access to resource."""

        if hasattr(obj, 'raccess'):
            self._cache_queryset(obj, 'cached_owners', obj.raccess.owners.all())
            return [owner.username for owner in obj.cached_owners]
        return []

    # TODO: should utilize name from user profile rather than from User field
    def prepare_owner(self, obj):
        """Return list of names of resource owners."""
        names = []
        if hasattr(obj, 'raccess'):
            self._cache_queryset(obj, 'cached_owners', obj.raccess.owners.all())
            for owner in obj.cached_owners:
                name = normalize_name(owner.first_name + ' ' + owner.last_name)
                names.append(name)
        return names

    # TODO: should utilize name from user profile rather than from User field
    def prepare_person(self, obj):
        """Return list of normalized names of resource contributors and owners."""
        output0 = []
        output1 = []
        output2 = []

        if hasattr(obj, 'raccess'):
            self._cache_queryset(obj, 'cached_owners', obj.raccess.owners.all())
            for owner in obj.cached_owners:
                name = normalize_name(owner.first_name + ' ' + owner.last_name)
                output0.append(name)

        if self._has_metadata(obj):
            self._cache_queryset(obj, 'cached_creators', obj.metadata.creators.all())
            self._cache_queryset(obj, 'cached_contributors', obj.metadata.contributors.all())
            for creator in obj.cached_creators:
                if creator.name is not None and creator.name != '':
                    output1.append(normalize_name(creator.name))
            for contributor in obj.cached_contributors:
                if contributor.name is not None and contributor.name != '':
                    output2.append(normalize_name(contributor.name))

        return list(set(output0 + output1 + output2))  # eliminate duplicates

    # TODO: These should probably be multi-value fields and pick up all types.
    def prepare_geometry_type(self, obj):
        """
        Return geometry type if metadata exists, otherwise return [].
        TODO: there can be multiples of these now.
        """
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_geofeature_logical_files', obj.geofeaturelogicalfile_set.all())
            for f in obj.cached_geofeature_logical_files:
                geometry_info = f.metadata.geometryinformation
                if geometry_info is not None:
                    return geometry_info.geometryType
        return None

    def prepare_field_name(self, obj):
        """
        Return metadata field name if exists, otherwise return [].
        TODO: there can be multiples of these now.
        """

        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_geofeature_logical_files', obj.geofeaturelogicalfile_set.all())
            for f in obj.cached_geofeature_logical_files:
                field_info = f.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldName is not None:
                    return field_info.fieldName.strip()
        return None

    def prepare_field_type(self, obj):
        """
        Return metadata field type if exists, otherwise return None.
        TODO: there can be multiples of these now.
        """
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_geofeature_logical_files', obj.geofeaturelogicalfile_set.all())
            for f in obj.cached_geofeature_logical_files:
                field_info = f.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldType is not None:
                    return field_info.fieldType.strip()
        return None

    def prepare_field_type_code(self, obj):
        """
        Return metadata field type code if exists, otherwise return [].
        """
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_geofeature_logical_files', obj.geofeaturelogicalfile_set.all())
            for f in obj.cached_geofeature_logical_files:
                field_info = f.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldTypeCode is not None:
                    return field_info.fieldTypeCode.strip()
        return None

    def prepare_variable(self, obj):
        """
        Return metadata variable names if exists, otherwise return empty array.
        """

        variables = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_netcdf_logical_files', obj.netcdflogicalfile_set.all())
            for f in obj.cached_netcdf_logical_files:
                for v in f.metadata.variables.all():
                    if discoverable(v.name):
                        variables.add(v.name.strip())

            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.variables:
                    # TODO: inconsistent use of variable code and variable name
                    if discoverable(v.variable_name):
                        variables.add(v.variable_name.strip())
            self._cache_queryset(obj, 'cached_reftimeseries_logical_files', obj.reftimeserieslogicalfile_set.all())
            for f in obj.cached_reftimeseries_logical_files:
                for v in f.metadata.variables:
                    # TODO: inconsistent use of variable code and variable name
                    if discoverable(v.name):
                        variables.add(v.name.strip())
            for f in obj.georasterlogicalfile_set.all():
                for b in f.metadata.bandInformations:
                    if discoverable(b.variableName):
                        variables.add(b.variableName)
        return list(variables)

    def prepare_variable_type(self, obj):
        """
        Return metadata variable types if exists, otherwise return empty array.
        Variable type does not exist for referenced time series files.
        TODO: Deprecated. Not particularly useful as a search locator.
        """

        variable_types = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_netcdf_logical_files', obj.netcdflogicalfile_set.all())
            for f in obj.cached_netcdf_logical_files:
                for v in f.metadata.variables.all():
                    if discoverable(v.type):
                        variable_types.add(v.type.strip())

            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.variables:
                    if discoverable(v.variable_type):
                        variable_types.add(v.variable_type.strip())
        return list(variable_types)

    def prepare_variable_shape(self, obj):
        """
        Return metadata variable shapes if exists, otherwise return empty array.
        Shape only exists for NetCDF resources.
        """

        variable_shapes = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_netcdf_logical_files', obj.netcdflogicalfile_set.all())
            for f in obj.cached_netcdf_logical_files:
                for v in f.metadata.variables.all():
                    if discoverable(v.shape):
                        variable_shapes.add(v.shape.strip())
        return list(variable_shapes)

    def prepare_variable_descriptive_name(self, obj):
        """
        Return metadata variable descriptive names if exists, otherwise return empty array.
        TODO: Deprecated. This is empty for all resources and should be deleted.
        """
        return []

    def prepare_variable_speciation(self, obj):
        """
        Return metadata variable speciations if exists, otherwise return empty array.
        Speciation only exists for the time series file type.
        """

        variable_speciations = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.variables:
                    if discoverable(v.speciation):
                        variable_speciations.add(v.speciation.strip())
        return list(variable_speciations)

    def prepare_site(self, obj):
        """
        Return list of sites if exists, otherwise return empty array.
        Sites only exist for time series.
        TODO: inconsistent use of site name and site code
        """

        sites = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for s in f.metadata.sites:
                    if discoverable(s.site_name):
                        sites.add(s.site_name.strip())
            self._cache_queryset(obj, 'cached_reftimeseries_logical_files', obj.reftimeserieslogicalfile_set.all())
            for f in obj.cached_reftimeseries_logical_files:
                for s in f.metadata.sites:
                    if discoverable(s.name):
                        sites.add(s.name.strip())
        return list(sites)

    def prepare_method(self, obj):
        """
        Return list of methods if exists, otherwise return empty array.
        Methods only exist for time series and referenced time series.
        """

        methods = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for s in f.metadata.methods:
                    if discoverable(s.method_description):
                        methods.add(s.method_description.strip())

            self._cache_queryset(obj, 'cached_reftimeseries_logical_files', obj.reftimeserieslogicalfile_set.all())
            for f in obj.cached_reftimeseries_logical_files:
                for s in f.metadata.methods:
                    if discoverable(s.description):
                        methods.add(s.description.strip())
        return list(methods)

    def prepare_quality_level(self, obj):
        """
        Return list of quality levels if exists, otherwise return empty array.
        TODO: Deprecated. No longer present in data.
        """
        return []

    def prepare_data_source(self, obj):
        """
        Return list of data sources if exists, otherwise return empty array.
        TODO: Deprecated: doesn't seem to exist any more.
        """
        return []

    def prepare_sample_medium(self, obj):
        """
        Return list of sample mediums if exists, otherwise return empty array.
        Sample mediums only exist for time-series types.
        """

        mediums = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.time_series_results:
                    if discoverable(v.sample_medium):
                        mediums.add(v.sample_medium.strip())

            self._cache_queryset(obj, 'cached_reftimeseries_logical_files', obj.reftimeserieslogicalfile_set.all())
            for f in obj.cached_reftimeseries_logical_files:
                for v in f.metadata.sample_mediums:
                    if discoverable(v):
                        mediums.add(v.strip())
        return list(mediums)

    def prepare_units(self, obj):
        """
        Return list of units names if exists, otherwise return empty array.
        Match both units name and units type in this field.
        TODO: Seriously consider blurring the distinction between units and variables during discovery.
        """

        units = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.time_series_results:
                    # TODO: inconsistent use of units name and units type
                    if discoverable(v.units_name):
                        units.add(v.units_name.strip())
        return list(units)

    def prepare_units_type(self, obj):
        """
        Return list of units types if exists, otherwise return empty array.
        TODO: Deprecated. In future, use "units" to refer to name and type.
        """

        units_types = set()
        if obj.resource_type == 'CompositeResource':
            self._cache_queryset(obj, 'cached_timeseries_logical_files', obj.timeserieslogicalfile_set.all())
            for f in obj.cached_timeseries_logical_files:
                for v in f.metadata.time_series_results:
                    if discoverable(v.units_type):
                        units_types.add(v.units_type.strip())
        return list(units_types)

    def prepare_absolute_url(self, obj):
        """Return absolute URL of object."""
        return obj.get_absolute_url()

    def prepare_extra(self, obj):
        """ For extra metadata, include both key and value """
        extra = []
        for key, value in obj.extra_metadata.items():
            extra.append(key + ': ' + value)
        return extra
