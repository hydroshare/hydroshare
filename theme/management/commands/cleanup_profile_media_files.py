import os
from django.core.management.base import BaseCommand

from theme.models import UserProfile


class Command(BaseCommand):
    help = "This commond can be run to clean up the deleted media files"

    def add_arguments(self, parser):
        parser.add_argument('profile_path',
                            help='profile_path in the container, i.e., /hydroshare/hydroshare/static/media/profile')

    def handle(self, *args, **options):
        ups = UserProfile.objects.all()
        profile_path = options['profile_path']
        pic_list = list(ups.values_list('picture', flat=True))
        cv_list = list(ups.values_list('cv', flat=True))
        # remove empty fields and remove relative path
        pic_list = [pic.split('/')[-1] for pic in pic_list if pic]
        cv_list = [cv.split('/')[-1] for cv in cv_list if cv]
        ref_list = pic_list + cv_list
        for file_name in os.listdir(profile_path):
            if file_name not in ref_list:
                # file_name is not used, remove it
                file_to_be_removed = os.path.join(profile_path, file_name)
                os.remove(file_to_be_removed)
                print(file_to_be_removed, ' has been removed')
