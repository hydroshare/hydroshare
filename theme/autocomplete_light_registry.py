import autocomplete_light

from .models import Organization


autocomplete_light.register(
    Organization,
    search_fields=('name',),
    split_words=True,
)
