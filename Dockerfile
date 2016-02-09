FROM mjstealey/hs_docker_base:1.6.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

RUN pip install -U pip
RUN pip uninstall -y django-celery
RUN pip uninstall -y Mezzanine Django
RUN pip install Django==1.8.9 Mezzanine==4.1.0
### Begin - HydroShare Development Image Additions ###
RUN pip install -U pylint==1.5.0
RUN pip install -U OWSLib==0.10.3
RUN pip install -U kombu==3.0.33
RUN pip install -U celery==3.1.20
### ^^^ from existing
RUN apt-get install -y fuse
RUN pip install --no-deps -U django-appconf
RUN pip install --no-deps -U django-autocomplete-light==2.3.3
RUN pip install --no-deps -U django-braces
RUN pip install --no-deps -U django-cors-headers
RUN pip install --no-deps -U django-crispy-forms
RUN pip install --no-deps -U django-debug-toolbar
RUN pip install --no-deps -U django-extensions
RUN pip install --no-deps -U django-filter
RUN pip install --no-deps -U django-haystack
RUN pip install --no-deps -U django-inplaceedit
RUN pip install --no-deps -U django-jenkins
RUN pip install --no-deps -U django-jsonfield
RUN pip install --no-deps -U django-nose
RUN pip install --no-deps -U django-oauth-toolkit
RUN pip install --no-deps -U django-picklefield
RUN pip install --no-deps -U django-timedeltafield
RUN pip install --no-deps -U django-widget-tweaks
RUN pip install --no-deps -U djangorestframework
RUN pip install --no-deps -U django-contrib-comments


### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]