FROM nginx:1.11
MAINTAINER Phuong Doan <phuongdm79@gmail.com>

COPY . /tmp

RUN cp /tmp/config-files/hs-nginx.conf /etc/nginx/conf.d/default.conf \
    && cp /tmp/config-files/nginx.conf-default /etc/nginx/nginx.conf \
    && groupadd -g SENDFILE_IRODS_GROUP_ID SENDFILE_IRODS_GROUP \
    && echo 'SENDFILE_IRODS_USER:x:SENDFILE_IRODS_USER_ID:SENDFILE_IRODS_GROUP_ID::/home/SENDFILE_IRODS_USER:/bin/bash' >> /etc/passwd

CMD ["nginx", "-g", "daemon off;"]
