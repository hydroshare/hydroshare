from haystack import indexes
from hs_core.models import GenericResource


class GenericResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='first_creator', faceted=True)
    title = indexes.CharField(model_attr='title')
    abstract = indexes.CharField(model_attr='description')
    creators = indexes.MultiValueField()
    subjects = indexes.MultiValueField(faceted=True)
    publisher = indexes.CharField(model_attr='publisher');
    def get_model(self):
        return GenericResource

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_creators(self, obj):
        return obj.metadata.creators.values_list('name', flat=True)

    def prepare_subjects(self, obj):
        return obj.metadata.subjects.values_list('value', flat=True)
