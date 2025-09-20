# HARVEST Backend Makefile
# Provides convenient commands for development and deployment

.PHONY: help install dev test clean lint format build run docker-up docker-down

# Default target
help:
	@echo "HARVEST Backend - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code"
	@echo ""
	@echo "Database:"
	@echo "  db-init     Initialize database"
	@echo "  db-migrate  Run database migrations"
	@echo "  db-seed     Seed database with sample data"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up   Start Docker services"
	@echo "  docker-down Stop Docker services"
	@echo "  docker-logs View Docker logs"
	@echo ""
	@echo "Production:"
	@echo "  build       Build production image"
	@echo "  deploy      Deploy to production"
	@echo ""

# Development commands
install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app/ tests/
	mypy app/
	black --check app/ tests/
	isort --check app/ tests/

format:
	black app/ tests/
	isort app/ tests/

# Database commands
db-init:
	python scripts/init_db.py

db-migrate:
	alembic upgrade head

db-seed:
	python scripts/seed_db.py

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

# Production commands
build:
	docker build -t harvest-backend .

deploy:
	@echo "Deploying to production..."
	@echo "Make sure to set production environment variables!"
	docker-compose -f docker-compose.prod.yml up -d

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

# Development setup
setup: install db-init db-seed
	@echo "Development environment setup complete!"
	@echo "Run 'make dev' to start the development server"

# Run all checks
check: lint test
	@echo "All checks passed!"