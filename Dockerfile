FROM mjstealey/hs_docker_base:1.6.6
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip uninstall -y Django Mezzanine
RUN pip install -U Django==1.8.9
RUN pip install --no-deps Mezzanine==4.1.0
RUN pip install -U nose
RUN pip install --no-deps django-nose==1.4.3
RUN pip install --no-deps django-contrib-comments==1.6.2
RUN pip install --no-deps django-debug-toolbar==1.4.0
RUN pip install --no-deps djangorestframework==3.3.2
### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]