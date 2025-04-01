# -*- coding: utf-8 -*-


from django.db import migrations
from django.core.exceptions import ValidationError
from django_irods.storage import S3Storage
import os.path

# This migration converts ResourceFiles from a variety of forms to a consistent form
# containing only two possible file names and not employing deprecated field names.
# 1. This recognizes the following forms of file names as valid:
#    a. folder + file
#    b. data/contents + folder + file
#    c. fully qualified name starting with absolute resource path.
#    It converts (a) and (b) to (c) as needed. It also converts
#    fed_resource_file_name_or_path into a fully qualified fed_resource_file.
# 2. This script does not:
#    a. do anything useful with filenames that are not one of the above.
#    b. delete Django ResourceFiles that do not exist in iRODS.
#    c. delete iRODS files that do not exist in Django.
#    It does -- however -- generate printout about these.
#
# This PR will be followed by other PRs that clean up these issues.
# Due to the limits of migration, it is going to be easier for these to
# be written as administrative functions than migrations. They do not require
# structural modifications of the ResourceFile type.
#
# Detailed implementation notes:
#
# Methods in models are not available during migrations and must be made available
# as regular functions by copying them here and changing their arguments.
# To make matters even more painful, GenericRelation's are difficult to traverse
# during migrations while GenericForeignKey's are easy to traverse.

# Thus, the function get_resource_from_rfile traverses the GenericForeignKey ContentType
# hack manually from ResourceFile to BaseResource. This means -- in turn --
# that every function that needs to do this translation needs to be explicitly
# passed the type of the foreign key, which is a transitional type computed
# during the migration. We are extremely lucky in this case that there **is**
# a Generic Foreign key in use. GenericRelation hides the ContentType hack
# parameters object_id and content_type from users and makes this more difficult.

# Note that -- in general -- the GenericRelation "files" in BaseResource is redundant
# and could be replaced with related_name='files' in this GenericForeignKey...!
# That change is beyond the scope of this PR, though.


def get_resource_from_rfile(rtype, rfile):
    """
    follow a generic foreign key in a ResourceFile to the resource it references.
    :param rtype: type of target object (typically BaseResource but computed dynamically)
    :param rfile: ResourceFile for which to compute the object.
    """
    return rtype.objects.get(id=rfile.object_id)


def is_federated(resource):
    """ Copy of BaseResource.is_federated """
    return resource.resource_federation_path is not None and \
        resource.resource_federation_path != ''


def get_path(rtype, rfile, filename, folder=None):
    """
    Copy of hs_core.models.get_path (without model method references)

    Get a path from a ResourceFile, filename, and folder

    :param rfile: instance of ResourceFile to use
    :param filename: file name to use (without folder)
    :param folder: can override folder for ResourceFile instance
    The filename is only a single name. This routine converts it to an absolute
    path that can be federated or local.  The instance points to the Resource record,
    which contains the federation path. The folder in the instance will be used unless
    overridden.

    Note: this does not change the default behavior.
    Thus it can be used to compute a new path for file that
    one wishes to move.
    """
    if not folder:
        folder = rfile.file_folder
    return get_resource_file_path(get_resource_from_rfile(rtype, rfile), filename, folder)


def get_resource_file_path(resource, filename, folder=None):
    """
    Copy of hs_core.models.get_resource_file_path (without model method references)

    Dynamically determine storage path for a FileField based upon whether resource is federated

    :param resource: resource containing the file.
    :param filename: name of file without folder.
    :param folder: folder of file

    The filename is only a single name. This routine converts it to an absolute
    path that can be federated or local. The resource contains information on how
    to do this.

    """
    # folder can be absolute pathname; strip qualifications off of folder if necessary
    if folder is not None and folder.startswith(root_path(resource)):
        # TODO: does this now start with /?
        folder = folder[len(root_path(resource)):]
    if folder == '':
        folder = None

    # retrieve federation path -- if any -- from Resource object containing the file
    if filename.startswith(file_path(resource)):
        return filename

    # otherwise, it is an unqualified name.
    if folder is not None:
        # use subfolder
        return os.path.join(file_path(resource), folder, filename)
    else:
        # use root folder
        return os.path.join(file_path(resource), filename)


