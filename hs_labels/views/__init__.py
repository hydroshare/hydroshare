from __future__ import absolute_import
import json

from django.http import HttpResponse

from hs_core.views import authorize


def resource_labeling_action(request, shortkey=None, *args, **kwargs):
    """
    This must be a POST request. The following data needs to be passed as part of the POST request:
    shortkey: Id of the resource (Must be None when the label_type is 'SAVEDLABEL')
    action: resource labeling action - has to be either 'CREATE' or 'DELETE'
    label_type: type of label - one of these: 'LABEL', 'FAVORITE', 'MINE', 'SAVEDLABEL'
    label: a string value required if the label_type is either 'LABEL', 'SAVEDLABEL',
           or 'FOLDER' and action is 'CREATE'

    """
    LABEL = 'LABEL'
    FAVORITE = 'FAVORITE'
    MINE = 'MINE'
    SAVEDLABEL = 'SAVEDLABEL'

    # TODO: clear all labels, clear all saved labels
    res = None
    if shortkey:
        res, _, user = authorize(request, shortkey, view=True, full=True, superuser=True)
    else:
        user = request.user

    action = request.POST['action']

    label_type = request.POST['label_type']
    label = request.POST.get('label', None)
    err_msg = None

    # TODO: Use form for input data validation
    # validate post data
    if not user.is_authenticated():
        err_msg = "Permission denied"
    elif label_type not in (LABEL, FAVORITE, MINE, SAVEDLABEL):
        err_msg = "Invalid type of label"
    elif label_type == LABEL or label_type == SAVEDLABEL:
        if label is None:
            err_msg = "A value for label is missing"
    elif label_type != SAVEDLABEL and shortkey is None:
            err_msg = "Resource ID is missing"

    if err_msg is None:
        try:
            if action == 'CREATE':
                if label_type == LABEL:
                    user.ulabels.label_resource(res, label)
                elif label_type == SAVEDLABEL:
                    user.ulabels.save_label(label)
                elif label_type == FAVORITE:
                    user.ulabels.favorite_resource(res)
                elif label_type == MINE:
                    user.ulabels.claim_resource(res)
            elif action == 'DELETE':
                if label_type == LABEL:
                    user.ulabels.unlabel_resource(res, label)
                elif label_type == SAVEDLABEL:
                    user.ulabels.unsave_label(label)
                elif label_type == FAVORITE:
                    user.ulabels.unfavorite_resource(res)
                elif label_type == MINE:
                    user.ulabels.unclaim_resource(res)
        except Exception as exp:
            err_msg = exp.message

    if err_msg:
        ajax_response_data = {'status': 'error', 'message': err_msg}
    else:
        ajax_response_data = {'status': 'success', 'label_type': label_type, 'action': action,
                              'resource_id': shortkey}

    return HttpResponse(json.dumps(ajax_response_data))
