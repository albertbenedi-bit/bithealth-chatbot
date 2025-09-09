#!/bin/sh
set -e

# This script injects runtime environment variables into a configuration file
# for the React application. This allows the same Docker image to be used
# across different environments (dev, staging, production).

echo "Creating runtime config..."

# Create a temporary config file with the environment variables
cat <<EOF > /usr/share/nginx/html/config.js
window.APP_CONFIG = {
  VITE_BACKEND_URL: "${VITE_BACKEND_URL}",
  VITE_APP_NAME: "${VITE_APP_NAME}",
  VITE_ENABLE_MOCK_AUTH: "${VITE_ENABLE_MOCK_AUTH}"
};
EOF

# Start Nginx in the foreground
exec nginx -g 'daemon off;'