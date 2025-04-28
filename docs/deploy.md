# Deployment Guide

This document describes the deployment process for the Painting Contract System, including dynamic domain handling for the webserver.

## Prerequisites

- Docker and Docker Compose installed
- SSL certificates for your domain (placed under `nginx/ssl/live/$SERVER_NAME/`)
- Environment variables configured, including `SERVER_NAME`

## Dynamic Domain Handling

The webserver configuration uses a dynamic domain name via the `SERVER_NAME` environment variable.

### How it works

- Nginx configuration files are templates located in `nginx/templates/`.
- At container startup, the entrypoint script renders these templates with the current `SERVER_NAME`.
- This allows deploying to any domain by simply changing the environment variable without rebuilding images.

### Setting SERVER_NAME

In your `docker-compose.override.yml` or equivalent, set:

```yaml
services:
  nginx:
    environment:
      - SERVER_NAME=your-domain.com
```

Replace `your-domain.com` with your actual domain.

### SSL Certificates

Place your SSL certificates in:

```
nginx/ssl/live/your-domain.com/fullchain.pem
nginx/ssl/live/your-domain.com/privkey.pem
```

### Entrypoint Script

The entrypoint script `nginx/entrypoint.sh` performs the template rendering and starts Nginx.

## Starting the Application

Run:

```bash
docker-compose up -d
```

This will start all services, including the nginx proxy with dynamic domain handling.

## Verifying Deployment

- Access your domain via HTTPS.
- Verify HTTP requests redirect to HTTPS.
- Check logs in `logs/nginx/` for any errors.
- Confirm proxying to the Flask backend works correctly.

## Troubleshooting

- Ensure `SERVER_NAME` is set and matches your SSL certificate domain.
- Check container logs for errors.
- Verify SSL certificate files exist in the expected paths.

## Future Extensions

- Multi-domain support via SAN certificates or wildcards can be added by extending the template and environment variables.
