#!/usr/bin/env bash
set -Eeuo pipefail

# =============================================================================
# Configuration — adjust these paths or override them with environment vars.
# =============================================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"
NOTEBOOK_PATH="${NOTEBOOK_PATH:-$PROJECT_DIR/notebook/AI_Related_State_Policy_Activity_Pipeline.ipynb}"
EXECUTED_DIR="${EXECUTED_DIR:-$PROJECT_DIR/notebook/executed}"
STATE_NEWS_OUTPUT_DIR="${STATE_NEWS_OUTPUT_DIR:-$PROJECT_DIR/state_news_output}"
OUTPUT_CSV_PATH="${OUTPUT_CSV_PATH:-$STATE_NEWS_OUTPUT_DIR/ai_policy_activity_candidates.csv}"
DASHBOARD_CSV_PATH="${DASHBOARD_CSV_PATH:-$PROJECT_DIR/data/ai_policy_activity_candidates.csv}"
PORT="${PORT:-8501}"

SKIP_NOTEBOOK=0
for arg in "$@"; do
  case "$arg" in
    --skip-notebook) SKIP_NOTEBOOK=1 ;;
    -h|--help)
      echo "Usage: ./run_pipeline.sh [--skip-notebook]"
      echo "  --skip-notebook  Reuse OUTPUT_CSV_PATH, or the packaged data CSV if present."
      exit 0
      ;;
    *) echo "Unknown argument: $arg" >&2; exit 64 ;;
  esac
done

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  fail "Python was not found. Install Python 3.10+ and set PYTHON_BIN if needed."
fi
PY_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
log "Using Python $PY_VERSION ($PYTHON_BIN)"

if [[ ! -d "$VENV_DIR" ]]; then
  log "Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR" || fail "Could not create venv. On Debian/Ubuntu, install python3-venv."
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$PROJECT_DIR/requirements.txt"

mkdir -p "$PROJECT_DIR/data" "$EXECUTED_DIR" "$STATE_NEWS_OUTPUT_DIR"

if [[ "$SKIP_NOTEBOOK" -eq 0 ]]; then
  [[ -f "$NOTEBOOK_PATH" ]] || fail "Notebook not found: $NOTEBOOK_PATH"
  export STATE_NEWS_OUTPUT_DIR
  log "Executing notebook: $NOTEBOOK_PATH"
  python -m jupyter nbconvert \
    --to notebook \
    --execute "$NOTEBOOK_PATH" \
    --output "executed_ai_policy_pipeline.ipynb" \
    --output-dir "$EXECUTED_DIR" \
    --ExecutePreprocessor.timeout=1800 \
    --ExecutePreprocessor.kernel_name=python3 \
    || fail "Notebook execution failed. See the nbconvert error above."
  SOURCE_CSV="$STATE_NEWS_OUTPUT_DIR/ai_policy_activity_candidates.csv"
  [[ "$OUTPUT_CSV_PATH" == "$SOURCE_CSV" ]] || {
    [[ -f "$SOURCE_CSV" ]] || fail "Expected notebook output not found: $SOURCE_CSV"
    mkdir -p "$(dirname "$OUTPUT_CSV_PATH")"
    cp "$SOURCE_CSV" "$OUTPUT_CSV_PATH"
    SOURCE_CSV="$OUTPUT_CSV_PATH"
  }
else
  log "Notebook execution skipped. Reusing an existing candidate CSV."
  if [[ -f "$OUTPUT_CSV_PATH" ]]; then
    SOURCE_CSV="$OUTPUT_CSV_PATH"
  elif [[ -f "$DASHBOARD_CSV_PATH" ]]; then
    SOURCE_CSV="$DASHBOARD_CSV_PATH"
  else
    fail "No CSV found. Set OUTPUT_CSV_PATH or add data/ai_policy_activity_candidates.csv."
  fi
fi

python "$PROJECT_DIR/scripts/validate_and_copy.py" --input "$SOURCE_CSV" --output "$DASHBOARD_CSV_PATH" \
  || fail "Candidate CSV validation/copy failed."

export DASHBOARD_CSV_PATH
log "Starting dashboard at http://localhost:$PORT"
exec python -m streamlit run "$PROJECT_DIR/dashboard.py" --server.port "$PORT" --server.address 127.0.0.1
