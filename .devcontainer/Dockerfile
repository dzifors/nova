FROM python:3.11

RUN apt update && apt install -y git curl build-essential python3-dev default-libmysqlclient-dev build-essential pkg-config && rm -rf /var/lib/apt/lists/*

ENV PATH "${PATH}:/home/bancho/.local/bin"

WORKDIR /bancho

RUN python3.11 -m pip install --upgrade pip

ADD ./requirements.txt /bancho/requirements.txt

RUN python3.11 -m pip install --upgrade pip

RUN python3.11 -m pip install -r requirements.txt