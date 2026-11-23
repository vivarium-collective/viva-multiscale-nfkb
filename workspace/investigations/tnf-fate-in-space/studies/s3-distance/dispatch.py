"""Run the distance study's 378 batches on compose-api and bring their results home (decision 59;
docs/design/plan-compose-api-dispatch.md).

compose-api is the record. Every run is private, tagged `nfkb-s3-distance` and `s3:<point>-batch<k>`, and runs in
mash-bb433b1002@3, the version that has viva-basic-processes' TimeSeriesStep, for 24 h of simulated time (a long run:
the submitter needs compose-api's `long-runs` role).

- `submit` sends every batch that has no run there yet, or whose runs all failed (once more; a batch that failed twice
  is reported and left), and never lets more than --max-active of the study's runs be active at once: the service's
  queue is shared and has no per-user limit. It returns when every batch has a run that completed or is under way. A
  run compose-api calls `unknown` (a SLURM state it does not map, such as NODE_FAIL) never ends there, so one
  submitted longer ago than the job limit counts as failed. One submit runs at a time (a lock), and only as the account
  that first submitted: the runs are private, so another account would see none of them and send them all again.
- `collect` fetches each completed run's results and writes them to parquet-runs/ through distance_study.write_batch, as
  a local run writes them, after checking that the run ran in the right environment version and that its document is
  the one distance_study.document builds today. distance_study.py then reads every batch back and summarizes.

    uv run --frozen --extra simulators python -I \\
        workspace/investigations/tnf-fate-in-space/studies/s3-distance/dispatch.py submit [--max-active N]
    uv run --frozen --extra simulators python -I \\
        workspace/investigations/tnf-fate-in-space/studies/s3-distance/dispatch.py collect

compose-api's CLI runs from COMPOSE_API_DIR (default ~/uchc/biosimulations/compose-api), signed in as the submitter.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
STUDY_TAG = "nfkb-s3-distance"
ENVIRONMENT, VERSION = "mash-bb433b1002", 3
TERMINAL = {"completed", "failed", "cancelled", "out_of_memory", "timeout"}  # compose-api's JobStatus; others: active
ATTEMPTS = 2
POLL_S = 60.0
JOB_LIMIT = datetime.timedelta(minutes=720)  # compose-api's longest job (LONG_RUN_MAX_MINUTES); a run takes ~17 min
LOCK, OWNER = HERE / ".dispatch.lock", HERE / ".dispatch-owner"  # git-ignored


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


study = _load("distance_study", HERE / "distance_study.py")
live = _load("live", ROOT / "compose" / "live.py")  # compose-api's CLI, as the MVP's live record calls it


def key(arm: str, minutes: int, ring: str, bolus: float, batch: int) -> str:
    return f"s3:{study.point_name(arm, minutes, ring, bolus)}-batch{batch}"


def batches() -> dict[str, tuple[str, int, str, float, int]]:
    """Every batch of every point, by its run key, in the order distance_study.py runs them."""
    return {key(arm, minutes, ring, bolus, b): (arm, minutes, ring, bolus, b)
            for b in range(1, study.BATCHES + 1) for arm, minutes, ring, bolus in study.points()}


def runs() -> dict[str, list[dict]]:
    """The study's runs on compose-api, by run key, newest first."""
    found: dict[str, list[dict]] = {}
    offset = 0
    while True:
        page = json.loads(live.compose_api("simulations", "list", "--mine", "--tag", STUDY_TAG,
                                           "--limit", "200", "--offset", str(offset)))
        if not page:  # an empty page, not a short one, ends the listing: a missed run would be sent twice
            break
        for run in page:
            for tag in run["tags"]:
                if tag.startswith("s3:"):
                    found.setdefault(tag, []).append(run)
        offset += len(page)
    for listed in found.values():
        listed.sort(key=lambda r: r["simulation_id"], reverse=True)
    return found


def stuck(run: dict) -> bool:
    """A run compose-api will never finish: `unknown`, and submitted longer ago than any job may run (`created_at` is
    UTC with its zone; `start_time` comes without one, in the service's or the cluster's local time)."""
    submitted = datetime.datetime.fromisoformat(run["created_at"])
    return run["status"] == "unknown" and datetime.datetime.now(datetime.UTC) - submitted > JOB_LIMIT


