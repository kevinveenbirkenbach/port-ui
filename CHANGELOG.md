## [2.0.0] - 2026-05-18

* * Asset resolution: new probe-first resolver tries a HEAD request and embeds reachable image URLs directly via a new external_url field, falling back to the cache-download path only when the probe fails; broken /static/https://... URLs no longer appear when the source cannot be downloaded
* Template integration: an asset_src context processor in app.py picks external_url first and url_for(static, cache) second, so base.html.j2, navigation.html.j2, and card.html.j2 never wrap an absolute URL in the static prefix
* Test coverage: 16 new unit tests cover every probe, cache, and fallback branch; a live integration test exercises https://file.infinito.nexus/assets/img/logo.png to prove the probe-first path works end-to-end without writing to the cache directory
* Sample configuration: new Infinito.Nexus card in app/config.sample.yaml driven by the canonical file.infinito.nexus asset URL
* SPOT for build variables: env.example is the single source of truth for IMAGE_NAME and PORT; the Makefile and docker-compose.yml reference both with no defaults and fail loudly when either variable is missing
* Bootstrap targets: make env and make config materialise .env and app/config.yaml from their checked-in templates without overwriting existing files; build, build-no-cache, up, run-dev, run-prod, dev, prod, and browse depend on both so a fresh checkout runs in a single make invocation
* Recipe sourcing: Makefile recipes load .env at recipe-execution time via a shared _require_env helper, so a freshly bootstrapped .env is picked up in the same make invocation that created it
* README: PortUI screenshot added under the title
* Lint: removed an unused sys import in the live integration test


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

