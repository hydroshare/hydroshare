from hs_core.hydroshare.utils import resource_modified


def add_or_remove_relation_metadata(add=True, target_res_obj=None, relation_type="",
                                    relation_value="", set_res_modified=False,
                                    last_change_user=None):
    """
    add new or remove relation metadata to/from target res obj
    :param add: True -- add metadata; False -- remove metadata
    :param target_res_obj: the target res obj to receive the change
    :param relation_type: "hasPart" or "isPartOf"
    :param relation_value: value of relation
    :param set_res_modified: set bag modified flag to True or False
    :param last_change_user: the User obj represents the last_change_by user
            (only works when set_res_modified is True)
    :return:
    """

    if add:
        meta_dict = {}
        meta_dict['type'] = relation_type
        meta_dict['value'] = relation_value
        target_res_obj.metadata.create_element("relation", **meta_dict)
    else:
        first_relation_obj = target_res_obj.metadata.relations.\
            filter(type=relation_type, value=relation_value)
        if first_relation_obj.exists():
            first_relation_obj.first().delete()

    if set_res_modified:
        resource_modified(target_res_obj, last_change_user)