def root_path(resource):
    """
    Copy of BaseResource.root_path (without model method references)

    Return the root folder of the iRODS structure containing resource files

    Note that this folder doesn't directly contain the resource files;
    They are contained in ./data/contents/* instead.
    """
    if is_federated(resource):
        return os.path.join(resource.resource_federation_path, resource.short_id)
    else:
        return resource.short_id


def file_path(resource):
    """
    Copy of BaseResource.file_path (without model method references)

    Return the file path of the resource. This is the root path plus "data/contents".

    This is the root of the folder structure for resource files.
    """
    return os.path.join(root_path(resource), "data", "contents")


def storage_path(rtype, rfile):
    """
    Copy of ResourceFile.storage_path (without model method references)

    Return the qualified name for a file in the storage hierarchy.
    This is a valid input to S3Storage for manipulating the file.
    The output depends upon whether the S3Storage instance is running
    in federated mode.

    """
    # instance.content_object can be stale after changes.
    # Re-fetch based upon key; bypass type system; it is not relevant
    resource = get_resource_from_rfile(rtype, rfile)
    if is_federated(resource):
        if rfile.resource_file.name is not None:
            print("fed resource: unfed file name is not None: {}"
                  .format(rfile.resource_file.name))
        return rfile.fed_resource_file.name
    else:
        if rfile.fed_resource_file.name is not None:
            print("unfed resource: fed file name is not None: {}"
                  .format(rfile.fed_resource_file.name))
        return rfile.resource_file.name


def set_storage_path(rtype, rfile, path, test_exists=True):
    """
    Copy of ResourceFile.set_storage_path (without model method references)

    Bind this ResourceFile instance to an existing file.

    :param path: the path of the object.
    :param test_exists: if True, test for path existence in iRODS

    Path can be absolute or relative.

        * absolute paths contain full irods path to local or federated object.
        * relative paths start with anything else and can start with optional folder

    :raises ValidationError: if the pathname is inconsistent with resource configuration.
    It is rather important that applications call this rather than simply calling
    resource_file = "text path" because it takes the trouble of making that path
    fully qualified so that S3Storage will work properly.

    This records file_folder for future possible uploads and searches.

    The heavy lifting in this routine is accomplished via path_is_acceptable and get_path,
    which together normalize the file name.  Regardless of whether the internal file name
    is qualified or not, this makes it fully qualified from the point of view of the
    S3Storage module.

    """
    folder, base = path_is_acceptable(rtype, rfile, path, test_exists=test_exists)
    rfile.file_folder = folder
    rfile.save()

    # rfile.content_object can be stale after changes. Re-fetch based upon key
    # bypass type system; it is not relevant
    resource = get_resource_from_rfile(rtype, rfile)

    # switch FileFields based upon federation path
    if is_federated(resource):
        rfile.fed_resource_file = get_path(rtype, rfile, base)
        rfile.resource_file = None
    else:
        rfile.fed_resource_file = None
        rfile.resource_file = get_path(rtype, rfile, base)
    rfile.save()


def short_path(rtype, rfile):
    """
    Copy of ResourceFile.short_path (without model method references)

    Return the unqualified path to the file object.

    * This path is invariant of where the object is stored.

    * Thus, it does not change if the resource is moved.

    This is the path that should be used as a key to index things such as file type.
    """
    resource = get_resource_from_rfile(rtype, rfile)
    if is_federated(resource):
        folder, base = path_is_acceptable(rtype, rfile, rfile.fed_resource_file.name,
                                          test_exists=False)
    else:
        folder, base = path_is_acceptable(rtype, rfile, rfile.resource_file.name,
                                          test_exists=False)
    if folder is not None:
        return os.path.join(folder, base)
    else:
        return base


def set_short_path(rtype, rfile, path):
    """
    Copy of ResourceFile.set_short_path (without model method references)

    Set a path to a given path, relative to resource root

    There is some question as to whether the short path should be stored explicitly or
    derived as in short_path above. The latter is computationally expensive but results
    in a single point of truth.
    """
    folder, base = os.path.split(path)
    if folder == "":
        folder = None
    rfile.file_folder = folder  # must precede call to get_path
    resource = get_resource_from_rfile(rtype, rfile)
    if is_federated(resource):
        rfile.resource_file = None
        rfile.fed_resource_file = get_path(rtype, rfile, base)
    else:
        rfile.resource_file = get_path(rtype, rfile, base)
        rfile.fed_resource_file = None
    rfile.save()


