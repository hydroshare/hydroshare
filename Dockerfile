FROM python:3.9-buster AS hs_docker_base

ENV DEBIAN_FRONTEND noninteractive
ENV PY_SAX_PARSER=hs_core.xmlparser

RUN printf "deb http://deb.debian.org/debian/ buster main\ndeb http://security.debian.org/debian-security buster/updates main" > /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    lsb-release \
    sudo

RUN sudo mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN curl -sL https://deb.nodesource.com/setup_lts.x | sudo -E bash -

COPY docker.list /etc/apt/sources.list.d/
RUN sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 7EA0A9C3F273FCD8

RUN sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
    apt-utils \
    libfuse2 \
    libjpeg62-turbo \
    libjpeg62-turbo-dev \
    binutils \
    libproj-dev \
    gdal-bin \
    build-essential \
    libgdal-dev \
    postgresql-15 \
    postgresql-client-15 \
    git \
    rsync \
    openssh-client \
    openssh-server \
    netcdf-bin \
    supervisor \
    nodejs
RUN npm install -g phantomjs-prebuilt

WORKDIR /

RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal 
RUN export C_INCLUDE_PATH=/usr/include/gdal 
RUN export GEOS_CONFIG=/usr/bin/geos-config 
RUN HDF5_INCDIR=/usr/include/hdf5/serial 
RUN pip install --upgrade pip 
RUN pip install 'setuptools<58.0.0'

RUN wget https://ftp.osuosl.org/pub/osgeo/download/gdal/3.6.2/gdal-3.6.2.tar.gz \
    && tar -xzf gdal-3.6.2.tar.gz \
    && rm gdal-3.6.2.tar.gz

WORKDIR /gdal-3.6.2
RUN ./configure --with-python --with-geos=yes \
    && make \
    && sudo make install \
    && sudo ldconfig
WORKDIR /

# TODO: iROds 4.2.x is holding us to Debian Buster which is EOL. It also requires libssl1.0.0 which is obsolete
# we should upgrade to iRods 4.3, Debian Bullseye, etc but this will require at a minimum, changes to our iinit use in HS
RUN wget http://snapshot.debian.org/archive/debian/20190501T215844Z/pool/main/g/glibc/multiarch-support_2.28-10_amd64.deb
RUN sudo dpkg -i multiarch-support*.deb
RUN wget http://snapshot.debian.org/archive/debian/20170705T160707Z/pool/main/o/openssl/libssl1.0.0_1.0.2l-1%7Ebpo8%2B1_amd64.deb
RUN sudo dpkg -i libssl1.0.0*.deb

# Install iRODS
RUN wget -qO - https://packages.irods.org/irods-signing-key.asc | sudo apt-key add - \
    && echo "deb [arch=amd64] https://packages.irods.org/apt/ bionic main" | \
    sudo tee /etc/apt/sources.list.d/renci-irods.list \
    && sudo apt-get update && sudo apt-get install -y \
    apt-transport-https \
    irods-runtime=4.2.10 \
    irods-icommands=4.2.10

# Removed defusedexpat (as part of upgrade to python 3.9)
# Added defusedxml
# https://docs.python.org/3.9/library/xml.html?highlight=xml#the-defusedxml-package
# https://github.com/python/cpython/issues/82766

# Install pip based packages (due to dependencies some packages need to come first)
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

# Install SSH for remote PyCharm debugging
RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Explicitly set user/group IDs for hydroshare service account
RUN groupadd --system storage-hydro --gid=10000 \
    && useradd --system -g storage-hydro --uid=10000 --shell /bin/bash --home /hydroshare hydro-service
RUN echo 'hydro-service:docker' | chpasswd
ENV DEBIAN_FRONTEND teletype

# set UTF-8 env locale
RUN echo UTF-8/en_US.UTF-8 UTF-8 > /etc/local.gen; locale-gen
# Cleanup
RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*






FROM hs_docker_base

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN pip install django-health-check==3.17.0

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
