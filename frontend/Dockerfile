# ---- Estágio 1: Build ----
# Usa uma imagem Node.js para construir os arquivos estáticos do frontend.
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
# Copia o yarn.lock se existir para garantir uma instalação determinística.
COPY yarn.lock* ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

# ---- Estágio 2: Produção ----
# Usa uma imagem Nginx super leve para servir os arquivos estáticos.
FROM nginx:1.25-alpine AS production

EXPOSE 80
# Copia os arquivos estáticos gerados no estágio de build para o diretório do Nginx.
COPY --from=build /app/dist /usr/share/nginx/html
CMD ["nginx", "-g", "daemon off;"]