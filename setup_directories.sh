#!/bin/bash

# Exit on error
set -e

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

# Create base directories
create_directories() {
    log_info "Creating directory structure..."
    
    # Application directories
    mkdir -p app/static/{css,js,img,fonts}
    mkdir -p app/templates/{admin,auth,contracts,errors}
    mkdir -p app/uploads
    
    # Data directories
    mkdir -p data/{ml_models,sqlite,contracts,ganache}
    
    # Apache directories
    mkdir -p apache/{certs,logs}
    
    # Log directories
    mkdir -p logs/{app,apache}
    
    log_info "Directory structure created successfully"
}

# Set up static files structure
setup_static_files() {
    log_info "Setting up static files structure..."
    
    # CSS directories
    mkdir -p app/static/css/{components,layouts,pages}
    touch app/static/css/components/.gitkeep
    touch app/static/css/layouts/.gitkeep
    touch app/static/css/pages/.gitkeep
    
    # JavaScript directories
    mkdir -p app/static/js/{components,utils,vendors}
    touch app/static/js/components/.gitkeep
    touch app/static/js/utils/.gitkeep
    touch app/static/js/vendors/.gitkeep
    
    # Image directories
    mkdir -p app/static/img/{logos,icons,backgrounds}
    touch app/static/img/logos/.gitkeep
    touch app/static/img/icons/.gitkeep
    touch app/static/img/backgrounds/.gitkeep
    
    # Font directory
    touch app/static/fonts/.gitkeep
    
    log_info "Static files structure set up successfully"
}

# Set up template structure
setup_templates() {
    log_info "Setting up template structure..."
    
    # Admin templates
    touch app/templates/admin/{base_admin,dashboard,users,contracts,files}.html
    
    # Auth templates
    touch app/templates/auth/{login,register,forgot_password,reset_password}.html
    
    # Contract templates
    touch app/templates/contracts/{list,view,create,edit}.html
    
    # Error templates
    touch app/templates/errors/{403,404,500}.html
    
    # Base templates
    touch app/templates/{base,index}.html
    
    log_info "Template structure set up successfully"
}

# Set permissions
set_permissions() {
    log_info "Setting file permissions..."
    
    # Set directory permissions
    find . -type d -exec chmod 755 {} \;
    
    # Set file permissions
    find . -type f -exec chmod 644 {} \;
    
    # Make scripts executable
    chmod +x *.sh
    
    # Set data directory permissions
    chmod -R 777 data
    chmod -R 777 logs
    
    log_info "Permissions set successfully"
}

# Create .gitkeep files for empty directories
create_gitkeep_files() {
    log_info "Creating .gitkeep files..."
    
    find . -type d -empty -not -path "*/\.*" -exec touch {}/.gitkeep \;
    
    log_info ".gitkeep files created successfully"
}

# Main function
main() {
    log_info "Starting directory setup..."
    
    create_directories
    setup_static_files
    setup_templates
    set_permissions
    create_gitkeep_files
    
    log_info "Directory setup completed successfully!"
    
    # Display structure
    log_info "Directory structure:"
    tree -L 3 --dirsfirst
}

# Run main function
main
