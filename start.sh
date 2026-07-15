#!/usr/bin/env bash
# SynaptixLabs project start script (Linux/macOS/CI)
# Generic scaffold — edit the CONFIGURATION section for your project.
# Based on AGENTS project start.sh patterns.
#
# Usage:
#   ./start.sh              # Default: full dev stack (backend --reload + frontend) — same as `dev --ui`
#   ./start.sh setup        # One-time/refresh: install deps, create .env, verify — sprint-1 ready
#   ./start.sh dev          # Local dev: backend only (--reload); auto-updates deps when they changed
#   ./start.sh dev --ui     # Local dev: backend + frontend
#   ./start.sh production   # Production server (Docker/CI — no reload, no frontend)
#   ./start.sh test         # Run tests
#   ./start.sh status|stop  # Health check / kill project processes
#   ./start.sh help         # This help + URLs and links
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# CONFIGURATION — Edit this section per project
# ============================================================================
PROJECT_NAME="{{PROJECT_NAME}}"
PROJECT_TAGLINE="One brain, every CLI — synaptix-scaffold template"   # CUSTOMIZE
REPO_URL="https://github.com/SynaptixLabs/scaffold"                   # CUSTOMIZE: your repo
ORG_URL="https://synaptixlabs.ai"                                     # CUSTOMIZE: your org/site
LICENSE_NAME="MIT"
BACKEND_TYPE="python"           # "python" | "node"
BACKEND_DIR="backend"           # "." for monolith
BACKEND_CMD="uvicorn app.main:app"  # Python entrypoint
RELOAD_DIRS="app modules"       # Space-separated --reload-dir targets (empty = watch all)
FRONTEND_DIR="frontend"         # matches the shipped skeleton; "" if no separate frontend
DEFAULT_PORT=8000
UI_PORT=5173
HEALTH_PATH="/health"
ENV_FILE=".env"
# ============================================================================

: "${PORT:=$DEFAULT_PORT}"
log() { echo "[start.sh] $*"; }

# colors (auto-off when not a terminal)
if [ -t 1 ]; then
  C_B=$'\033[1m'; C_CY=$'\033[36m'; C_GR=$'\033[32m'; C_DIM=$'\033[2m'; C_OFF=$'\033[0m'
else
  C_B=""; C_CY=""; C_GR=""; C_DIM=""; C_OFF=""
fi

# Rich info block — printed after setup and under the dev banner. $1 = "running"|"next".
info_links() {
  local mode="${1:-next}"
  echo "   ${C_B}Local URLs${C_OFF}$([ "$mode" = "next" ] && echo " ${C_DIM}(after ./start.sh)${C_OFF}")"
  echo "     Frontend         ${C_CY}http://localhost:$UI_PORT${C_OFF}"
  echo "     API              ${C_CY}http://localhost:$PORT${C_OFF}"
  echo "     API docs         ${C_CY}http://localhost:$PORT/docs${C_OFF}"
  echo "     Health           ${C_CY}http://localhost:$PORT$HEALTH_PATH${C_OFF}"
  # WSL: the Windows→WSL localhost relay can silently break (even with localhostForwarding=true).
  # Offer the direct-IP fallback so a Windows browser always has a working URL.
  if grep -qi microsoft /proc/version 2>/dev/null; then
    local wsl_ip; wsl_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    [ -n "$wsl_ip" ] && echo "     ${C_DIM}From Windows, if localhost fails: http://$wsl_ip:$UI_PORT · http://$wsl_ip:$PORT (relay fix: wsl --shutdown)${C_OFF}"
  fi
  echo ""
  echo "   ${C_B}Read me first${C_OFF}"
  echo "     Constitution     AGENTS.md   ·   Router  .claude/00_INDEX.md"
  echo "     Sprint 1 entry   project-management/sprints/sprint_01/index.md"
  echo "     Drift guard      python3 scripts/check_adapters.py"
  echo ""
  echo "   ${C_B}Project${C_OFF}"
  echo "     GitHub           ${C_CY}$REPO_URL${C_OFF}"
  echo "     Web              ${C_CY}$ORG_URL${C_OFF}"
  echo "     License          $LICENSE_NAME (see LICENSE)"
}

find_python() {
  for p in "$SCRIPT_DIR/$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/$BACKEND_DIR/venv/bin/python"; do
    [ -x "$p" ] && echo "$p" && return
  done
  echo "python3"
}

