from json import loads, dumps
from datetime import datetime, timedelta

from django.db import models
from django.core import signing
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from theme.models import UserProfile


SESSION_TIMEOUT = 60 * 15
PROFILE_FIELDS = ["title", "user_type", "subject_areas", "public", "state", "country"]
USER_FIELDS = ["username", "email", "first_name", "last_name"]
VISITOR_FIELDS = ["id"] + USER_FIELDS + PROFILE_FIELDS
if set(PROFILE_FIELDS) & set(USER_FIELDS):
    raise ImproperlyConfigured("hs_tracking PROFILE_FIELDS and USER_FIELDS must not contain overlapping field names")


class SessionManager(models.Manager):
    def for_request(self, request):
        signed_id = request.session.get('hs_tracking_id')
        if signed_id:
            tracking_id = signing.loads(signed_id)
            cut_off = datetime.now() - timedelta(seconds=SESSION_TIMEOUT)
            session = None
            try:
                session = Session.objects.filter(begin__gte=cut_off).get(id=tracking_id['id'])
            except Session.DoesNotExist:
                pass
            if session is not None:
                if session.visitor.user is None and request.user.is_authenticated():
                    session.visitor.user = request.user
                    session.visitor.save()
                return session
        # No session found, create one
        if request.user.is_authenticated():
            visitor, _ = Visitor.objects.get_or_create(user=request.user)
        else:
            visitor = Visitor.objects.create()
        session = Session.objects.create(visitor=visitor)
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
    )
    TYPE_CHOICES = (
        (i, label)
        for (i, label) in
        enumerate((label for (label, coercer) in TYPES), 1)
    )

    session = models.ForeignKey(Session)
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=32)
    type = models.IntegerField(choices=TYPES)
    value = models.CharField(max_length=130)

    def get_value(self):
        try:
            f = float(self.value)
        except ValueError:
            f = None
        try:
            i = int(self.value)
        except ValueError:
            i = None
        if i is not None and i == f:
            return i
        elif f is not None:
            return f
        elif self.value == 'true':
            return True
        elif self.value == 'false':
            return False
        return self.value

    @classmethod
    def record(cls, session, name, value):
        for i, (label, coercer) in enumerate(cls.TYPES, 1):
            try:
                if value == coercer(value):
                    type_code = i
                    break
            except ValueError:
                continue
        return Variable.objects.create(session=session, name=name, type=type_code, value=cls.encode(value))

    @classmethod
    def encode(cls, value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, (int, float, str, unicode)):
            return unicode(value)
        else:
            raise ValueError("Unknown type (%s) for tracking variable: %r" % (type(value).__name__, value))
