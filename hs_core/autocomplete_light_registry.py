from dal import autocomplete
from django.contrib.auth.models import Group, User
from django.db.models import Q


class UserAutocompleteView(autocomplete.Select2QuerySetView):
    search_fields = ["username", "first_name", "last_name"]

    def get_queryset(self):
        qs = User.objects.filter(is_active=True)

        if self.q:
            qs = qs.filter(
                Q(username__istartswith=self.q)
                | Q(first_name__istartswith=self.q)
                | Q(last_name__istartswith=self.q)
            )
            return qs

        return qs

    def get_result_label(self, item):
        label = " ".join(
            [
                item.first_name or "",
                item.userprofile.middle_name or "",
                item.last_name or "",
            ]
        )

        if item.userprofile.organization:
            if item.first_name or item.last_name:
                label += ", "
            label += item.userprofile.organization

        if item.username:
            label += "".join([" (", item.username, ")"])

        return label


class GroupAutocompleteView(autocomplete.Select2QuerySetView):
    search_fields = ["name"]

    def get_queryset(self):
        qs = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")

        if self.q:
            qs = qs.filter(name__istartswith=self.q)
            return qs

        return qs
