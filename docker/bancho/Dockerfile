FROM python:3.11-slim

RUN apt update && apt install -y git curl build-essential python3-dev default-libmysqlclient-dev build-essential pkg-config && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home bancho
WORKDIR /home/bancho
USER bancho

ENV PATH "${PATH}:/home/bancho/.local/bin"

COPY requirements.txt ./
RUN python3.11 -m pip install -r requirements.txt

RUN mkdir /home/bancho/.data

COPY . .

ENTRYPOINT ["python3.11", "main.py"]