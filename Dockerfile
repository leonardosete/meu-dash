# Stage 1: Build do Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build do Backend
FROM python:3.10-slim AS backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY migrations/ ./migrations/

# Stage 3: Imagem Final de Produção com Nginx e Gunicorn
FROM python:3.10-slim
WORKDIR /app

# Instala Nginx e dependências
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copia a configuração do Nginx para o lugar certo no contêiner.
COPY nginx.conf /etc/nginx/nginx.conf

# Copia o código do backend e as dependências do stage de backend
COPY --from=backend-builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=backend-builder /app/backend/ ./backend/
COPY --from=backend-builder /app/migrations/ ./migrations/

# Copia o build do frontend do stage de frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Expõe a porta 80, que é a porta que o Nginx vai escutar
EXPOSE 80

# Define o ponto de entrada e o comando padrão
# O entrypoint garante que o banco de dados seja migrado antes de iniciar.
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["flask db upgrade --directory backend/migrations && gunicorn --workers 4 --bind 127.0.0.1:5000 'backend.src.app:create_app()' --chdir /app/backend & nginx -g 'daemon off;'"]