#!/bin/sh
# Run the Cypress suite against a Flask app started by this script.
#
# Server and browser share one shell, so this works where act cannot reach the
# host network. ELECTRON_RUN_AS_NODE is dropped before invoking Cypress because
# VS Code exports it to child processes, which makes Cypress' bundled Electron
# behave as Node and reject its own launch flags.
#
# Env:
#   PORT     required, the port Flask binds and Cypress targets
#   PYTHON   interpreter to run app.py with (default: python3)
#   E2E_LOG  where Flask's output goes (default: /tmp/portfolio-e2e-flask.log)
set -u

PORT="${PORT:?PORT must be set (see env.example)}"
PYTHON="${PYTHON:-python3}"
E2E_LOG="${E2E_LOG:-/tmp/portfolio-e2e-flask.log}"
FLASK_HOST=127.0.0.1
export PORT FLASK_HOST

APP_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")/../app" && pwd)"
BASE_URL="http://127.0.0.1:$PORT/"

# cypress.config.js defaults to localhost, which resolves to ::1 first on a
# dual-stack host — a different listener from the 127.0.0.1 one Flask binds and
# this script probes. Pin all three to the same origin.
export CYPRESS_baseUrl="$BASE_URL"

# A foreign listener would be tested instead of the working tree. The predicate
# is "something answers", deliberately without curl's -f: a foreign server that
# is still returning 5xx right now would otherwise pass the guard and then be
# picked up by the readiness probe once it recovers. --noproxy is what keeps
# that same looser predicate from matching an HTTP proxy instead of the port.
if curl -s --noproxy '*' --connect-timeout 2 --max-time 10 -o /dev/null "$BASE_URL"; then
    echo "ERROR: something already serves port $PORT — Cypress would test that"
    echo "       instead of your working tree. Stop it first ('make down' for"
    echo "       the container, otherwise a stray 'python app.py')."
    exit 1
fi

cd "$APP_DIR" || exit 1
$PYTHON app.py > "$E2E_LOG" 2>&1 &
flask_pid=$!
trap 'kill "$flask_pid" 2>/dev/null || true' EXIT INT TERM

echo "Waiting for $BASE_URL — follow with: tail -f $E2E_LOG"
attempt=0
while [ "$attempt" -lt 120 ]; do
    # Liveness first: a server answering while ours is dead means we are about
    # to hand Cypress somebody else's app.
    if ! kill -0 "$flask_pid" 2>/dev/null; then
        echo "ERROR: Flask exited during startup"
        cat "$E2E_LOG"
        exit 1
    fi
    if curl -sf --noproxy '*' --connect-timeout 2 --max-time 10 -o /dev/null "$BASE_URL"; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if ! curl -sf --noproxy '*' --connect-timeout 2 --max-time 10 -o /dev/null "$BASE_URL"; then
    echo "ERROR: app never became ready"
    cat "$E2E_LOG"
    exit 1
fi

env -u ELECTRON_RUN_AS_NODE npx cypress run
status=$?

kill "$flask_pid" 2>/dev/null || true
exit "$status"
