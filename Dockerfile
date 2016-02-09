FROM new_hs_base
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install -U pip
#RUN pip install -U pylint==1.5.0
#RUN pip install -U OWSLib==0.10.3
#RUN pip install -U django-nose==1.4.3
#RUN pip install -U django-debug-toolbar==1.4.0
RUN pip install -U django-appconf
RUN pip install -U django-autocomplete-light
RUN pip install -U django-braces
RUN pip install -U django-cors-headers
RUN pip install -U django-crispy-forms
RUN pip install -U django-debug-toolbar
RUN pip install -U django-extensions
RUN pip install -U django-filter
RUN pip install -U django-haystack
RUN pip install -U django-inplaceedit
RUN pip install -U django-jenkins
RUN pip install -U django-jsonfield
RUN pip install -U django-nose
RUN pip install -U django-oauth-toolkit
RUN pip install -U django-picklefield
#django-tastypie
#django-tastypie-swagger
RUN pip install -U django-timedeltafield
RUN pip install -U django-widget-tweaks
RUN pip install -U djangorestframework
RUN pip install -U django-contrib-comments

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]