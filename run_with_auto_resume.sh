#!/bin/bash

# Auto-resume script for MSR GenAI Test Miner
# Automatically waits when rate limit is hit, then resumes

LOGFILE="output/mining_output.log"
RATE_CHECK_INTERVAL=300  # Check rate limit every 5 minutes
WAIT_TIME=1800  # Wait 30 minutes (1800 seconds) when exhausted

echo "======================================"
echo "MSR GenAI Test Miner - Auto Resume Mode"
echo "======================================"
echo "Started at:  $(date)"
echo "Log file: $LOGFILE"
echo ""

# Load environment
source .venv/bin/activate

# Function to check rate limit
check_rate_limit() {
    python3 -m src.main --check-rate-limit 2>/dev/null | grep "Core API:" | awk '{print $3}' | cut -d'/' -f1
}

# Function to run miner until rate limit exhausted
run_miner() {
    echo "[$(date)] Starting mining process..."
    python3 -m src.main >> "$LOGFILE" 2>&1
    exit_code=$?
    echo "[$(date)] Mining process exited with code:  $exit_code"
}

# Main loop
while true; do
    # Check current rate limit
    remaining=$(check_rate_limit)

    if [ -z "$remaining" ]; then
        echo "[$(date)] ⚠️  Could not check rate limit, retrying in 1 minute..."
        sleep 60
        continue
    fi

    echo "[$(date)] 📊 Core API remaining: $remaining/5000"

    if [ "$remaining" -lt 100 ]; then
        echo "[$(date)] ⏸️  Rate limit low ($remaining requests left)"
        echo "[$(date)] ⏰ Waiting 30 minutes for rate limit reset..."
        echo "[$(date)] Will resume at: $(date -v+30M)"
        sleep $WAIT_TIME
        echo "[$(date)] ✅ Wait complete, resuming..."
    else
        echo "[$(date)] ✅ Sufficient API quota available"
        run_miner

        # Check if mining completed successfully
        if [ $exit_code -eq 0 ]; then
            echo "[$(date)] 🎉 Mining completed successfully!"
            break
        else
            echo "[$(date)] ⚠️  Mining stopped (possibly rate limited)"
            echo "[$(date)] ⏰ Waiting 30 minutes before retry..."
            sleep $WAIT_TIME
        fi
    fi
done

echo ""
echo "======================================"
echo "Mining session ended at:  $(date)"
echo "======================================"
