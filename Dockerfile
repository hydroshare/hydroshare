FROM mjstealey/hs_docker_base:1.9.5
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN pip install --upgrade pip && pip install \
  robot_detection \
  django-ipware \
  django-test-without-migrations

# Patch for Mezzanone 4.10 collecttemplates bugfix
RUN echo -e "\
\n42c42,44\
\n<         to_dir = settings.TEMPLATE_DIRS[0]\
\n---\
\n>         # Mezzanine 4.10 fix for collecttemplates.py\
\n>         # to_dir = settings.TEMPLATE_DIRS[0]\
\n>         to_dir = settings.TEMPLATES[0]["DIRS"][0]\
" | patch /usr/local/lib/python2.7/site-packages/mezzanine/core/management/commands/collecttemplates.py -

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
