from ga_resources.utils import get_user, json_or_jsonp
from hs_core.models import GenericResource, Party, Contributor, Creator
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

    # Party calculations are expensive and complicated. Deferring to focus on lower hanging fruit
    #
    parties = []
    def get_party_type(party):
        if Contributor.objects.filter(id=party.id).exists():
            return 'Contributor'
        elif Creator.objects.filter(id=party.id).exists():
            return 'Author'
        else:
            return None
    for model in (Creator, Contributor):
        for party in model.objects.filter(name__istartswith=term) | model.objects.filter(email__istartswith=term):
            party_type = get_party_type(party)
            if party_type:
                name = model.__name__
                if model is Creator:
                    name = "Author"
                resp.append({
                    'label': name,
                    'type': 'party',
                    'id': party.email or party.name,
                    'value': party.name,
                })

    # resources = get_resource_list(
    #     full_text_search=term,
    # )

    # todo: users
    # todo: groups
    # todo: other conditions?

    return json_or_jsonp(request, resp)
