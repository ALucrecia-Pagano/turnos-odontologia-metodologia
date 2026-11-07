# Imagen de desarrollo: Vite con HMR. El código llega por bind mount desde docker-compose.yml.
FROM node:24-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
