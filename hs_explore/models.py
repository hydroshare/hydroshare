from django.db import models, transaction
from hs_core.models import BaseResource
from django.contrib.auth.models import User
from hs_core.hydroshare import user_from_id, get_resource_by_shortkey
from django.contrib.postgres.fields import HStoreField
import copy


class Status(object):
    """ define the status of recommended resources and
        the number for recommended resources made for users
        STATUS_NEW: a new recommended resource for a user
        STATUS_SHOWN: a recommended resource has been shown to the user
        STATUS_EXPLORED: a recommended resource has been explored by the user
        STATUS_APPROVED: a recommended resource has been approved to be a correct
        recommendation by the user
        STATUS_DISMISSED: a recommended resouce is dismissed by the user
    """
    STATUS_NEW = 1
    STATUS_SHOWN = 2
    STATUS_EXPLORED = 3
    STATUS_APPROVED = 4
    STATUS_DISMISSED = 5
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_SHOWN, 'Shown'),
        (STATUS_EXPLORED, 'Explored'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_DISMISSED, 'Dismissed')
    )
    RECOMMENDATION_LIMIT = 10


class RecommendedResource(models.Model):
    """ Resource whose attributes cause them to be recommended """
    user = models.ForeignKey(User, editable=False)
    candidate_resource = models.ForeignKey(BaseResource, editable=False,
                                           related_name='resource_recommendation_test')
    rec_type = models.CharField(max_length=11, null=True,
                                choices=(('Ownership', 'Ownership'), ('Propensity', 'Propensity'),
                                         ('Combination', 'Combination')))
    relevance = models.FloatField(editable=False, default=0.0)
    state = models.IntegerField(choices=Status.STATUS_CHOICES,
                                default=Status.STATUS_NEW,
                                editable=False)
    keywords = HStoreField(default={})

    class Meta:
        unique_together = ('user', 'candidate_resource', 'rec_type')

    @staticmethod
    def recommend(u, r, t, relevance=None, state=None, keywords={}):
        """ recommend a resource to a user
            :param u, (User type) the user, who is recommended for
            :param r, (Resource type) the resource that recommended to the user
            :param t, recommend type describes what kind of preferences that the
            recommendation is  made based upon
            :param relevance, a float represents the similarity between the user's
            preferences and recommended resource's keywords set
            :param state, the viewable state option for the recommended resource
            :param keywords, a {keyword: frequency} dictionary stores the user's
            preferences to each common keywords in the resource's keywords set
        """
        defaults = {}
        if relevance is not None:
            defaults['relevance'] = relevance
        if state is not None:
            defaults['state'] = state
        if len(keywords) > 0:
            defaults['keywords'] = keywords
        with transaction.atomic():
            object, created = RecommendedResource.objects.get_or_create(user=u,
                                                                        candidate_resource=r,
                                                                        rec_type=t,
                                                                        defaults=defaults)
            if not created:
                if relevance is not None:
                    object.relevance = relevance
                if state is not None:
                    object.state = state
                if len(keywords) > 0:
                    defaults['keywords'] = keywords
                if relevance is not None or state is not None or len(keywords) > 0:
                    object.save()

        return object

    @staticmethod
    def recommend_ids(uid, rid, t, relevance=None, state=None, keywords=()):
        """ use string ids rather than User and Resource objects """
        u = user_from_id(uid, raise404=False)
        r = get_resource_by_shortkey(rid, or_404=False)
        RecommendedResource.recommend(u, r, t, relevance=relevance, state=state, keywords=keywords)

    def relate(self, keyword, frequency):
        """ relate a keyword to a recommended resource
            :param keyword, a string keyword to be added
            :param frequency, a string frequency represents how much
            the user interests in the given keyword
        """
        updated_keyword_frequency = self.keywords
        updated_keyword_frequency[keyword] = frequency
        self.keywords = updated_keyword_frequency
        self.save()

    def unrelate(self, keyword):
        """ unrelate a keyword to a recommended resource
            :param keyword, the string keyword to be unrelated
        """
        updated_keyword_frequency = copy.deepcopy(self.keywords)
        updated_keyword_frequency.pop(keyword, None)
        self.keywords = updated_keyword_frequency
        self.save()

    def shown(self):
        """ set the recommended resource status to shown """
        self.state = Status.STATUS_SHOWN
        self.save()

    def explored(self):
        """ set the recommended resource status to explored """
        self.state = Status.STATUS_EXPLORED
        self.save()
        self.state = Status.STATUS_APPROVED
        self.save()

    def dismissed(self):
        """ set the recommended resource status to dismissed """
        self.state = Status.STATUS_DISMISSED
        self.save()

    @staticmethod
    def delete(u, r):
        """ delete a recommended resource record for a user
            :param u, a User to delete a recommended resource
            :param r, a Resource to be removed from the user's recommended resources
        """
        try:
            record = RecommendedResource.objects.get(user=u, candidate_resource=r)
            record.delete()
        except Exception:
            pass

    @staticmethod
    def clear():
        """ clear all data records  """
        RecommendedResource.objects.all().delete()

    def to_json(self):
        json_obj = {}
        json_obj['user'] = self.user.username
        json_obj['candidate_resource_id'] = self.candidate_resource.short_id
        json_obj['candidate_resource_title'] = self.candidate_resource.title
        json_obj['relevance'] = self.relevance
        json_obj['rec_type'] = self.rec_type
        json_obj['state'] = self.state
        keywords = []
        for keyword in list(self.keywords.items()):
            keywords.append(keyword.to_json())
        json_obj['keywords'] = keywords
        return json_obj


