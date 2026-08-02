#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=/opt/old-iron-ai
STATE_ROOT=/var/lib/old-iron-ai
CURRENT="$STATE_ROOT/current"
cmd="${1:-status}"

unit(){ cat "$STATE_ROOT/current-unit" 2>/dev/null || true; }
run_dir(){ cat "$STATE_ROOT/current-run" 2>/dev/null || true; }

launch_existing() {
  local run_dir="$1" unit stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  unit="old-iron-ai-$stamp"
  printf '%s\n' "$run_dir" >"$STATE_ROOT/current-run"
  printf '%s\n' "$unit" >"$STATE_ROOT/current-unit"
  ln -sfn "$run_dir" "$CURRENT"
  systemd-run --unit="$unit" --description="Old Iron AI benchmark suite" \
    --property=KillMode=control-group --property=TimeoutStartSec=infinity \
    --working-directory="$ROOT" \
    /usr/bin/python3 "$ROOT/benchmarks/tools/run_suite.py" \
      --env "$run_dir/runtime.env" --matrix "$run_dir/matrix.json" --run-dir "$run_dir"
  echo RESULT=SUITE_STARTED
  echo UNIT="$unit"
  echo RUN_DIR="$run_dir"
}

case "$cmd" in
  start)
    [[ $# -eq 3 ]] || { echo "usage: old-iron-control start ENV MATRIX"; exit 2; }
    env_file="$(realpath "$2")"; matrix="$(realpath "$3")"
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"; r="$STATE_ROOT/runs/$stamp"
    mkdir -p "$r"
    cp "$env_file" "$r/runtime.env"; chmod 0600 "$r/runtime.env"
    cp "$matrix" "$r/matrix.json"
    launch_existing "$r" ;;
  resume)
    r="$(run_dir)"; [[ -d "$r" ]] || { echo ERROR=NO_RUN; exit 1; }
    u="$(unit)"; [[ -z "$u" || "$(systemctl is-active "$u" 2>/dev/null || true)" != active ]] || { echo ERROR=RUN_ALREADY_ACTIVE; exit 1; }
    rm -f "$r/PAUSE_REQUESTED" "$r/ABORT_REQUESTED"
    launch_existing "$r" ;;
  pause)
    r="$(run_dir)"; u="$(unit)"; [[ -d "$r" ]] || exit 1
    touch "$r/PAUSE_REQUESTED"
    systemctl kill --signal=SIGTERM "$u" 2>/dev/null || true
    echo RESULT=PAUSE_REQUESTED ;;
  abort)
    r="$(run_dir)"; u="$(unit)"; [[ -d "$r" ]] || exit 1
    touch "$r/ABORT_REQUESTED"
    systemctl kill --signal=SIGTERM "$u" 2>/dev/null || true
    echo RESULT=ABORT_REQUESTED ;;
  status)
    r="$(run_dir)"; u="$(unit)"; echo UNIT="$u"; echo RUN_DIR="$r"
    [[ -n "$u" ]] && systemctl show "$u" -p ActiveState -p SubState -p Result -p MainPID --no-pager 2>/dev/null || true
    [[ -f "$r/state.json" ]] && cat "$r/state.json" || true
    [[ -f "$r/results.jsonl" ]] && { echo '=== LAST RESULTS ==='; tail -5 "$r/results.jsonl"; } || true ;;
  journal)
    u="$(unit)"; journalctl -u "$u" -n "${2:-200}" --no-pager ;;
  report)
    r="$(run_dir)"; [[ -f "$r/results.jsonl" ]] || { echo ERROR=NO_RESULTS; exit 1; }
    python3 "$ROOT/benchmarks/tools/analyze_runs.py" --input "$r/results.jsonl" --output "$r/summary.json"
    cat "$r/summary.json" ;;
  *) echo "usage: old-iron-control {start ENV MATRIX|status|journal [N]|pause|resume|abort|report}"; exit 2 ;;
esac
