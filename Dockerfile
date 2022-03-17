FROM hydroshare/hs_docker_base:release-1.13
MAINTAINER Phuong Doan pdoan@cuahsi.org

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
# TODO: these installs need to be part of the hs_docker_base image
RUN pip install deepdiff pytest-cov hsmodels
RUN pip install --upgrade rdflib==5.0.0
RUN pip install --upgrade Django==2.2.27
RUN pip install --upgrade Mezzanine==5.0.0
RUN pip install --upgrade requests
RUN pip install --upgrade django-security==0.12.0
RUN pip install --upgrade django-braces==1.15.0 django-compressor==3.1 django-appconf==1.0.5 django-contrib-comments==2.2.0 django-cors-headers==3.10.1 django-crispy-forms==1.13.0 django-debug-toolbar==3.2.4 django-jsonfield==1.4.1 django-oauth-toolkit==1.7.0 django-robots==4.0 django-security==0.12.0
RUN pip install --upgrade django-autocomplete-light==3.9.4
RUN pip install --upgrade git+https://github.com/sblack-usu/django-inplaceedit.git@c5b8a84fc3ebe1ddab6fe6e9767bdb35d438a371
RUN pip install --upgrade django-haystack==2.8.1

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
