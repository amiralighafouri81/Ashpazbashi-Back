# GitHub Actions Deployment Guide - Backend

## Prerequisites

1. **VPS Server** with:
   - Docker and Docker Compose installed
   - Git installed
   - SSH access configured
   - Port 8000 available (or configure reverse proxy)
   - PostgreSQL client tools (optional, for manual DB access)

2. **GitHub Repository** with Actions enabled

3. **PostgreSQL Database** (can be on same VPS or separate server)

## Step 1: Configure GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

### Required Secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `VPS_HOST` | Your VPS server IP or domain | `123.45.67.89` or `vps.example.com` |
| `VPS_USER` | SSH username for VPS | `root` or `deploy` |
| `VPS_SSH_KEY` | Private SSH key for authentication | (see below) |
| `VPS_PORT` | SSH port (optional, defaults to 22) | `22` |
| `VPS_BACKEND_DEPLOY_PATH` | Path on VPS where code is deployed (optional) | `/var/www/ashpazbashi-backend` |
| `VPS_GH_TOKEN` | GitHub Personal Access Token for pulling images (required) | (see below) |

### Backend-Specific Secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `BACKEND_SECRET_KEY` | Django secret key (generate a strong one) | `django-insecure-...` (change in production!) |
| `BACKEND_DB_NAME` | PostgreSQL database name | `ashpazyar_db` |
| `BACKEND_DB_USER` | PostgreSQL database user | `postgres` |
| `BACKEND_DB_PASSWORD` | PostgreSQL database password | `your-secure-password` |
| `BACKEND_ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `yourdomain.com,api.yourdomain.com` |
| `BACKEND_CORS_ORIGINS` | Comma-separated CORS allowed origins | `https://yourdomain.com,https://www.yourdomain.com` |
| `BACKEND_ENV_VARS` | Additional environment variables (optional) | `KEY1=value1\nKEY2=value2` |

### How to Generate SSH Key:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy-backend" -f ~/.ssh/github_actions_deploy_backend

# Copy the PUBLIC key to your VPS
ssh-copy-id -i ~/.ssh/github_actions_deploy_backend.pub user@your-vps-ip

# Or manually add to VPS ~/.ssh/authorized_keys
cat ~/.ssh/github_actions_deploy_backend.pub | ssh user@your-vps-ip "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Copy the PRIVATE key content to GitHub Secret VPS_SSH_KEY
cat ~/.ssh/github_actions_deploy_backend
```

**Important:** Copy the entire private key including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`

### Generate GitHub Personal Access Token (PAT)

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Name it: `VPS-Backend-Docker-Pull`
4. Select scopes:
   - ✅ `read:packages` (to pull Docker images)
