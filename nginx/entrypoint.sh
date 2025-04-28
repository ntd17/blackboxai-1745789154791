#!/bin/sh

# Check if SERVER_NAME is set
if [ -z "$SERVER_NAME" ]; then
  echo "Error: SERVER_NAME environment variable is not set."
  exit 1
fi

# Render the Nginx config from template
envsubst '$SERVER_NAME' < /etc/nginx/templates/painting-contract.conf.template > /etc/nginx/conf.d/painting-contract.conf

# Start Nginx in the foreground
exec nginx -g 'daemon off;'
