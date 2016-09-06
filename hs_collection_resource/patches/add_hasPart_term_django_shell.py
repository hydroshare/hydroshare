# This script is to add "hasPart" metadata to all collection resources (github issue #1403)
# how to run:
# docker exec -i hydroshare python manage.py shell \
# < "hs_collection_resource/patches/add_hasPart_term_django_shell.py"

from datetime import datetime

from django.contrib.auth.models import User

from hs_core.hydroshare.utils import resource_modified, current_site_url
from hs_collection_resource.utils import add_or_remove_relation_metadata
from hs_collection_resource.models import CollectionResource

last_changed_by_user = None
try:
    last_changed_by_user = User.objects.get(username='admin')
except Exception as ex:
    print "[{0}] Failed to get Admin user obj, set 'last_changed_by_user = None'\n"

hasPart = "hasPart"
site_url = current_site_url()
relation_value_template = site_url + "/resource/{0}/"
collection_res_list = list(CollectionResource.objects.all())
collection_count = len(collection_res_list)
print "[{0}] Find {1} Collection Resources\n".format(str(datetime.now()),
                                                     collection_count)
counter = 0
success_counter = 0
error_counter = 0
for collection_res_obj in collection_res_list:
    try:
        counter += 1
        print "[{0}] Processing on collection {1}: ({2}/{3})\n".format(str(datetime.now()),
                                                                       collection_res_obj.short_id,
                                                                       counter,
                                                                       collection_count)
        for contained_res_obj in collection_res_obj.resources.all():
            value = relation_value_template.format(contained_res_obj.short_id)
            add_or_remove_relation_metadata(add=True, target_res_obj=collection_res_obj,
                                            relation_type=hasPart, relation_value=value,
                                            set_res_modified=False)

        resource_modified(collection_res_obj, last_changed_by_user)
        print "[{0}] Done with Collection {1}\n".format(str(datetime.now()),
                                                        collection_res_obj.short_id)
        success_counter += 1
    except Exception as ex:
        print "[{0}] Error on Collection {1}: {2}\n".format(str(datetime.now()),
                                                            collection_res_obj.short_id,
                                                            ex.message)
        error_counter += 1

print "[{0}] All Done!\n".format(str(datetime.now()))
print "TOTAL: {0}; SUCCESS: {1};  ERROR: {2}\n".\
    format(collection_count, success_counter, error_counter)