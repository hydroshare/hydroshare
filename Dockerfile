FROM mjstealey/hydroshare_base
MAINTAINER Michael J. Stealey <stealey@renci.org>

USER root
WORKDIR /home/docker

# Install iRODS 4.1.5 packages
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-runtime-4.1.5-ubuntu14-x86_64.deb -o irods-runtime.deb
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.5/ubuntu14/irods-icommands-4.1.5-ubuntu14-x86_64.deb -o irods-icommands.deb
RUN sudo dpkg -i irods-runtime.deb irods-icommands.deb
RUN sudo apt-get -f install
RUN rm irods-runtime.deb irods-icommands.deb

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

CMD /bin/bash
