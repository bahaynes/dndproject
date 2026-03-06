# DnD Westmarches Hub - Makefile
# Run make help for available commands

.PHONY: help dev stop test migrate revision docs-serve docs-build

# Default target
help:
	@echo "Development Commands:"
	@echo "  make dev          Start development environment"
	@echo "  make stop         Stop development environment"
	@echo "  make test         Run all tests"
	@echo "  make logs         Follow pod logs"
	@echo ""
	@echo "Database Commands:"
	@echo "  make migrate      Apply pending database migrations"
	@echo "  make revision m=\"message\"  Create new migration"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  make docs-serve   Serve docs locally (http://localhost:8001)"
	@echo "  make docs-build   Build static documentation"


# --- Development ---

dev:
	./kube/dev.sh

stop:
	./kube/teardown.sh

test:
	./run_tests.sh

logs:
	podman pod logs -f dnd-westmarches-dev


# --- Database ---

migrate:
	podman exec -it dnd-westmarches-dev-backend alembic upgrade head

revision:
ifndef m
	$(error Usage: make revision m="Description of changes")
endif
	podman exec -it dnd-westmarches-dev-backend alembic revision --autogenerate -m "$(m)"


# --- Documentation ---

docs-serve:
	mkdocs serve

docs-build:
	mkdocs build
