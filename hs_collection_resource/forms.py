from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import Layout, Field

from models import CollectionItems
from hs_core.forms import BaseFormHelper


class MetadataField(Field):
    def __init__(self, *args, **kwargs):
        kwargs['css_class'] = 'form-control input-sm'
        super(MetadataField, self).__init__(*args, **kwargs)


class CollectionItemsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(MetadataField('collection_items'))
        kwargs['element_name_label'] = 'Collection Items'
        super(CollectionItemsFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout,  *args, **kwargs)
def get_res_id_list(all_res_list):
     if all_res_list is not None:
        return [r.short_id for r in all_res_list]

class CollectionItemsForm(ModelForm):
    collection_items = forms.MultipleChoiceField(choices=[],
                                                    widget=forms.CheckboxSelectMultiple(
                                                        attrs={'style': 'width:auto;margin-top:-5px'}))
    all_res_list = None
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, all_res_list=None, *args, **kwargs):
        try:
            collection_items = kwargs['collection_items']
            kwargs.pop('collection_items')
        except:
            collection_items = None

        super(CollectionItemsForm, self).__init__(*args, **kwargs)
        self.helper = CollectionItemsFormHelper(allow_edit, res_short_id, element_id, element_name='CollectionItems')
        self.all_res_list = all_res_list
        self.fields['collection_items'].choices = self.getChoices()
        if self.instance:
            try:
                collection_items = self.instance.collection_items.all()
                if len(collection_items) > 0:
                    checked_item_list = []
                    for res in collection_items:
                        checked_item_list.append(res.short_id)

                    self.fields['collection_items'].initial = checked_item_list
                else:
                    self.fields['collection_items'].initial = []
            except:
                self.fields['collection_items'].initial = []

    class Meta:
        model = CollectionItems

    def getChoices(self):
        if self.all_res_list is not None:
            return [(r.short_id, r.title + ":" + r.resource_type ) for r in self.all_res_list]




