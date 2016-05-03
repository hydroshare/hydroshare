from haystack import indexes
from hs_core.models import BaseResource
from django.db.models import Q


class BaseResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    short_id = indexes.CharField(model_attr='short_id')
    doi = indexes.CharField(model_attr='doi', null=True)
    author = indexes.CharField(model_attr='first_creator', default='none', faceted=True)
    title = indexes.CharField(faceted=True)
    abstract = indexes.CharField(model_attr='description')
    creators = indexes.MultiValueField(faceted=True)
    contributors = indexes.MultiValueField()
    subjects = indexes.MultiValueField(faceted=True)
    public = indexes.BooleanField(faceted=True)
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
    resource_type = indexes.CharField(faceted=True)
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
        return self.get_model().objects.filter(Q(raccess__discoverable=True) | Q(raccess__public=True))

    def prepare_title(self, obj):
        if hasattr(obj, 'metadata'):
            return obj.metadata.title.value
        else:
            return 'none'

    def prepare_creators(self, obj):
        if hasattr(obj, 'metadata'): 
            return [creator.name for creator in obj.metadata.creators.all()]
        else:
            return []

    def prepare_contributors(self, obj):
        if hasattr(obj, 'metadata'): 
            return [contributor.name for contributor in obj.metadata.contributors.all()]
        else:
            return []

    def prepare_subjects(self, obj):
        if hasattr(obj, 'metadata'): 
            return [subject.value for subject in obj.metadata.subjects.all()]
        else:
            return []

    def prepare_organizations(self, obj):
        organizations = []
        if hasattr(obj, 'metadata'): 
            for creator in obj.metadata.creators.all():
                if(creator.organization is not None):
                    organizations.append(creator.organization)
                else:
                    organizations.append('none')
        return organizations

    def prepare_publisher(self, obj):
        if hasattr(obj, 'metadata'): 
            publisher = obj.metadata.publisher
            if publisher is not None:
                return publisher
            else:
                return 'none'
        else:
            return 'none'

    def prepare_author_emails(self, obj):
        if hasattr(obj, 'metadata'): 
            return [creator.email for creator in obj.metadata.creators.all()]
        else:
            return []

    def prepare_discoverable(self, obj):
        if hasattr(obj, 'raccess'):
            if obj.raccess.public or obj.raccess.discoverable:
                return True
            else: 
                return False
        else:
            return False

    def prepare_public(self, obj):
        if hasattr(obj, 'raccess'):
            if obj.raccess.public:
                return True
            else:
                return False
        else:
            return False

    def prepare_coverages(self, obj):
        if hasattr(obj, 'metadata'): 
            return [coverage._value for coverage in obj.metadata.coverages.all()]
        else:
            return []

    def prepare_formats(self, obj):
        if hasattr(obj, 'metadata'): 
            return [format.value for format in obj.metadata.formats.all()]
        else:
            return []

    def prepare_identifiers(self, obj):
        if hasattr(obj, 'metadata'): 
            return [identifier.name for identifier in obj.metadata.identifiers.all()]
        else:
            return []

    def prepare_language(self, obj):
        if hasattr(obj.metadata.language, 'code'):
            return obj.metadata.language.code
        else:
            return 'none'

    def prepare_sources(self, obj):
        if hasattr(obj, 'metadata'): 
            return [source.derived_from for source in obj.metadata.sources.all()]
        else:
            return []

    def prepare_relations(self, obj):
        if hasattr(obj, 'metadata'): 
            return [relation.value for relation in obj.metadata.relations.all()]
        else:
            return []

    def prepare_resource_type(self, obj):
        return obj.verbose_name

    def prepare_comments(self, obj):
        return [comment.comment for comment in obj.comments.all()]

    def prepare_comments_count(self, obj):
        return obj.comments_count

    def prepare_owners_logins(self, obj):
        if hasattr(obj, 'raccess'): 
            return [owner.username for owner in obj.raccess.owners.all()]
        else:
            return []

    def prepare_owners_names(self, obj):
        names = []
        if hasattr(obj, 'raccess'): 
            for owner in obj.raccess.owners.all():
                name = owner.first_name + ' ' + owner.last_name
                names.append(name)
        return names

    def prepare_owners_count(self, obj):
        if hasattr(obj, 'raccess'): 
            return obj.raccess.owners.all().count()
        else:
            return 0

    def prepare_viewers_logins(self, obj):
        if hasattr(obj, 'raccess'): 
            return [viewer.username for viewer in obj.raccess.view_users.all()]
        else:
            return []

    def prepare_viewers_names(self, obj):
        names = []
        if hasattr(obj, 'raccess'): 
            for viewer in obj.raccess.view_users.all():
                name = viewer.first_name + ' ' + viewer.last_name
                names.append(name)
        return names

    def prepare_viewers_count(self, obj):
        if hasattr(obj, 'raccess'): 
            return obj.raccess.view_users.all().count()
        else:
            return 0

    def prepare_editors_logins(self, obj):
        if hasattr(obj, 'raccess'): 
            return [editor.username for editor in obj.raccess.edit_users.all()]
        else:
            return 0

    def prepare_editors_names(self, obj):
        names = []
        if hasattr(obj, 'raccess'): 
            for editor in obj.raccess.edit_users.all():
                name = editor.first_name + ' ' + editor.last_name
                names.append(name)
        return names

    def prepare_editors_count(self, obj):
        if hasattr(obj, 'raccess'): 
            return obj.raccess.edit_users.all().count()
        else:
            return 0
