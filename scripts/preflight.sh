#!/usr/bin/env bash
set -euo pipefail

env_file=${1:-config/host.env}
[[ -f "$env_file" ]] || { echo "Missing $env_file" >&2; exit 2; }
set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

required=(LLAMA_SERVER_BIN MODEL_PATH CANDIDATE_HOST CANDIDATE_PORT STARTUP_TIMEOUT REQUEST_TIMEOUT)
for key in "${required[@]}"; do
  [[ -n "${!key:-}" ]] || { echo "Missing $key" >&2; exit 2; }
done
[[ -x "$LLAMA_SERVER_BIN" ]] || { echo "Not executable: $LLAMA_SERVER_BIN" >&2; exit 2; }
[[ -r "$MODEL_PATH" ]] || { echo "Model not readable: $MODEL_PATH" >&2; exit 2; }
[[ "$CANDIDATE_HOST" == 127.0.0.1 || "$CANDIDATE_HOST" == localhost || "$CANDIDATE_HOST" == ::1 ]] || {
  echo "Candidate host must be loopback" >&2; exit 2;
}
if ss -ltn "sport = :$CANDIDATE_PORT" | tail -n +2 | grep -q .; then
  echo "Candidate port $CANDIDATE_PORT is already in use" >&2; exit 2
fi
command -v python3 >/dev/null
command -v numactl >/dev/null
"$LLAMA_SERVER_BIN" --help > /tmp/old-iron-ai-llama-help.txt 2>&1 || true
for flag in --model --ctx-size --batch-size --ubatch-size --threads --threads-batch --host --port; do
  grep -q -- "$flag" /tmp/old-iron-ai-llama-help.txt || { echo "Unsupported required flag: $flag" >&2; exit 2; }
done
printf 'PREFLIGHT=PASS\nBINARY=%s\nMODEL=%s\nCANDIDATE=%s:%s\n' "$LLAMA_SERVER_BIN" "$MODEL_PATH" "$CANDIDATE_HOST" "$CANDIDATE_PORT"
