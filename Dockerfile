FROM python:3.8.12-buster AS python-base
MAINTAINER STRV DS Department

RUN apt-get --allow-releaseinfo-change update && apt-get install -y unixodbc-dev

FROM python-base as venv-image

RUN apt-get install -y build-essential g++ tk python-tk python3-tk tk-dev

COPY requirements.txt .

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

FROM python-base AS app-image

COPY --from=venv-image /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/src/app

RUN chown -R nobody /usr/src/app/
RUN usermod --home /tmp nobody

USER nobody

ENV PYTHONPATH=/usr/src/app
