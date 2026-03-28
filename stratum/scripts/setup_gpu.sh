#!/bin/bash
# ============================================================
# STRATUM — Remote GPU Setup Script
# Run this on a Lambda Labs / RunPod / Vast.ai A100 instance
# ============================================================
# Cost estimate:
#   Lambda A100 (40GB): ~$1.10/hr  → $40 for ~36 hours
#   RunPod A100 (40GB): ~$1.64/hr  → $60 for ~36 hours
#   H100 (faster):      ~$2.50/hr  → $90 for ~36 hours
# ============================================================

set -e

echo "=========================================="
echo "  STRATUM GPU Setup"
echo "=========================================="

# 1. System packages
echo "[1/6] Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq git python3-pip > /dev/null 2>&1

# 2. Clone repo
echo "[2/6] Cloning STRATUM..."
if [ ! -d "stratum" ]; then
    # Replace with your actual repo URL
    git clone https://github.com/YOUR_USERNAME/stratum.git
    cd stratum
else
    cd stratum
    git pull
fi

# 3. Python environment
echo "[3/6] Setting up Python environment..."
pip install -q --upgrade pip
pip install -e ".[dev]"

# 4. Install mamba-ssm (requires CUDA)
echo "[4/6] Installing mamba-ssm (this takes ~5 minutes, compiling C++)..."
pip install -q mamba-ssm causal-conv1d

# 5. Install flash-attention
echo "[5/6] Installing flash-attn..."
pip install -q flash-attn --no-build-isolation

# 6. Verify
echo "[6/6] Verifying installation..."
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB')

import mamba_ssm
print(f'mamba-ssm: {mamba_ssm.__version__}')

from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained('EleutherAI/gpt-neox-20b')
print(f'Tokenizer: loaded ({tok.vocab_size} tokens)')

print('\n✓ All dependencies ready.')
"

echo ""
echo "=========================================="
echo "  Setup complete! Run experiments:"
echo "=========================================="
echo ""
echo "  # Experiment 1 (~4 hrs, ~\$5-10)"
echo "  python -m experiments.exp1_oracle.run --config configs/exp1_oracle.yaml"
echo ""
echo "  # Experiment 2 (~16 hrs, ~\$20-40)"
echo "  python -m experiments.exp2_scorer.run --config configs/exp2_scorer.yaml"
echo ""
echo "  # Experiment 3 (~16 hrs, ~\$20-40)"
echo "  python -m experiments.exp3_e2e.run --config configs/exp3_e2e.yaml"
echo ""
echo "  # Or run all three sequentially:"
echo "  bash scripts/run_all.sh"
echo ""
