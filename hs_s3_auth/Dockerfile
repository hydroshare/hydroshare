FROM python:3.11

WORKDIR /app

COPY --from=quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z-cpuv1 /usr/bin/mc /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/"

COPY ./api /app/api

CMD ["fastapi", "run", "api/main.py", "--port", "80"]
