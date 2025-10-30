# Dockerfile de Produção Multi-Estágio com Nginx + Gunicorn

# --- Estágio 1: Build do Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./

RUN npm run build

# --- Estágio 2: Aplicação Final (Nginx + Gunicorn) ---
FROM python:3.14-alpine

WORKDIR /app

# Copia a configuração do Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Instala Nginx, dependências de build, pacotes Python e depois limpa, tudo em uma única camada.
COPY backend/requirements.txt .
RUN apk add --no-cache nginx curl && \
    apk add --no-cache --virtual .build-deps build-base python3-dev gcc libc-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Copia o código-fonte do backend
COPY ./backend/src ./src

# Copia o diretório de migrações do banco de dados. ESSENCIAL para 'flask db upgrade'.
COPY ./backend/migrations ./migrations

# Copia os templates HTML necessários para a geração de relatórios para o diretório /app/templates.
COPY ./backend/templates /app/templates

# Copia a documentação estática para que possa ser servida pelo backend.
COPY ./docs ./docs

# Copia os arquivos estáticos do frontend (gerados no estágio 1)
# para o diretório que o Nginx irá servir.
COPY --from=frontend-builder /app/frontend/dist /var/www/html

# Garante que o usuário 'nginx' (padrão do Alpine) possa ler os arquivos do frontend.
RUN chown -R nginx:nginx /var/www/html && chmod -R 755 /var/www/html

# Define o comando padrão que será executado quando o contêiner iniciar.
# Usar a "forma exec" (array JSON) é a melhor prática.
# Este comando pode ser completamente sobrescrito pelo Kubernetes,
# o que nos dá flexibilidade para rodar o servidor, migrações, etc.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "src.app:app", "--chdir", "/app"]