kill_port() {
  # Must always return 0: under `set -e`, a nonzero return from the port-is-free
  # case would abort the whole script. lsof may return multiple PIDs → xargs.
  local pids; pids=$(lsof -ti :"$1" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    log "Port $1 in use by PID(s) $(echo $pids | tr '\n' ' ')— killing..."
    echo "$pids" | xargs -r kill -9 2>/dev/null || true
    sleep 1
  fi
}

# dev-mode only (set in cmd_dev): kill the background frontend when the backend exits
cleanup() { log "Shutting down..."; jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true; }

backend_dir() { [ "$BACKEND_DIR" = "." ] && echo "$SCRIPT_DIR" || echo "$SCRIPT_DIR/$BACKEND_DIR"; }

# Create/refresh the backend venv. Cheap when current: a stamp file tracks the last install,
# so deps re-install only when requirements.txt is newer (that's the "update" in update-the-env).
ensure_backend_env() {
  [ "$BACKEND_TYPE" = "python" ] || return 0
  local be_dir; be_dir="$(backend_dir)"
  local req="$be_dir/requirements.txt" venv="$be_dir/.venv"
  [ -f "$req" ] || return 0
  if [ ! -x "$venv/bin/python" ]; then
    log "Creating backend venv..."
    python3 -m venv "$venv"
  fi
  local stamp="$venv/.deps-stamp"
  if [ ! -f "$stamp" ] || [ "$req" -nt "$stamp" ]; then
    log "Installing/updating backend deps (requirements.txt)..."
    "$venv/bin/pip" install -q -r "$req" && touch "$stamp"
  fi
}

# Same idea for the frontend: npm install when node_modules is missing or package.json changed.
ensure_frontend_env() {
  [ -n "$FRONTEND_DIR" ] || return 0
  local fe_dir="$SCRIPT_DIR/$FRONTEND_DIR" pkg stamp
  pkg="$fe_dir/package.json"; stamp="$fe_dir/node_modules/.deps-stamp"
  [ -f "$pkg" ] || return 0
  if [ ! -d "$fe_dir/node_modules" ] || [ ! -f "$stamp" ] || [ "$pkg" -nt "$stamp" ]; then
    log "Installing/updating frontend deps (package.json)..."
    (cd "$fe_dir" && npm install --silent) && touch "$stamp"
  fi
}

# ── Commands ──────────────────────────────────────────
cmd_help() {
  echo ""
  echo "  ${C_B}$PROJECT_NAME${C_OFF}  ${C_DIM}· $PROJECT_TAGLINE${C_OFF}"
  echo ""
  echo "   ${C_B}Commands${C_OFF}"
  echo "     ./start.sh              full dev stack: backend (--reload) + frontend  ${C_DIM}(default)${C_OFF}"
  echo "     ./start.sh setup        install/update deps, create .env, verify — sprint-1 ready"
  echo "     ./start.sh dev [--ui]   backend only, or backend + frontend"
  echo "     ./start.sh production   production server (Docker/CI — no reload)"
  echo "     ./start.sh test         run the test suite"
  echo "     ./start.sh status       ports + health   ·   ./start.sh stop"
  echo ""
  info_links next
  echo ""
  echo "   ${C_DIM}Windows: .\\start.cmd (same commands as flags: -Setup, -Test, -Status, -Stop, -Help)${C_OFF}"
  echo ""
}

cmd_setup() {
  log "Setting up / updating the environment..."
  ensure_backend_env
  ensure_frontend_env
  # .env from the example (never overwrites an existing one)
  local env_dst; env_dst="$(backend_dir)/$ENV_FILE"
  if [ ! -f "$env_dst" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$env_dst"
    log "Created $env_dst from .env.example — fill in real values."
  fi
  # verify: agent layer consistent + tests green (evidence, not assertion)
  [ -f "$SCRIPT_DIR/scripts/check_adapters.py" ] && python3 "$SCRIPT_DIR/scripts/check_adapters.py" "$SCRIPT_DIR"
  if [ "$BACKEND_TYPE" = "python" ]; then
    (cd "$(backend_dir)" && "$(find_python)" -m pytest -q) || log "WARNING: tests not green — fix before starting sprint work."
  fi
  echo ""
  echo "  ${C_CY}════════════════════════════════════════════════════${C_OFF}"
  echo "   ${C_B}$PROJECT_NAME${C_OFF}  ${C_DIM}· $PROJECT_TAGLINE${C_OFF}"
  echo "  ${C_CY}────────────────────────────────────────────────────${C_OFF}"
  echo "   ${C_GR}✔ Environment ready — you're set for sprint 1.${C_OFF}"
  echo ""
  echo "   ${C_B}Run it${C_OFF}"
  echo "     ./start.sh             dev: backend + frontend (default)"
  echo "     ./start.sh test        run the test suite"
  echo "     ./start.sh status      health check   ·   ./start.sh stop   ·   ./start.sh help"
  echo ""
  info_links next
  echo "  ${C_CY}════════════════════════════════════════════════════${C_OFF}"
  echo ""
  exit 0
}

cmd_stop() { kill_port "$PORT"; [ -n "$FRONTEND_DIR" ] && kill_port "$UI_PORT"; log "Done."; exit 0; }

cmd_status() {
  local be_up=false fe_up=false
  lsof -ti :"$PORT" >/dev/null 2>&1 && be_up=true
  [ -n "$FRONTEND_DIR" ] && lsof -ti :"$UI_PORT" >/dev/null 2>&1 && fe_up=true
  log "Backend  (port $PORT):   $($be_up && echo 'UP' || echo 'DOWN')"
  [ -n "$FRONTEND_DIR" ] && log "Frontend (port $UI_PORT): $($fe_up && echo 'UP' || echo 'DOWN')"
  if $be_up; then
    local health; health=$(curl -sf "http://localhost:$PORT$HEALTH_PATH" 2>/dev/null)
    if [ -n "$health" ]; then
      log "Health: $(echo "$health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('status','?')} | build={d.get('build_stamp','?')}\")" 2>/dev/null || echo "$health")"
    else
      log "Health: endpoint unreachable"
    fi
  fi
  exit 0
}

