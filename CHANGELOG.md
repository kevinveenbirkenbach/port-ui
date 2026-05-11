## [1.2.0] - 2026-05-11

* * Navigation behavior: Top-level dropdowns now open reliably on hover and click via Bootstrap, escape the header and navbar overflow clips, and flip between downward and upward based on whether more space is above or below the toggle
* Compose-driven dependencies: docker-compose runs npm install inside the container on every up and persists node_modules plus static/vendor in named volumes, removing the host-side npm-install step from up, dev, prod, and test-e2e
* Test coverage: New Cypress specs cover both header and footer dropdown directions, with a Jinja unit test guarding the data-bs-toggle attribute on top-level dropdown toggles
* Harness configuration: Enabled the Claude Code sandbox with scoped filesystem rules, consolidated the bash allowlist behind a single wildcard, and gitignored local-only state under .claude


## [1.1.0] - 2026-03-30

* *CI stabilization and modularization*: Split into reusable workflows (lint, security, tests) with correct permissions for CodeQL and SARIF uploads
* *Modern Python packaging*: Migration to pyproject.toml and updated Dockerfile using Python 3.12
* *Improved test coverage*: Added unit, integration, lint, security, and E2E tests using act
* *Local vendor assets*: Replaced external CDNs with npm-based local asset pipeline
* *Enhanced build workflow*: Extended Makefile with targets for test, lint, security, and CI plus vendor build process
* *Frontend fix*: Prevented navbar wrapping and improved layout behavior
* *Developer guidelines*: Introduced AGENTS.md and CLAUDE.md with enforced pre-commit rules


## [1.0.0] - 2026-02-19

* Official Release🥳

