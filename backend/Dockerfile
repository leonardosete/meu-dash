# ---- Estágio de Build (Builder) ----
FROM python:3.14-alpine AS builder

# Atualiza o sistema e instala as dependências de build
RUN apk update && apk upgrade --available && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        musl-dev \
        gcc

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
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Estágio Final (Final) ----
FROM python:3.14-alpine AS final

# Define o timezone para São Paulo
RUN apk update && apk add --no-cache tzdata
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

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
COPY --chown=nonroot:nonroot src ./src
COPY --chown=nonroot:nonroot migrations ./migrations
COPY --chown=nonroot:nonroot entrypoint.sh .

# Garante que o script de entrypoint seja executável
RUN chmod +x ./entrypoint.sh

EXPOSE 5000

# Impede o Python de criar arquivos .pyc, mantendo a imagem limpa e menor.
ENV PYTHONDONTWRITEBYTECODE=1
# Força a saída de logs (stdout/stderr) a não ter buffer, garantindo que os logs apareçam em tempo real.
ENV PYTHONUNBUFFERED=1

# Define o entrypoint que irá preparar o DB e iniciar a aplicação.
ENTRYPOINT ["./entrypoint.sh"]