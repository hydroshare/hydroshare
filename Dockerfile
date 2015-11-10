FROM mjstealey/hs_base

WORKDIR /home/docker

# Install iRODS packages
RUN apt-get install -y libssl0.9.8 libfuse2
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-runtime-4.1.5-ubuntu14-x86_64.deb -o irods-runtime.deb
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-icommands-4.1.5-ubuntu14-x86_64.deb -o irods-icommands.deb
RUN sudo dpkg -i irods-runtime.deb irods-icommands.deb
RUN sudo apt-get -f install
RUN pip install -e git+https://github.com/iPlantCollaborativeOpenSource/python-irodsclient.git@master#egg=python-irodsclient

ADD . /home/docker/hydroshare
WORKDIR /home/docker
RUN chown -R docker:docker /home/docker
RUN npm install carto

USER root
WORKDIR /home/docker/hydroshare

RUN rm -rf /tmp/pip-build-root
RUN mkdir -p /var/run/sshd
RUN echo root:docker | chpasswd
RUN sed "s/without-password/yes/g" /etc/ssh/sshd_config > /etc/ssh/sshd_config2
RUN sed "s/UsePAM yes/UsePAM no/g" /etc/ssh/sshd_config2 > /etc/ssh/sshd_config
RUN mkdir -p /home/docker/hydroshare/static/media/.cache
RUN chown -R docker:docker /home/docker
RUN mkdir -p /tmp
RUN chmod 777 /tmp

# Cleanup iRODS install files
WORKDIR /home/docker
RUN rm irods-runtime.deb
RUN rm irods-icommands.deb

# Install test coverage module

RUN pip install coverage==3.7.1
RUN pip install django-oauth-toolkit django-cors-headers

WORKDIR /home/docker/hydroshare

CMD /bin/bash
