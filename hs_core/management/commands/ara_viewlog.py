from django.core.management.base import BaseCommand
from datetime import datetime
from hs_tracking.models import Variable


class Command(BaseCommand):
    help = "Print information about a user."

    def handle(self, *args, **options):
        for v in Variable.objects.filter(timestamp__gte=datetime(2017, 11, 20, 0, 0, 0, 0),
                                         timestamp__lte=datetime(2017, 12, 29, 0, 0, 0, 0)):
            user = v.session.visitor.user
            if user is not None and user.username != 'test' and user.username != 'demo':
                print("user:{} name:{} value:{}".format(user.username, v.name, str(v.get_value())))
