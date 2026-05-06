FROM ghcr.io/osgeo/gdal:ubuntu-small-3.11.4

WORKDIR /app

RUN apt-get update
RUN apt-get -y install python3.12
RUN apt-get -y install python3-pip

RUN python -m pip config set global.break-system-packages true

RUN apt-get update
RUN apt-get -y upgrade

RUN curl -O https://dl.min.io/client/mc/release/linux-amd64/mc \
    && chmod +x mc \
    && mv mc /usr/local/bin/

COPY hs_extract/requirements.txt .
RUN pip install -r requirements.txt
RUN rm requirements.txt

COPY hs_extract hs_extract
COPY hs_cloudnative_schemas hs_extract/hs_cloudnative_schemas

ENV PYTHONPATH "${PYTHONPATH}:/app/hs_extract/hsextract/:/app/hs_extract/hs_cloudnative_schemas/:/app:/app/hs_extract"

CMD ["celery", "-A", "hs_extract.celery_app", "worker", "-Q", "extract", "--loglevel=info"]