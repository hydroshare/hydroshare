FROM hydroshare/hs_docker_base:release-1.12
MAINTAINER Phuong Doan pdoan@cuahsi.org

### Begin - HydroShare Development Image Additions ###
RUN pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations \
  django-rest-swagger \
  jsonschema \
  nameparser \
  probablepeople \
  geopy \
  numpy==1.16.0 \
  pandas \
  scikit-learn \
  gensim \
  scipy \
  nltk 
### End - HydroShare Development Image Additions ###
# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec
# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
