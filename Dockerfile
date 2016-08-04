FROM mjstealey/hs_docker_base:1.7.2
MAINTAINER Michael J. Stealey <stealey@renci.org>

### Begin - HydroShare Development Image Additions ###
RUN sudo pip install pycrs

WORKDIR /home/docker/
RUN wget http://download.osgeo.org/gdal/2.1.0/gdal-2.1.0.tar.gz
RUN tar xvfz gdal-2.1.0.tar.gz

WORKDIR /home/docker/gdal-2.1.0
RUN ./configure -with-python -with-geos=yes
RUN make
RUN sudo make install
RUN sudo ldconfig

ENV PY_SAX_PARSER=hs_core.xmlparser

### End - HydroShare Development Image Additions ###

USER root
WORKDIR /home/docker/hydroshare

CMD ["/bin/bash"]
