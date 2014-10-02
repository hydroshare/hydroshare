__author__ = 'valentin'

from django.views.generic import ListView,DetailView,TemplateView,UpdateView,CreateView
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from uuid import uuid4

from ..models.person import Person
from ..models.organization import Organization
from ..models.organization_association import OrganizationAssociation
from django.forms.models import inlineformset_factory



from ..forms.person import PersonEditorForm,PersonCreateForm
from ..forms.person import LocationFormSet,EmailFormSet,PhoneFormSet,IdentifierFormSet,NameFormSet
from ..forms.person import OrgAssociationsFormSet


from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
#from ..forms import ScholarForm,ScholarProfileForm,OrgAssociationsForm




class PersonList(ListView):
    model = Person
    #template_name = "pages/person/person_list.html"
    queryset = Person.objects.prefetch_related('primaryOrganizationRecord').all()

    def get_context_data(self, **kwargs):
        context = super(PersonList, self).get_context_data(**kwargs)
        #context['now'] = timezone.now()
        return context

#@login_required
class PersonCreate(CreateView):

    model = Person
    template_name = "pages/person/person_create.html"
    fields = ["name",'givenName','familyName',
             'primaryOrganizationRecord',
            # 'primaryAddress',
              'notes']
    form_class = PersonCreateForm



#@login_required
class PersonEdit(UpdateView):
    model = Person
    #template_name = "pages/person/person_edit.html"
    form_class = PersonEditorForm




    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = Person.objects.select_related().get(pk=self.kwargs['pk'])
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        location_form = LocationFormSet()
        name_form = NameFormSet()
        email_form = EmailFormSet()
        phone_form = PhoneFormSet()
        identifier_form = IdentifierFormSet()
       # orgs_form = OrgAssociationsFormSet(queryset=OrganizationAssociation.objects.filter(person__pk=self.kwargs['pk']),)


        return self.render_to_response(
            self.get_context_data(form=form,
                                  location_form=location_form,
                                  name_form=name_form,
                                  email_form=email_form,
                                  phone_form=phone_form,
                                  identifier_form=identifier_form,
#                                  orgs_form=orgs_form
                                  )
        )

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formsets with the passed POST variables and then checking them for
        validity.
        """
        self.object = Person.objects.select_related().get(pk=self.kwargs['pk'])
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        location_form = LocationFormSet(self.request.POST)
        name_form = NameFormSet(self.request.POST)
        email_form = EmailFormSet(self.request.POST)
        phone_form = PhoneFormSet(self.request.POST)
        identifier_form = IdentifierFormSet(self.request.POST)
#        orgs_form = OrgAssociationsFormSet(self.request.POST)

        if ( form.is_valid() and location_form.is_valid()
        and email_form.is_valid() and name_form.is_valid()
        and phone_form.is_valid() and identifier_form.is_valid()
#        and orgs_form.is_valid()
        ):

            return self.form_valid(form, location_form, email_form, name_form, phone_form, identifier_form
#                                   ,orgs_form
            )
        else:
            return self.form_invalid(form, location_form, email_form, name_form, phone_form, identifier_form
#                                     ,orgs_form
            )

    def form_valid(self, form, location_form, email_form, name_form, phone_form, identifier_form
#                   ,orgs_form
    ):
        """
        Called if all forms are valid. Creates a Recipe instance along with
        associated Ingredients and Instructions and then redirects to a
        success page.
        """
        self.object = form.save()
        location_form.instance = self.object
        location_form.save()
        name_form.instance = self.object
        name_form.save()
        email_form.instance = self.object
        email_form.save()
        phone_form.instance = self.object
        phone_form.save()
        identifier_form.instance = self.object
        identifier_form.save()

#        orgs_form.instance=self.object
#        orgs_form.save()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, location_form, email_form, name_form, phone_form, identifier_form
#                     ,orgs_form
    ):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  location_form=location_form,
                                  name_form=name_form,
                                  email_form=email_form,
                                  phone_form=phone_form,
                                  identifier_form=identifier_form,
#                                  orgs_form=orgs_form
            ))

    pass

class PersonDetail(DetailView):
    model = Person
    # examples of detail view use all()
    queryset = Person.objects.select_related().all()
    #template_name = "pages/person/person.html"

    def get_context_data(self, **kwargs):
        context = super(PersonDetail, self).get_context_data(**kwargs)
        #context['now'] = timezone.now()
        return context

    def get_object(self,**kwargs):
        # Call the superclass
        object = super(PersonDetail, self).get_object(**kwargs)
        # Record the last accessed date
        #object.last_accessed = timezone.now()
        #object.save()
        # Return the object
        return object

