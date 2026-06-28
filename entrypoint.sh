#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Job dispatcher for Railway (and local) runs.
#
# Deploying the service does NOT automatically run any job. The container idles
# until you explicitly choose a job via the RUN_JOB environment variable. This
# prevents the failure mode where simply re-deploying / waking the service
# re-launches a long mining run.
#
# A completion sentinel written to the output volume stops a redeploy or restart
# from re-running a job that already finished. Set FORCE_RERUN=1 to override.
#
#   RUN_JOB=mine             → python -m src.main           (Phase 1 mining)
#   RUN_JOB=phase2           → Phase 2 validation + Stage B (language gate)
#   RUN_JOB=phase2-stage-a   → Phase 2 validation, Stage A only (no API)
#   RUN_JOB unset / idle     → container just idles, ready to inspect/exec
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

JOB="${RUN_JOB:-idle}"
OUTPUT_DIR="${OUTPUT_DIR:-output}"
mkdir -p "$OUTPUT_DIR"
SENTINEL="$OUTPUT_DIR/.completed_${JOB}"

idle() {
  echo "[entrypoint] idling. Set RUN_JOB=mine|phase2|phase2-stage-a and redeploy (or exec a runner) to start a job."
  exec tail -f /dev/null
}

if [ "$JOB" = "idle" ]; then
  echo "[entrypoint] RUN_JOB not set — nothing to run on this deploy."
  idle
fi

if [ -f "$SENTINEL" ] && [ "${FORCE_RERUN:-0}" != "1" ]; then
  echo "[entrypoint] job '$JOB' already completed (found $SENTINEL)."
  echo "[entrypoint] set FORCE_RERUN=1 to run it again."
  idle
fi

echo "[entrypoint] starting job: $JOB"
case "$JOB" in
  mine)            python -m src.main ;;
  phase2)          python scripts/phase2_validation.py --stage-b ;;
  phase2-stage-a)  python scripts/phase2_validation.py ;;
  *)
    echo "[entrypoint] unknown RUN_JOB='$JOB' (expected: mine | phase2 | phase2-stage-a)"
    idle
    ;;
esac

touch "$SENTINEL"
echo "[entrypoint] job '$JOB' finished successfully. Sentinel written: $SENTINEL"
idle
