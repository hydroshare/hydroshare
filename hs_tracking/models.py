from json import loads, dumps

from django.db import models
from django.core import signing


SESSION_TIMEOUT = 60 * 15


class SessionManager(models.Manager):
    def for_request(self, request):
        signed_id = request.session.get('hs_tracking_id')
        if signed_id:
            tracking_id = signing.loads(signed_id)
            try:
                return Session.objects.get(id=tracking_id['id'])
            except Session.DoesNotExist:
                pass
        # No session found, create one
        session = Session.objects.create()
        request.session['hs_tracking_id'] = signing.dumps({'id': session.id})
        return session


class Session(models.Model):
    begin = models.DateTimeField(auto_now_add=True)

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
        return loads(self.value)

    @classmethod
    def record(cls, session, name, value):
        for i, (label, coercer) in enumerate(cls.TYPES, 1):
            try:
                if value == coercer(value):
                    type_code = i
                    break
            except ValueError:
                continue
        Variable.objects.create(session=session, name=name, type=type_code, value=dumps(value))
