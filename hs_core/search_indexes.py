import datetime
from haystack import indexes
from hs_core.models import BaseResource


class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    resource_type = indexes.CharField()
    title = indexes.CharField(model_attr='user')
    created = indexes.DateTimeField(model_attr='created')
    creator_name = indexes.CharField()
    creator_email = indexes.CharField()
    authors = indexes.CharField()
    public = indexes.BooleanField()
    discoverable = indexes.BooleanField()
    short_id = indexes.CharField(model_attr='short_id')

    #Social
    rating = indexes.CharField()

    # Meta Data
    description = indexes.CharField()
    title = indexes.CharField()
    creators = indexes.CharField()
    contributors = indexes.CharField()
    dates = indexes.CharField()
    coverages = indexes.CharField()
    formats = indexes.CharField()
    identifiers = indexes.CharField()
    language = indexes.CharField()
    subjects = indexes.CharField()
    sources = indexes.CharField()
    relations = indexes.CharField()
    rights = indexes.CharField()
    type = indexes.CharField()
    publisher = indexes.CharField()

    def get_model(self):
        return BaseResource

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""

        return self.get_model().objects.filter(
            #raccess__public=True,
        )
