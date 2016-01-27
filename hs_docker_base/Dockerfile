FROM ubuntu:trusty
MAINTAINER Michael J. Stealey <stealey@renci.org>

# Install base packages and pre-reqs for HydroShare
USER root
RUN apt-get update && apt-get install -y \
    python2.7-mapnik python2.7-scipy python2.7-numpy python2.7-psycopg2 cython python2.7-pysqlite2 \
    nodejs npm python-virtualenv \
    postgresql-9.3 postgresql-client-common postgresql-common postgresql-client-9.3 redis-tools \
    sqlite3 sqlite3-pcre libspatialite-dev libspatialite5 spatialite-bin \
    ssh git libfreetype6 libfreetype6-dev libxml2-dev libxslt-dev libprotobuf-dev \
    python2.7-gdal gdal-bin libgdal-dev gdal-contrib python-pillow protobuf-compiler \
    libtokyocabinet-dev tokyocabinet-bin libreadline-dev ncurses-dev \
    docker.io curl libssl0.9.8 libfuse2 \
    nco netcdf-bin

# Add docker user
RUN useradd -m docker -g docker
RUN echo docker:docker | chpasswd

# Build add-ons and pip install requirements.txt
ADD . /home/docker
WORKDIR /home/docker/pysqlite-2.6.3/
RUN python setup.py install
RUN pip install numexpr==2.4
WORKDIR /home/docker
RUN pip install -r requirements.txt
RUN npm install carto

# Install iRODS 4.1.5 packages
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-runtime-4.1.5-ubuntu14-x86_64.deb -o irods-runtime.deb
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-icommands-4.1.5-ubuntu14-x86_64.deb -o irods-icommands.deb
RUN sudo dpkg -i irods-runtime.deb irods-icommands.deb
RUN sudo apt-get -f install
RUN rm irods-runtime.deb irods-icommands.deb

# Install netcdf4 python
RUN curl -O https://pypi.python.org/packages/source/n/netCDF4/netCDF4-1.1.1.tar.gz
RUN tar -xvzf netCDF4-1.1.1.tar.gz
WORKDIR /home/docker/netCDF4-1.1.1
RUN python setup.py install
WORKDIR /home/docker
RUN rm netCDF4-1.1.1.tar.gz

# Add the hydroshare directory
ADD . /home/docker/hydroshare
RUN chown -R docker:docker /home/docker
WORKDIR /home/docker/hydroshare

# Configure and Cleanup
RUN rm -rf /tmp/pip-build-root
RUN mkdir -p /var/run/sshd
RUN echo root:docker | chpasswd
RUN sed "s/without-password/yes/g" /etc/ssh/sshd_config > /etc/ssh/sshd_config2
RUN sed "s/UsePAM yes/UsePAM no/g" /etc/ssh/sshd_config2 > /etc/ssh/sshd_config
RUN mkdir -p /home/docker/hydroshare/static/media/.cache
RUN chown -R docker:docker /home/docker
RUN mkdir -p /tmp
RUN chmod 777 /tmp