def path_is_acceptable(rtype, rfile, path, test_exists=True):
    """
    Copy of ResourceFile.path_is_acceptable (without model method references)

    Determine whether a path is acceptable for this resource file

    Called inside ResourceFile objects to check paths

    :param path: path to test
    :param test_exists: if True, test for path existence in iRODS

    """
    return resource_path_is_acceptable(get_resource_from_rfile(rtype, rfile), path, test_exists)


def resource_path_is_acceptable(resource, path, test_exists=True):
    """
    Determine whether a path is acceptable for this resource file

    Called outside ResourceFile objects or before such an object exists

    :param path: path to test
    :param test_exists: if True, test for path existence in iRODS

    This has the side effect of returning the short path for the resource
    as a folder/filename pair.
    """
    if test_exists:
        storage = get_s3_storage(resource)
    locpath = os.path.join(resource.short_id, "data", "contents") + "/"
    relpath = path
    fedpath = resource.resource_federation_path
    if fedpath and relpath.startswith(fedpath + '/'):
        if test_exists and not storage.exists(path):
            raise ValidationError("Federated path does not exist in irods")
        plen = len(fedpath + '/')
        relpath = relpath[plen:]  # omit /

        # strip resource id from path
        if relpath.startswith(locpath):
            plen = len(locpath)
            relpath = relpath[plen:]  # omit /
        else:
            raise ValidationError("Malformed federated resource path")
    elif path.startswith(locpath):
        # strip optional local path prefix
        if test_exists and not storage.exists(path):
            raise ValidationError("Local path does not exist in irods")
        plen = len(locpath)
        relpath = relpath[plen:]  # strip local prefix, omit /

    # now we have folder/file. We could have gotten this from the input, or
    # from stripping qualification folders. Note that this can contain
    # misnamed header content misinterpreted as a folder unless one tests
    # for existence
    if '/' in relpath:
        folder, base = os.path.split(relpath)
        abspath = get_resource_file_path(resource, base, folder=folder)
        if test_exists and not storage.exists(abspath):
            raise ValidationError("Local path does not exist in irods")
    else:
        folder = None
        base = relpath
        abspath = get_resource_file_path(resource, base, folder=folder)
        if test_exists and not storage.exists(abspath):
            raise ValidationError("Local path does not exist in irods")

    return folder, base


def get_s3_storage(resource):
    """ Copy of BaseResource.get_s3_storage """
    if is_federated(resource):
        return S3Storage("federated")
    else:
        return S3Storage()


