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
# ADIÇÃO: Adiciona 'curl' para o HEALTHCHECK
COPY backend/requirements.txt .
RUN apk add --no-cache --virtual .build-deps build-base gcc libc-dev postgresql-dev python3-dev && \
    apk add --no-cache curl postgresql-client && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# ... (todos os seus comandos COPY) ...
COPY ./backend/src ./src
COPY ./backend/migrations ./migrations
COPY ./backend/templates /app/templates
COPY ./docs ./docs
COPY backend/wsgi.py .
COPY --from=frontend-builder /app/frontend/dist /app/frontend-dist

# --- MELHORIA DE SEGURANÇA ---
RUN addgroup -S appgroup && adduser -S appuser -G appgroup && chown -R appuser:appgroup /app
USER appuser
# --- FIM DA MELHORIA ---

# Expõe a porta 5000
EXPOSE 5000

# --- MELHORIA DE QUALIDADE: HEALTHCHECK ---
# Verifica a saúde da aplicação internamente
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://127.0.0.1:5000/health || exit 1
# --- FIM DA MELHORIA ---

# Comando final
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "wsgi:app"]