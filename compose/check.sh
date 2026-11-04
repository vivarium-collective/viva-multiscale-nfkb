#!/usr/bin/env bash
# Run this workspace's checks exactly as compose-api runs a compliance case:
#   1. the case's document (and its files, zipped as an .omex, as /simulation/run receives them) runs through
#      compose-api's own runner.py (vendored here, see RUNNER_SOURCE) in the pinned mash-up environment (this
#      directory's pyproject.toml / uv.lock);
#   2. the results file is scored by compose-api's own compliance.evaluate (from a compose-api checkout).
#
# usage: compose/check.sh <group> [<case>]        cases live in checks/<group>/<case>/case.yaml
#   COMPOSE_API_DIR  compose-api checkout to score with (default: ~/uchc/biosimulations/compose-api)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(dirname "$here")"
checks="$root/checks"
group="${1:?usage: compose/check.sh <group> [<case>]}"
only="${2:-}"
compose_api="${COMPOSE_API_DIR:-$HOME/uchc/biosimulations/compose-api}"
out_root="$root/.checks-out/$group"

status=0
for case_dir in "$checks/$group"/*/; do
  case_name="$(basename "$case_dir")"
  [[ -n "$only" && "$case_name" != "$only" ]] && continue
  [[ -f "$case_dir/case.yaml" ]] || continue
  out="$out_root/$case_name"
  rm -rf "$out" && mkdir -p "$out/input"

  # the case's document, interval and files, read with the pinned environment's yaml
  read -r document interval files < <(uv run --project "$here" --frozen python -I -c '
import sys, yaml
case = yaml.safe_load(open(sys.argv[1]))
print(case["document"], case.get("interval", 1.0), ",".join(case.get("files", [])) or "-")
' "$case_dir/case.yaml")

  if [[ "$files" == "-" ]]; then
    input="$out/input/$document"
    cp "$case_dir/$document" "$input"
  else
    input="$out/input/$case_name.omex"
    (cd "$case_dir" && zip -q -X "$input" "$document" ${files//,/ })
  fi

  echo "== $group/$case_name (interval $interval)"
  uv run --project "$here" --frozen python -I "$here/runner.py" run "$input" -o "$out/output" -n "$interval" \
    > "$out/runner.log" 2>&1 || { echo "   runner FAILED (see $out/runner.log)"; tail -5 "$out/runner.log"; status=1; continue; }

  pber="$(ls "$out"/output/results_*.pber 2>/dev/null | head -1)"
  [[ -n "$pber" ]] || { echo "   no results file (see $out/runner.log)"; status=1; continue; }

  uv run --project "$compose_api" --frozen python -I -c '
import sys
from pathlib import Path
from compose_api.environments.compliance import case_problems, evaluate, load_cases, results_of
checks, group, name, pber = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
[case] = [c for c in load_cases(group, checks) if c.name == name]
problems = case_problems(case)
outcome = evaluate(case, results_of(pber.read_text()))
for line in problems + outcome.failures:
    print("   FAIL", line)
print("   PASS" if outcome.passed and not problems else "   FAILED")
sys.exit(0 if outcome.passed and not problems else 1)
' "$checks" "$group" "$case_name" "$pber" || status=1
done
exit $status
