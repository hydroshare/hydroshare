

# TODO: not used anywhere. delete.
class HydroshareAuthorization(object):
    def read_list(self, object_list, bundle):
        return [x for x in object_list if x.can_view(bundle.request)]

    def read_detail(self, object_list, bundle):
        return bundle.obj.can_view(bundle.request)

    def create_list(self, object_list, bundle):
        return object_list

    def create_detail(self, object_list, bundle):
        return bundle.obj.parent and bundle.obj.parent.can_add(bundle.request)

    def update_list(self, object_list, bundle):
        return [x for x in object_list if x.can_change(bundle.request)]

    def update_detail(self, object_list, bundle):
        return bundle.obj.can_change(bundle.request)

    def delete_list(self, object_list, bundle):
        return [x for x in object_list if x.can_delete(bundle.request)]

    def delete_detail(self, object_list, bundle):
        return bundle.obj.can_delete(bundle.request)
