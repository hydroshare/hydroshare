from autocomplete_light import shortcuts as autocomplete_light
from django.contrib.auth.models import User, Group

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields = ['username', 'first_name', 'last_name']
    split_words = True

    def choices_for_request(self):
        self.choices = self.choices.filter(is_active=True)
        return super(UserAutocomplete, self).choices_for_request()

    def choice_label(self, choice):
        label = ""

        if choice.first_name:
            label += choice.first_name

        if choice.last_name:
            if choice.first_name:
                label += " "
            label += choice.last_name

        if choice.userprofile.organization:
            if choice.first_name or choice.last_name:
                label += ", "
            label += choice.userprofile.organization

        if choice.username:
            label += "".join([" (", choice.username, ")"])

        return label

autocomplete_light.register(User, UserAutocomplete)


class GroupAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields=['name']

    def choices_for_request(self):
        self.choices = self.choices.filter(gaccess__active=True).exclude(name='Hydroshare Author')
        return super(GroupAutocomplete, self).choices_for_request()

autocomplete_light.register(Group, GroupAutocomplete)

