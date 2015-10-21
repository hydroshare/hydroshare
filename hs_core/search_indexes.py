from haystack import indexes
from hs_core.models import BaseResource


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(model_attr='first_creator', faceted=True)
    title = indexes.CharField(model_attr='title')
    abstract = indexes.CharField(model_attr='description')
    creators = indexes.MultiValueField()
    subjects = indexes.MultiValueField(faceted=True)
    public = indexes.BooleanField(model_attr='raccess__public', faceted=True)
    discoverable = indexes.BooleanField(faceted=True)
    created = indexes.DateTimeField(model_attr='created')
    modified = indexes.DateTimeField(model_attr='updated')
    organization = indexes.CharField(faceted=True, null=True)
    author_email = indexes.CharField()
    #publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    type = indexes.CharField()

    def get_model(self):
        return BaseResource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_creators(self, obj):
        return obj.metadata.creators.values_list('name', flat=True)

    def prepare_subjects(self, obj):
        return obj.metadata.subjects.values_list('value', flat=True)

    def prepare_organization(self, obj):
        return obj.first_creator.organization

    def prepare_author_email(self, obj):
        return obj.first_creator.email

    def prepare_discoverable(self, obj):
        if(obj.raccess.public | obj.raccess.discoverable):
            return True
        else:
            return False

    def prepare_type(self, obj):
        return obj.metadata.type