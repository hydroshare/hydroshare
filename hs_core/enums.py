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
    relation = 'relation'
    isSimilarTo = 'isSimilarTo'
