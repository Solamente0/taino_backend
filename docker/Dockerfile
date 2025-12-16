FROM python:3.11-slim-bullseye as builder
#FROM mhzatwork/django-5-base-req:latest as builder

ENV APP_HOME=/home/app/api

RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONHASHSEED 0

RUN apt-get update && apt-get install -y --no-install-recommends gcc file gettext

RUN pip install --upgrade pip
COPY ./requirements.txt $APP_HOME

RUN pip wheel --no-cache-dir --no-deps --wheel-dir $APP_HOME/wheels -r requirements.txt

###################################
FROM python:3.11-slim-bullseye
#FROM mhzatwork/django-5-base-req:latest

ENV HOME=/home/app
ENV APP_HOME=/home/app/api
RUN mkdir -p $APP_HOME

RUN apt update && apt install -y --no-install-recommends curl file nano gettext bash

RUN groupadd -r app && useradd -m -d $HOME -s /bin/bash -g app app

RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME


COPY --from=builder $APP_HOME/wheels /wheels
COPY --from=builder $APP_HOME/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

COPY . $APP_HOME

#RUN chown -R app:app $APP_HOME
RUN chmod +x /home/app/api/docker/entrypoint.sh

#USER app
EXPOSE 8088


CMD ["/home/app/api/docker/entrypoint.sh"]
