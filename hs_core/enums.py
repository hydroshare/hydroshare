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


class CrossRefSubmissionStatus(str, enum.Enum):
    """CrossRef metadata deposit submission status"""

    FAILURE = 'failure'
    PENDING = 'pending'
    UPDATE = 'CROSSREF_UPDATE'
