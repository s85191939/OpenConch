#!/bin/bash
# ============================================================
# Run all three STRATUM experiments sequentially
# Estimated total: ~36 GPU-hours, ~$40-90 depending on instance
# ============================================================

set -e

echo "Starting STRATUM experiment suite..."
echo "Estimated time: ~36 hours on A100"
echo ""

# Experiment 1: Oracle proof (~4 hours)
echo "=========================================="
echo "  EXPERIMENT 1: Oracle Anchor Proof"
echo "=========================================="
python -m experiments.exp1_oracle.run --config configs/exp1_oracle.yaml

# Check if Exp 1 passed before continuing
if python3 -c "
import json
r = json.load(open('results/exp1_oracle/results.json'))
avg_delta = sum(v['delta'] for v in r.values()) / len(r)
exit(0 if avg_delta > 0.05 else 1)
"; then
    echo "✓ Experiment 1 passed. Proceeding to Experiment 2..."
else
    echo "✗ Experiment 1 failed. Oracle anchors don't help enough."
    echo "  Stopping here to save compute budget."
    exit 1
fi

# Experiment 2: Scorer learnability (~16 hours)
echo ""
echo "=========================================="
echo "  EXPERIMENT 2: Scorer Learnability"
echo "=========================================="
python -m experiments.exp2_scorer.run --config configs/exp2_scorer.yaml

# Check if Exp 2 passed
if python3 -c "
import json
r = json.load(open('results/exp2_scorer/results.json'))
exit(0 if r['precision'] > 0.3 else 1)
"; then
    echo "✓ Experiment 2 passed. Proceeding to Experiment 3..."
else
    echo "✗ Experiment 2 failed. Scorer can't learn salience."
    echo "  Stopping here to save compute budget."
    exit 1
fi

# Experiment 3: End-to-end (~16 hours)
echo ""
echo "=========================================="
echo "  EXPERIMENT 3: End-to-End STRATUM"
echo "=========================================="
python -m experiments.exp3_e2e.run --config configs/exp3_e2e.yaml

echo ""
echo "=========================================="
echo "  ALL EXPERIMENTS COMPLETE"
echo "=========================================="
echo "  Results saved to results/"
echo ""
