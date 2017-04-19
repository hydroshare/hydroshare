import os
import tempfile
import csv
import shutil
import logging

from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare.utils import resource_modified, current_site_url
from hs_core.hydroshare.resource import delete_resource_file_only, add_resource_files

logger = logging.getLogger(__name__)
CSV_FULL_NAME_TEMPLATE = "collection_list_{0}.csv"
DELETED_RES_STRING = "Resource Deleted"


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
        target_res_obj.metadata.relations.\
                filter(type=relation_type, value=relation_value).all().delete()

    if set_res_modified:
        resource_modified(target_res_obj, last_change_user, overwrite_bag=False)


def update_collection_list_csv(collection_obj):
    """
    This function is to create a new csv file in bag that lists info of all contained resources.
    A list that contains all csv content will be returned for unit test use.
    :param collection_obj: collection resource object
    :return: the csv content in a list object
    """

    tmp_dir = None
    short_key = ""
    csv_content_list = []
    try:
        short_key = collection_obj.short_id
        csv_full_name = CSV_FULL_NAME_TEMPLATE.format(collection_obj.short_id)

        # remove all files in bag
        # The only possible file is a .csv file.
        # It is removed before another is added.
        for f in collection_obj.files.all():
            delete_resource_file_only(collection_obj, f)

        if collection_obj.resources.count() > 0 or collection_obj.deleted_resources.count() > 0:
            # prepare csv content
            # create headers
            csv_header_row = ['Title',
                              'Type',
                              'ID',
                              'URL',
                              'Owners',
                              'Sharing Status'
                              ]
            csv_content_list.append(csv_header_row)
            # create rows for currently contained resources
            for res in collection_obj.resources.all():
                csv_data_row = [res.metadata.title,
                                res.resource_type,
                                res.short_id,
                                current_site_url(res.get_absolute_url()),
                                _get_owners_string(list(res.raccess.owners.all())),
                                _get_sharing_status_string(res)
                                ]
                csv_content_list.append(csv_data_row)

            # create rows for deleted resources
            for deleted_res_log in collection_obj.deleted_resources:
                csv_data_row = [deleted_res_log.resource_title,
                                deleted_res_log.resource_type,
                                deleted_res_log.resource_id,
                                DELETED_RES_STRING,
                                _get_owners_string(list(deleted_res_log.resource_owners.all()))
                                if deleted_res_log.resource_owners.count() > 0
                                else DELETED_RES_STRING,
                                DELETED_RES_STRING
                                ]
                csv_content_list.append(csv_data_row)

            # create a new csv on django server
            tmp_dir = tempfile.mkdtemp()
            csv_full_path = os.path.join(tmp_dir, csv_full_name)
            with open(csv_full_path, 'w') as csv_file_handle:
                w = csv.writer(csv_file_handle)
                for row in csv_content_list:
                    w.writerow(row)

            # push the new csv file to irods bag
            files = (UploadedFile(file=open(csv_full_path, 'r'), name=csv_full_name))
            add_resource_files(collection_obj.short_id, files)

    except Exception as ex:
        logger.error("Failed to update_collection_list_csv in {}"
                     "Error:{} ".format(short_key, ex.message))
        raise Exception("update_collection_list_csv error: " + ex.message)
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir)
        return csv_content_list


def _get_owners_string(owners_list):

    name_list = []
    for owner in owners_list:
        if owner.first_name:
            name_str = "{0} {1}".format(owner.first_name, owner.last_name)
        else:
            name_str = owner.username
        name_list.append(name_str)
    if len(name_list) > 1:
        # csv.writer can correctly handle comma in string. No need to add extra quotes here.
        return ', '.join(name_list)
    else:
        return name_list[0]


def _get_sharing_status_string(res_obj):

    if res_obj.raccess.published:
        status_str = "Published"
    elif res_obj.raccess.public:
        status_str = "Public"
    elif res_obj.raccess.discoverable:
        status_str = "Discoverable"
    else:
        status_str = "Private"

    if res_obj.raccess.shareable:
        status_str += "&Shareable"
    return status_str
