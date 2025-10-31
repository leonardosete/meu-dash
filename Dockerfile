# Stage 1: Build do Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build do Backend (sem mudanças aqui)
FROM python:3.10-slim AS backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY migrations/ ./migrations/

# Stage 3: Imagem Final de Produção com Nginx e Gunicorn
FROM python:3.10-slim
WORKDIR /app

# Instala Nginx
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copia a nova e correta configuração do Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copia os artefatos dos stages anteriores
COPY --from=backend-builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=backend-builder /app/backend/ ./
COPY --from=backend-builder /app/migrations/ ./migrations

COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expõe a porta 80 do Nginx
EXPOSE 80

# Comando final simplificado.
# A migração do DB é responsabilidade do initContainer no Kubernetes.
# Este comando apenas inicia os dois serviços: Gunicorn em background e Nginx em foreground.
CMD ["/bin/sh", "-c", "gunicorn --workers 4 --bind 127.0.0.1:5000 'src.app:app' --chdir /app & nginx -g 'daemon off;'"]