# --- Сборка ---
FROM node:20-alpine AS build
WORKDIR /app

# Адрес API для браузера. По умолчанию — backend на хосте (docker compose).
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Раздача статики ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
