# Load environment variables from .env
ifneq (,$(wildcard .env))
    include .env
    # Export variables defined in .env
    export $(shell sed 's/=.*//' .env)
endif

PYTHON ?= python3
ACT ?= act

# Bootstrap the local .env from the checked-in env.example template.
# Idempotent: leaves an existing .env untouched.
.PHONY: env
env:
	@if [ -f .env ]; then \
		echo ".env already exists — leaving it alone."; \
	else \
		cp env.example .env; \
		echo "Created .env from env.example — review and adjust."; \
	fi

# Bootstrap app/config.yaml from the checked-in app/config.sample.yaml
# template. Idempotent: leaves an existing config.yaml untouched. The
# Dockerfile COPYs the whole app/ directory at build time, so this file
# must exist before `make build` / `make up`.
.PHONY: config
config:
	@if [ -f app/config.yaml ]; then \
		echo "app/config.yaml already exists — leaving it alone."; \
	else \
		cp app/config.sample.yaml app/config.yaml; \
		echo "Created app/config.yaml from app/config.sample.yaml — review and adjust."; \
	fi

# Build/run recipes source .env at recipe-execution time (not at make
# parse time) so they work in the same invocation that bootstrapped
# .env via the `env` prereq. Without this, the inner $$IMAGE_NAME /
# $$PORT would be empty on the very first `make build` after a fresh
# checkout — the parse-time `include .env` happens before `env` runs.
define _require_env
	if [ ! -f .env ]; then echo "ERROR: .env missing"; exit 1; fi; \
	. ./.env; \
	for v in $(1); do \
		eval "val=\$$$$v"; \
		[ -n "$$val" ] || { echo "ERROR: $$v is empty in .env (see env.example)"; exit 1; }; \
	done
endef

.PHONY: build
build: env config
	# Build the Docker image.
	@$(call _require_env,IMAGE_NAME); \
		docker build -t "$$IMAGE_NAME" .

.PHONY: build-no-cache
build-no-cache: env config
	# Build the Docker image without cache.
	@$(call _require_env,IMAGE_NAME); \
		docker build --no-cache -t "$$IMAGE_NAME" .

.PHONY: up
up: env config
	# Start the application using docker-compose with build.
	docker-compose up -d --build --force-recreate

.PHONY: down
down:
	# Stop and remove the 'portfolio' container, ignore errors, and bring down compose.
	- docker stop portfolio || true
	- docker rm portfolio || true
	- docker-compose down

.PHONY: run-dev
run-dev: env config config
	# Run the container in development mode (hot-reload).
	@$(call _require_env,IMAGE_NAME PORT); \
		docker run -d \
			-p "$$PORT:$$PORT" \
			--name portfolio \
			-v "$(PWD)/app/:/app" \
			-e FLASK_APP=app.py \
			-e FLASK_ENV=development \
			"$$IMAGE_NAME"

.PHONY: run-prod
run-prod: env config config
	# Run the container in production mode.
	@$(call _require_env,IMAGE_NAME PORT); \
		docker run -d \
			-p "$$PORT:$$PORT" \
			--name portfolio \
			"$$IMAGE_NAME"

.PHONY: logs
logs:
	# Display the logs of the 'portfolio' container.
	docker logs -f portfolio

.PHONY: dev
dev: env config
	# Start the application in development mode using docker-compose.
	FLASK_ENV=development docker-compose up -d

.PHONY: prod
prod: env config
	# Start the application in production mode using docker-compose (with build).
	docker-compose up -d --build

.PHONY: cleanup
cleanup:
	# Remove all stopped Docker containers to reclaim space.
	docker container prune -f

.PHONY: delete
delete:
	# Force remove the 'portfolio' container if it exists.
	- docker rm -f portfolio

.PHONY: browse
browse: env
	# Open the application in the browser at http://localhost:$$PORT
	@$(call _require_env,PORT); \
		chromium "http://localhost:$$PORT"

.PHONY: install
install:
	# Install runtime Python dependencies from pyproject.toml.
	$(PYTHON) -m pip install -e .

.PHONY: install-dev
install-dev:
	# Install runtime and developer dependencies from pyproject.toml.
	$(PYTHON) -m pip install -e ".[dev]"

.PHONY: lint-actions
lint-actions:
	# Lint GitHub Actions workflows.
	docker run --rm -v "$$PWD:/repo" -w /repo rhysd/actionlint:latest

.PHONY: lint-python
lint-python: install-dev
	# Run Python lint and format checks.
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

.PHONY: lint-docker
lint-docker:
	# Lint the Dockerfile.
	docker run --rm -i hadolint/hadolint < Dockerfile

.PHONY: test-lint
test-lint:
	# Run lint guardrail tests.
	$(PYTHON) -m unittest discover -s tests/lint -t .

.PHONY: test-integration
test-integration: install
	# Run repository integration tests.
	$(PYTHON) -m unittest discover -s tests/integration -t .

.PHONY: test-unit
test-unit: install
	# Run repository unit tests.
	$(PYTHON) -m unittest discover -s tests/unit -t .

.PHONY: test-security
test-security: install
	# Run repository security guardrail tests.
	$(PYTHON) -m unittest discover -s tests/security -t .

.PHONY: lint
lint: lint-actions lint-python lint-docker test-lint
	# Run the full lint suite.

.PHONY: security
security: install-dev test-security
	# Run security checks.
	$(PYTHON) -m bandit -q -ll -ii -r app main.py
	$(PYTHON) utils/export_runtime_requirements.py > /tmp/portfolio-runtime-requirements.txt
	$(PYTHON) -m pip_audit -r /tmp/portfolio-runtime-requirements.txt

.PHONY: test-e2e
test-e2e:
	# Run Cypress end-to-end tests via act (stop portfolio container to free port first).
	-docker stop portfolio 2>/dev/null || true
	$(ACT) workflow_dispatch -W .github/workflows/tests.yml -j e2e
	-docker start portfolio 2>/dev/null || true

.PHONY: test-workflow
test-workflow:
	# Run the GitHub test workflow locally via act.
	$(ACT) workflow_dispatch -W .github/workflows/tests.yml

.PHONY: lint-workflow
lint-workflow:
	# Run the GitHub lint workflow locally via act.
	$(ACT) workflow_dispatch -W .github/workflows/lint.yml

.PHONY: quality
quality: lint-workflow test-workflow
	# Run the GitHub lint and test workflows locally via act.

.PHONY: ci
ci: lint security test-unit test-integration test-e2e
	# Run the local CI suite.

.PHONY: test
test: ci
	# Run the full validation suite.
