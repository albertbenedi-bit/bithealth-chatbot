# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the PV Chatbot Frontend application in various environments, from local development to production deployment.

## Prerequisites

### System Requirements

#### Development Environment
- **Node.js**: Version 18.0.0 or higher
- **npm**: Version 8.0.0 or higher (comes with Node.js)
- **Git**: Version 2.20.0 or higher
- **Modern Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

#### Production Environment
- **Web Server**: Nginx, Apache, or similar
- **SSL Certificate**: For HTTPS deployment
- **CDN**: Optional but recommended for static assets
- **Monitoring**: Application monitoring service

### Backend Services

The frontend requires the following backend services to be running:

1. **Backend Orchestrator**: Port 8000 (required)
2. **Authentication Service**: Port 8004 (optional for dummy auth)
3. **Database**: Redis for session storage
4. **Message Queue**: Kafka for agent communication

## Local Development Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/pjoetan/pv_chatbot_general.git
cd pv_chatbot_general/frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env
```

### 2. Environment Configuration

Edit the `.env` file with your local configuration:

```bash
# Backend Services
VITE_BACKEND_URL=http://localhost:8000
VITE_AUTH_URL=http://localhost:8004

# Application Settings
VITE_APP_NAME=PV Chatbot
VITE_APP_VERSION=1.0.0
VITE_DEBUG=true

# Feature Flags
VITE_ENABLE_MOCK_AUTH=true
VITE_ENABLE_ANALYTICS=false
```

### 3. Start Development Server

```bash
# Start the development server
npm run dev

# The application will be available at:
# http://localhost:5173
```

### 4. Development Commands

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

## Production Deployment

### 1. Build Process

#### Prepare for Production Build

```bash
# Install dependencies
npm ci --only=production

# Set production environment variables
export NODE_ENV=production
export VITE_BACKEND_URL=https://api.your-domain.com
export VITE_AUTH_URL=https://auth.your-domain.com
export VITE_DEBUG=false
export VITE_ENABLE_ANALYTICS=true

# Build the application
npm run build
```

#### Build Output

The build process creates a `dist/` directory containing:

```
dist/
├── index.html              # Main HTML file
├── assets/
│   ├── index-[hash].js     # Main JavaScript bundle
│   ├── index-[hash].css    # Main CSS bundle
│   └── [asset]-[hash].*    # Other assets (images, fonts)
└── favicon.ico             # Favicon
```

### 2. Web Server Configuration

#### Nginx Configuration

Create `/etc/nginx/sites-available/pv-chatbot`:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Document root
    root /var/www/pv-chatbot/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json image/svg+xml;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (optional)
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/pv-chatbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Apache Configuration

Create `/etc/apache2/sites-available/pv-chatbot.conf`:

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    Redirect permanent / https://your-domain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName your-domain.com
    ServerAlias www.your-domain.com
    
    DocumentRoot /var/www/pv-chatbot/dist
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/your/certificate.crt
    SSLCertificateKeyFile /path/to/your/private.key
    
    # Security headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Content-Type-Options "nosniff"
    
    # Compression
    LoadModule deflate_module modules/mod_deflate.so
    <Location />
        SetOutputFilter DEFLATE
        SetEnvIfNoCase Request_URI \
            \.(?:gif|jpe?g|png)$ no-gzip dont-vary
        SetEnvIfNoCase Request_URI \
            \.(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary
    </Location>
    
    # Cache static assets
    <LocationMatch "\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$">
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </LocationMatch>
    
    # Handle client-side routing
    <Directory "/var/www/pv-chatbot/dist">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
</VirtualHost>
```

Enable the site:

```bash
sudo a2ensite pv-chatbot
sudo a2enmod rewrite ssl headers expires
sudo systemctl reload apache2
```

### 3. Docker Deployment

#### Dockerfile

Create `Dockerfile` in the frontend directory:

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Nginx Configuration

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json image/svg+xml;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Include backend services
  backend:
    image: pv-chatbot-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/chatbot
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=chatbot
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Build and run:

```bash
# Build the image
docker build -t pv-chatbot-frontend .

# Run with docker-compose
docker-compose up -d

# Check status
docker-compose ps
```

## Cloud Deployment

### AWS S3 + CloudFront

#### 1. Build and Upload

```bash
# Build the application
npm run build

# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create S3 bucket
aws s3 mb s3://your-chatbot-bucket

# Upload files
aws s3 sync dist/ s3://your-chatbot-bucket --delete

# Set bucket policy for public read
aws s3api put-bucket-policy --bucket your-chatbot-bucket --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-chatbot-bucket/*"
    }
  ]
}'
```

