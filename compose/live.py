"""Compare live compose-api runs of a composite with local runs of the same documents, one emitted key at a time.

usage: uv run --project compose --frozen python -I compose/live.py <record.yaml> [<simulation id> ... --interval N]
       uv run --project compose --frozen python -I compose/live.py <record.yaml> --check

Each run's results archive is fetched with compose-api's own CLI (`compose-api results <id> --extract`, from
COMPOSE_API_DIR, default ~/uchc/biosimulations/compose-api; a private run needs its owner signed in), with the
environment version it ran in (`compose-api simulations show`). The archive holds the document exactly as the service
ran it, and that document runs here through runner.py in this directory's pinned environment; the record names this
machine and the simulator packages that ran locally. Every run is compared with the local run of its own document and
with every other live run, over every row and every emitted value: a value missing on one side, or not finite on one
side only, differs. Per top-level emitted key, the record gives a verdict (identical; within RTOL, the largest
relative difference |a - b| / max(|a|, |b|) being at most RTOL; or differs) and that largest difference to two
significant figures.

With ids, the record is written. With --check, its runs are fetched and compared again, and the script fails if a
run's environment or document, or any key's verdict, has changed. The differences below RTOL are floating-point noise
that can vary by machine, so --check compares verdicts, not those numbers.
"""

import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from itertools import combinations
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
COMPOSE_API = Path(os.environ.get("COMPOSE_API_DIR", Path.home() / "uchc/biosimulations/compose-api"))
RTOL = 1e-9
PACKAGES = ("process-bigraph", "viva-maboss", "viva-tellurium", "viva-pde-particle", "viva-basic-processes")


def compose_api(*args: str) -> str:
    """compose-api's CLI, in its own project (uv warns when it inherits this one's VIRTUAL_ENV)."""
    done = subprocess.run(
        ["uv", "run", "--project", str(COMPOSE_API), "--frozen", "compose-api", "-q", "-o", "json", *args],
        capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"},
    )
    if done.returncode != 0:  # say why: a refusal reads differently from a timeout whose outcome is uncertain
        raise RuntimeError(f"compose-api {' '.join(args[:2])} failed ({done.returncode}): {done.stderr.strip()[-2000:]}")
    return done.stdout


def fetch(simulation_id: int, into: Path) -> tuple[str, Path, Path]:
    """The environment version the run used, and its document and results file, from its archive."""
    shown = json.loads(compose_api("simulations", "show", str(simulation_id)))
    compose_api("results", str(simulation_id), "--extract", str(into))
    [document] = [p for p in into.glob("*.pbg") if not p.name.startswith("state_")]
    [results] = into.glob("results_*.pber")
    return shown["labels"]["environment_version"], document, results


def run_locally(document: Path, interval: float, into: Path) -> Path:
    """The document, run beside the files its archive carried (an SBML model it names, say), as the service ran it."""
    subprocess.run(
        [sys.executable, "-I", str(HERE / "runner.py"), "run", str(document), "-o", str(into), "-n", str(interval)],
        check=True, stdout=subprocess.DEVNULL, cwd=document.parent,
    )
    [results] = into.glob("results_*.pber")
    return results


def local_environment() -> dict:
    """This machine, and the version and commit of each simulator package that ran here."""
    packages = {}
    for name in PACKAGES:
        dist = distribution(name)
        commit = json.loads(dist.read_text("direct_url.json") or "{}").get("vcs_info", {}).get("commit_id")
        packages[name] = f"{dist.version} ({commit[:7]})" if commit else dist.version
    return {"platform": f"{platform.system()} {platform.machine()}", "packages": packages}


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, (*path, key))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield path, float(value)
    else:
        raise SystemExit(f"{'/'.join(path)}: not a number: {value!r}")


def relative(x: float, y: float) -> float:
    """|x - y| / max(|x|, |y|): 0 when equal (NaN with NaN included), infinite when only one side is finite."""
    if x == y or (math.isnan(x) and math.isnan(y)):
        return 0.0
    if not (math.isfinite(x) and math.isfinite(y)):
        return math.inf
    return abs(x - y) / max(abs(x), abs(y))


def rows_of(results: Path) -> list[dict]:
    return json.loads(results.read_text())["emitter"]


def compare(a: list[dict], b: list[dict]) -> dict:
    if len(a) != len(b):
        raise SystemExit(f"row counts differ: {len(a)} and {len(b)}")
    largest: dict[str, float] = {}
    for row_a, row_b in zip(a, b, strict=True):
        values_a, values_b = dict(leaves(row_a)), dict(leaves(row_b))
        for path in values_a.keys() | values_b.keys():
            if path in values_a and path in values_b:
                difference = relative(values_a[path], values_b[path])
            else:
                difference = math.inf
            largest[path[0]] = max(largest.get(path[0], 0.0), difference)
    return {key: {"verdict": verdict(value), "relative_difference": float(f"{value:.2g}")}
            for key, value in sorted(largest.items())}


def verdict(relative_difference: float) -> str:
    if relative_difference == 0:
        return "identical"
    return "within RTOL" if relative_difference <= RTOL else "differs"


def measure(ids: list[int], interval: float) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        runs, results, local = [], {}, {}
        for simulation_id in ids:
            environment, document, results[simulation_id] = fetch(simulation_id, work / str(simulation_id))
            digest = hashlib.sha256(document.read_bytes()).hexdigest()
            if digest not in local:
                local[digest] = run_locally(document, interval, work / f"local-{digest[:12]}")
            runs.append({"id": simulation_id, "environment": environment, "document_sha256": digest,
                         "rows": len(rows_of(results[simulation_id]))})
        comparisons = [
            {"between": [run["id"], "local"],
             "keys": compare(rows_of(results[run["id"]]), rows_of(local[run["document_sha256"]]))}
            for run in runs
        ] + [
            {"between": [a, b], "keys": compare(rows_of(results[a]), rows_of(results[b]))}
            for a, b in combinations(ids, 2)
        ]
    return {"interval": interval, "rtol": RTOL, "local": local_environment(), "runs": runs, "comparisons": comparisons}


def verdicts(record: dict) -> list:
    return [(c["between"], {k: v["verdict"] for k, v in c["keys"].items()}) for c in record["comparisons"]]


def main(argv: list[str]) -> int:
    record_path, rest = Path(argv[0]), argv[1:]
    if rest == ["--check"]:
        committed = yaml.safe_load(record_path.read_text())
        fresh = measure([run["id"] for run in committed["runs"]], committed["interval"])
        if verdicts(fresh) != verdicts(committed) or fresh["runs"] != committed["runs"]:
            print(yaml.safe_dump(fresh, sort_keys=False))
            print(f"{record_path} is stale: the runs or verdicts above differ from it", file=sys.stderr)
            return 1
        print(f"{record_path}: runs and verdicts unchanged")
        return 0
    interval = float(rest[rest.index("--interval") + 1])
    ids = [int(a) for a in rest[: rest.index("--interval")]]
    record = measure(ids, interval)
    header = "# written by compose/live.py (see its docstring); regenerate, never edit by hand\n"
    record_path.write_text(header + yaml.safe_dump(record, sort_keys=False))
    print(yaml.safe_dump(verdicts(record), sort_keys=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
