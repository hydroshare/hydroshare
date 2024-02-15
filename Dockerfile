FROM hydroshare/hs_docker_base:0bc6b1d

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN pip install django==4.2.*
RUN pip install djangorestframework==3.14.*
RUN pip install django-haystack==3.2.*
RUN pip install drf-yasg==1.21.*
RUN pip install django-robots==6.1
RUN pip install django-autocomplete-light==3.9.*
RUN pip install django-widget-tweaks==1.5.*
RUN pip install django-crispy-forms==2.1
RUN pip install crispy-bootstrap3==2024.1
RUN pip install Mezzanine==6.0.0
RUN pip install mozilla-django-oidc
RUN pip install spam_patterns@git+https://github.com/CUAHSI/spam_patterns.git@0.0.4
RUN pip install freezegun

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
