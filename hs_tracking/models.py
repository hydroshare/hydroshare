from datetime import datetime, timedelta

from django.db import models
from django.db.models import F
from django.core import signing
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User

from theme.models import UserProfile
from utils import get_std_log_fields
from hs_core.models import BaseResource
from hs_core.hydroshare import get_resource_by_shortkey

SESSION_TIMEOUT = settings.TRACKING_SESSION_TIMEOUT
PROFILE_FIELDS = settings.TRACKING_PROFILE_FIELDS
USER_FIELDS = settings.TRACKING_USER_FIELDS
VISITOR_FIELDS = ["id"] + USER_FIELDS + PROFILE_FIELDS
if set(PROFILE_FIELDS) & set(USER_FIELDS):
    raise ImproperlyConfigured("hs_tracking PROFILE_FIELDS and USER_FIELDS must not contain"
                               " overlapping field names")


class SessionManager(models.Manager):
    def for_request(self, request, user=None):
        if hasattr(request, 'user'):
            user = request.user

        signed_id = request.session.get('hs_tracking_id')
        if signed_id:
            tracking_id = signing.loads(signed_id)
            cut_off = datetime.now() - timedelta(seconds=SESSION_TIMEOUT)
            session = None

            try:
                session = Session.objects.filter(
                    variable__timestamp__gte=cut_off).filter(id=tracking_id['id']).first()
            except Session.DoesNotExist:
                pass

            if session is not None and user is not None:
                if session.visitor.user is None and user.is_authenticated():
                    try:
                        session.visitor = Visitor.objects.get(user=user)
                        session.save()
                    except Visitor.DoesNotExist:
                        session.visitor.user = user
                        session.visitor.save()
                return session

        # No session found, create one
        if user.is_authenticated():
            visitor, _ = Visitor.objects.get_or_create(user=user)
        else:
            visitor = Visitor.objects.create()

        session = Session.objects.create(visitor=visitor)

        # get standard fields and format
        fields = get_std_log_fields(request, session)
        msg = Variable.format_kwargs(**fields)

        session.record('begin_session', msg)
        request.session['hs_tracking_id'] = signing.dumps({'id': session.id})
        return session


class Visitor(models.Model):
    first_seen = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True,
                                on_delete=models.SET_NULL,
                                related_name='visitor')

    def export_visitor_information(self):
        """Exports visitor profile information."""
        info = {
            "id": self.id,
        }
        if self.user:
            profile = UserProfile.objects.get(user=self.user)
            for field in PROFILE_FIELDS:
                info[field] = getattr(profile, field)
            for field in USER_FIELDS:
                info[field] = getattr(self.user, field)
        else:
            profile = None
            for field in PROFILE_FIELDS:
                info[field] = None
            for field in USER_FIELDS:
                info[field] = None
        return info


class Session(models.Model):
    begin = models.DateTimeField(auto_now_add=True)
    visitor = models.ForeignKey(Visitor, related_name='session')
    # TODO: hostname = models.CharField(null=True, default=None, max_length=256)

    objects = SessionManager()

    def get(self, name):
        return Variable.objects.filter(session=self, name=name).first().get_value()

    def getlist(self, name):
        return [v.get_value() for v in Variable.objects.filter(session=self, name=name)]

    def record(self, *args, **kwargs):
        args = (self,) + args
        return Variable.record(*args, **kwargs)