#### 2. CloudFront Distribution

```json
{
  "CallerReference": "pv-chatbot-distribution",
  "Comment": "PV Chatbot Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-your-chatbot-bucket",
        "DomainName": "your-chatbot-bucket.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-your-chatbot-bucket",
    "ViewerProtocolPolicy": "redirect-to-https",
    "TrustedSigners": {
      "Enabled": false,
      "Quantity": 0
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "Enabled": true,
  "PriceClass": "PriceClass_100"
}
```

### Vercel Deployment

#### 1. Install Vercel CLI

```bash
npm install -g vercel
```

#### 2. Deploy

```bash
# Login to Vercel
vercel login

# Deploy
vercel --prod

# Set environment variables
vercel env add VITE_BACKEND_URL production
vercel env add VITE_AUTH_URL production
```

#### 3. Vercel Configuration

Create `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### Netlify Deployment

#### 1. Build Configuration

Create `netlify.toml`:

```toml
[build]
  publish = "dist"
  command = "npm run build"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "SAMEORIGIN"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

#### 2. Deploy

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
netlify deploy --prod --dir=dist
```

## Environment-Specific Configuration

### Development Environment

```bash
# .env.development
VITE_BACKEND_URL=http://localhost:8000
VITE_AUTH_URL=http://localhost:8004
VITE_DEBUG=true
VITE_ENABLE_MOCK_AUTH=true
VITE_LOG_LEVEL=debug
```

### Staging Environment

```bash
# .env.staging
VITE_BACKEND_URL=https://api-staging.your-domain.com
VITE_AUTH_URL=https://auth-staging.your-domain.com
VITE_DEBUG=false
VITE_ENABLE_MOCK_AUTH=false
VITE_LOG_LEVEL=info
VITE_ENABLE_ANALYTICS=true
```

### Production Environment

```bash
# .env.production
VITE_BACKEND_URL=https://api.your-domain.com
VITE_AUTH_URL=https://auth.your-domain.com
VITE_DEBUG=false
VITE_ENABLE_MOCK_AUTH=false
VITE_LOG_LEVEL=warn
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=https://your-sentry-dsn
```

## Monitoring and Logging

### Application Monitoring

#### Sentry Integration

```bash
npm install @sentry/react @sentry/tracing
```

Add to `src/main.tsx`:

```typescript
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      new BrowserTracing(),
    ],
    tracesSampleRate: 1.0,
  });
}
```

#### Google Analytics

```bash
npm install gtag
```

Add to `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Health Checks

Create health check endpoints:

```typescript
// src/utils/health.ts
export const healthCheck = async () => {
  try {
    const response = await fetch('/api/health');
    return response.ok;
  } catch {
    return false;
  }
};
```

### Performance Monitoring

#### Web Vitals

```bash
npm install web-vitals
```

```typescript
// src/utils/vitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: any) {
  // Send to your analytics service
  console.log(metric);
}

getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

## Security Considerations

### Content Security Policy

Add to your HTML or server configuration:

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://www.googletagmanager.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.your-domain.com https://auth.your-domain.com;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
">
```

### HTTPS Configuration

Ensure all environments use HTTPS:

```bash
# Generate SSL certificate with Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Environment Variables Security

Never commit sensitive environment variables:

```bash
# .env.example (safe to commit)
VITE_BACKEND_URL=http://localhost:8000
VITE_AUTH_URL=http://localhost:8004
VITE_APP_NAME=PV Chatbot

# .env (never commit)
VITE_SENTRY_DSN=https://your-actual-sentry-dsn
VITE_GA_MEASUREMENT_ID=GA_MEASUREMENT_ID
```

## Troubleshooting

### Common Deployment Issues

#### Build Failures

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Run type checking
npm run type-check
```

#### Runtime Errors

```bash
# Check browser console for errors
# Verify environment variables are set correctly
# Ensure backend services are accessible
```

#### Performance Issues

```bash
# Analyze bundle size
npm run build -- --analyze

# Check network requests in browser dev tools
# Verify CDN and caching configuration
```

### Rollback Strategy

```bash
# Keep previous builds
mv dist dist-backup-$(date +%Y%m%d-%H%M%S)

# Quick rollback
mv dist-backup-YYYYMMDD-HHMMSS dist
sudo systemctl reload nginx
```

This deployment guide provides comprehensive instructions for deploying the PV Chatbot Frontend in various environments while maintaining security, performance, and reliability standards.
