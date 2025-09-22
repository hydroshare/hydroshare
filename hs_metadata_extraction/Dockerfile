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

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY hsextract .
COPY extract_metadata_pipeline.yaml .
COPY extract_metadata_plugin.yaml .
RUN touch __init__.py

ENV PYTHONPATH "${PYTHONPATH}:/app/hsextract/"

ENTRYPOINT ["rpk", "connect", "run", "--rpc-plugins=/app/extract_metadata_plugin.yaml", "/app/extract_metadata_pipeline.yaml"]