FROM django-1.11:latest
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip
RUN pip install \
  robot_detection \
  drf-yasg \
  flex \
  swagger_spec_validator \
  django-ipware \
  django-autocomplete-light==2.3.3 \
  django-test-without-migrations \
  django-rest-swagger \
  jsonschema \
  nameparser \
  probablepeople \
  geopy

RUN pip uninstall -y django-inplaceedit
RUN pip install git+https://github.com/theromis/django-inplaceedit.git

RUN pip install --upgrade numpy
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
