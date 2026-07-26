FROM python:3.7-alpine

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /requirements.txt
COPY ./requirements.dev.txt /requirements.dev.txt
COPY ./app /app

WORKDIR /app

EXPOSE 8000

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /requirements.txt && \
    if [ "$DEV" = "true" ]; then \
        /py/bin/pip install -r /requirements.dev.txt; \
    fi && \
    adduser \
        --disabled-password \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

USER django-user