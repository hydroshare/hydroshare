FROM nginx:1.11
MAINTAINER Michael J. Stealey <michael.j.stealey@gmail.com>

COPY . /tmp
RUN cp /tmp/config-files/hs-nginx.conf /etc/nginx/conf.d/default.conf \
    && cp /tmp/.htpasswd /etc/nginx/.htpasswd \
    && cp /tmp/docker-entrypoint.sh /docker-entrypoint.sh

# cleanup
RUN rm -rf /tmp/*

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["run"]