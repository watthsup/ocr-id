# ==============================================================================
# Production Dockerfile for Thai ID Card Frontend Web Application (React + Vite)
# ==============================================================================

# Stage 1: Build React Production Bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests first for Docker layer caching
COPY package.json package-lock.json ./

# Clean dependency installation
RUN npm ci

# Copy full frontend source code
COPY . .

# Build production assets into /app/dist
RUN npm run build

# Stage 2: Serve Production Assets via Nginx
FROM nginx:alpine AS runner

# Remove default nginx HTML files
RUN rm -rf /usr/share/nginx/html/*

# Copy built production assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy internal Nginx SPA routing and cache configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
