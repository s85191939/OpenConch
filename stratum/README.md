# STRATUM

**Stratified Recurrent Attention with Unbounded Memory**

A hybrid SSM-attention architecture that achieves effective ultra-long context by routing
only salient tokens (~0.5%) through full quadratic attention while processing the remaining
99.5% with linear-time Mamba. Three memory strata operate at different timescales to eliminate
the "lost in the middle" failure mode that plagues both transformers and pure SSMs.

## The Core Hypothesis

> A learned salience scorer can identify ~0.5% of tokens that, when given full attention,
> recovers most of the recall quality lost by pure SSM models at long context distances.

If this hypothesis is true, it means:
- You can process 1 billion tokens in linear time (Mamba handles 99.5%)
- The O(n²) attention cost only applies to ~5M anchor tokens (manageable)
- Critical information is never "lost in the middle" because it's elevated to anchor status
  regardless of position

## Architecture

```
                    ┌─────────────────────────┐
                    │      Fusion Gate         │  ← learned per-token weighting
                    │  α·S1 + β·S2 + γ·S3     │
                    └────┬────────┬────────┬───┘
                         │        │        │
              ┌──────────┴──┐  ┌──┴──┐  ┌──┴──────────┐
              │ S3: Anchor  │  │ S2: │  │ S1: Episodic │
              │ Attention   │  │Mamba│  │ Memory       │
              │ (top 0.5%)  │  │ -2  │  │ (compressed  │
              │ Full QKV on │  │chunk│  │  summaries)  │
              │ anchors only│  │proc │  │              │
              └──────┬──────┘  └──┬──┘  └──────┬───────┘
                     │            │             │
                     └────────────┴─────────────┘
                              │
                     ┌────────┴────────┐
                     │ Salience Scorer  │  ← 2-layer MLP on Mamba hidden state
                     │ flags top-k as   │    trained with contrastive signal
                     │ "anchor" tokens  │
                     └────────┬────────┘
                              │
                     ┌────────┴────────┐
                     │   Token Stream   │
                     │  (unbounded)     │
                     └─────────────────┘
```

### Stratum 1 — Episodic Memory
As Mamba processes chunks, it writes compressed summaries into a fixed-size differentiable
memory store. Unlike RAG, this is part of the forward pass — the memory vectors receive
gradients during training, so the model learns *what* to compress. Important information
from any position gets written here and stays accessible.

### Stratum 2 — Mamba-2 Chunk Processor
The workhorse. Processes the raw token stream with O(n) complexity and constant-time
inference (no KV cache). A salience scorer (2-layer MLP) runs on each hidden state and
flags tokens whose salience exceeds a dynamic threshold.

### Stratum 3 — Anchor Attention
Only the ~0.5% of tokens flagged as anchors receive full quadratic attention against each
other. At 1B tokens with 0.5% anchor rate, that's ~5M tokens under attention — tractable
with FlashAttention-3 and pipeline parallelism.

### Fusion Gate
A learned gate combines the three strata per-token per-layer:
- Leans on S2 for local/syntactic reasoning
- Leans on S1 for distant factual recall
- Leans on S3 for precision-critical cross-comparisons

## Complexity Comparison

| Model         | Time Complexity | Memory     | Effective Context |
|---------------|----------------|------------|-------------------|
| Transformer   | O(n²)          | O(n) KV    | ~65% of claimed   |
| Mamba-2       | O(n)           | O(1) state | Degrades >100K    |
| Jamba          | O(n + w²)      | O(w) KV    | 256K              |
| **STRATUM**   | O(n + a²)      | O(s + a)   | Near-100% of n    |

Where: n = sequence length, w = attention window, a = anchor count (~0.5% of n),
s = episodic memory slots (fixed)

## Experiments — Proving It for Under $200

We validate the hypothesis in three stages, from cheapest to most expensive:

### Experiment 1 — Oracle Anchor Proof (~$20, ~4 GPU-hours)
Take pretrained Mamba-130M. On synthetic long-context tasks (passkey retrieval),
measure baseline accuracy. Then **cheat**: manually flag ground-truth important tokens
and give them full attention. If oracle-anchored attention recovers accuracy over pure
Mamba, the architectural ceiling is proven.

### Experiment 2 — Scorer Learnability (~$80, ~16 GPU-hours)
Train the salience scorer on frozen Mamba-130M. Use a surrogate signal: tokens that
cause the largest prediction loss when masked are labeled salient. Train the scorer to
predict these labels. If it achieves >60% precision vs. the oracle, the mechanism is
learnable.

### Experiment 3 — End-to-End Tiny STRATUM (~$80, ~16 GPU-hours)
Train a full STRATUM-130M end-to-end on synthetic long-context data at 16K-32K tokens.
Compare against Mamba-130M and Transformer-130M baselines on recall tasks.

## Project Structure

```
stratum/
├── README.md
├── pyproject.toml
├── configs/
│   ├── exp1_oracle.yaml
│   ├── exp2_scorer.yaml
│   └── exp3_e2e.yaml
├── models/
│   ├── mamba_backbone/       # Mamba-2 wrapper + loading
│   ├── salience_scorer/      # 2-layer MLP scorer
│   ├── anchor_attention/     # Sparse attention on anchors
│   ├── episodic_memory/      # Differentiable memory store
│   └── fusion/               # Learned fusion gate
├── experiments/
│   ├── exp1_oracle/          # Oracle proof-of-concept
│   ├── exp2_scorer/          # Scorer training
│   └── exp3_e2e/             # End-to-end training
├── data/                     # Synthetic data generators
├── eval/                     # RULER-lite evaluation harness
└── scripts/                  # Remote GPU setup + launch
```

## Quick Start

```bash
# On a GPU machine (Lambda Labs, RunPod, etc.)
git clone <repo-url> && cd stratum
pip install -e .

# Run Experiment 1 (cheapest — start here)
python -m experiments.exp1_oracle.run --config configs/exp1_oracle.yaml

# Run Experiment 2
python -m experiments.exp2_scorer.run --config configs/exp2_scorer.yaml

# Run Experiment 3
python -m experiments.exp3_e2e.run --config configs/exp3_e2e.yaml
```

## What Success Looks Like

| Experiment | Metric | Baseline (Mamba) | Target |
|-----------|--------|-----------------|--------|
| Exp 1 | Passkey accuracy @ 8K | ~40% | >85% with oracle anchors |
| Exp 2 | Scorer precision vs oracle | 0% | >60% |
| Exp 3 | RULER-lite recall @ 16K | ~50% | >75% |

If Exp 1 fails (oracle anchors don't help), the architecture is fundamentally flawed.
If Exp 2 fails (scorer can't learn), the mechanism needs redesign.
If Exp 3 fails (end-to-end doesn't converge), it's a training problem, not an architecture problem.

## The Publishable Result

"We demonstrate that learned salience selection recovers X% of oracle-attention recall
quality in an SSM hybrid, suggesting the approach scales to ultra-long contexts."

This is a credible ICLR/NeurIPS workshop paper and a foundation for a larger compute grant.

## Hardware Requirements

- Experiments 1-3: Single A100 (40GB) or H100
- ~36 GPU-hours total (~$180 on Lambda Labs at $2-3/hr)
- No multi-node needed for the proof-of-concept
