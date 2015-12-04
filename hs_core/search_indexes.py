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
    created = indexes.DateTimeField(model_attr='created', faceted=True)
    modified = indexes.DateTimeField(model_attr='updated', faceted=True)
    organizations = indexes.MultiValueField(faceted=True)
    author_emails = indexes.MultiValueField()
    publisher = indexes.CharField(faceted=True)
    rating = indexes.IntegerField(model_attr='rating_sum')
    coverages = indexes.MultiValueField()
    formats = indexes.MultiValueField()
    identifiers = indexes.MultiValueField()
    language = indexes.CharField(faceted=True)
    sources = indexes.MultiValueField()
    relations = indexes.MultiValueField()
    resource_type = indexes.CharField(model_attr='resource_type', faceted=True)
    comments = indexes.MultiValueField()
    comments_count = indexes.IntegerField(faceted=True)
    owners_logins = indexes.MultiValueField(faceted=True)
    owners_names = indexes.MultiValueField(faceted=True)
    owners_count = indexes.IntegerField(faceted=True)
    viewers_logins = indexes.MultiValueField(faceted=True)
    viewers_names = indexes.MultiValueField(faceted=True)
    viewers_count = indexes.IntegerField(faceted=True)
    editors_logins = indexes.MultiValueField(faceted=True)
    editors_names = indexes.MultiValueField(faceted=True)
    editors_count = indexes.IntegerField(faceted=True)


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

    def prepare_organizations(self, obj):
        organizations = []
        for creator in obj.metadata.creators.all():
            if(creator.organization is not None):
                organizations.append(creator.organization)
            else:
                organizations.append('none')
        return organizations

    def prepare_publisher(self, obj):
        publisher = obj.metadata.publisher
        if(publisher is not None):
            return publisher
        else:
            return 'none'

    def prepare_author_emails(self, obj):
        return [creator.email for creator in obj.metadata.creators.all()]

    def prepare_discoverable(self, obj):
        if(obj.raccess.public | obj.raccess.discoverable):
            return True
        else:
            return False

    def prepare_coverages(self, obj):
        return [coverage._value for coverage in obj.metadata.coverages.all()]

    def prepare_formats(self, obj):
        return [format.value for format in obj.metadata.formats.all()]

    def prepare_identifiers(self, obj):
        return [identifier.name for identifier in obj.metadata.identifiers.all()]

    def prepare_language(self, obj):
        return obj.metadata.language.code

    def prepare_sources(self, obj):
        return [source.derived_from for source in obj.metadata.sources.all()]

    def prepare_relations(self, obj):
        return [relation.value for relation in obj.metadata.relations.all()]

    def prepare_comments(self, obj):
        return [comment.comment for comment in obj.comments.all()]

    def prepare_comments_count(self, obj):
        return obj.comments_count

    def prepare_owners_logins(self, obj):
        return [owner.username for owner in obj.raccess.owners.all()]

    def prepare_owners_names(self, obj):
        names = []
        for owner in obj.raccess.owners.all():
            name = owner.first_name + ' ' + owner.last_name
            names.append(name)
        return names

    def prepare_owners_count(self, obj):
        return obj.raccess.owners.all().count()

    def prepare_viewers_logins(self, obj):
        return [viewer.username for viewer in obj.raccess.view_users.all()]

    def prepare_viewers_names(self, obj):
        names = []
        for viewer in obj.raccess.view_users.all():
            name = viewer.first_name + ' ' + viewer.last_name
            names.append(name)
        return names

    def prepare_viewers_count(self, obj):
        return obj.raccess.view_users.all().count()

    def prepare_editors_logins(self, obj):
        return [editor.username for editor in obj.raccess.edit_users.all()]

    def prepare_editors_names(self, obj):
        names = []
        for editor in obj.raccess.edit_users.all():
            name = editor.first_name + ' ' + editor.last_name
            names.append(name)
        return names

    def prepare_editors_count(self, obj):
        return obj.raccess.edit_users.all().count()