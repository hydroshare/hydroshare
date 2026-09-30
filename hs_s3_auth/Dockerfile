FROM python:3.11

WORKDIR /app

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/"

COPY ./api /app/api

CMD ["fastapi", "run", "api/main.py", "--port", "80"]
