from django.views.generic import ListView,DetailView,TemplateView,UpdateView,CreateView
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required

from ..models.person import Person
from ..models.organization import Organization
from ..models.organization_association import OrganizationAssociation

from ..forms.organization_association import OrganizationAssociationEditorForm

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist



#@login_required
class OrganizationAssociationEdit(UpdateView):
    model = OrganizationAssociation
    #template_name = "pages/associations/organization_association_edit.html"
    form_class = OrganizationAssociationEditorForm

#@login_required
class OrganizationAssociationCreate(CreateView):
    model = OrganizationAssociation
    template_name = "pages/associations/organization_association_create.html"
    fields = ["person","organization","jobTitle","beginDate",
              "endDate","presentOrganization"]

class OrganizationAssociationDetail(DetailView):
    model = OrganizationAssociation
    queryset = OrganizationAssociation.objects.select_related().all()
    template_name = "pages/associations/organization_association.html"

    def get_context_data(self, **kwargs):
        context = super(OrganizationAssociationDetail, self).get_context_data(**kwargs)
        #context['now'] = timezone.now()
        return context

    def get_object(self,**kwargs):
        # Call the superclass
        object = super(OrganizationAssociationDetail, self).get_object(**kwargs)
        # Record the last accessed date
        #object.last_accessed = timezone.now()
        #object.save()
        # Return the object
        return object
