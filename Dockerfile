# Dockerfile de Produção Multi-Estágio

# --- Estágio 1: Build do Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./

RUN npm run build

# --- Estágio 2: Aplicação Final (Python Backend + Frontend Assets) ---
FROM python:3.14-alpine

WORKDIR /app

# Instala dependências de build, pacotes Python e depois limpa.
COPY backend/requirements.txt .
RUN apk add --no-cache --virtual .build-deps build-base python3-dev gcc libc-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Copia o código-fonte do backend
COPY ./backend/src ./src

# Copia o diretório de migrações do banco de dados.
COPY ./backend/migrations ./migrations

# Copia os templates HTML necessários para a geração de relatórios.
COPY ./backend/templates /app/templates

# Copia a documentação estática.
COPY ./docs ./docs

# Copia o ponto de entrada do WSGI
COPY backend/wsgi.py .

# Copia os arquivos estáticos do frontend (gerados no estágio 1) para um diretório na imagem final.
# O initContainer 'frontend-copier' usará este diretório como fonte.
COPY --from=frontend-builder /app/frontend/dist /app/frontend-dist

# Expõe a porta do Gunicorn
EXPOSE 5000

# Define o comando padrão para iniciar a API com Gunicorn.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]