

from . import utils
from mezzanine.generic.models import Rating, ThreadedComment
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from hs_core.models import BaseResource
# social API

def endorse_resource(resource_short_id, user, endorse=True):
    """
    Add +1 ratings to a resource if the user has not already done so

    :param resource_short_id: short_id of the resource to be endorsed
    :param user: The user id or username or user instance for the user who is endorsing
    :param endorse: True for a +1.  False to remove any previous endorsement.
    """
    res = utils.get_resource_by_shortkey(resource_short_id)
    user = utils.user_from_id(user)
    # first check this user has not already endorsed this resource
    # then create a Rating object using the res and user
    # when creating the Rating object set the value attribute to 1 (+1)
    resource_type = ContentType.objects.get_for_model(BaseResource)
    rating = Rating.objects.filter(content_type=resource_type, object_pk=res.id, user=user).first()
    # user has not endorsed this resource before
    if not rating and endorse:
        rating = Rating.objects.create(content_object=res, user=user, value=1)
        return rating

    # user has already endorsed this resource - can't endorse twice
    elif rating and endorse:
        return rating

    # user wants to delete his/her endorsement
    elif rating and not endorse:
        rating.delete()


def follow_user(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def delete_follow_user(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def follow_resource(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def delete_follow_resource(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def follow_group(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def delete_follow_group(name):
    """
    NOT IN API DOC
    """
    raise NotImplemented()


def comment_on_resource(resource_short_id, comment, user, in_reply_to=None):
    """
    Add a comment to a resource or in reply to another comment of the resource.

    :param resource_short_id: short_id of the resource to be commented
    :param comment: The text of the comment to add (HTML is allowed)
    :param user: The user id or username (use user_from_id(user) to resolve the object instance)
    :param in_reply_to: Id of the comment to reply to (creates threaded comment)

    :return: The comment instance (ThreadedComment)
    """

    if not isinstance(comment, basestring):
        raise ValueError("Comment was not found to be a string value")

    if len(comment) == 0:
        raise ValueError("No comment was provided")

    res = utils.get_resource_by_shortkey(resource_short_id)
    user = utils.user_from_id(user)
    if in_reply_to:
        try:
            comment_to_reply_to = ThreadedComment.objects.get(pk=in_reply_to)
            if comment_to_reply_to.content_object != res:
                raise ValueError("Invalid in_reply_to comment")

            # one is not allowed to reply to his/her own comment
            if comment_to_reply_to.user == user:
                raise ValueError("One can't reply to his/her own comment")
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist(in_reply_to)

    new_comment = ThreadedComment.objects.create(content_object=res, user=user, comment=comment)
    if in_reply_to:
        new_comment.replied_to = comment_to_reply_to
        new_comment.save()

    return new_comment


def endorse_comment(comment_id, resource_short_id, user, endorse=True):
    """
    Adds a +1 to the comment from the user.  Checks first to make sure the user has not +1'd previously.

    :param comment_id: The comment ID (primary key) of the comment to be endorsed
    :param resource_short_id: short_id of the resource (for user access authorization purposes)
    :param user: The user endorsing the comment. user id, user name or user instance
    :param endorse: True for a +1.  False to remove any previous endorsement.
    :return: The rating instance (Rating)
    """

    resource = utils.get_resource_by_shortkey(resource_short_id)
    user = utils.user_from_id(user)
    comment_to_endorse = ThreadedComment.objects.get(pk=comment_id)

    # check the comment belongs to the specified resource
    if comment_to_endorse.content_object != resource:
        raise ValueError("Comment does not belong to the specified resource")

    # first, make sure the user hasn't already added a rating to this comment.
    comment_type = ContentType.objects.get_for_model(ThreadedComment)
    rating = Rating.objects.filter(content_type=comment_type, object_pk=comment_to_endorse.id, user=user).first()

    # if user has already endorsed and endorse is false, delete the Rating object
    if rating and not endorse:
        rating.delete()
    # user can't endorse the same comment twice -just return the user's existing rating object
    elif rating and endorse:
        return rating
    # if user has not endorsed this comment before and endorse is true then create a new rating object
    elif not rating and endorse:
        rating = Rating.objects.create(content_object=comment_to_endorse, user=user, value=1)
        return rating


def get_comments(resource_short_id):
    """
    Get the list of comment for a resource identified by pid.

    :param resource_short_id: short_id of the resource (for user access authorization purposes)

    """

    # get resource instance
    resource = utils.get_resource_by_shortkey(resource_short_id)

    # get all comments objects of the resource
    comments = ThreadedComment.objects.filter(object_pk=resource.pk)

    return comments


def get_endorsements(for_object):
    """
    Get the list of rating objects for a resource or a comment object.

    :param for_object an object of a resource or a comment

    """

    if isinstance(for_object, BaseResource):
        resource_type = ContentType.objects.get_for_model(BaseResource)
        endorsements = Rating.objects.filter(content_type=resource_type, object_pk=for_object.id)

    elif isinstance(for_object, ThreadedComment):
        comment_type = ContentType.objects.get_for_model(ThreadedComment)
        endorsements = Rating.objects.filter(content_type=comment_type, object_pk=for_object.id)

    return endorsements