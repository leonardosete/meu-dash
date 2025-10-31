# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
# Use --no-optional to speed up install and reduce image size
RUN npm install --no-optional
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Backend
FROM python:3.10-slim AS backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
# CORREÇÃO: O caminho de origem deve ser 'backend/migrations'
COPY backend/migrations/ ./migrations/

# Stage 3: Imagem Final de Produção com Nginx e Gunicorn
FROM python:3.10-slim
WORKDIR /app
# Instala o Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Copia os artefatos do backend
COPY --from=backend-builder /app/backend ./src
COPY --from=backend-builder /app/migrations ./migrations
COPY --from=backend-builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copia o build do frontend para a pasta de estáticos que o Nginx servirá
COPY --from=frontend-builder /app/dist ./src/static

# Copia as configurações e o ponto de entrada
COPY nginx.conf /etc/nginx/nginx.conf
COPY backend/wsgi.py .

# Define as variáveis de ambiente
ENV FLASK_APP=src.app

EXPOSE 80

# Define um ENTRYPOINT robusto e um CMD padrão
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["gunicorn --workers 4 --bind 127.0.0.1:5000 'src.app:app' --chdir /app & nginx -g 'daemon off;'"]