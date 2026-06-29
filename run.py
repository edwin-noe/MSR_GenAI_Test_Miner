#!/usr/bin/env python3
"""
Manual job runner.

Deploying the service does NOT run anything (the container just idles). Open a
shell and run a job explicitly:

    python run.py mine            # Phase 1 mining
    python run.py phase2          # Phase 2 validation + Stage B (README language gate)
    python run.py phase2-stage-a  # Phase 2 validation, Stage A only (no API calls)

For a long job that should survive your shell disconnecting, run it detached:

    nohup python run.py phase2 > output/phase2_run.log 2>&1 &
    tail -f output/phase2_run.log

(Do NOT redeploy while a manual job is running — a redeploy restarts the
container and kills the job. It will resume from its checkpoint if relaunched.)
"""
import subprocess
import sys

JOBS = {
    "mine": [sys.executable, "-m", "src.main"],
    "main": [sys.executable, "-m", "src.main"],            # alias for mine
    "phase2": [sys.executable, "scripts/phase2_validation.py", "--stage-b"],
    "phase2-stage-a": [sys.executable, "scripts/phase2_validation.py"],
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(__doc__)
        print("Available jobs:", ", ".join(k for k in JOBS if k != "main"))
        sys.exit(1)
    job = sys.argv[1]
    # pass any extra args through (e.g. python run.py mine --check-rate-limit)
    sys.exit(subprocess.call(JOBS[job] + sys.argv[2:]))


if __name__ == "__main__":
    main()
