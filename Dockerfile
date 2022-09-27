# This configuration is inspired by: https://luis-sena.medium.com/creating-the-perfect-python-dockerfile-51bdec41f1c8
# using ubuntu LTS latest version
FROM ubuntu:22.04

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /project

# install the prerequisite for adding custom PPAs and add one with python3.9
RUN apt update
RUN apt install --no-install-recommends -y software-properties-common gpg-agent
RUN add-apt-repository -y ppa:deadsnakes/ppa

# install all system libraries to build binaries and packages, create python env and connect to pg database
RUN apt install --no-install-recommends -y python3.9 python3.9-dev python3.9-venv python3-pip python3-wheel build-essential openssl libssl-dev git libpq-dev

# create and activate virtual environment using final folder name to avoid path issues with packages
RUN python3.9 -m venv /project/venv
ENV PATH="/project/venv/bin:$PATH"

# install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir wheel
RUN pip install --no-cache-dir -r requirements.txt

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