cmd_test() {
  local PY; PY="$(find_python)"
  if [ "$BACKEND_TYPE" = "python" ]; then
    cd "$SCRIPT_DIR/$BACKEND_DIR"
    "$PY" -m pytest -v --tb=short || {
      rc=$?
      [ "$rc" -eq 5 ] && log "pytest collected no tests — the template ships none; add yours under $BACKEND_DIR/."
      exit "$rc"
    }
  else
    cd "$SCRIPT_DIR" && npm test
  fi
}

cmd_production() {
  local be_dir="$SCRIPT_DIR/$BACKEND_DIR"
  [ "$BACKEND_DIR" = "." ] && be_dir="$SCRIPT_DIR"
  cd "$be_dir"
  if [ "$BACKEND_TYPE" = "python" ]; then
    ensure_backend_env
    local PY; PY="$(find_python)"
    log "Starting $BACKEND_CMD on 0.0.0.0:${PORT} (production)"
    exec "$PY" -m $BACKEND_CMD --host 0.0.0.0 --port "${PORT}"
  else
    npm run build && exec npm run start
  fi
}

cmd_dev() {
  trap cleanup EXIT   # dev runs a background frontend job; reap it on exit
  local with_ui=false
  [[ "${1:-}" == "--ui" ]] && with_ui=true

  local PY=""
  if [ "$BACKEND_TYPE" = "python" ]; then
    ensure_backend_env
    PY="$(find_python)"
  fi

  # Kill stale, clean caches
  kill_port "$PORT"
  $with_ui && kill_port "$UI_PORT"
  local be_dir="$SCRIPT_DIR/$BACKEND_DIR"
  [ "$BACKEND_DIR" = "." ] && be_dir="$SCRIPT_DIR"
  if [ "$BACKEND_TYPE" = "python" ]; then
    export PYTHONDONTWRITEBYTECODE=1
    find "$be_dir" -type d -name __pycache__ -not -path '*/.venv/*' -exec rm -rf {} + 2>/dev/null || true
  fi

  # Build stamp (shown in the banner)
  BUILD_STAMP=$(date "+%Y-%m-%d_%H:%M:%S"); export BUILD_STAMP

  # Start frontend in background
  if $with_ui && [ -n "$FRONTEND_DIR" ]; then
    local fe_dir="$SCRIPT_DIR/$FRONTEND_DIR"
    ensure_frontend_env
    (cd "$fe_dir" && npx vite --port "$UI_PORT" --host --clearScreen false --logLevel warn) &
  fi

  # Banner
  echo ""
  echo "  ${C_CY}════════════════════════════════════════════════════${C_OFF}"
  echo "   ${C_B}$PROJECT_NAME${C_OFF}  ${C_DIM}· $PROJECT_TAGLINE${C_OFF}"
  echo "  ${C_CY}────────────────────────────────────────────────────${C_OFF}"
  echo "   Build $BUILD_STAMP   ·   ${C_B}Ctrl+C to stop${C_OFF}"
  echo ""
  if $with_ui; then
    info_links running
  else
    echo "   API   ${C_CY}http://localhost:$PORT${C_OFF}   docs ${C_CY}/docs${C_OFF}   health ${C_CY}$HEALTH_PATH${C_OFF}"
    echo "   ${C_DIM}(frontend not started — use ./start.sh dev --ui)${C_OFF}"
  fi
  echo "  ${C_CY}════════════════════════════════════════════════════${C_OFF}"
  echo ""

  cd "$be_dir"
  if [ "$BACKEND_TYPE" = "python" ]; then
    local reload_args="--reload"
    for rd in $RELOAD_DIRS; do
      [ -n "$rd" ] && reload_args="$reload_args --reload-dir $rd"
    done
    "$PY" -m $BACKEND_CMD --host 0.0.0.0 --port "${PORT}" $reload_args
  else
    PORT="$PORT" npm run dev
  fi
}

# ── Main dispatch ─────────────────────────────────────
case "${1:-}" in
  "")             cmd_dev --ui ;;     # bare `./start.sh` = full dev stack (parity with .\start.ps1)
  setup)          cmd_setup ;;
  stop)           cmd_stop ;;
  status)         cmd_status ;;
  test)           shift; cmd_test "$@" ;;
  dev)            shift; cmd_dev "$@" ;;
  production)     cmd_production ;;
  help|-h|--help) cmd_help; exit 0 ;;
  *)              log "Unknown command: '$1'"; cmd_help; exit 2 ;;
esac
