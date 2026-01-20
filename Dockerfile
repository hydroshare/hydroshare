FROM hydroshare/hs_docker_base:a73451a
# make sure to update multistage-node dockerfile as well if you update this base image

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN curl https://dl.min.io/client/mc/release/linux-amd64/mc \
    --create-dirs \
    -o $HOME/minio-binaries/mc
RUN mv $HOME/minio-binaries/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

RUN apt-get update
RUN apt-get -y upgrade
RUN curl -1sLf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.deb.sh' | bash
RUN apt install -y redpanda-rpk redpanda-connect jq

RUN pip install redpanda-connect

RUN pip install confluent-kafka

RUN pip install pymongo

RUN pip install django-ninja

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
