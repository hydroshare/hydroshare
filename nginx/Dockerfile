FROM nginx:1.19
MAINTAINER Michael J. Stealey <michael.j.stealey@gmail.com>

COPY . /tmp
RUN cp /tmp/config-files/hs-nginx.conf /etc/nginx/conf.d/default.conf \
    && cp /tmp/config-files/nginx.conf-default /etc/nginx/nginx.conf \
    && cp /tmp/.htpasswd /etc/nginx/.htpasswd \
    && cp /tmp/docker-entrypoint.sh /docker-entrypoint.sh \
    && groupadd -g 998 irods \
    && echo 'irods:x:998:998::/home/irods:/bin/bash' >> /etc/passwd

# cleanup - rm from tmp began failing on 4/9/17 for some reason
#RUN rm -rf /tmp/*

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["run"]

