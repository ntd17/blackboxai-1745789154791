#!/bin/bash

# Production deployment script for Painting Contract System

# Exit on error
set -e

# Configuration
APP_NAME="painting-contract"
DEPLOY_USER="appuser"
DEPLOY_GROUP="appuser"
BASE_DIR="/var/www/${APP_NAME}"
BACKUP_DIR="${BASE_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
ENV_FILE=".env.production"
DOCKER_COMPOSE_PROD="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    }
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found"
        exit 1
    }
}

create_directories() {
    log_info "Creating directory structure..."
    
    # Create necessary directories
    mkdir -p "${BASE_DIR}"/{data,logs,backups}
    mkdir -p "${BASE_DIR}/data"/{ml_models,sqlite,contracts}
    mkdir -p "${BASE_DIR}/logs"/{app,nginx}
    
    # Set permissions
    chown -R ${DEPLOY_USER}:${DEPLOY_GROUP} "${BASE_DIR}"
    chmod -R 755 "${BASE_DIR}"
}

backup_existing() {
    if [ -d "${BASE_DIR}/current" ]; then
        log_info "Backing up existing deployment..."
        
        # Create backup directory
        mkdir -p "${BACKUP_DIR}"
        
        # Backup database
        if [ -f "${BASE_DIR}/data/sqlite/app.db" ]; then
            cp "${BASE_DIR}/data/sqlite/app.db" "${BACKUP_DIR}/app.db"
        fi
        
        # Backup environment file
        if [ -f "${BASE_DIR}/current/.env" ]; then
            cp "${BASE_DIR}/current/.env" "${BACKUP_DIR}/.env"
        fi
        
        # Backup ML models
        if [ -d "${BASE_DIR}/data/ml_models" ]; then
            cp -r "${BASE_DIR}/data/ml_models" "${BACKUP_DIR}/"
        fi
    fi
}

deploy_application() {
    log_info "Deploying application..."
    
    # Copy new files
    mkdir -p "${BASE_DIR}/current"
    cp -r . "${BASE_DIR}/current/"
    
    # Copy environment file
    cp "$ENV_FILE" "${BASE_DIR}/current/.env"
    
    # Set permissions
    chown -R ${DEPLOY_USER}:${DEPLOY_GROUP} "${BASE_DIR}/current"
    chmod -R 755 "${BASE_DIR}/current"
    
    # Build and start containers
    cd "${BASE_DIR}/current"
    docker-compose -f ${DOCKER_COMPOSE_PROD} build
    docker-compose -f ${DOCKER_COMPOSE_PROD} up -d
}

run_migrations() {
    log_info "Running database migrations..."
    
    cd "${BASE_DIR}/current"
    docker-compose -f ${DOCKER_COMPOSE_PROD} exec -T app flask db upgrade
}

check_health() {
    log_info "Checking application health..."
    
    # Wait for application to start
    sleep 10
    
    # Check health endpoint
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
    
    if [ "$HEALTH_CHECK" == "200" ]; then
        log_info "Application is healthy"
    else
        log_error "Health check failed"
        log_info "Checking logs..."
        docker-compose -f ${DOCKER_COMPOSE_PROD} logs app
        exit 1
    fi
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove old backups (keep last 5)
    cd "${BASE_DIR}/backups"
    ls -1t | tail -n +6 | xargs -r rm -rf
    
    # Remove unused Docker images
    docker image prune -f
}

# Main deployment process
main() {
    log_info "Starting deployment of ${APP_NAME}..."
    
    check_requirements
    create_directories
    backup_existing
    deploy_application
    run_migrations
    check_health
    cleanup
    
    log_info "Deployment completed successfully!"
}

# Run main function
main

# Display final instructions
cat << EOF

${GREEN}Deployment completed!${NC}

To verify the deployment:
1. Check the application: http://localhost
2. Check the logs: docker-compose -f ${DOCKER_COMPOSE_PROD} logs -f
3. Monitor the containers: docker-compose -f ${DOCKER_COMPOSE_PROD} ps

To rollback:
1. Stop the containers: docker-compose -f ${DOCKER_COMPOSE_PROD} down
2. Restore from backup: ${BACKUP_DIR}
3. Restart the containers: docker-compose -f ${DOCKER_COMPOSE_PROD} up -d

For support:
- Check the logs in ${BASE_DIR}/logs
- Contact the development team
EOF
