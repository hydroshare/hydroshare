FROM node:14.14.0 as node-build
# When running local development, optionally comment out this build step to save build time
# the hs_discover directory will be mounted in local-dev.yml and would override the built files

COPY ./hs_discover /hs_discover

WORKDIR /hs_discover

RUN rm -rf static templates && \
    mkdir static templates && \
    mkdir templates/hs_discover && \
    npm install && \
    npm run build && \
    cp -rp templates/hs_discover/js static/ && \
    cp -rp templates/hs_discover/css static/ && \
    cp -p templates/hs_discover/map.js static/js/ && \
    rm -rf node_modules

FROM hydroshare/hs_docker_base:42e31f1

COPY . /hydroshare
RUN cd /hydroshare && rm -rf hs_discover

COPY --from=node-build /hs_discover /hydroshare/hs_discover

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]