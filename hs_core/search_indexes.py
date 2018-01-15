"""Define search indexes for hs_core module."""

from haystack import indexes
from hs_core.models import BaseResource
from hs_geographic_feature_resource.models import GeographicFeatureMetaData
from hs_app_netCDF.models import NetcdfMetaData
from ref_ts.models import RefTSMetadata
from hs_app_timeseries.models import TimeSeriesMetaData
from django.db.models import Q
from datetime import datetime
from nameparser import HumanName


def normalize_human_name(name):
    nameparts = HumanName(name.lstrip())
    normalized = nameparts.last
    if nameparts.suffix:
        normalized = normalized + ' ' + nameparts.suffix
    normalized = normalized + ','
    if nameparts.title:
        normalized = normalized + ' ' + nameparts.title
    if nameparts.first:
        normalized = normalized + ' ' + nameparts.first
    if nameparts.middle:
        normalized = ' ' + normalized + ' ' + nameparts.middle
    return normalized


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    """Define base class for resource indexes."""

    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(faceted=True)  # normalized to last, first, middle
    author_raw = indexes.CharField(indexed=False)  # not normalized
    author_url = indexes.CharField(indexed=False)
    title = indexes.CharField(faceted=True)
    abstract = indexes.CharField()
    creator = indexes.MultiValueField(faceted=True)
    contributor = indexes.MultiValueField()
    subject = indexes.MultiValueField(faceted=True)
    # These are REPLACED by availability 
    # public = indexes.BooleanField(faceted=True)
    # discoverable = indexes.BooleanField(faceted=True)
    # published = indexes.BooleanField(faceted=True)
    availability = indexes.CharField()
    # TODO: We might need more information than a bool in the future
    replaced = indexes.BooleanField()
    created = indexes.DateTimeField(model_attr='created', faceted=True)
    modified = indexes.DateTimeField(model_attr='updated', faceted=True)
    organization = indexes.MultiValueField(faceted=True)
    creator_email = indexes.MultiValueField()
    publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    coverage = indexes.MultiValueField()
    coverage_type = indexes.MultiValueField()
    coverage_east = indexes.FloatField()
    coverage_north = indexes.FloatField()
    coverage_northlimit = indexes.FloatField()
    coverage_eastlimit = indexes.FloatField()
    coverage_southlimit = indexes.FloatField()
    coverage_westlimit = indexes.FloatField()
    coverage_start_date = indexes.DateField()
    coverage_end_date = indexes.DateField()
    format = indexes.MultiValueField()
    identifier = indexes.MultiValueField()
    language = indexes.CharField(faceted=True)
    source = indexes.MultiValueField()
    relation = indexes.MultiValueField()
    resource_type = indexes.CharField(faceted=True)
    comment = indexes.MultiValueField()
    comments_count = indexes.IntegerField(faceted=True)
    owner_login = indexes.MultiValueField(faceted=True)
    owner = indexes.MultiValueField(faceted=True)
    owners_count = indexes.IntegerField(faceted=True)
    viewer_login = indexes.MultiValueField(faceted=True)
    viewer = indexes.MultiValueField(faceted=True)
    viewers_count = indexes.IntegerField(faceted=True)
    editor_login = indexes.MultiValueField(faceted=True)
    editor = indexes.MultiValueField(faceted=True)
    editors_count = indexes.IntegerField(faceted=True)

    # non-core metadata
    geometry_type = indexes.CharField(faceted=True)
    field_name = indexes.CharField()
    field_type = indexes.CharField()
    field_type_code = indexes.CharField()
    variable = indexes.MultiValueField(faceted=True)
    variable_type = indexes.MultiValueField()
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
    aggregation_statistics = indexes.MultiValueField(faceted=False)
    absolute_url = indexes.CharField(indexed=False)

    def get_model(self):
        """Return BaseResource model."""
        return BaseResource

    def index_queryset(self, using=None):
        """Return queryset including discoverable and public resources."""
        return self.get_model().objects.filter(Q(raccess__discoverable=True) |
                                               Q(raccess__public=True))

    def prepare_title(self, obj):
        """Return metadata title if exists, otherwise return none."""
        if hasattr(obj, 'metadata') and obj.metadata.title.value is not None:
            return obj.metadata.title.value.lstrip()
        else:
            return 'none'

    def prepare_abstract(self, obj):
        """Return metadata abstract if exists, otherwise return none."""
        if hasattr(obj, 'metadata') and obj.metadata.description is not None and \
                obj.metadata.description.abstract is not None:
            return obj.metadata.description.abstract
        else:
            return 'none'

    def prepare_author_raw(self, obj):
        """Return metadata author if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.name is not None:
                return first_creator.name.lstrip()
            else:
                return 'none'
        else:
            return 'none'

    # TODO: it is confusing that the author is the first creator
    # This is an artificial distinction
    def prepare_author(self, obj):
        """Return metadata author if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.name is not None and first_creator.name != '':
                normalized = normalize_human_name(first_creator.name)
                return normalized
            else:
                return 'none'
        else:
            return 'none'

    # stored, unindexed field
    def prepare_author_url(self, obj):
        """Return metadata author description url if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            first_creator = obj.metadata.creators.filter(order=1).first()
            if first_creator.description is not None:
                return first_creator.description
            else:
                return 'none'
        else:
            return 'none'

    def prepare_creator(self, obj):
        """Return metadata creators if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [normalize_human_name(creator.name) for creator in obj.metadata.creators.all()
                    .exclude(name__isnull=True).exclude(name='')]
        else:
            return []

    def prepare_contributor(self, obj):
        """Return metadata contributors if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [normalize_human_name(contributor.name)
                    for contributor in obj.metadata.contributors.all()
                    .exclude(name__isnull=True).exclude(name='')]
        else:
            return []

    def prepare_subject(self, obj):
        """Return metadata subjects if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [subject.value for subject in obj.metadata.subjects.all()
                    .exclude(value__isnull=True)]
        else:
            return []

    def prepare_organization(self, obj):
        """Return metadata organizations if exists, otherwise return empty array."""
        organizations = []
        none = False  # only enter one value "none"
        if hasattr(obj, 'metadata'):
            for creator in obj.metadata.creators.all():
                if(creator.organization is not None):
                    organizations.append(creator.organization)
                else:
                    if not none:
                        none = True
                        organizations.append('none')
        return organizations

    def prepare_publisher(self, obj):
        """Return metadata publisher if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            publisher = obj.metadata.publisher
            if publisher is not None:
                return publisher
            else:
                return 'none'
        else:
            return 'none'

    def prepare_creator_email(self, obj):
        """Return metadata emails if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [creator.email for creator in obj.metadata.creators.all()
                    .exclude(email__isnull=True).exclude(email='')]
        else:
            return []

    # These are REPLACED by the availability field
    # def prepare_discoverable(self, obj):
    #     """Return resource discoverability if exists, otherwise return False."""
    #     if hasattr(obj, 'raccess'):
    #         if obj.raccess.public or obj.raccess.discoverable:
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False

    # def prepare_public(self, obj):
    #     """Return resource access if exists, otherwise return False."""
    #     if hasattr(obj, 'raccess'):
    #         if obj.raccess.public:
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False

    # def prepare_published(self, obj):
    #     """Return resource published status if exists, otherwise return False."""
    #     if hasattr(obj, 'raccess'):
    #         if obj.raccess.published:
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False

    def prepare_availability(self, obj):
        """ availability is published, public, or discoverable"""
        if hasattr(obj, 'raccess'):
            if obj.raccess.published:
                return 'published'
            elif obj.raccess.public:
                return 'MY public'
            elif obj.raccess.discoverable:
                return 'discoverable'
            else:
                return 'private'
        else:
            return 'private'

    def prepare_replaced(self, obj):
        """Return 'isReplacedBy' attribute if exists, otherwise return False."""
        if hasattr(obj, 'metadata'):
            return obj.metadata.relations.all().filter(type='isReplacedBy').exists()
        else:
            return False

    def prepare_coverage(self, obj):
        """Return resource coverage if exists, otherwise return empty array."""
        # TODO: reject empty coverages
        if hasattr(obj, 'metadata'):
            return [coverage._value for coverage in obj.metadata.coverages.all()]
        else:
            return []

    def prepare_coverage_type(self, obj):
        """Return resource coverage types if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [coverage.type for coverage in obj.metadata.coverages.all()]
        else:
            return []

    def prepare_coverage_east(self, obj):
        """Return resource coverage east bound if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'point':
                    return float(coverage.value["east"])
                # TODO: this returns the box center, not the extent
                elif coverage.type == 'box':
                    return (float(coverage.value["eastlimit"]) +
                            float(coverage.value["westlimit"])) / 2
        else:
            return 'none'

    def prepare_coverage_north(self, obj):
        """Return resource coverage north bound if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'point':
                    return float(coverage.value["north"])
                # TODO: This returns the box center, not the extent
                elif coverage.type == 'box':
                    return (float(coverage.value["northlimit"]) +
                            float(coverage.value["southlimit"])) / 2
        else:
            return 'none'

    def prepare_coverage_northlimit(self, obj):
        """Return resource coverage north limit if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["northlimit"]
        else:
            return 'none'

    def prepare_coverage_eastlimit(self, obj):
        """Return resource coverage east limit if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["eastlimit"]
        else:
            return 'none'

    def prepare_coverage_southlimit(self, obj):
        """Return resource coverage south limit if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["southlimit"]
        else:
            return 'none'

    def prepare_coverage_westlimit(self, obj):
        """Return resource coverage west limit if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            # TODO: does not index properly if there are multiple coverages of the same type.
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'box':
                    return coverage.value["westlimit"]
        else:
            return 'none'

    # TODO: time coverages do not specify timezone, and timezone support is active.

    def prepare_coverage_start_date(self, obj):
        """Return resource coverage start date if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period':
                    clean_date = coverage.value["start"][:10]
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        start_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    else:
                        parsed_date = clean_date.split("-")
                        start_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    start_date_object = datetime.strptime(start_date, '%Y-%m-%d')
                    return start_date_object
        else:
            return 'none'

    def prepare_coverage_end_date(self, obj):
        """Return resource coverage end date if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            for coverage in obj.metadata.coverages.all():
                if coverage.type == 'period' and 'end' in coverage.value:
                    clean_date = coverage.value["end"][:10]
                    if "/" in clean_date:
                        parsed_date = clean_date.split("/")
                        end_date = parsed_date[2] + '-' + parsed_date[0] + '-' + parsed_date[1]
                    else:
                        parsed_date = clean_date.split("-")
                        end_date = parsed_date[0] + '-' + parsed_date[1] + '-' + parsed_date[2]
                    end_date_object = datetime.strptime(end_date, '%Y-%m-%d')
                    return end_date_object
        else:
            return 'none'

    def prepare_format(self, obj):
        """Return metadata formats if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [format.value for format in obj.metadata.formats.all()]
        else:
            return []

    def prepare_identifier(self, obj):
        """Return metadata identifiers if metadata exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [identifier.name for identifier in obj.metadata.identifiers.all()]
        else:
            return []

    def prepare_language(self, obj):
        """Return resource language if exists, otherwise return none."""
        if hasattr(obj, 'metadata'):
            return obj.metadata.language.code
        else:
            return 'none'

    def prepare_source(self, obj):
        """Return resource sources if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [source.derived_from for source in obj.metadata.sources.all()]
        else:
            return []

    def prepare_relation(self, obj):
        """Return resource relations if exists, otherwise return empty array."""
        if hasattr(obj, 'metadata'):
            return [relation.value for relation in obj.metadata.relations.all()]
        else:
            return []

    def prepare_resource_type(self, obj):
        """Return verbose_name attribute of obj argument."""
        return obj.verbose_name

    def prepare_comment(self, obj):
        """Return list of all comments on resource."""
        return [comment.comment for comment in obj.comments.all()]

    def prepare_comments_count(self, obj):
        """Return count of resource comments."""
        return obj.comments_count

    def prepare_owner_login(self, obj):
        """Return list of usernames that have ownership access to resource."""
        if hasattr(obj, 'raccess'):
            return [owner.username for owner in obj.raccess.owners.all()]
        else:
            return []

    def prepare_owner(self, obj):
        """Return list of names of resource owners."""
        names = []
        if hasattr(obj, 'raccess'):
            for owner in obj.raccess.owners.all():
                name = owner.last_name + ', ' + owner.first_name
                names.append(name)
        return names

    def prepare_owners_count(self, obj):
        """Return count of resource owners if 'raccess' attribute exists, othrerwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.owners.all().count()
        else:
            return 0

    def prepare_viewer_login(self, obj):
        """Return usernames of users that can view resource, otherwise return empty array."""
        if hasattr(obj, 'raccess'):
            return [viewer.username for viewer in obj.raccess.view_users.all()]
        else:
            return []

    def prepare_viewer(self, obj):
        """Return full names of users that can view resource, otherwise return empty array."""
        names = []
        if hasattr(obj, 'raccess'):
            for viewer in obj.raccess.view_users.all():
                name = viewer.last_name + ', ' + viewer.first_name
                names.append(name)
        return names

    def prepare_viewers_count(self, obj):
        """Return count of users who can view resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.view_users.all().count()
        else:
            return 0

    def prepare_editor_login(self, obj):
        """Return usernames of editors of a resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return [editor.username for editor in obj.raccess.edit_users.all()]
        else:
            return 0

    def prepare_editor(self, obj):
        """Return full names of editors of a resource, otherwise return empty array."""
        names = []
        if hasattr(obj, 'raccess'):
            for editor in obj.raccess.edit_users.all():
                name = editor.last_name + ', ' + editor.first_name
                names.append(name)
        return names

    def prepare_editors_count(self, obj):
        """Return count of editors of a resource, otherwise return 0."""
        if hasattr(obj, 'raccess'):
            return obj.raccess.edit_users.all().count()
        else:
            return 0

    def prepare_geometry_type(self, obj):
        """Return geometry type if metadata exists, otherwise return 'none'."""
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                geometry_info = obj.metadata.geometryinformation
                if geometry_info is not None:
                    return geometry_info.geometryType
                else:
                    return 'none'
            else:
                return 'none'
        else:
            return 'none'

    def prepare_field_name(self, obj):
        """Return metadata field name if exists, otherwise return 'none'."""
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None:
                    return field_info.fieldName
                else:
                    return 'none'
            else:
                return 'none'
        else:
            return 'none'

    def prepare_field_type(self, obj):
        """Return metadata field type if exists, otherwise return 'none'."""
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None:
                    return field_info.fieldType
                else:
                    return 'none'
            else:
                return 'none'
        else:
            return 'none'

    def prepare_field_type_code(self, obj):
        """Return metadata field type code if exists, otherwise return 'none'."""
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, GeographicFeatureMetaData):
                field_info = obj.metadata.fieldinformations.all().first()
                if field_info is not None:
                    return field_info.fieldTypeCode
                else:
                    return 'none'
            else:
                return 'none'
        else:
            return 'none'

    def prepare_variable(self, obj):
        """Return metadata variable names if exists, otherwise return empty array."""
        variable_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_names.append(variable.name)
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    variable_names.append(variable.name)
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    variable_names.append(variable.variable_name)
        return variable_names

    def prepare_variable_type(self, obj):
        """Return metadata variable types if exists, otherwise return empty array."""
        variable_types = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_types.append(variable.type)
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    variable_types.append(variable.data_type)
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    variable_types.append(variable.variable_type)
        return variable_types

    def prepare_variable_shape(self, obj):
        """Return metadata variable shapes if exists, otherwise return empty array."""
        variable_shapes = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_shapes.append(variable.shape)
        return variable_shapes

    def prepare_variable_descriptive_name(self, obj):
        """Return metadata variable descriptive names if exists, otherwise return empty array."""
        variable_descriptive_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, NetcdfMetaData):
                for variable in obj.metadata.variables.all():
                    variable_descriptive_names.append(variable.descriptive_name)
        return variable_descriptive_names

    def prepare_variable_speciation(self, obj):
        """Return metadata variable speciations if exists, otherwise return empty array."""
        variable_speciations = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for variable in obj.metadata.variables:
                    variable_speciations.append(variable.speciation)
        return variable_speciations

    def prepare_site(self, obj):
        """Return metadata sites if exists, otherwise return empty array."""
        sites = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for site in obj.metadata.sites.all():
                    sites.append(site.name)
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for site in obj.metadata.sites:
                    sites.append(site.site_name)
        return sites

    def prepare_method(self, obj):
        """Return metadata methods if exists, otherwise return empty array."""
        methods = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for method in obj.metadata.methods.all():
                    methods.append(method.description)
            elif isinstance(obj.metadata, TimeSeriesMetaData):
                for method in obj.metadata.methods:
                    methods.append(method.method_description)
        return methods

    def prepare_quality_level(self, obj):
        """Return metadata quality levels if exists, otherwise return empty array."""
        quality_levels = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for quality_level in obj.metadata.quality_levels.all():
                    quality_levels.append(quality_level.code)
        return quality_levels

    def prepare_data_source(self, obj):
        """Return metadata datasources if exists, otherwise return empty array."""
        data_sources = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, RefTSMetadata):
                for data_source in obj.metadata.datasources.all():
                    data_sources.append(data_source.code)
        return data_sources

    def prepare_sample_medium(self, obj):
        """Return metadata sample mediums if exists, otherwise return empty array."""
        sample_mediums = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    sample_mediums.append(time_series_result.sample_medium)
            elif isinstance(obj.metadata, RefTSMetadata):
                for variable in obj.metadata.variables.all():
                    sample_mediums.append(variable.sample_medium)
        return sample_mediums

    def prepare_units(self, obj):
        """Return metadata units names if exists, otherwise return empty array."""
        units_names = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    units_names.append(time_series_result.units_name)
        return units_names

    def prepare_units_type(self, obj):
        """Return metadata units types if exists, otherwise return empty array."""
        units_types = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    units_types.append(time_series_result.units_type)
        return units_types

    def prepare_aggregation_statistics(self, obj):
        """Return metadata aggregation statistics if exists, otherwise return empty array."""
        aggregation_statistics = []
        if hasattr(obj, 'metadata'):
            if isinstance(obj.metadata, TimeSeriesMetaData):
                for time_series_result in obj.metadata.time_series_results:
                    aggregation_statistics.append(time_series_result.aggregation_statistics)
        return aggregation_statistics

    def prepare_absolute_url(self, obj):
        """Return absolute URL of object."""
        return obj.get_absolute_url()
