# Deployment Guide for Production

## Deploying with Docker and Apache

1. Build and start the production containers:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

2. Verify that the containers are running:

```bash
docker ps
```

3. Apache is configured to serve the Flask app and handle SSL termination.

## Generating SSL Certificates with Let's Encrypt

1. Install Certbot on your server.

2. Run Certbot to obtain certificates:

```bash
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com
```

3. Follow the prompts to complete the SSL setup.

4. Certbot will automatically configure Apache to use the certificates.

## Notes

- Ensure ports 80 and 443 are open on your server.
- Renew certificates automatically with:

```bash
sudo certbot renew --dry-run
```

- Check Apache configuration files in the `apache/` directory for custom settings.

![Deployment](https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg)
