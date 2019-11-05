from hs_core.tasks import create_bag_by_irods, create_bag_by_irods_wait
from hs_core.hydroshare.utils import get_resource_by_shortkey


def create_bag_by_irods_async(res_id):
    res = get_resource_by_shortkey(res_id)

    if res.locked:
        # resource is locked meaning its bag is being created by another celery task
        task = create_bag_by_irods_wait.apply_async((res_id,), countdown=3)
        return task
    else:
        task = create_bag_by_irods.apply_async((res_id,), countdown=3)
        return task
