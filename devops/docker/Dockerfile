# --- ESTÁGIO 1: Build da Aplicação React + Vite ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY site/package*.json ./
RUN npm ci
COPY site/ ./
RUN npm run build

# --- ESTÁGIO 2: Servidor Web Seguro (Non-Root) ---
FROM nginxinc/nginx-unprivileged:alpine-slim
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 8080
USER 10001
CMD ["nginx", "-g", "daemon off;"]