from haystack import indexes
from hs_core.models import GenericResource


class GenericResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    keywords = indexes.MultiValueField()

    def prepare_keywords(self, obj):
        return obj.get_dublin_metadata().get('keywords', '').split(',')

    def prepare_text(self, obj):
        return obj.description

    def get_model(self):
        return GenericResource

    def index_queryset(self, using=None):
        # TODO filter non-public resources based on permissions of the current user
        # Do not index non-public resources until those criteria are in place
        return self.get_model().objects.filter(public=True)
