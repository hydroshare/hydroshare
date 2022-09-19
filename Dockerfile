FROM hydroshare/hs_docker_base:release-1.13
MAINTAINER Phuong Doan pdoan@cuahsi.org

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
# TODO: these installs need to be part of the hs_docker_base image
RUN pip uninstall -y enum34
RUN pip install deepdiff==1.7.0
RUN pip install pytest-cov
RUN pip install --upgrade rdflib==5.0.0
RUN pip install -e git+https://github.com/hydroshare/hsmodels.git@0.5.3#egg=hsmodels
RUN pip install six==1.16.0
RUN pip install sorl-thumbnail==12.8.0
RUN pip install --upgrade Django==3.2.15
RUN pip install --upgrade Mezzanine==5.1.4
RUN pip install --upgrade requests
RUN pip install --upgrade django-security
RUN pip install --upgrade django-braces django-compressor django-appconf django-contrib-comments django-cors-headers django-crispy-forms django-debug-toolbar django-jsonfield django-oauth-toolkit django-robots django-security
RUN pip install --upgrade django-autocomplete-light==3.9.4
RUN pip install --upgrade django-haystack
RUN pip install --upgrade djangorestframework==3.13.1
RUN pip install --upgrade drf-haystack==1.8.11
RUN pip install --upgrade drf-yasg==1.20.0

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
