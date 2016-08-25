import copy

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
        target_res_obj.metadata.relations.filter(type=relation_type, value=relation_value).delete()

    if set_res_modified:
       resource_modified(target_res_obj, last_change_user)

class FoundLoopException(Exception):
     def __init__(self, node_id, path_list):
        self.node_id = node_id
        self.path_list = path_list
     def __str__(self):
        return repr(self.node_id)

def traverse_collection(collection_node):
    list = [collection_node]
    if collection_node.resource_type.lower() == "collectionresource":
        for node in collection_node.resources.all():
            list += traverse_collection(node)
    return list

def detect_loop_in_collection(collection_node, visited_collection_list=None):
    if visited_collection_list is None:
        visited_collection_list_this_level = []
    else:
        visited_collection_list_this_level = copy.copy(visited_collection_list)
    if collection_node.resource_type.lower() == "collectionresource":
        visited_collection_list_this_level.append(collection_node.short_id)
        for node in collection_node.resources.all():
            if collection_node.resource_type.lower() == "collectionresource":
                if node.short_id in visited_collection_list_this_level:
                    raise FoundLoopException(node.short_id, visited_collection_list_this_level)
                else:
                    detect_loop_in_collection(node, visited_collection_list=visited_collection_list_this_level)
    return visited_collection_list