5. Click **Generate token**
6. **Copy the token immediately** (you won't see it again!)
7. Add it as `VPS_GH_TOKEN` secret in GitHub

### Generate Django Secret Key

```bash
# On your local machine or VPS
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and add it as `BACKEND_SECRET_KEY` secret in GitHub.

## Step 2: Prepare VPS Server

### 2.1 Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group (if not root)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2.2 Create Project Directory

```bash
# Create directory
sudo mkdir -p /var/www/ashpazbashi-backend
sudo chown $USER:$USER /var/www/ashpazbashi-backend

# Or use custom path (update VPS_BACKEND_DEPLOY_PATH secret)
mkdir -p ~/ashpazbashi-backend
```

### 2.3 Set Up PostgreSQL Database

The `docker-compose.prod.yml` includes a PostgreSQL service, but if you want to use an external database:

```bash
# Install PostgreSQL client (optional, for manual access)
sudo apt install postgresql-client -y

# If using external database, update DB_HOST in environment variables
# Otherwise, the docker-compose will create a PostgreSQL container
```

### 2.4 Create Production Environment File

The workflow will create `.env.production` automatically, but you can create it manually:

```bash
cd /var/www/ashpazbashi-backend
nano .env.production
```

Add your production environment variables:

```env
# Django Settings
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Database Configuration
DB_NAME=ashpazyar_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Additional environment variables
# Add any other required variables here
```

**Important:** 
- If using external database, change `DB_HOST` from `db` to your database host
- Never commit `.env.production` to git (it's in `.gitignore`)

## Step 3: Configure GitHub Container Registry Access

The workflow uses GitHub Container Registry (ghcr.io). The `GITHUB_TOKEN` is automatically available, but you may need to:

1. **Enable GitHub Packages** in repository settings
2. **Set package visibility** to public or configure access

## Step 4: Deploy

### Option A: Automatic Deployment (on push)

1. Push to `dev` branch:
```bash
git checkout dev
git add .
git commit -m "Deploy backend to production"
git push origin dev
```

The workflow will automatically:
- Build Docker image
- Push to GitHub Container Registry
- Deploy to VPS
- Run database migrations
- Collect static files
- Perform health checks

### Option B: Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select **Deploy Backend to VPS** workflow
3. Click **Run workflow**
4. Select branch (usually `dev`)
5. Click **Run workflow**

## Step 5: Verify Deployment

### Check GitHub Actions Logs

1. Go to **Actions** tab
2. Click on the latest workflow run
3. Check for any errors

### Check VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Check running containers
docker ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Check backend logs specifically
docker compose -f docker-compose.prod.yml logs backend

# Check database logs
docker compose -f docker-compose.prod.yml logs db

# Check if service is running
curl http://localhost:8000/api/

# Check admin panel
curl http://localhost:8000/admin/
```

### Test API Endpoints

```bash
# Test health endpoint (if available)
curl http://localhost:8000/api/

# Test authentication endpoint
curl -X POST http://localhost:8000/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"testpass123"}'
```

## Step 6: Configure Reverse Proxy (Optional but Recommended)

### Using Nginx

```nginx
# /etc/nginx/sites-available/ashpazbashi-backend
server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS (if using SSL)
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Serve static files directly
    location /static/ {
        alias /var/www/ashpazbashi-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias /var/www/ashpazbashi-backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/ashpazbashi-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Using Caddy (Simpler)

```caddy
api.yourdomain.com {
    reverse_proxy localhost:8000
    
    # Serve static files
    handle /static/* {
        file_server root /var/www/ashpazbashi-backend/staticfiles
    }
    
    # Serve media files
    handle /media/* {
        file_server root /var/www/ashpazbashi-backend/media
    }
}
```

## Step 7: Database Management

### Run Migrations Manually

```bash
# SSH into VPS
ssh user@your-vps-ip
cd /var/www/ashpazbashi-backend

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Backup Database

```bash
# Backup PostgreSQL database
docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres ashpazyar_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Or if using external database
pg_dump -h your-db-host -U postgres ashpazyar_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
docker compose -f docker-compose.prod.yml exec -T db psql -U postgres ashpazyar_db < backup_file.sql
```

## Troubleshooting

### Issue: Workflow fails at "Deploy to VPS"

**Check:**
- SSH key is correct in GitHub secrets
- VPS_HOST, VPS_USER are correct
- SSH port is correct (if not 22)
- VPS_BACKEND_DEPLOY_PATH exists and is writable

### Issue: Docker pull fails

**Check:**
- GitHub Container Registry package is accessible
- Image was built successfully
- Check package visibility settings
- VPS_GH_TOKEN is correct

### Issue: Database connection fails

**Check:**
- Database container is running: `docker compose -f docker-compose.prod.yml ps db`
- Database credentials in `.env.production` are correct
- If using external database, DB_HOST is correct
- Database is accessible from backend container
- Check database logs: `docker compose -f docker-compose.prod.yml logs db`

### Issue: Migrations fail

**Check:**
- Database is running and accessible
- Database user has proper permissions
- Check migration logs: `docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --verbosity 2`
- Try running migrations manually (see Step 7)

### Issue: Container doesn't start

**Check:**
- `.env.production` file exists
- Environment variables are correct
- Port 8000 is not already in use: `sudo lsof -i :8000`
- Check logs: `docker compose -f docker-compose.prod.yml logs backend`
- Check if Gunicorn is configured correctly

### Issue: Static files not served

**Check:**
- Static files are collected: `docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic`
- Static files volume is mounted correctly
- Nginx/Caddy configuration points to correct path
- File permissions are correct

### Issue: Health check fails

**Check:**
- Application is actually running: `docker ps`
- Check application logs: `docker compose -f docker-compose.prod.yml logs backend`
- Verify port mapping in docker-compose.prod.yml
- Check firewall settings
- Test endpoint manually: `curl http://localhost:8000/api/`

### Issue: CORS errors

**Check:**
- `CORS_ALLOWED_ORIGINS` in `.env.production` includes your frontend URL
- No trailing slashes in CORS origins
- Frontend is making requests to correct backend URL

## Workflow Details

The workflow:
1. **Builds** Docker image using Dockerfile
2. **Pushes** to `ghcr.io/YOUR_USERNAME/ashpazbashi-backend:dev` (or `:latest` for main)
3. **Creates** `.env.production` file with secrets
4. **SSH** into VPS
5. **Copies** `docker-compose.prod.yml` and `.env.production` to VPS
6. **Pulls** Docker image from registry
7. **Stops** old containers
8. **Starts** new containers (backend + database)
9. **Waits** for database to be ready
10. **Runs** database migrations
11. **Collects** static files
12. **Performs** health checks

## Branch Strategy

- **dev branch**: Deploys with tag `dev`
- **main branch**: Deploys with tag `latest` (currently commented out)

To enable main branch deployment, uncomment line 7 in `.github/workflows/deploy.yml`:

```yaml
branches:
  # - main  # Uncomment this
  - dev
```

## Updating Deployment

Simply push to the `dev` branch or manually trigger the workflow. The workflow will:
- Build a new image
- Deploy it automatically
- Run migrations if needed
- Keep the old image until cleanup runs

## Rollback

If deployment fails, you can rollback:

```bash
# SSH into VPS
ssh user@your-vps-ip
cd /var/www/ashpazbashi-backend

# Check previous images
docker images | grep ashpazbashi-backend

# Use previous image tag
export IMAGE_TAG=ghcr.io/YOUR_USERNAME/ashpazbashi-backend:dev-OLD_SHA
docker compose -f docker-compose.prod.yml up -d

# Or restore database backup if needed
docker compose -f docker-compose.prod.yml exec -T db psql -U postgres ashpazyar_db < backup_file.sql
```

## Security Best Practices

1. **Never commit secrets** to git (use GitHub Secrets)
2. **Use strong passwords** for database and Django secret key
3. **Keep Django secret key secret** - regenerate if exposed
4. **Use HTTPS** in production (configure SSL certificates)
5. **Restrict ALLOWED_HOSTS** to your actual domains
6. **Keep dependencies updated** - regularly update requirements.txt
7. **Monitor logs** for suspicious activity
8. **Backup database regularly**
9. **Use firewall** to restrict access to necessary ports only
10. **Keep Docker and system updated**

## Monitoring

### View Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Backend only
docker compose -f docker-compose.prod.yml logs -f backend

# Database only
docker compose -f docker-compose.prod.yml logs -f db

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Volume usage
docker volume ls
docker volume inspect ashpazbashi-backend_postgres_data
```

## Additional Commands

### Access Django Shell

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

### Access Database Shell

```bash
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d ashpazyar_db
```

### Restart Services

```bash
# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart backend only
docker compose -f docker-compose.prod.yml restart backend
```

### Stop Services

```bash
docker compose -f docker-compose.prod.yml down
```

### Start Services

```bash
docker compose -f docker-compose.prod.yml up -d
```

