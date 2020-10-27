"""Define search indexes for hs_core module."""

from haystack import indexes
from hs_core.models import BaseResource
from hs_geographic_feature_resource.models import GeographicFeatureMetaData
from hs_app_netCDF.models import NetcdfMetaData
from ref_ts.models import RefTSMetadata
from hs_app_timeseries.models import TimeSeriesMetaData
from datetime import datetime
from nameparser import HumanName
import probablepeople
from django.conf import settings
import logging
import re

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

        This is only meaningful for Generic or Composite resources.
    """

    resource = res.get_content_model()  # enable full logical file interface

    types = set([res.discovery_content_type])  # accumulate high-level content types.
    exts = set()  # track individual file extensions

    # categorize logical files by type, and files without a logical file by extension.
    for f in resource.files.all():
        if f.has_logical_file:
            candidate_type = type(f.logical_file).get_discovery_content_type()
            types.add(candidate_type)
        else:  # collect extensions of files not corresponding to logical metadata
            path = f.short_path
            path = path.split(".")  # determine last extension
            if len(path) > 1:
                ext = path[len(path)-1]
                if len(ext) <= 5:  # skip obviously non-MIME extensions
                    exts.add(ext.lower())

    # categorize common extensions that are not part of logical files.
    for ext_type in settings.DISCOVERY_EXTENSION_CONTENT_TYPES:
        if exts & settings.DISCOVERY_EXTENSION_CONTENT_TYPES[ext_type]:
            types.add(ext_type)
            exts -= settings.DISCOVERY_EXTENSION_CONTENT_TYPES[ext_type]

    if exts:  # if there is anything left over, then mark as Generic
        types.add('Generic Data')

    return (types, exts)


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    """Define base class for resource indexes."""

    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(faceted=True)  # normalized to last, first, middle
    author_raw = indexes.CharField(indexed=False)  # not normalized
    author_url = indexes.CharField(indexed=False, null=True)
    title = indexes.CharField()
    abstract = indexes.CharField()
    creator = indexes.MultiValueField(faceted=True)
    contributor = indexes.MultiValueField(faceted=True)
    subject = indexes.MultiValueField(faceted=True)
    availability = indexes.MultiValueField(faceted=True)
    # TODO: We might need more information than a bool in the future
    replaced = indexes.BooleanField()
    created = indexes.DateTimeField(model_attr='created')
    modified = indexes.DateTimeField(model_attr='last_updated')
    organization = indexes.MultiValueField(faceted=True)
    creator_email = indexes.MultiValueField()
    publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    coverage = indexes.MultiValueField()
    coverage_type = indexes.MultiValueField()
    east = indexes.FloatField(null=True)
    north = indexes.FloatField(null=True)
    northlimit = indexes.FloatField(null=True)
    eastlimit = indexes.FloatField(null=True)
    southlimit = indexes.FloatField(null=True)
    westlimit = indexes.FloatField(null=True)
    start_date = indexes.DateField(null=True)
    end_date = indexes.DateField(null=True)
    storage_type = indexes.CharField()

    # # TODO: SOLR extension needs to be installed for these to work
    # coverage_point = indexes.LocationField(null=True)
    # coverage_southwest = indexes.LocationField(null=True)
    # coverage_northeast = indexes.LocationField(null=True)

    format = indexes.MultiValueField()
    identifier = indexes.MultiValueField()
    language = indexes.CharField(faceted=True)
    source = indexes.MultiValueField()
    relation = indexes.MultiValueField()
    resource_type = indexes.CharField(faceted=True)
    content_type = indexes.MultiValueField(faceted=True)
    comment = indexes.MultiValueField()
    comments_count = indexes.IntegerField(faceted=True)
    owner_login = indexes.MultiValueField(faceted=True)
    owner = indexes.MultiValueField(faceted=True)
    owners_count = indexes.IntegerField(faceted=True)
    # # TODO: We might need these later for social discovery
    # viewer_login = indexes.MultiValueField(faceted=True)
    # viewer = indexes.MultiValueField(faceted=True)
    # viewers_count = indexes.IntegerField(faceted=True)
    # editor_login = indexes.MultiValueField(faceted=True)
    # editor = indexes.MultiValueField(faceted=True)
    # editors_count = indexes.IntegerField(faceted=True)
    person = indexes.MultiValueField(faceted=True)

    # non-core metadata
    geometry_type = indexes.CharField(faceted=True)
    field_name = indexes.CharField()
    field_type = indexes.CharField()
    field_type_code = indexes.CharField()
    variable = indexes.MultiValueField(faceted=True)
    variable_type = indexes.MultiValueField(faceted=True)
    variable_shape = indexes.MultiValueField()
    variable_descriptive_name = indexes.MultiValueField()
    variable_speciation = indexes.MultiValueField()
    site = indexes.MultiValueField()
    method = indexes.MultiValueField()
    quality_level = indexes.MultiValueField()
    data_source = indexes.MultiValueField()
    sample_medium = indexes.MultiValueField(faceted=True)
    units = indexes.MultiValueField(faceted=True)
    units_type = indexes.MultiValueField(faceted=True)
    aggregation_statistics = indexes.MultiValueField()
    absolute_url = indexes.CharField(indexed=False)

    # extra metadata
    extra = indexes.MultiValueField()

    def get_model(self):
        """Return BaseResource model."""
        return BaseResource

    def index_queryset(self, using=None):
        """Return queryset including discoverable (and public) resources."""
        candidates = self.get_model().objects.filter(raccess__discoverable=True)
        show = [x.short_id for x in candidates if x.show_in_discover]
        # this must return a queryset; this inefficient method is the best I can do
        return self.get_model().objects.filter(short_id__in=show)

    def prepare_created(self, obj):
        return obj.created.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_modified(self, obj):
        return obj.last_updated.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_title(self, obj):
        """Return metadata title if exists, otherwise return 'none'."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.title is not None and \
                obj.metadata.title.value is not None:
            return obj.metadata.title.value.lstrip()
        else:
            return 'none'

    def prepare_abstract(self, obj):
        """Return metadata abstract if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.description is not None and \
                obj.metadata.description.abstract is not None:
            return obj.metadata.description.abstract.lstrip()
        else:
            return None

    def prepare_author_raw(self, obj):
        """
        Return metadata author if exists, otherwise return None.

        This must be represented as a single-value field to enable sorting.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator is None:
                return 'none'
            elif first_creator.name:
                return first_creator.name.lstrip()
            elif first_creator.organization:
                return first_creator.organization.strip()
            else:
                return 'none'
        else:
            return 'none'

    # TODO: it is confusing that the "author" is the first "creator"
    def prepare_author(self, obj):
        """
        Return first creator if exists, otherwise return empty list.

        This must be represented as a single-value field to enable sorting.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator is None:
                return 'none'
            elif first_creator.name:
                normalized = normalize_name(first_creator.name)
                return normalized
            elif first_creator.organization:
                return first_creator.organization.strip()
            else:
                return 'none'
        else:
            return 'none'

    def prepare_author_url(self, obj):
        """
        Return metadata author description url if exists, otherwise return None.

        This field is stored but not indexed, to avoid hitting the Django database during response.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator is not None and first_creator.description is not None:
                return first_creator.description
            else:
                return None
        else:
            return None

    def prepare_creator(self, obj):
        """
        Return metadata creators if they exist, otherwise return empty array.

        This field can have multiple values
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            return [normalize_name(creator.name)
                    for creator in obj.metadata.creators.all()
                    .exclude(name__isnull=True).exclude(name='')]
        else:
            return []

    def prepare_contributor(self, obj):
        """
        Return metadata contributors if they exist, otherwise return empty array.

        This field can have multiple values. Contributors include creators.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.contributors is not None:
            output1 = [normalize_name(contributor.name)
                       for contributor in obj.metadata.contributors.all()
                       .exclude(name__isnull=True).exclude(name='')]
            return list(set(output1))  # eliminate duplicates
        else:
            return []

    def prepare_subject(self, obj):
        """
        Return metadata subjects if they exist, otherwise return empty array.

        This field can have multiple values.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.subjects is not None:
            return [subject.value.strip() for subject in obj.metadata.subjects.all()
                    .exclude(value__isnull=True)]
        else:
            return []

    def prepare_organization(self, obj):
        """
        Return metadata organization if it exists, otherwise return empty array.
        """
        organizations = []
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            for creator in obj.metadata.creators.all():
                if(creator.organization is not None):
                    organizations.append(creator.organization.strip())
        return organizations

    def prepare_publisher(self, obj):
        """
        Return metadata publisher if it exists; otherwise return empty array.
        """
        if hasattr(obj, 'metadata') and obj.metadata is not None:
            publisher = obj.metadata.publisher
            if publisher is not None:
                return str(publisher).lstrip()
            else:
                return None
        else:
            return None

    def prepare_creator_email(self, obj):
        """Return metadata emails if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            return [creator.email.strip() for creator in obj.metadata.creators.all()
                    .exclude(email__isnull=True).exclude(email='')]
        else:
            return []

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

    def prepare_replaced(self, obj):
        """Return True if 'isReplacedBy' attribute exists, otherwise return False."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.relations is not None:
            return obj.metadata.relations.filter(type='isReplacedBy').exists()
        else:
            return False

    def prepare_coverage(self, obj):
        """Return resource coverage if exists, otherwise return empty array."""
        # TODO: reject empty coverages
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            return [coverage._value.strip() for coverage in obj.metadata.coverages.all()]
        else:
            return []

    def prepare_coverage_type(self, obj):
        """
        Return resource coverage types if exists, otherwise return empty array.

        This field can have multiple values.
        """
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            return [coverage.type.strip() for coverage in obj.metadata.coverages.all()]
        else:
            return []

    # TODO: THIS IS SIMPLY THE WRONG WAY TO DO THINGS.
    # Should use geopy Point and Haystack LocationField throughout,
    # instead of encoding limits literally.
    # See http://django-haystack.readthedocs.io/en/v2.6.0/spatial.html

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_east(self, obj):
        """Return resource coverage east bound if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'point':
                    return float(coverage.value["east"])
                # TODO: this returns the box center, not the extent
                # TODO: probably better to call this something different.
                elif coverage.type == 'box':
                    return (float(coverage.value["eastlimit"]) +
                            float(coverage.value["westlimit"])) / 2
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_north(self, obj):
        """Return resource coverage north bound if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'point':
                    return float(coverage.value["north"])
                # TODO: This returns the box center, not the extent
                elif coverage.type == 'box':
                    return (float(coverage.value["northlimit"]) +
                            float(coverage.value["southlimit"])) / 2
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_northlimit(self, obj):
        """Return resource coverage north limit if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["northlimit"]
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_eastlimit(self, obj):
        """Return resource coverage east limit if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["eastlimit"]
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_southlimit(self, obj):
        """Return resource coverage south limit if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["southlimit"]
        else:
            return None

    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_westlimit(self, obj):
        """Return resource coverage west limit if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["westlimit"]
        else:
            return None

    # TODO: time coverages do not specify timezone, and timezone support is active.
    # TODO: Why aren't time coverages specified as Django DateTime objects?
    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_start_date(self, obj):
        """Return resource coverage start date if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period':
                    clean_date = coverage.value["start"][:10]
                    start_date = ""
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        if len(parsed_date) == 3:
                            start_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    elif "-" in clean_date:
                        parsed_date = clean_date.split("-")
                        if len(parsed_date) == 3:
                            start_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    start_date = remove_whitespace(start_date)  # no embedded spaces
                    try:
                        start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
                    except ValueError:
                        logger = logging.getLogger(__name__)
                        logger.error("invalid start date {} in resource {}".format(obj.short_id,
                                                                                   start_date))
                        return None
                    return start_date_object
        else:
            return None

    # TODO: time coverages do not specify timezone, and timezone support is active.
    # TODO: Why aren't time coverages specified as Django DateTime objects?
    # TODO: If there are multiple coverage objects with the same type, only first is returned.
    def prepare_end_date(self, obj):
        """Return resource coverage end date if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.coverages is not None:
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period' and 'end' in coverage.value:
                    clean_date = coverage.value["end"][:10]
                    end_date = ""
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        if len(parsed_date) == 3:
                            end_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    else:
                        parsed_date = clean_date.split("-")
                        if len(parsed_date) == 3:
                            end_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    end_date = remove_whitespace(end_date)  # no embedded spaces
                    try:
                        end_date_object = datetime.strptime(end_date, '%Y-%m-%d')
                    except ValueError:
                        logger = logging.getLogger(__name__)
                        logger.error("invalid end date {} in resource {}".format(end_date,
                                                                                 obj.short_id))
                        return None
                    return end_date_object
        else:
            return None

    def prepare_storage_type(self, obj):
        return obj.storage_type

    # # TODO: SOLR extension needs to be installed for these to work
    # def prepare_coverage_point(self, obj):
    #     """ Return Point object associated with coverage, or None """
    #     if hasattr(obj, 'metadata') and \
    #             obj.metadata is not None and \
    #             obj.metadata.coverages is not None:
    #         for coverage in obj.metadata.coverages.all():
    #             if coverage.type == 'point':
    #                 return Point(float(coverage.value["east"]),
    #                              float(coverage.value["north"]))
    #     return None

    # def prepare_coverage_southwest(self, obj):
    #     """ Return southwest limit of bounding box, or None """
    #     if hasattr(obj, 'metadata') and \
    #             obj.metadata is not None and \
    #             obj.metadata.coverages is not None:
    #         for coverage in obj.metadata.coverages.all():
    #             if coverage.type == 'box':
    #                 return Point(float(coverage.value["westlimit"]),
    #                              float(coverage.value["southlimit"]))
    #     return None

    # def prepare_coverage_northeast(self, obj):
    #     """ Return northeast limit of bounding box, or None """
    #     if hasattr(obj, 'metadata') and \
    #             obj.metadata is not None and \
    #             obj.metadata.coverages is not None:
    #         for coverage in obj.metadata.coverages.all():
    #             if coverage.type == 'box':
    #                 return Point(float(coverage.value["eastlimit"]),
    #                              float(coverage.value["northlimit"]))
    #     return None

    def prepare_format(self, obj):
        """Return metadata formats if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.formats is not None:
            return [format.value.strip() for format in obj.metadata.formats.all()]
        else:
            return []

    def prepare_identifier(self, obj):
        """Return metadata identifiers if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.identifiers is not None:
            return [identifier.name.strip() for identifier in obj.metadata.identifiers.all()]
        else:
            return []

    def prepare_language(self, obj):
        """Return resource language if exists, otherwise return None."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.language is not None:
            return obj.metadata.language.code.strip()
        else:
            return None

    def prepare_source(self, obj):
        """Return resource sources if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.sources is not None:
            return [source.derived_from.strip() for source in obj.metadata.sources.all()]
        else:
            return []

    def prepare_relation(self, obj):
        """Return resource relations if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.relations is not None:
            return [relation.value.strip() for relation in obj.metadata.relations.all()]
        else:
            return []

    def prepare_resource_type(self, obj):
        """Resource type is verbose_name attribute of obj argument."""
        return obj.verbose_name

    def prepare_content_type(self, obj):
        """ register content types for both logical files and some MIME types """
        if obj.verbose_name == 'Composite Resource' or \
           obj.verbose_name == 'Generic Resource':
            output = get_content_types(obj)[0]
            return list(output)
        else:
            return [obj.discovery_content_type]

    def prepare_comment(self, obj):
        """Return list of all comments on resource."""
        return [comment.comment.strip() for comment in obj.comments.all()]

    def prepare_comments_count(self, obj):
        """Return count of resource comments."""
        return obj.comments_count

    def prepare_owner_login(self, obj):
        """Return list of usernames that have ownership access to resource."""
        if hasattr(obj, 'raccess'):
            return [owner.username for owner in obj.raccess.owners.all()]
        else:
            return []

    # TODO: should utilize name from user profile rather than from User field
    def prepare_owner(self, obj):
        """Return list of names of resource owners."""
        names = []
        if hasattr(obj, 'raccess'):
            for owner in obj.raccess.owners.all():
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
            for owner in obj.raccess.owners.all():
                name = normalize_name(owner.first_name + ' ' + owner.last_name)
                output0.append(name)

        if hasattr(obj, 'metadata') and \
                obj.metadata is not None and \
                obj.metadata.creators is not None:
            output1 = [normalize_name(creator.name)
                       for creator in obj.metadata.creators.all()
                       .exclude(name__isnull=True).exclude(name='')]
            output2 = [normalize_name(contributor.name)
                       for contributor in obj.metadata.contributors.all()
                       .exclude(name__isnull=True).exclude(name='')]
        return list(set(output0 + output1 + output2))  # eliminate duplicates

    def prepare_owners_count(self, obj):
        """Return count of resource owners if 'raccess' attribute exists, othrerwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.owners.all().count()
        else:
            return 0

    # # TODO: We might need these later for social discovery
    # def prepare_viewer_login(self, obj):
    #     """Return usernames of users that can view resource, otherwise return empty array."""
    #     if hasattr(obj, 'raccess'):
    #         return [viewer.username for viewer in obj.raccess.view_users.all()]
    #     else:
    #         return []

    # def prepare_viewer(self, obj):
    #     """Return full names of users that can view resource, otherwise return empty array."""
    #     names = []
    #     if hasattr(obj, 'raccess'):
    #         for viewer in obj.raccess.view_users.all():
    #             name = viewer.last_name + ', ' + viewer.first_name
    #             names.append(name)
    #     return names

    # def prepare_viewers_count(self, obj):
    #     """Return count of users who can view resource, otherwise return 0."""
    #     if hasattr(obj, 'raccess'):
    #         return obj.raccess.view_users.all().count()
    #     else:
    #         return 0

    # def prepare_editor_login(self, obj):
    #     """Return usernames of editors of a resource, otherwise return 0."""
    #     if hasattr(obj, 'raccess'):
    #         return [editor.username for editor in obj.raccess.edit_users.all()]
    #     else:
    #         return 0

    # def prepare_editor(self, obj):
    #     """Return full names of editors of a resource, otherwise return empty array."""
    #     names = []
    #     if hasattr(obj, 'raccess'):
    #         for editor in obj.raccess.edit_users.all():
    #             name = editor.last_name + ', ' + editor.first_name
    #             names.append(name)
    #     return names

    # def prepare_editors_count(self, obj):
    #     """Return count of editors of a resource, otherwise return 0."""
    #     if hasattr(obj, 'raccess'):
    #         return obj.raccess.edit_users.all().count()
    #     else:
    #         return 0

    # TODO: These should probably be multi-value fields and pick up all types.
    def prepare_geometry_type(self, obj):
        """
        Return geometry type if metadata exists, otherwise return [].
        """
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                geometry_info = obj.metadata.geometryinformation
                if geometry_info is not None:
                    return geometry_info.geometryType
                else:
                    return None
            else:
                return None
        else:
            return None

    def prepare_field_name(self, obj):
        """
        Return metadata field name if exists, otherwise return [].
        """
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldName is not None:
                    return field_info.fieldName.strip()
                else:
                    return None
            else:
                return None
        else:
            return None

    def prepare_field_type(self, obj):
        """
        Return metadata field type if exists, otherwise return None.
        """
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldType is not None:
                    return field_info.fieldType.strip()
                else:
                    return None
            else:
                return None
        else:
            return None

    def prepare_field_type_code(self, obj):
        """
        Return metadata field type code if exists, otherwise return [].
        """
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None and field_info.fieldTypeCode is not None:
                    return field_info.fieldTypeCode.strip()
                else:
                    return None
            else:
                return None
        else:
            return None

    def prepare_variable(self, obj):
        """
        Return metadata variable names if exists, otherwise return empty array.
        """
        variable_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_names.append(variable.name.strip())
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    variable_names.append(variable.name.strip())
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    variable_names.append(variable.variable_name.strip())
        return variable_names

    def prepare_variable_type(self, obj):
        """
        Return metadata variable types if exists, otherwise return empty array.
        """
        variable_types = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_types.append(variable.type.strip())
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    variable_types.append(variable.data_type.strip())
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    variable_types.append(variable.variable_type.strip())
        return variable_types

    def prepare_variable_shape(self, obj):
        """
        Return metadata variable shapes if exists, otherwise return empty array.
        """
        variable_shapes = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    if variable.shape is not None:
                        variable_shapes.append(variable.shape.strip())
        return variable_shapes

    def prepare_variable_descriptive_name(self, obj):
        """
        Return metadata variable descriptive names if exists, otherwise return empty array.
        """
        variable_descriptive_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    if variable.descriptive_name is not None:
                        variable_descriptive_names.append(variable.descriptive_name.strip())
        return variable_descriptive_names

    def prepare_variable_speciation(self, obj):
        """
        Return metadata variable speciations if exists, otherwise return empty array.
        """
        variable_speciations = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    if variable.speciation is not None:
                        variable_speciations.append(variable.speciation.strip())
        return variable_speciations

    def prepare_site(self, obj):
        """
        Return list of sites if exists, otherwise return empty array.
        """
        sites = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for site in obj.metadata.sites.all():
                    if site.name is not None and site.name != '':
                        sites.append(site.name.strip())
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for site in obj.metadata.sites:
                    if site.site_name is not None and site.site_name != '':
                        sites.append(site.site_name.strip())
        return sites

    def prepare_method(self, obj):
        """
        Return list of methods if exists, otherwise return empty array.
        """
        methods = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for method in obj.metadata.methods.all():
                    if method.description is not None:
                        methods.append(method.description.strip())
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for method in obj.metadata.methods:
                    if method.method_description is not None:
                        methods.append(method.method_description.strip())
        return methods

    def prepare_quality_level(self, obj):
        """
        Return list of quality levels if exists, otherwise return empty array.
        """
        quality_levels = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for quality_level in obj.metadata.quality_levels.all():
                    if quality_level.code is not None:
                        quality_levels.append(quality_level.code.strip())
        return quality_levels

    def prepare_data_source(self, obj):
        """
        Return list of data sources if exists, otherwise return empty array.
        """
        data_sources = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for data_source in obj.metadata.datasources.all():
                    if data_source.code is not None:
                        data_sources.append(data_source.code.strip())
        return data_sources

    def prepare_sample_medium(self, obj):
        """
        Return list of sample mediums if exists, otherwise return empty array.
        """
        sample_mediums = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    if time_series_result.sample_medium is not None:
                        sample_mediums.append(time_series_result.sample_medium)
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    if variable.sample_medium is not None:
                        sample_mediums.append(variable.sample_medium)
        return list(set(sample_mediums))

    def prepare_units(self, obj):
        """
        Return list of units names if exists, otherwise return empty array.
        """
        units_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    if time_series_result.units_name is not None:
                        units_names.append(time_series_result.units_name)
        return units_names

    def prepare_units_type(self, obj):
        """
        Return list of units types if exists, otherwise return empty array.
        """
        units_types = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    if time_series_result.units_type is not None:
                        units_types.append(time_series_result.units_type.strip())
        return units_types

    def prepare_aggregation_statistics(self, obj):
        """
        Return list of aggregation statistics if exists, otherwise return empty array.
        """
        aggregation_statistics = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    if time_series_result.aggregation_statistics is not None:
                        aggregation_statistics.append(time_series_result.aggregation_statistics)
        return aggregation_statistics

    def prepare_absolute_url(self, obj):
        """Return absolute URL of object."""
        return obj.get_absolute_url()

    def prepare_extra(self, obj):
        """ For extra metadata, include both key and value """
        extra = []
        for key, value in list(obj.extra_metadata.items()):
            extra.append(key + ': ' + value)
        return extra
