FROM python:3.11

WORKDIR /app

RUN curl https://dl.min.io/client/mc/release/linux-amd64/archive/mc.RELEASE.2025-03-12T17-29-24Z -o /usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/"

COPY ./api /app/api

CMD ["fastapi", "run", "api/main.py", "--port", "80"]
