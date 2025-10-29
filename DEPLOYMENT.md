# InternalTTS Docker Deployment Guide

## Overview
This guide covers deploying the InternalTTS application using Docker with UV package manager and private registry support.

## Prerequisites
- Docker and Docker Compose installed
- Access to private Docker registry
- Proper network connectivity to registry

## Quick Start

### 1. Local Development
```bash
# Build and run locally
docker-compose up --build

# Or use the deployment script
./deploy.sh build
```

### 2. Private Registry Deployment

#### Setup Environment
```bash
# Copy and configure environment file
cp .env.example .env
# Edit .env with your registry details
```

#### Deploy to Registry
```bash
# Set your registry URL
export REGISTRY_URL=registry.company.com
export TTS_APP_SECRET=your-secure-secret

# Full deployment cycle
./deploy.sh full
```

#### Deploy from Registry
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration Options

### Environment Variables
- `REGISTRY_URL`: Private registry hostname
- `REGISTRY_PORT`: Registry port (default: 5000)
- `TTS_APP_SECRET`: Flask secret key for sessions
- `APP_PORT`: Host port mapping (default: 5000)
- `DATA_VOLUME`: Path for persistent data storage
- `AUDIO_VOLUME`: Path for audio file storage

### Docker Compose Files
- `docker-compose.yml`: Local development
- `docker-compose.prod.yml`: Production deployment from registry

## Security Considerations

### 1. Change Default Secrets
```bash
# Generate a secure secret
openssl rand -hex 32
# Update TTS_APP_SECRET in .env
```

### 2. Registry Authentication
```bash
# Login to private registry
docker login registry.company.com:5000
```

### 3. Non-root User
The Dockerfile runs as non-root user `appuser` for security.

## Monitoring and Health Checks

### Health Check
The container includes a health check that verifies the application is responding:
```bash
# Check container health
docker ps
# Look for "healthy" status
```

### Logs
```bash
# View application logs
docker logs internal-tts-app

# Follow logs in real-time
docker logs -f internal-tts-app
```

## Troubleshooting

### Common Issues

1. **Registry Connection Issues**
   ```bash
   # Test registry connectivity
   curl -I http://registry.company.com:5000/v2/
   ```

2. **Permission Issues**
   ```bash
   # Ensure volumes are writable
   sudo chown -R 1000:1000 ./data ./audio
   ```

3. **Port Conflicts**
   ```bash
   # Check if port is in use
   netstat -tulpn | grep :5000
   ```

### Debug Mode
```bash
# Run container in debug mode
docker run -it --rm \
  -p 5000:5000 \
  -e TTS_APP_SECRET=debug \
  internal-tts:latest \
  /bin/bash
```

## Performance Optimization

### UV Package Manager Benefits
- Faster dependency resolution
- Better caching
- Parallel downloads
- Reduced image size

### Production Recommendations
1. Use multi-stage builds for smaller images
2. Enable Docker layer caching
3. Use specific image tags instead of `latest`
4. Implement proper logging and monitoring

## Backup and Recovery

### Data Backup
```bash
# Backup data directory
tar -czf internal-tts-backup-$(date +%Y%m%d).tar.gz data/ audio/
```

### Restore Data
```bash
# Restore from backup
tar -xzf internal-tts-backup-YYYYMMDD.tar.gz
```

## Support
For issues or questions, contact your system administrator or refer to the application logs.
