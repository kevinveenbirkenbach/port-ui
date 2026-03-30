# Agent Instructions

## Pre-Commit Validation

- You MUST run `make test` before every commit whenever the staged change includes at least one file that is not `.md` or `.rst`, unless explicitly instructed otherwise.
- You MUST commit only after all tests pass.
- You MUST NOT commit automatically without explicit confirmation from the user.

## Vendor Assets

- Browser vendor assets (Bootstrap, Font Awesome, etc.) are managed via npm.
- Run `npm install` inside `app/` to populate `app/static/vendor/` before starting the dev server or running e2e tests.
- Never commit `app/node_modules/` or `app/static/vendor/` — both are gitignored and generated at build time.
