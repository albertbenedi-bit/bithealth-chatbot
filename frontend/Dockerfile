# ---- Build Stage ----
# Build the React application
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of the source code and build the app
COPY . .
RUN npm run build

# ---- Production Stage ----
# Serve the built app with Nginx
FROM nginx:1.29.0-alpine

# Copy the static files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
# Ensure the script has Unix-style line endings (LF) instead of Windows (CRLF).
# This prevents the "no such file or directory" error when running in a Linux container.
RUN sed -i 's/\r$//' /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]