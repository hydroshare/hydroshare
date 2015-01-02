from haystack import indexes
from hs_core.models import GenericResource
from dublincore.models import AbstractQualifiedDublinCoreTerm


class GenericResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    keywords = indexes.MultiValueField()

    for code, name in AbstractQualifiedDublinCoreTerm.DCTERMS:
        locals()[name] = indexes.CharField(null=True)

    def prepare_keywords(self, obj):
        return [k.keyword.title for k in obj.keywords.all()]

    def prepare_text(self, obj):
        return obj.description

    def prepare(self, obj):
        dublindata = obj.get_dublin_metadata()
        data = super(GenericResourceIndex, self).prepare(obj)
        data.update(dublindata)
        return data

    def get_model(self):
        return GenericResource

    def index_queryset(self, using=None):
        # TODO filter non-public resources based on permissions of the current user
        # Do not index non-public resources until those criteria are in place
        return self.get_model().objects.filter(public=True)
