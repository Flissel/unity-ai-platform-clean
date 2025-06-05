# UnityAI Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev test lint format clean build up down logs shell migrate backup restore

# Default target
help:
	@echo "UnityAI Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install dependencies"
	@echo "  dev         Setup development environment"
	@echo ""
	@echo "Development:"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  build       Build Docker images"
	@echo "  up          Start services"
	@echo "  down        Stop services"
	@echo "  logs        View logs"
	@echo "  shell       Access app container shell"
	@echo ""
	@echo "Database:"
	@echo "  migrate     Run database migrations"
	@echo "  backup      Backup database"
	@echo "  restore     Restore database"

# Setup commands
install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Development commands
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - UnityAI API: http://localhost:8000"
	@echo "  - n8n: http://localhost:5678"
	@echo "  - Grafana: http://localhost:3000"
	@echo "  - Prometheus: http://localhost:9090"

up-dev:
	BUILD_TARGET=development docker-compose up -d

down:
	docker-compose down

down-volumes:
	docker-compose down -v

logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

shell:
	docker-compose exec app /bin/bash

shell-db:
	docker-compose exec db psql -U postgres -d unityai

# Database commands
migrate:
	docker-compose exec app python -m alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec app python -m alembic revision --autogenerate -m "$$msg"

backup:
	@mkdir -p backups
	docker-compose exec db pg_dump -U postgres unityai > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	restore:
	@read -p "Enter backup file path: " file; \
	docker-compose exec -T db psql -U postgres -d unityai < "$$file"

# Monitoring
metrics:
	curl -s http://localhost:8000/metrics

health:
	curl -s http://localhost:8000/health | jq .

# Security
security-scan:
	docker run --rm -v $(PWD):/app securecodewarrior/docker-security-scan /app

# Production deployment
deploy-prod:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Update dependencies
update-deps:
	pip-compile requirements.in
	pip-sync requirements.txt

# Generate API documentation
docs:
	docker-compose exec app python -c "from src.api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > docs/openapi.json

# Performance testing
load-test:
	@echo "Running load tests..."
	# Add your load testing commands here

# Code quality checks
quality:
	make lint
	make test
	make security-scan