def under_way(run: dict) -> bool:
    return run["status"] not in TERMINAL and not stuck(run)


def signed_in_as() -> str:
    identity = json.loads(live.compose_api("auth", "status")).get("identity") or {}
    if not identity.get("subject"):
        raise SystemExit("not signed in to compose-api: run `compose-api auth login` (the runs are long and private)")
    return f"{identity['issuer']}#{identity['subject']}"


def submit(max_active: int) -> None:
    with LOCK.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(f"another submit holds {LOCK}") from None
        account = signed_in_as()
        if OWNER.exists() and OWNER.read_text().strip() != account:
            raise SystemExit(f"the study's runs were submitted by another account ({OWNER}); sign in as that one")
        OWNER.write_text(account + "\n")
        _submit(max_active)


def _submit(max_active: int) -> None:
    todo, population = batches(), study._population()
    while True:
        state = runs()
        active = sum(1 for listed in state.values() for r in listed if under_way(r))
        pending, given_up = [], []
        for k in todo:
            listed = state.get(k, [])
            if any(r["status"] == "completed" or under_way(r) for r in listed):
                continue
            (given_up if len(listed) >= ATTEMPTS else pending).append(k)
        unknown = [r["simulation_id"] for listed in state.values() for r in listed if r["status"] == "unknown"]
        print(f"{time.strftime('%H:%M:%S')} {active} active, {len(pending)} to send, {len(given_up)} failed "
              f"{ATTEMPTS} times" + (f"; unknown to compose-api: {unknown}" if unknown else ""), flush=True)
        if not pending:
            for k in given_up:
                print(f"  {k}:", ", ".join(f"{r['simulation_id']} {r['status']}" for r in state[k]))
            return
        with tempfile.TemporaryDirectory() as tmp:
            for k in pending[: max(0, max_active - active)]:
                archive = population.pack(study.document(*todo[k]), Path(tmp) / f"{k[3:]}.omex")
                sent = json.loads(live.compose_api(
                    "run", str(archive), "--environment", ENVIRONMENT, "--environment-version", str(VERSION),
                    "--interval", str(study.HOURS * 3600.0), "--visibility", "private", "--tag", STUDY_TAG, "--tag", k,
                    "--description", f"NF-kB distance study (decision 59), {k[3:]}"))
                print(f"  sent {k}: {sent['simulation_database_id']}", flush=True)
        time.sleep(POLL_S)


def collect() -> None:
    state = runs()
    written = waiting = 0
    for k, task in batches().items():
        out = study.batch_path(*task)
        if out.exists():
            continue
        done = next((r for r in state.get(k, []) if r["status"] == "completed"), None)
        if done is None:
            waiting += 1
            continue
        with tempfile.TemporaryDirectory() as tmp:
            environment, document, results = live.fetch(done["simulation_id"], Path(tmp))
            if environment != f"{ENVIRONMENT}@{VERSION}":
                raise SystemExit(f"{k}: run {done['simulation_id']} ran in {environment}, not {ENVIRONMENT}@{VERSION}")
            expected = hashlib.sha256(json.dumps(study.document(*task)).encode()).hexdigest()
            if hashlib.sha256(document.read_bytes()).hexdigest() != expected:
                raise SystemExit(f"{k}: run {done['simulation_id']} ran another document than distance_study builds")
            sbml = study._population().SBML
            if (document.parent / sbml.name).read_bytes() != sbml.read_bytes():
                raise SystemExit(f"{k}: run {done['simulation_id']} ran another {sbml.name} than this workspace's")
            study.write_batch(results, out)
        written += 1
    print(f"wrote {written} batches; {waiting} have no completed run yet")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    send = commands.add_parser("submit", help="send every batch not yet run, at most --max-active at once")
    send.add_argument("--max-active", type=int, default=20, help="the study's runs active at once (a shared queue)")
    commands.add_parser("collect", help="write each completed run's results to parquet-runs/")
    args = parser.parse_args()
    if args.command == "submit":
        submit(args.max_active)
    else:
        collect()


if __name__ == "__main__":
    main()
