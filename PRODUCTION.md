# Production Deployment Guide

This guide covers deploying the Painting Contract System in a production environment using Apache with mod_wsgi.

## Prerequisites

1. Server Requirements:
   ```
   - Ubuntu 20.04 LTS or newer
   - Python 3.9+
   - Apache 2.4+
   - mod_wsgi
   - Let's Encrypt (for SSL)
   ```

2. Required Apache Modules:
   ```bash
   sudo a2enmod ssl
   sudo a2enmod rewrite
   sudo a2enmod headers
   sudo a2enmod wsgi
   ```

## Installation Steps

1. Install System Dependencies:
   ```bash
   # Update system
   sudo apt update
   sudo apt upgrade -y

   # Install required packages
   sudo apt install -y python3-pip python3-venv apache2 libapache2-mod-wsgi-py3 certbot python3-certbot-apache
   ```

2. Create Project Directory:
   ```bash
   sudo mkdir -p /var/www/painting-contract
   sudo chown -R www-data:www-data /var/www/painting-contract
   ```

3. Set Up Virtual Environment:
   ```bash
   cd /var/www/painting-contract
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Configure Environment Variables:
   ```bash
   # Create production .env file
   cp .env.example .env
   
   # Edit with production values
   nano .env
   ```

5. Initialize Database:
   ```bash
   flask db upgrade
   ```

6. Set Up SSL Certificate:
   ```bash
   sudo certbot --apache -d your-domain.com
   ```

7. Configure Apache:
   ```bash
   # Copy Apache configuration
   sudo cp apache/painting-contract.conf /etc/apache2/sites-available/

   # Edit configuration with correct paths
   sudo nano /etc/apache2/sites-available/painting-contract.conf

   # Enable site
   sudo a2ensite painting-contract.conf
   sudo systemctl restart apache2
   ```

## Security Considerations

1. File Permissions:
   ```bash
   # Set correct permissions
   sudo chown -R www-data:www-data /var/www/painting-contract
   sudo chmod -R 755 /var/www/painting-contract
   sudo chmod 640 /var/www/painting-contract/.env
   ```

2. Firewall Configuration:
   ```bash
   # Allow only necessary ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

3. SSL Configuration:
   - Enable HSTS
   - Use strong SSL ciphers
   - Regular certificate renewal

4. Database Security:
   - Use strong passwords
   - Regular backups
   - Limited network access

## Monitoring & Maintenance

1. Log Files:
   ```bash
   # Apache logs
   tail -f /var/log/apache2/painting-contract-error.log
   tail -f /var/log/apache2/painting-contract-access.log

   # Application logs
   tail -f /var/www/painting-contract/logs/app.log
   ```

2. Regular Maintenance:
   ```bash
   # Update SSL certificates
   sudo certbot renew

   # Update system packages
   sudo apt update
   sudo apt upgrade

   # Backup database
   ./backup_db.sh
   ```

3. Health Checks:
   - Monitor /health endpoint
   - Set up uptime monitoring
   - Configure error notifications

## Performance Optimization

1. Apache Configuration:
   - Enable HTTP/2
   - Configure worker MPM
   - Enable compression
   - Set up caching

2. Database Optimization:
   - Regular vacuum
   - Index optimization
   - Query optimization

3. Static Files:
   - Use CDN for static assets
   - Enable browser caching
   - Compress static files

## Backup & Recovery

1. Database Backups:
   ```bash
   # Set up daily backups
   sudo nano /etc/cron.daily/backup-painting-contract
   ```

2. File Backups:
   - Regular backups of uploaded files
   - Configuration backup
   - SSL certificate backup

3. Recovery Procedures:
   - Document recovery steps
   - Test recovery regularly
   - Maintain backup logs

## Scaling Considerations

1. Load Balancing:
   - Configure multiple app servers
   - Set up load balancer
   - Session management

2. Database Scaling:
   - Connection pooling
   - Read replicas
   - Sharding strategy

3. Caching:
   - Redis/Memcached setup
   - Cache invalidation
   - Cache warming

## Troubleshooting

Common issues and solutions:

1. 500 Internal Server Error:
   - Check Apache error logs
   - Verify permissions
   - Check WSGI configuration

2. SSL Certificate Issues:
   - Verify certificate renewal
   - Check SSL configuration
   - Update SSL settings

3. Performance Issues:
   - Monitor resource usage
   - Check slow queries
   - Analyze access patterns

## Contact & Support

For production support:
- Email: support@your-domain.com
- Emergency: +1-XXX-XXX-XXXX
- Documentation: https://docs.your-domain.com

## License

[Your License Information]
