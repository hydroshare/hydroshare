FROM mjstealey/hs_docker_base:1.6.6
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --no-deps django-filter==0.11.0 # Update to 0.12.0 after Django 1.8 upgrade
RUN pip install -U djangorestframework==3.2.5 # 3.3.0+ causes some tests to fail, but 3.2.5 is 1.8 compatible.
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]