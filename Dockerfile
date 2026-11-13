#build the MinIO client from source with patched dependency
FROM golang:1.25 AS mc-build
# Pin to a specific mc commit so builds are reproducible
ARG MC_COMMIT=77f82e18b5401a65958f1619df6ebb994634bd88
RUN git clone https://github.com/minio/mc /src && \
    cd /src && git checkout ${MC_COMMIT}
WORKDIR /src
# Force the fixed x/crypto version (CVE-2026-46595)
RUN go get golang.org/x/crypto@v0.52.0 && go mod tidy
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -trimpath -ldflags "-s -w" -o /out/mc .

FROM hydroshare/hs_docker_base:bf8a7e3

ADD . /hydroshare

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

COPY --from=mc-build /out/mc /usr/local/bin/mc
COPY --from=mc-build /out/mc /usr/bin/mc

RUN apt-get update
RUN apt-get -y upgrade
RUN pip install pymongo
RUN pip install "pillow==13.0.0"

RUN pip install django-rest-knox
RUN pip install django-celery-beat==2.7.0

# installs specific commit until hsmodels gets a full release
RUN pip install --upgrade git+https://github.com/hydroshare/hsmodels.git@22b7d610814a28065511ff03ba044ad66cc1bc98

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
