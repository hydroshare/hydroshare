FROM python:3.11

WORKDIR /app

RUN wget https://storage.googleapis.com/minio-client-mirror-tmp/mc -O /usr/bin/mc && \
    cp /usr/bin/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/"

COPY ./api /app/api

CMD ["fastapi", "run", "api/main.py", "--port", "80"]
