# ---- Base Stage ----
FROM python:3.13.8-alpine AS base

# ---- Estágio de Build (Builder) ----
FROM python:3.13-alpine AS builder

# Atualize sistema e remova pacotes desnecessários
RUN apk update && apk upgrade --available && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        musl-dev \
        gcc \
        py3-pip \
    && rm -rf /var/cache/apk/*

# Crie usuário não-root
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
ENV HOME=/home/nonroot

# Cria um ambiente virtual e ajusta permissões
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV && chown -R nonroot:nonroot $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
COPY requirements.txt .

# Mude para usuário não-root para instalar dependências no venv (agora com permissão!)
USER nonroot
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ---- Estágio Final (Final) ----
FROM python:3.13-alpine AS final

WORKDIR /app

# Crie usuário não-root para segurança
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

# Copia o ambiente virtual do builder e configura PATH
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Cria diretórios de dados e define permissões
RUN mkdir -p /app/data/uploads /app/data/reports && \
    chown -R nonroot:nonroot /app/data

# Mude para usuário não-root
USER nonroot

# Copia o código da aplicação e o script de entrypoint
COPY --chown=nonroot:nonroot src/ ./src
COPY --chown=nonroot:nonroot templates/ ./templates
COPY --chown=nonroot:nonroot docs/ ./docs
COPY --chown=nonroot:nonroot requirements.txt .

EXPOSE 5000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# O CMD executa a migração do banco de dados e, em seguida, inicia o Gunicorn.
CMD ["/bin/sh", "-c", "python -c 'from src.app import app, db; app.app_context().push(); db.create_all()' && gunicorn --bind 0.0.0.0:5000 src.app:app"]
