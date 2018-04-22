from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.features import Features
from django.contrib.auth.models import Group
from hs_explore.utils import Utils
from hs_explore.topic_modeling import TopicModeling
from datetime import datetime
from pprint import pprint
import pickle
import sys


class Command(BaseCommand):
    help = "Print information about a user."

    def handle(self, *args, **options):
        # x = Features.visited_resources(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                                datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_viewers(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                               datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.resource_owners()
        # pprint(x)
        # x = Features.resource_editors()
        # pprint(x)

        user_resource_downloads = []
        x = Features.resource_downloads(datetime(2017, 11, 20, 0, 0, 0, 0),
                                        datetime(2018, 1, 1, 0, 0, 0, 0))
        user_resource_downloads.append(x)
        # pprint(x)

        x = Features.user_downloads(datetime(2017, 11, 20, 0, 0, 0, 0),
                                    datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        user_resource_downloads.append(x)


        # x = Features.resource_apps(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                            datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)
        # x = Features.user_apps(datetime(2017, 11, 20, 0, 0, 0, 0),
        #                        datetime(2018, 1, 1, 0, 0, 0, 0))
        # pprint(x)


        # print the feature vector for all resources.
        PICKLE_FILE = "resource_features.pkl"
        USE_PICKLE = 0

        if USE_PICKLE:
            input = open(PICKLE_FILE, 'rb')
            all_resource_features = pickle.load(input)
            input.close()
        else:
            all_resource_features = []
            len_objects_all = len(BaseResource.objects.all())
            print "len(BaseResource.objects.all())", len_objects_all
            for index,r in enumerate(BaseResource.objects.all()):
                # pprint(Features.resource_features(r))
                # Utils.write_dict("ALL_RESOURCES_ALL_FEATURES.OUT", Features.resource_features(r))
                # Utils.write_dict("resource_features.txt", Features.resource_features(r))
                # print ".",
                print 1.0*index / len_objects_all, "%"
                sys.stdout.flush()
                all_resource_features.append(Features.resource_features(r))
            output = open(PICKLE_FILE, 'wb')
            pickle.dump(all_resource_features, output)

        user_resource_other = []
        x = Features.user_my_resources()
        # Utils.write_dict("CF_user_my_resources.out", x)
        # pprint(x)
        user_resource_other.append(x)

        x = Features.user_favorites()
        # Utils.write_dict("CF_user_favorites.out", x)
        user_resource_other.append(x)

        tm = TopicModeling()
        tm.start(all_resource_features, user_resource_downloads, user_resource_other)


        # x = Features.user_owned_groups()
        # Utils.write_dict("CF_user_owned_groups.out", x)
        #
        # x = Features.user_edited_groups()
        # Utils.write_dict("CF_user_edited_groups.out", x)
        #
        # x = Features.user_viewed_groups()
        # Utils.write_dict("CF_user_viewed_groups.out", x)

        # for g in Group.objects.all(): 
        #     x = Features.resources_viewable_via_group(g)
        #     pprint(g)
        #     pprint(Features.explain_group(g))
        #     pprint(x)

        # for g in Group.objects.all():
        #     x = Features.resources_editable_via_group(g)
        #     pprint(g)
        #     pprint(Features.explain_group(g))
        #     pprint(x)
