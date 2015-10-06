from haystack import indexes
from hs_core.models import GenericResource


class GenericResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    #author = indexes.CharField(model_attr='first_creator')
    #creators = indexes.CharField(model_attr='creators')
    title = indexes.CharField(model_attr='title')
    #description = indexes.CharField(model_attr='description')
    #creators = indexes.MultiValueField()
    def get_model(self):
        return GenericResource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


    #def prepare_creators(self, obj):
    #    return [creator.name for creator in obj.metadata.creators.all()]