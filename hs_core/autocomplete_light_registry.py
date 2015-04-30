import autocomplete_light
from django.contrib.auth.models import User, Group

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields=['username','email','first_name','last_name']
    
    def choice_label(self, choice):
        label = ""

        if choice.first_name:
            label += choice.first_name

        if choice.last_name:
            if choice.first_name:
                label += " "
            label += choice.last_name

        if choice.email:
            if choice.first_name or choice.last_name:
                label += " - "
            label += choice.email

        return label

autocomplete_light.register(User, UserAutocomplete)

autocomplete_light.register(Group,
    search_fields=['name'])
