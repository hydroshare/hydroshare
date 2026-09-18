FROM hydroshare/hs_docker_base:bf8a7e3

ADD . /hydroshare

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

COPY --from=quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z-cpuv1 /usr/bin/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

RUN apt-get update
RUN apt-get -y upgrade
RUN pip install pymongo

RUN pip install django-rest-knox

# installs specific commit until hsmodels gets a full release
RUN pip install --upgrade git+https://github.com/hydroshare/hsmodels.git@22b7d610814a28065511ff03ba044ad66cc1bc98

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
