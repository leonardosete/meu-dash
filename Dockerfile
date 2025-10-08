# ---- Base Stage ----
FROM python:3.13.8-alpine AS base
# ---- Estágio de Build (Builder) ----
# Usa uma imagem base com ferramentas de compilação para instalar as dependências.
FROM python:3.13-alpine AS builder

# Atualize sistema e remova pacotes desnecessários
RUN apk update && \
    apk upgrade && \
RUN apk update && apk upgrade --available && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        musl-dev \
        gcc \
        py3-pip \
        libffi-dev
    && rm -rf /var/cache/apk/*

# Crie usuário não-root
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
ENV HOME=/home/nonroot
# Cria um ambiente virtual para isolar as dependências
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

USER nonroot
# Atualiza o pip e instala as dependências no ambiente virtual
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
# ---- Estágio Final (App) ----
# Usa uma imagem Alpine limpa e copia apenas o necessário do estágio anterior.
FROM python:3.13-alpine AS app

# Atualize o pip e prepare para install
RUN python -m pip install --upgrade pip setuptools wheel --user
# Cria um usuário não-root para segurança
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot

# Instale dependências
COPY --chown=nonroot:nonroot requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- App Stage ----
FROM python:3.13.8-alpine AS app

WORKDIR /app

# Repita upgrade só se necessário (Alpine é bem enxuto)
RUN addgroup -S nonroot && adduser -S nonroot -G nonroot
# Copia o ambiente virtual com as dependências instaladas do estágio builder
ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

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
# O uso de "/bin/sh -c" permite encadear comandos sem a necessidade de um
# script .sh separado, atendendo aos requisitos de segurança.
CMD ["/bin/sh", "-c", "python -c 'from src.app import app, db; app.app_context().push(); db.create_all()' && gunicorn --bind 0.0.0.0:5000 src.app:app"]
