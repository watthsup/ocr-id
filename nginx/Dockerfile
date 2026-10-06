# ==============================================================================
# Reverse Proxy Gateway Nginx for Thai ID Card OCR & KIE Service
# ==============================================================================
FROM nginx:alpine

# Remove default configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy reverse proxy gateway configuration
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
