FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1 \
	PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends gcc libpq-dev curl \
	&& rm -rf /var/lib/apt/lists/*

COPY config/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
	&& pip install -r /tmp/requirements.txt \
	&& rm -f /tmp/requirements.txt

COPY . /app