from datetime import datetime, timedelta

from django.db import models
from django.core import signing
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from theme.models import UserProfile


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
        session.record('begin_session')
        request.session['hs_tracking_id'] = signing.dumps({'id': session.id})
        return session


class Visitor(models.Model):
    first_seen = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, unique=True)

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
    visitor = models.ForeignKey(Visitor)

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

    session = models.ForeignKey(Session)
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=32)
    type = models.IntegerField(choices=TYPE_CHOICES)
    value = models.CharField(max_length=500)

    def get_value(self):
        v = self.value
        t = self.TYPES[self.type][0]
        if t == 'Integer':
            return int(v)
        elif t == 'Floating Point':
            return float(v)
        elif t == 'Text':
            return v
        elif t == 'Flag':
            return v == 'true'
        elif t == 'None':
            return None

    @classmethod
    def format_kwargs(cls, **kwargs):
        msg_items = []
        for k, v in kwargs.iteritems():
            msg_items.append('%s=%s' % (unicode(k).encode(), unicode(v).encode()))
        return ' '.join(msg_items)

    @classmethod
    def record(cls, session, name, value=None):
        for i, (label, coercer) in enumerate(cls.TYPES, 0):
            try:
                if value == coercer(value):
                    type_code = i
                    break
            except (ValueError, TypeError):
                continue
        else:
            raise TypeError("Unable to record variable of unrecognized type %s",
                            type(value).__name__)
        return Variable.objects.create(session=session, name=name, type=type_code,
                                       value=cls.encode(value))

    @classmethod
    def encode(cls, value):
        if value is None:
            return 'none'
        elif isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float, str, unicode)):
            return unicode(value)
        else:
            raise ValueError("Unknown type (%s) for tracking variable: %r",
                             type(value).__name__, value)
