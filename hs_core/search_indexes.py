from haystack import indexes
from hs_core.models import BaseResource


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(model_attr='first_creator', faceted=True)
    title = indexes.CharField(model_attr='title', faceted=True)
    abstract = indexes.CharField(model_attr='description')
    creators = indexes.MultiValueField(faceted=True)
    contributors = indexes.MultiValueField()
    subjects = indexes.MultiValueField(faceted=True)
    public = indexes.BooleanField(model_attr='raccess__public', faceted=True)
    discoverable = indexes.BooleanField(faceted=True)
    created = indexes.DateTimeField(model_attr='created')
    modified = indexes.DateTimeField(model_attr='updated')
    organization = indexes.CharField(faceted=True, null=True)
    author_email = indexes.CharField()
    publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    coverages = indexes.MultiValueField()
    formats = indexes.MultiValueField()
    identifiers = indexes.MultiValueField()
    language = indexes.CharField(faceted=True)
    sources = indexes.MultiValueField()
    relations = indexes.MultiValueField()
    #type = indexes.CharField()

    def get_model(self):
        return BaseResource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_creators(self, obj):
         return [creator.name for creator in obj.metadata.creators.all()]

    def prepare_contributors(self, obj):
        return [contributor.name for contributor in obj.metadata.contributors.all()]

    def prepare_subjects(self, obj):
        return [subject.value for subject in obj.metadata.subjects.all()]

    def prepare_organization(self, obj):
        organization = obj.first_creator.organization
        if(organization is not None):
            return organization
        else:
            return 'none'

    def prepare_publisher(self, obj):
        publisher = obj.metadata.publisher
        if(publisher is not None):
            return publisher
        else:
            return 'none'
        #return foo

    def prepare_author_email(self, obj):
        return obj.first_creator.email

    def prepare_discoverable(self, obj):
        if(obj.raccess.public | obj.raccess.discoverable):
            return True
        else:
            return False

    def prepare_coverages(self, obj):
        return [coverage._value for coverage in obj.metadata.coverages.all()]

    def prepare_formates(self, obj):
        return [format.value for format in obj.metadata.formats.all()]

    def prepare_identifiers(self, obj):
        return [identifier.name for identifier in obj.metadata.identifiers.all()]

    def prepare_language(self, obj):
        return obj.metadata.language.code

    def prepare_sources(self, obj):
        return [source.derived_from for source in obj.metadata.sources.all()]

    def prepare_relations(self, obj):
        return [relation.value for relation in obj.metadata.relations.all()]