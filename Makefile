.PHONY: help setup services-up services-down run-backend run-mobile test lint format clean

.DEFAULT_GOAL := help

help:
	@echo "VerifAI - Development Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && pip install poetry && poetry install
	@echo "Installing mobile dependencies..."
	cd mobile && npm install
	@echo "Setup complete!"

services-up: ## Start PostgreSQL and Redis
	@echo "Starting services..."
	docker-compose up -d
	@sleep 3
	@echo "Services ready!"

services-down: ## Stop all services
	docker-compose down

run-backend: ## Run FastAPI backend
	@echo "Starting backend on http://localhost:8000..."
	cd backend && poetry run python -m app.main

run-mobile: ## Run React Native mobile app
	@echo "Starting Expo dev server..."
	cd mobile && npm start

test: ## Run backend tests
	cd backend && poetry run pytest tests/ -v --cov=app

lint: ## Lint code
	cd backend && poetry run ruff check app/ tests/
	cd mobile && npm run lint

format: ## Format code
	cd backend && poetry run black app/ tests/

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true

check-health: ## Check backend health
	@curl -s http://localhost:8000/health | python -m json.tool