class Variable(models.Model):
    TYPES = (
        ('Integer', int),
        ('Floating Point', float),
        ('Text', unicode),
        ('Flag', bool),
        ('None', lambda o: None)
    )
    TYPE_CHOICES = [
        (i, label)
        for (i, label) in
        enumerate(label for (label, coercer) in TYPES)
    ]

    from hs_core.models import BaseResource

    session = models.ForeignKey(Session, related_name='variable')
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=32)
    type = models.IntegerField(choices=TYPE_CHOICES)
    # change value to TextField to be less restrictive as max_length of CharField has been
    # exceeded a couple of times
    value = models.TextField()

    # If a resource no longer exists, last_resource_id remains valid but resource is NULL
    resource = models.ForeignKey(BaseResource, null=True,
                                 related_name='variable',
                                 on_delete=models.SET_NULL)
    last_resource_id = models.CharField(null=True, max_length=32)

    # flags describe kind of visit. False for non-visits
    landing = models.BooleanField(null=False, default=False)
    rest = models.BooleanField(null=False, default=False)
    # REDUNDANT: internal = models.BooleanField(null=False, default=False)

    def get_value(self):
        v = self.value
        if self.type == 3:  # boolean types don't coerce reflexively
            if v == 'true':
                return True
            else:
                return False
        else:
            t = self.TYPES[self.type][1]
            return t(v)

    @classmethod
    def format_kwargs(cls, **kwargs):
        msg_items = []
        for k, v in kwargs.iteritems():
            msg_items.append('%s=%s' % (unicode(k).encode(), unicode(v).encode()))
        return '|'.join(msg_items)

    @classmethod
    def record(cls, session, name, value=None, resource=None, resource_id=None,
               rest=False, landing=False):
        if resource is None and resource_id is not None:
            try:
                resource = get_resource_by_shortkey(resource_id, or_404=False)
            except BaseResource.DoesNotExist:
                resource = None
        return Variable.objects.create(session=session, name=name,
                                       type=cls.encode_type(value),
                                       value=cls.encode(value),
                                       last_resource_id=resource_id,
                                       resource=resource,
                                       rest=rest,
                                       landing=landing)

    @classmethod
    def encode(cls, value):
        if value is None:
            return ''
        elif isinstance(value, bool):
            return 'true' if value else 'false'  # only empty strings are False
        elif isinstance(value, (int, float, str, unicode)):
            return unicode(value)
        else:
            raise ValueError("Unknown type (%s) for tracking variable: %r",
                             type(value).__name__, value)

    @classmethod
    def encode_type(cls, value):
        if value is None:
            return 4
        elif isinstance(value, bool):
            return 3
        elif isinstance(value, (str, unicode)):
            return 2
        elif isinstance(value, float):
            return 1
        elif isinstance(value, int):
            return 0
        else:
            raise TypeError("Unable to record variable of unrecognized type %s",
                            type(value).__name__)

    @classmethod
    def recent_resources(cls, user, n_resources=5, days=60):
        """
        fetch the most recent n resources with which a specific user has interacted

        :param user: The user to document.
        :param n_resources: the number of resources to return.
        :param days: the number of days to scan.

        The reason for the parameter `days` is that the runtime of this method
        is very dependent upon the days that one scans. Thus, there is a tradeoff
        between reporting history and timely responsiveness of the dashboard.
        """
        # TODO: document actions like labeling and commenting (currently these are 'visit's)
        return BaseResource.objects.filter(
                variable__session__visitor__user=user,
                variable__timestamp__gte=(datetime.now()-timedelta(days)),
                variable__resource__isnull=False,
                variable__name='visit')\
            .only('short_id', 'created')\
            .distinct()\
            .annotate(public=F('raccess__public'),
                      discoverable=F('raccess__discoverable'),
                      published=F('raccess__published'),
                      last_accessed=models.Max('variable__timestamp'))\
            .filter(variable__timestamp=F('last_accessed'))\
            .order_by('-last_accessed')[:n_resources]

    @classmethod
    def popular_resources(cls, n_resources=5, days=60, today=None):
        """
        fetch the most recent n resources with which a specific user has interacted

        :param n_resources: the number of resources to return.
        :param days: the number of days to scan.

        The reason for the parameter `days` is that the runtime of this method
        is very dependent upon the days that one scans. Thus, there is a tradeoff
        between reporting history and timely responsiveness of the dashboard.
        """
        # TODO: document actions like labeling and commenting (currently these are 'visit's)
        if today is None:
            today = datetime.now()
        return BaseResource.objects.filter(
                variable__timestamp__gte=(today-timedelta(days)),
                variable__timestamp__lt=(today),
                variable__resource__isnull=False,
                variable__name='visit')\
            .distinct()\
            .annotate(users=models.Count('variable__session__visitor__user'))\
            .annotate(public=F('raccess__public'),
                      discoverable=F('raccess__discoverable'),
                      published=F('raccess__published'),
                      last_accessed=models.Max('variable__timestamp'))\
            .order_by('-users')[:n_resources]

    @classmethod
    def recent_users(cls, resource, n_users=5, days=60):
        """
        fetch the identities of the most recent users who have accessed a resource

        :param resource: The resource to document.
        :param n_users: the number of users to return.
        :param days: the number of days to scan.

        The reason for the parameter `days` is that the runtime of this method
        is very dependent upon the number of days that one scans. Thus, there is a
        tradeoff between reporting history and timely responsiveness of the dashboard.
        """
        return User.objects\
            .filter(visitor__session__variable__resource=resource,
                    visitor__session__variable__name='visit',
                    visitor__session__variable__timestamp__gte=(datetime.now() -
                                                                timedelta(days)))\
            .distinct()\
            .annotate(last_accessed=models.Max('visitor__session__variable__timestamp'))\
            .filter(visitor__session__variable__timestamp=F('last_accessed'))\
            .order_by('-last_accessed')[:n_users]
