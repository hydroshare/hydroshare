# This script is to investigate (github issue #2408)
# how to run:
# docker exec -i hydroshare python manage.py shell < "hs_tools_resource/patches/missing_constraint.py"
# Note: use "-i" instead of "-it" in above command as
# the latter may cause error "cannot enable tty mode on non tty input"

from datetime import datetime
from hs_tools_resource.models import ToolResource

tool_res_list = list(ToolResource.objects.all())
tool_res_count = len(tool_res_list)
print "[{0}] Find {1} Tools Resources\n".format(str(datetime.now()),
                                                     tool_res_count)
counter = 0
success_check_counter = 0
error_check_counter = 0
error_supported_res_types = []
error_supported_sharing_status = []
for tool_res_obj in tool_res_list:
    try:
        counter += 1
        print "[{0}] Checking Tool {1}: ({2}/{3})\n".format(str(datetime.now()),
                                                                tool_res_obj.short_id,
                                                                counter,
                                                                tool_res_count)
        print "Checking supported_res_types:"
        if tool_res_obj.metadata.supported_res_types is not None:
            if tool_res_obj.metadata.supported_res_types.count() != 1:
                print "obj count: {0}".format(tool_res_obj.metadata.supported_res_types.count())
                error_supported_res_types.append(tool_res_obj.short_id)
            else:
                print "Passed"
        else:
            print "supported_res_types is None"
            error_supported_res_types.append(tool_res_obj.short_id)

        print "Checking supported_sharing_status:"
        if tool_res_obj.metadata.supported_sharing_status is not None:
            if tool_res_obj.metadata.supported_sharing_status.count() != 1:
                print "obj count: {0}".format(tool_res_obj.metadata.supported_sharing_status.count())
                error_supported_sharing_status.append(tool_res_obj.short_id)
            else:
                print "Passed"
        else:
            print "supported_sharing_status is None"
            error_supported_sharing_status.append(tool_res_obj.short_id)

        success_check_counter += 1
    except Exception as ex:
        print "[{0}] Failed to check Tools {1}: {2}\n".format(str(datetime.now()),
                                                            tool_res_obj.short_id,
                                                            ex.message)
        error_check_counter += 1

print "[{0}] Check Done!\n".format(str(datetime.now()))
print "TOTAL RES: {0}; CHECK SUCCESS: {1}; CHECK ERROR: {2}\n".\
    format(tool_res_count, success_check_counter, error_check_counter)
print "Error supported_res_types: {0}\n".format(len(error_supported_res_types))
for res_id in error_supported_res_types:
    print res_id

print "Error supported_sharing_status: {0}\n".format(len(error_supported_sharing_status))
for res_id in error_supported_sharing_status:
    print res_id