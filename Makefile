SHELL := /bin/sh

COMPOSE ?= docker compose
BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend

.PHONY: help setup dev watch test lint migrate seed down logs ps

help: ## Show available targets
	@printf "AI GTM Engine targets\n"
	@printf "  setup   Copy .env.example to .env and install local dependencies when present\n"
	@printf "  dev     Start the stack with Docker Compose\n"
	@printf "  watch   Start the stack using Docker Compose watch mode\n"
	@printf "  test    Run backend and frontend tests when their toolchains exist\n"
	@printf "  lint    Run backend and frontend linters when their toolchains exist\n"
	@printf "  migrate Run Alembic migrations when the backend is ready\n"
	@printf "  seed    Seed a test org and sample data when the backend seed entrypoint exists\n"
	@printf "  down    Stop the compose stack\n"
	@printf "  logs    Follow compose logs\n"
	@printf "  ps      Show compose service status\n"

setup: ## Bootstrap local configuration and package installs
	@if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; fi
	@if [ -f "$(BACKEND_DIR)/requirements.txt" ]; then python -m pip install -r "$(BACKEND_DIR)/requirements.txt"; fi
	@if [ -f "$(BACKEND_DIR)/pyproject.toml" ] && [ ! -f "$(BACKEND_DIR)/requirements.txt" ]; then python -m pip install -e "$(BACKEND_DIR)"; fi
	@if [ -f "$(FRONTEND_DIR)/package.json" ]; then cd "$(FRONTEND_DIR)" && npm install; fi

dev: ## Run the full stack
	$(COMPOSE) up --build

watch: ## Run the full stack with Compose watch mode
	$(COMPOSE) watch

test: ## Run backend and frontend tests when configured
	@if [ -f "$(BACKEND_DIR)/pyproject.toml" ] || [ -f "$(BACKEND_DIR)/requirements.txt" ]; then cd "$(BACKEND_DIR)" && pytest; fi
	@if [ -f "$(FRONTEND_DIR)/package.json" ]; then cd "$(FRONTEND_DIR)" && npm test -- --runInBand; fi

lint: ## Run backend and frontend linters when configured
	@if [ -f "$(BACKEND_DIR)/pyproject.toml" ] || [ -f "$(BACKEND_DIR)/requirements.txt" ]; then ruff check "$(BACKEND_DIR)"; fi
	@if [ -f "$(FRONTEND_DIR)/package.json" ]; then cd "$(FRONTEND_DIR)" && npm run lint; fi

migrate: ## Run backend database migrations
	@if [ -f "$(BACKEND_DIR)/alembic.ini" ] || [ -d "$(BACKEND_DIR)/db/migrations" ]; then cd "$(BACKEND_DIR)" && alembic upgrade head; else echo "Backend migrations are not wired yet."; fi

seed: ## Seed sample data when a backend seed entrypoint exists
	@if [ -f "$(BACKEND_DIR)/db/seed.py" ]; then python -m backend.db.seed; else echo "Seed entrypoint not present yet."; fi

down: ## Stop the compose stack
	$(COMPOSE) down

logs: ## Follow compose logs
	$(COMPOSE) logs -f --tail=200

ps: ## Show compose service status
	$(COMPOSE) ps