class UserPreferences(models.Model):
    """ store user preferences to each keyword and resources that selected by the user """
    user = models.OneToOneField(User, editable=False)
    preferences = HStoreField(default={})
    pref_for = models.CharField(max_length=8, choices=(('Resource', 'Resource'),
                                ('User', 'User'), ('Group', 'Group')))

    @staticmethod
    def prefer(u, pf, preferences={}):
        """ build up a user's preferences profile
            :param u, a User to be set up the preferences
            :param pf, choices from pref_for that describes the preferences for
            :param preferences, a {keyword: frequency} dictionary represents the given
            user's preferences for each keyword
        """
        defaults = {}
        if len(preferences) > 0:
            defaults['preferences'] = preferences
        with transaction.atomic():
            object, created = UserPreferences.objects.get_or_create(user=u,
                                                                    pref_for=pf,
                                                                    defaults=defaults)
            if not created:
                if len(preferences) > 0:
                    defaults['preferences'] = preferences
                    object.save()

        return object

    def relate(self, keyword, frequency):
        """ relate a keyword to the user's preference
            :param keyword, a string keyword to be added
            :param frequency, a string frequency represents how much
            the user interests in the given keyword
        """
        updated_preferences = self.preferences
        updated_preferences[keyword] = frequency
        self.preferences = updated_preferences
        self.save()

    def unrelate(self, keyword):
        """ unrelate a keyword to a user's preferences profile
            :param keyword, the string keyword to be unrelated
        """
        updated_preferences = copy.deepcopy(self.preferences)
        updated_preferences.pop(keyword, None)
        self.preferences = updated_preferences
        self.save()

    @staticmethod
    def clear():
        """ clear all data records """
        UserPreferences.objects.all().delete()


class LDAStopWord(models.Model):
    """ store keep-word and stop-words used in our LDA model"""
    source = models.CharField(max_length=10, choices=(('English', 'English'),
                                                      ('Customized', 'Customized')))
    part = models.CharField(max_length=5, choices=(('name', 'name'), ('decor', 'decor')))
    value = models.CharField(max_length=255, editable=False, null=False, blank=False)

    @staticmethod
    def add_word(s, p, v):
        """ add a record to the LDAWord model
            :param s, a choice from source describes where the word from
            :param t, a choice from word_type describes whether the word is keep-word
            or stop-word
            :param p, a choice from part describes which part the word is extracted from
            :param, v, a string value for the word to be added
        """
        object, _ = LDAStopWord.objects.get_or_create(source=s, part=p, value=v)

        return object

    @staticmethod
    def clear():
        """ clear all data records """
        LDAStopWord.objects.all().delete()
