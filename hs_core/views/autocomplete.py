from django.contrib.auth.models import User

from hs_core.models import Contributor, Creator, Subject
from hs_core.hydroshare.utils import get_resource_types
from hs_core.views.utils import json_or_jsonp


def autocomplete(request):
    term = request.GET.get("term")
    resp = []

    types = [t for t in get_resource_types() if term.lower() in t.__name__.lower()]
    resp += [{"label": "type", "value": t.__name__, "id": t.__name__} for t in types]

    # Party calculations are expensive and complicated. Deferring to focus on lower hanging fruit
    #

    def get_party_type(party):
        if Contributor.objects.filter(id=party.id).exists():
            return "Contributor"
        elif Creator.objects.filter(id=party.id).exists():
            return "Author"
        else:
            return None

    seen = set()
    filter_types = {
        "name": "name__istartswith",
        "email": "email__iexact",
    }
    for model in (Creator, Contributor):
        for filter_type in filter_types:
            for party in model.objects.filter(**{filter_types[filter_type]: term}):
                party_type = get_party_type(party)
                if party_type:
                    name = model.__name__
                    if model is Creator:
                        name = "Author"
                    if (name, party.name) not in seen:
                        seen.add((name, party.name))
                        resp.append(
                            {
                                "label": name,
                                "type": "party",
                                "id": getattr(party, filter_type, "id"),
                                "value": party.name,
                            }
                        )

    owners = User.objects.filter(username__istartswith=term)
    for owner in owners:
        if owner.first_name and owner.last_name:
            name = "%s %s (%s)" % (owner.first_name, owner.last_name, owner.username)
        elif owner.first_name:
            name = "%s (%s)" % (owner.first_name, owner.username)
        elif owner.last_name:
            name = "%s (%s)" % (owner.last_name, owner.username)
        else:
            name = owner.username
        resp.append(
            {
                "label": "Owner",
                "type": "owner",
                "id": owner.username,
                "value": name,
            }
        )

    subjects = Subject.objects.filter(value__istartswith=term)
    for subject in subjects:
        if ("subject", subject.value) not in seen:
            seen.add(("subject", subject.value))
            resp.append(
                {
                    "label": "Subject",
                    "type": "subject",
                    "id": subject.value,
                    "value": subject.value,
                }
            )

    # todo: users
    # todo: groups
    # todo: other conditions?

    return json_or_jsonp(request, resp)
