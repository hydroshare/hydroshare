from ga_resources.utils import get_user, json_or_jsonp
from hs_core.models import GenericResource
from hs_core.hydroshare import get_resource_list
from hs_core.hydroshare.utils import get_resource_types

# def get_resource_list(
#         group=None, user=None, owner=None,
#         from_date=None, to_date=None,
#         start=None, count=None,
#         keywords=None, dc=None,
#         full_text_search=None,
#         published=False,
#         edit_permission=False,
#         public=False,
#         types=None
# ):

def autocomplete(request):
    term = request.GET.get('term')
    resp = []

    types = [t for t in get_resource_types() if term.lower() in t.__name__.lower()]
    resp += [{'label': 'type', 'value': t.__name__, 'id': t.__name__} for t in types]

    # resources = get_resource_list(
    #     full_text_search=term,
    # )

    # todo: users
    # todo: groups
    # todo: other conditions?

    return json_or_jsonp(request, resp)
