FROM node:14.14.0 as node-build

ADD . /hydroshare

WORKDIR /hydroshare/hs_discover

RUN rm -rf static templates && \
    mkdir static templates && \
    mkdir templates/hs_discover && \
    mkdir static/js && \
    mkdir static/css && \
    npm install && \
    npm run build && \
    mkdir -p static/js && \
    mkdir -p static/css && \
    cp -rp templates/hs_discover/js static/ && \
    cp -rp templates/hs_discover/css static/ && \
    cp -p templates/hs_discover/map.js static/js/ && \
    echo "----------------js--------------------" && \
    ls -l static/js && \
    echo "--------------------------------------" && \
    echo "----------------css-------------------" && \
    ls -l static/css && \
    echo "--------------------------------------" && \
    cd static/ && \
    cp js/app.*.js js/app.js && \
    cp js/chunk-vendors.*.js js/chunk-vendors.js

FROM hydroshare/hs_docker_base:0bc6b1d

COPY --from=node-build /hydroshare /hydroshare

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN pip install mozilla-django-oidc
RUN pip install spam_patterns@git+https://github.com/CUAHSI/spam_patterns.git@0.0.4
RUN pip install freezegun

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]