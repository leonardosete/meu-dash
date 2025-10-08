FROM python:3.13.8-alpine AS base
# ---- Estágio de Build (Builder) ----
# Usa uma imagem base com ferramentas de compilação para instalar as dependências.
FROM python:3.13-alpine AS builder

RUN apk update && \
    apk upgrade --available && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        musl-dev \
        gcc \
        py3-pip \
        busybox \
        libffi-dev
    && rm -rf /var/cache/apk/*

RUN python -m pip install --upgrade pip setuptools wheel --user
# Cria um ambiente virtual para isolar as dependências
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
ENV HOME=/home/nonroot
# Atualiza o pip e instala as dependências no ambiente virtual
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER nonroot
# ---- Estágio Final (App) ----
# Usa uma imagem Alpine limpa e copia apenas o necessário do estágio anterior.
FROM python:3.13-alpine AS app

WORKDIR /app

COPY --chown=nonroot:nonroot requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
# Cria um usuário não-root para segurança
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

# Copia o ambiente virtual com as dependências instaladas do estágio builder
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

FROM python:3.13.8-alpine AS app

WORKDIR /app

RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

# Cria diretórios de dados e define permissões
RUN mkdir -p /app/data/uploads /app/data/reports && \
    chown -R nonroot:nonroot /app/data

USER nonroot
# Copia o código da aplicação e o script de entrypoint
COPY --chown=nonroot:nonroot src/ ./src
COPY --chown=nonroot:nonroot templates/ ./templates
COPY --chown=nonroot:nonroot docs/ ./docs

EXPOSE 5000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER nonroot

# O CMD executa a migração do banco de dados e, em seguida, inicia o Gunicorn.
# Isso é feito em um único comando para evitar a necessidade de um script de entrypoint.
CMD ["/bin/sh", "-c", "python -c 'from src.app import app, db; app.app_context().push(); db.create_all()' && gunicorn --bind 0.0.0.0:5000 src.app:app"]
