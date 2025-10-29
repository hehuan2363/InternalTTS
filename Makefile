# InternalTTS Makefile
# Provides convenient commands for Docker operations

.PHONY: help build push deploy clean logs health

# Default target
help:
	@echo "InternalTTS Docker Management"
	@echo ""
	@echo "Available commands:"
	@echo "  make build     - Build Docker image locally"
	@echo "  make push      - Build and push to private registry"
	@echo "  make deploy    - Deploy from private registry"
	@echo "  make logs      - View application logs"
	@echo "  make health    - Check container health"
	@echo "  make clean     - Clean up containers and images"
	@echo "  make dev       - Start development environment"
	@echo "  make prod      - Start production environment"
	@echo ""
	@echo "Environment variables:"
	@echo "  REGISTRY_URL   - Private registry URL"
	@echo "  IMAGE_TAG      - Image tag (default: latest)"
	@echo "  TTS_APP_SECRET - Application secret"

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t internal-tts:$(or $(IMAGE_TAG),latest) .

# Push to private registry
push: build
	@if [ -z "$(REGISTRY_URL)" ]; then \
		echo "Error: REGISTRY_URL must be set"; \
		exit 1; \
	fi
	@echo "Tagging image for registry..."
	docker tag internal-tts:$(or $(IMAGE_TAG),latest) $(REGISTRY_URL):5000/internal-tts:$(or $(IMAGE_TAG),latest)
	@echo "Pushing to registry..."
	docker push $(REGISTRY_URL):5000/internal-tts:$(or $(IMAGE_TAG),latest)

# Deploy from private registry
deploy:
	@if [ -z "$(REGISTRY_URL)" ]; then \
		echo "Error: REGISTRY_URL must be set"; \
		exit 1; \
	fi
	@echo "Deploying from registry..."
	docker-compose -f docker-compose.prod.yml up -d

# Development environment
dev:
	@echo "Starting development environment..."
	docker-compose up --build

# Production environment
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up -d

# View logs
logs:
	@echo "Viewing application logs..."
	docker logs -f internal-tts-app

# Check health
health:
	@echo "Checking container health..."
	@docker ps --filter name=internal-tts-app --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Clean up
clean:
	@echo "Cleaning up containers and images..."
	docker stop internal-tts-app 2>/dev/null || true
	docker rm internal-tts-app 2>/dev/null || true
	docker rmi internal-tts:$(or $(IMAGE_TAG),latest) 2>/dev/null || true
	docker system prune -f

# Full deployment cycle
full: push deploy
	@echo "Full deployment completed!"

# Quick test
test:
	@echo "Testing application..."
	@curl -f http://localhost:5000/ || echo "Application not responding"
