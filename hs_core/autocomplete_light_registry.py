from dal import autocomplete
from django.contrib.auth.models import Group, User
from django.db.models import Q


class UserAutocompleteView(autocomplete.Select2QuerySetView):
    search_fields = ["username", "first_name", "last_name"]

    def get_queryset(self):
        qs = User.objects.filter(is_active=True)

        if self.q:
            name_parts = self.q.split(" ", 1)
            name_part_one = name_parts[0]
            name_part_two = name_parts[1] if len(name_parts) > 1 else ""
            if name_part_two:
                qs = qs.filter(
                    Q(username__icontains=self.q)
                    | Q(first_name__icontains=name_part_one, last_name__icontains=name_part_two)
                )
            else:
                qs = qs.filter(
                    Q(username__icontains=self.q)
                    | Q(first_name__icontains=name_part_one)
                    | Q(last_name__icontains=name_part_one)
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
            qs = qs.filter(name__icontains=self.q)
            return qs

        return qs
