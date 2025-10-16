# Dockerfile de Produção Multi-Estágio com Nginx + Gunicorn

# --- Estágio 1: Build do Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./

# A URL da API em produção será relativa (ex: /api), pois o Nginx fará o proxy.
ENV VITE_API_BASE_URL=/
RUN npm run build

# --- Estágio 2: Aplicação Final (Nginx + Gunicorn) ---
FROM python:3.14-alpine

WORKDIR /app

# Instala apenas o Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Instala as dependências do Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do backend
COPY ./backend/src ./src

# Copia os arquivos estáticos do frontend (gerados no estágio 1)
# para o diretório que o Nginx irá servir.
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Garante que o Nginx possa ler os arquivos do frontend
RUN chown -R www-data:www-data /var/www/html && chmod -R 755 /var/www/html

# O comando de inicialização será definido no manifesto do Kubernetes
# para cada contêiner (Nginx e Gunicorn).