def migrate_file_paths(apps, schema_editor):
    """
    Migrate file names to new standard

    This is the actual migration code.
    """
    BaseResource = apps.get_model("hs_core", "BaseResource")
    ResourceFile = apps.get_model("hs_core", "ResourceFile")
    for file in ResourceFile.objects.all():
        found = True  # should check existence.
        count = 0  # should be 1 afterward
        resource = get_resource_from_rfile(BaseResource, file)

        # First, normalize state of each potential file name.
        # In some cases, the word "None" was used instead of the symbol None!
        if file.resource_file.name == "" or \
           file.resource_file.name == "None":
            print("WARNING: resource {} ({}): NULL unfed file name of nonstandard type REPAIRED"
                  .format(resource.short_id, resource.resource_type))
            file.resource_file.name = None
            file.save()
        if file.fed_resource_file.name == "" or \
           file.fed_resource_file.name == "None":
            print("WARNING: resource {} ({}): NULL fed file name of nonstandard type REPAIRED"
                  .format(resource.short_id, resource.resource_type))
            file.fed_resource_file.name = None
            file.save()
        if file.fed_resource_file_name_or_path == "" or \
           file.fed_resource_file_name_or_path == "None":
            print("WARNING: resource {} ({}): NULL fed path of nonstandard type REPAIRED"
                  .format(resource.short_id, resource.resource_type))
            file.fed_resource_file_name_or_path = None
            file.save()

        # go through the options for defining a file
        # check that the file is defined according to one of these.
        # it is an error for the file to differ from the declared type of the resource
        if file.resource_file.name is not None:
            count = count + 1
            path = file.resource_file.name
            # print("found unfederated resource file '{}' in resource '{}'"
            #       .format(file.resource_file.name, resource.short_id))
            if is_federated(resource):
                print("ERROR: unfederated file declared for federated resource {} ({}): {}"
                      .format(resource.short_id, resource.resource_type, file.resource_file.name))
                found = False
                # none of these have been found in the database; no action need be taken
            else:
                if path.startswith(resource.short_id):
                    # fully qualified unfederated name
                    try:
                        folder, base = path_is_acceptable(BaseResource, file, path,
                                                          test_exists=False)
                        if file.file_folder != folder:
                            print("WARNING: declared folder {} is not path folder {} for {} ({})"
                                  .format(str(file.file_folder), str(folder), resource.short_id,
                                          resource.resource_type) + "... REPAIRED")
                            file.file_folder = folder
                            file.save()
                    except ValidationError:
                        print("ERROR: existing path {} is not conformant for {} ({})"
                              .format(path, resource.short_id,
                                      resource.resource_type))
                        found = False

                    # set_storage_path(BaseResource, file, path)  # NOT NEEDED
                    # print("found fully qualified unfederated name '{}'".format(path))
                    # pass
                elif path.startswith("data/contents/"):
                    print("WARNING: path {} starts with extra data header for {} ({}) ...REPAIRING"
                          .format(path, resource.short_id, resource.resource_type))
                    plen = len("data/contents/")
                    path = path[plen:]
                    # set fully qualified path
                    if file.file_folder is None:
                        set_short_path(BaseResource, file, path)
                        # print("found unqualified federated path '{}' qualified to '{}'"
                        #       + " for {} ({})"
                        #       .format(path, storage_path(BaseResource, file),
                        #               resource.short_path, resource.resource_type))
                    else:
                        set_short_path(BaseResource, file, os.path.join(file.file_folder, path))
                        # print("found unqualified federated name '{}'" +
                        #       " with folder '{}' qualified to '{}'"
                        #       .format(path, file.file_folder,
                        #               storage_path(BaseResource, file)))
                else:
                    # unqualified unfederated name
                    folder, base = os.path.split(path)
                    if folder != file.file_folder:
                        print("WARNING: declared folder {} is not path folder {} for {} ({})"
                              .format(str(file.file_folder), str(folder), resource.short_id,
                                      resource.resource_type) + "... REPAIRED")
                        file.file_folder = folder
                        file.save()

                        if file.file_folder is None:
                            set_short_path(BaseResource, file, path)
                            # print("found unqualified unfederated name '{}' qualified to '{}'"
                            #       .format(path, storage_path(BaseResource, file)))
                        else:
                            set_short_path(BaseResource, file, os.path.join(file.file_folder, path))
                            # print("found unqualified unfederated name '{}' with folder"
                            #       + " qualified to '{}'"
                            #       .format(path, storage_path(BaseResource, file)))

        if file.fed_resource_file.name is not None:
            count = count + 1
            if not is_federated(resource):
                print("ERROR: federated file declared for unfederated resource {} ({}): {}"
                      .format(resource.short_id, resource.resource_type, file.resource_file.name))
                if file.resource_file.name is None:  # not found so far
                    print("WARNING: Switching that file to be unfederated so open will work")
                    file.resource_file.name = file.fed_resource_file.name
                    file.fed_resource_file.name = None
                elif file.resource_file.name == file.fed_resource_file.name:
                    print("WARNING: clearing redundant fed_resource_file value")
                    file.fed_resource_file = None
                else:
                    print("ERROR: conflicting filenames {} and {} for same file ({})"
                          .format(file.resource_file.name, file.fed_resource_file.name,
                                  resource.resource_type))
                    found = False
            else:
                path = file.fed_resource_file.name
                if path.startswith(file_path(resource)):
                    # fully qualified federated name
                    try:
                        folder, base = path_is_acceptable(BaseResource, file, path,
                                                          test_exists=False)
                        if file.file_folder != folder:
                            print("WARNING: declared folder {} is not path folder {} for {} ({})"
                                  .format(str(file.file_folder), str(folder), resource.short_id,
                                          resource.resource_type) + "... REPAIRED")
                            file.file_folder = folder
                            file.save()
                    except ValidationError:
                        print("ERROR: existing path {} is not conformant for {} ({})"
                              .format(path, resource.short_id,
                                      resource.resource_type))
                        found = False
                    # set_storage_path(BaseResource, file, path)  # NOT NEEDED
                    # print("found fully qualified federated name '{}'".format(path))
                elif path.startswith(resource.short_id):
                    print("ERROR: unfederated path {} used for federated resource for {} ({})"
                          .format(path, resource.short_id, resource.resource_type))
                    found = False
                    # mediation only required if instances pop up during testing.
                elif path.startswith("/"):
                    print("ERROR: non-conformant full path {} for federated resource {} ({})"
                          .format(path, resource.short_id, resource.resource_type))
                    found = False
                elif path.startswith("data/contents/"):
                    print("WARNING: path {} starts with extra data header for {} ({}) ...REPAIRING"
                          .format(path, resource.short_id, resource.resource_type))
                    plen = len("data/contents/")
                    path = path[plen:]
                    # set fully qualified path
                    if file.file_folder is None:
                        set_short_path(BaseResource, file, path)
                        # print("found unqualified federated path '{}' qualified to '{}'"
                        #       .format(path, storage_path(BaseResource, file)))
                    else:
                        set_short_path(BaseResource, file, os.path.join(file.file_folder, path))
                        print("found unqualified federated name '{}'" +
                              " with folder '{}' qualified to '{}'"
                              .format(path, file.file_folder,
                                      storage_path(BaseResource, file)))

        if file.fed_resource_file_name_or_path is not None:
            count = count + 1
            path = file.fed_resource_file_name_or_path
            if path.startswith('data/contents/'):
                plen = len('data/contents/')
                path = path[plen:]
                print("WARNING: header path stripped from fed name or path: {} for {} ({})"
                      .format(path, resource.short_id, resource.resource_type))
            if not is_federated(resource):
                print("WARNING: federated file name or path" +
                      " declared for unfederated resource {} ({}): {} ...REPAIRING"
                      .format(resource.short_id, resource.resource_type, path))
                if path.startswith(file_path(resource)):
                    set_storage_path(BaseResource, file, path, test_exists=False)
                else:
                    set_short_path(BaseResource, file, path)
            elif file.fed_resource_file.name is not None:
                print("ERROR: federated file for resource {} has two paths: {} and {}"
                      .format(resource.short_id, file.fed_resource_file.name, path))
                # mediation only required if instances pop up during testing.
                found = False
            else:
                # print("text path is '{}' (len is {})".format(path, str(len(path))))
                if path.startswith(file_path(resource)):
                    set_storage_path(BaseResource, file, path, test_exists=False)
                    # print("found fully qualified federated text '{}'".format(path))
                else:
                    set_short_path(BaseResource, file, path)
                    # print("found unqualified federated text '{}' qualified to '{}'"
                    #       .format(path, storage_path(BaseResource, file)))

        if found and count == 1:
            pass
            # This existence test is fouled up by a mangled resource name.
            # Invalid istorage object. A name consisting of spaces is the
            # most likely culprit.
            # istorage = get_s3_storage(resource)
            # if not istorage.exists(storage_path(BaseResource, file)):
            #     print("ERROR: name '{}' does not exist".format(storage_path(BaseResource, file)))
            # else:
            #     # print("name '{}' exists".format(storage_path(BaseResource, file)))
            #     pass
        if not found:
            print("ERROR: no valid file name defined for {} ({})"
                  .format(resource.short_id, resource.resource_type))
        if count > 1:
            print("ERROR: more than one file name declared for resource {} ({})"
                  .format(resource.short_id, resource.resource_type))
            if file.resource_file.name is not None:
                print("   One name is {}".format(file.resource_file.name))
            if file.fed_resource_file.name is not None:
                print("   One name is {}".format(file.fed_resource_file.name))
            if file.fed_resource_file_name_or_path is not None:
                print("   One name is {}".format(file.fed_resource_file_name_or_path))


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0033_resourcefile_attributes'),
    ]

    operations = [
        migrations.RunPython(migrate_file_paths),
    ]
