import autocomplete_light
from django.contrib.auth.models import User, Group

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    search_fields=['username','email','first_name','last_name']
    
    def choice_label(self, choice):
        if (choice.first_name + choice.last_name) and choice.email:
            return choice.first_name + " " + choice.last_name + " - " + choice.email
        return choice.email

autocomplete_light.register(User, UserAutocomplete)

autocomplete_light.register(Group,
    search_fields=['name'])
