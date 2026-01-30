# syntax=docker/dockerfile:1.4
# Multi-stage build for Flutter mobile app with BuildKit cache mounts
FROM cirrusci/flutter:3.10.0 AS build

# Copy files to container and build with cache mounts
WORKDIR /app

# Cache pub packages
COPY pubspec.* ./
RUN --mount=type=cache,target=/root/.pub-cache \
    flutter pub get

# Copy source code and build
COPY . .
RUN --mount=type=cache,target=/root/.pub-cache \
    flutter build apk --release

# Production image - minimal nginx alpine
FROM nginx:alpine AS runner

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built APK
COPY --from=build /app/build/app/outputs/flutter-apk/app-release.apk /usr/share/nginx/html/app-release.apk

# Copy nginx configuration for static file serving
RUN printf 'server {\n    listen 80;\n    server_name _;\n    root /usr/share/nginx/html;\n    index index.html;\n    location / {\n        try_files $uri $uri/ =404;\n    }\n    location /app-release.apk {\n        add_header Content-Type application/vnd.android.package-archive;\n        add_header Content-Disposition "attachment; filename=jobswipe.apk";\n    }\n}' > /etc/nginx/conf.d/default.conf

# Security hardening
RUN chown -R nginx:nginx /usr/share/nginx/html /etc/nginx/conf.d
RUN chmod 755 /usr/share/nginx/html
RUN chmod 644 /usr/share/nginx/html/app-release.apk
RUN chmod 644 /etc/nginx/conf.d/default.conf

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
