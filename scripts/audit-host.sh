#!/usr/bin/env bash
set -euo pipefail

out=${1:-results/host-audit.json}
mkdir -p "$(dirname "$out")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

capture() {
  local name=$1; shift
  if "$@" >"$tmp/$name.out" 2>"$tmp/$name.err"; then
    printf 'ok' >"$tmp/$name.status"
  else
    printf 'failed' >"$tmp/$name.status"
  fi
}

capture lscpu lscpu
capture numa numactl --hardware
capture memory free -b
capture gpu nvidia-smi --query-gpu=name,memory.total,driver_version,pci.bus_id,pcie.link.gen.current,pcie.link.width.current --format=csv,noheader
capture processes bash -lc "ps -eo pid,ppid,user,etimes,args | grep -E 'llama-(server|cli)|llama\.cpp' | grep -v grep || true"
capture services bash -lc "systemctl --no-pager --plain --type=service --state=running 2>/dev/null | grep -Ei 'llama|opencode|inference|model' || true"

python3 - "$out" "$tmp" <<'PY'
import json, pathlib, platform, socket, sys, time
out=pathlib.Path(sys.argv[1]); tmp=pathlib.Path(sys.argv[2])
def text(name):
    p=tmp/f'{name}.out'; return p.read_text(errors='replace') if p.exists() else ''
def status(name):
    p=tmp/f'{name}.status'; return p.read_text() if p.exists() else 'missing'
def read(path):
    try:return pathlib.Path(path).read_text().strip()
    except Exception:return None
obj={
 'schema':1,
 'captured_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
 'hostname':socket.gethostname(),
 'platform':platform.platform(),
 'kernel_cmdline':read('/proc/cmdline'),
 'kernel':platform.release(),
 'numa_balancing':read('/proc/sys/kernel/numa_balancing'),
 'thp_enabled':read('/sys/kernel/mm/transparent_hugepage/enabled'),
 'thp_defrag':read('/sys/kernel/mm/transparent_hugepage/defrag'),
 'commands':{name:{'status':status(name),'stdout':text(name)} for name in ('lscpu','numa','memory','gpu','processes','services')}
}
out.write_text(json.dumps(obj,indent=2)+'\n')
PY

python3 -m json.tool "$out" >/dev/null
echo "Wrote read-only audit to $out"
