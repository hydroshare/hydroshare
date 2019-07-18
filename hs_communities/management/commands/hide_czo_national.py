from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


def hide_national_group():
    """
    CZO National is used to establish Community membership and privileges. It should be hidden from user view.

    :return:
    """
    national_group = list(Group.objects.filter(name="CZO National"))
    if len(national_group) > 1:
        print('Error: more than one CZO National group')
    else:
        print(national_group[0].id, national_group[0].name)
        national_group[0].gaccess.unlisted = True
        national_group[0].gaccess.save()
        print(national_group[0].gaccess.unlisted)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        hide_national_group()
