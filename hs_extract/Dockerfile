FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.4

WORKDIR /app

RUN apt-get update
RUN apt-get -y install python3.12
RUN apt-get -y install python3-pip

RUN python -m pip config set global.break-system-packages true

RUN apt-get update
RUN apt-get -y upgrade
RUN curl -1sLf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.deb.sh' | bash
RUN apt install -y redpanda-rpk redpanda-connect

COPY hs_extract/requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY hs_extract/hsextract hs_extract/hsextract
COPY hs_cloudnative_schemas hs_cloudnative_schemas

ENV PYTHONPATH "${PYTHONPATH}:/app/hs_extract/hsextract/:/app/hs_extract/hs_cloudnative_schemas/"

ENTRYPOINT ["rpk", "connect", "run", "--rpc-plugins=/app/hs_extract/extract_metadata_plugin.yaml", "/app/hs_extract/extract_metadata_pipeline.yaml"]