FROM hydroshare/hs_docker_base:release-1.13
MAINTAINER Phuong Doan pdoan@cuahsi.org

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
# TODO: these installs need to be part of the hs_docker_base image
RUN pip uninstall -y enum34
RUN pip install deepdiff==1.7.0
RUN pip install pytest-cov==3.0.0
RUN pip install --upgrade rdflib==5.0.0
RUN pip install -e git+https://github.com/hydroshare/hsmodels.git@0.5.3#egg=hsmodels
RUN pip install six==1.16.0
RUN pip install sorl-thumbnail==12.8.0
RUN pip install --upgrade Django==3.2.15
RUN pip install --upgrade Mezzanine==5.1.4
RUN pip install --upgrade requests==2.17.1
RUN pip install --upgrade django-security==0.12.0
RUN pip install --upgrade django-braces==1.15.0 django-compressor==4.1 django-appconf==1.0.5 django-contrib-comments==2.2.0 django-cors-headers==3.10.1 django-crispy-forms==1.13.0 django-debug-toolbar==3.2.4 django-jsonfield==1.4.1 django-oauth-toolkit==2.1.0 django-robots==4.0
RUN pip install --upgrade django-autocomplete-light==2.3.6
RUN pip install --upgrade django-haystack==3.1.1
RUN pip install --upgrade djangorestframework==3.13.1
RUN pip install --upgrade drf-haystack==1.8.11
RUN pip install --upgrade drf-yasg==1.20.0

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
