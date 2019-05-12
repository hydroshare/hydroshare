FROM nginx:1.11
MAINTAINER Michael J. Stealey <michael.j.stealey@gmail.com>

COPY . /tmp
RUN cp /tmp/config-files/hs-nginx.conf /etc/nginx/conf.d/default.conf \
    && cp /tmp/config-files/nginx.conf-default /etc/nginx/nginx.conf \
    && cp /tmp/.htpasswd /etc/nginx/.htpasswd \
    && cp /tmp/docker-entrypoint.sh /docker-entrypoint.sh \
    && groupadd -g SENDFILE_IRODS_GROUP_ID SENDFILE_IRODS_GROUP \
    && echo 'SENDFILE_IRODS_USER:x:SENDFILE_IRODS_USER_ID:SENDFILE_IRODS_GROUP_ID::/home/SENDFILE_IRODS_USER:/bin/bash' >> /etc/passwd

# cleanup - rm from tmp began failing on 4/9/17 for some reason
#RUN rm -rf /tmp/*

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["run"]

