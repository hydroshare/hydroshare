import enum


class RelationTypes(str, enum.Enum):
    """Relation types for the Relation metadata db model class"""

    isPartOf = 'isPartOf'
    hasPart = 'hasPart'
    isExecutedBy = 'isExecutedBy'
    isCreatedBy = 'isCreatedBy'
    isVersionOf = 'isVersionOf'
    isReplacedBy = 'isReplacedBy'
    isDescribedBy = 'isDescribedBy'
    conformsTo = 'conformsTo'
    hasFormat = 'hasFormat'
    isFormatOf = 'isFormatOf'
    isRequiredBy = 'isRequiredBy'
    requires = 'requires'
    isReferencedBy = 'isReferencedBy'
    references = 'references'
    replaces = 'replaces'
    source = 'source'
    isSimilarTo = 'isSimilarTo'

    # A "generic" related resource, http://purl.org/dc/terms/relation
    relation = 'relation'


class DataciteSubmissionStatus(str, enum.Enum):
    """Datacite metadata deposit submission status"""

    # 'failure' flag indicates the metadata deposition with Datacite failed when the resource was first published
    FAILURE = 'failure'
    # 'update_failure' flag indicates the metadata update with Datacite failed
    UPDATE_FAILURE = 'update_failure'
    # 'pending' flag indicates the metadata deposition with Datacite succeeds, but
    # pending activation with Datacite for DOI to take effect. this is the initial deposit when the resource
    # is first published
    PENDING = 'pending'
    # 'update_pending' flag indicates the metadata update with Datacite succeeds, but pending to be available
    UPDATE_PENDING = 'update_pending'
