FROM mjstealey/hs_base

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

WORKDIR /home/docker/hydroshare

CMD /bin/bash
