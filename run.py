#!/usr/bin/env python3
"""
Manual job runner.

Deploying the service does NOT run anything (the container just idles). Open a
shell and run a job explicitly:

    python run.py mine            # Phase 1 mining
    python run.py phase2          # Phase 2 validation + Stage B (README language gate)
    python run.py phase2-stage-a  # Phase 2 validation, Stage A only (no API calls)
    python run.py phase3          # Phase 3 SAGA detection over the validated corpus

For a long job that should survive your shell disconnecting, run it detached:

    nohup python run.py phase3 > output/phase3_run.log 2>&1 &
    tail -f output/phase3_run.log

phase3 reads output/phase2/validated_repos.csv and writes output/phase3/. It is
checkpointed and resumable: if the container restarts, just run it again and it
continues from where it stopped (skips repos already in output/phase3/.progress_full.txt).

(Do NOT redeploy while a manual job is running — a redeploy restarts the
container and kills the job. It will resume from its checkpoint if relaunched.)
"""
import os
import subprocess
import sys

# output/ is the Railway volume; point Phase 3 at the Phase 2 result there.
PHASE3_ENV = {
    "PHASE2_CSV": os.path.join("output", "phase2", "validated_repos.csv"),
    "PHASE3_DIR": os.path.join("output", "phase3"),
}

JOBS = {
    "mine": ([sys.executable, "-m", "src.main"], {}),
    "main": ([sys.executable, "-m", "src.main"], {}),            # alias for mine
    "phase2": ([sys.executable, "scripts/phase2_validation.py", "--stage-b"], {}),
    "phase2-stage-a": ([sys.executable, "scripts/phase2_validation.py"], {}),
    "phase3": ([sys.executable, "scripts/phase3_saga_detect.py", "--all",
                "--out-suffix", "_full"], PHASE3_ENV),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(__doc__)
        print("Available jobs:", ", ".join(k for k in JOBS if k != "main"))
        sys.exit(1)
    job = sys.argv[1]
    cmd, extra_env = JOBS[job]
    env = {**os.environ, **extra_env}
    # pass any extra args through (e.g. python run.py phase3 --max-commits 10000)
    sys.exit(subprocess.call(cmd + sys.argv[2:], env=env))


if __name__ == "__main__":
    main()
