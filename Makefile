# Load environment variables from .env
ifneq (,$(wildcard .env))
    include .env
    # Export variables defined in .env
    export $(shell sed 's/=.*//' .env)
endif

# Default port (can be overridden with PORT env var)
PORT ?= 5000
PYTHON ?= python3
ACT ?= act

# Default port (can be overridden with PORT env var)
.PHONY: build
build:
	# Build the Docker image.
	docker build -t application-portfolio .

.PHONY: build-no-cache
build-no-cache:
	# Build the Docker image without cache.
	docker build --no-cache -t application-portfolio .

.PHONY: up
up:
	# Start the application using docker-compose with build.
	docker-compose up -d --build --force-recreate

.PHONY: down
down:
	# Stop and remove the 'portfolio' container, ignore errors, and bring down compose.
	- docker stop portfolio || true
	- docker rm portfolio || true
	- docker-compose down

.PHONY: run-dev
run-dev:
	# Run the container in development mode (hot-reload).
	docker run -d \
		-p $(PORT):$(PORT) \
		--name portfolio \
		-v $(PWD)/app/:/app \
		-e FLASK_APP=app.py \
		-e FLASK_ENV=development \
		application-portfolio

.PHONY: run-prod
run-prod:
	# Run the container in production mode.
	docker run -d \
		-p $(PORT):$(PORT) \
		--name portfolio \
		application-portfolio

.PHONY: logs
logs:
	# Display the logs of the 'portfolio' container.
	docker logs -f portfolio

.PHONY: dev
dev:
	# Start the application in development mode using docker-compose.
	FLASK_ENV=development docker-compose up -d

.PHONY: prod
prod:
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
browse:
	# Open the application in the browser at http://localhost:$(PORT)
	chromium http://localhost:$(PORT)

.PHONY: install
install:
	# Install runtime Python dependencies from pyproject.toml.
	$(PYTHON) -m pip install -e .

.PHONY: install-dev
install-dev:
	# Install runtime and developer dependencies from pyproject.toml.
	$(PYTHON) -m pip install -e ".[dev]"

.PHONY: npm-install
npm-install:
	# Install Node.js dependencies for browser tests.
	cd app && npm install

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
