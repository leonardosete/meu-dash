# ---- Base Stage ----
FROM python:3.13.8-alpine AS base

# Atualize sistema e force upgrades
RUN apk update && \
    apk upgrade --available && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        musl-dev \
        gcc \
        py3-pip \
        busybox \
    && rm -rf /var/cache/apk/*

# Corrija busybox para última versão disponível
RUN apk add --no-cache --upgrade busybox

# Crie usuário não-root
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
ENV HOME=/home/nonroot

USER nonroot

WORKDIR /app

# Atualize pip e setuptools/wheel para evitar CVE em pip
RUN python -m pip install --upgrade "pip>=25.3" setuptools wheel --user

# Instale dependências
COPY --chown=nonroot:nonroot requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- App Stage ----
FROM python:3.13.8-alpine AS app

WORKDIR /app

RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

RUN mkdir -p /app/data/uploads /app/data/reports && \
    chown -R nonroot:nonroot /app/data

USER nonroot

COPY --from=base /home/nonroot/.local /home/nonroot/.local

ENV PATH=/home/nonroot/.local/bin:$PATH
ENV PYTHONPATH=/home/nonroot/.local/lib/python3.13/site-packages

COPY --chown=nonroot:nonroot src/app.py src/app.py
COPY --chown=nonroot:nonroot src/ src/
COPY --chown=nonroot:nonroot templates/ templates/
COPY --chown=nonroot:nonroot docs/ /app/docs/

EXPOSE 5000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["/bin/sh", "-c", "python -c 'from src.app import app, db; app.app_context().push(); db.create_all()' && gunicorn --bind 0.0.0.0:5000 src.app:app"]
