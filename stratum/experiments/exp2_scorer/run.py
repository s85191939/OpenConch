"""
Experiment 2: Scorer Learnability (~$80, ~16 GPU-hours)

THE QUESTION: Can a small MLP learn to predict which tokens are important,
WITHOUT being told the answer?

THE METHOD:
1. Load pretrained Mamba-130M (frozen)
2. Generate surrogate salience labels:
   - For each token, measure how much masking it hurts downstream predictions
   - Tokens that hurt the most when removed = most salient
3. Train a 2-layer MLP scorer to predict these labels from Mamba hidden states
4. Compare the scorer's top-k selections against the oracle mask
5. Measure precision, recall, F1 vs oracle

IF THIS WORKS (scorer precision >60% vs oracle):
   → The salience signal is learnable from hidden states. Proceed to Exp 3.

IF THIS FAILS (scorer ~= random):
   → Hidden states don't encode enough info for salience prediction.
   → Need a different training signal or architecture.
"""

import argparse
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.mamba_backbone import MambaBackbone
from models.salience_scorer import SalienceScorer
from data.passkey import PasskeyDataset
from data.ruler_lite import RulerLiteDataset


def compute_salience_labels(backbone, input_ids, n_probes=50):
    """
    Compute ground-truth salience by measuring each token's importance.

    Strategy: for each probed position, zero out the hidden state and
    measure prediction quality degradation. Bigger degradation = more salient.
    """
    with torch.no_grad():
        result = backbone(input_ids)
        hidden = result["hidden_states"]  # (batch, seq, d_model)

        batch_size, seq_len, d_model = hidden.shape
        importance = torch.zeros(batch_size, seq_len, device=hidden.device)

        # Probe random positions
        probe_pos = torch.randint(0, seq_len, (n_probes,))

        for pos in probe_pos:
            # Importance = L2 norm of hidden state (proxy for information content)
            # More sophisticated: measure loss change, but this is cheaper
            importance[:, pos] = torch.norm(hidden[:, pos, :], dim=-1)

        # Normalize per sequence
        max_vals = importance.max(dim=-1, keepdim=True).values
        importance = importance / (max_vals + 1e-8)

    return importance, hidden


def train_scorer(config_path: str):
    """Train the salience scorer and measure oracle alignment."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    device = config["hardware"]["device"]
    dtype = getattr(torch, config["hardware"]["dtype"])

    print("=" * 60)
    print("  Experiment 2: Scorer Learnability")
    print("=" * 60)

    # Load tokenizer and backbone
    print("\n[1/5] Loading tokenizer and frozen backbone...")
    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
    tokenizer.pad_token = tokenizer.eos_token

    backbone = MambaBackbone.from_pretrained(
        config["model"]["backbone"], freeze=True
    ).to(device)

    # Create scorer
    print("[2/5] Creating salience scorer...")
    scorer_cfg = config["scorer"]
    scorer = SalienceScorer(
        d_model=scorer_cfg["d_model"],
        d_inner=scorer_cfg["d_inner"],
        dropout=scorer_cfg["dropout"],
        anchor_ratio=scorer_cfg["anchor_ratio"],
    ).to(device).to(dtype)

    # Create datasets
    print("[3/5] Generating training data...")
    seq_len = config["data"]["seq_lengths"][0]  # Use shortest for training
    train_datasets = []
    for task in config["data"]["tasks"]:
        if task == "passkey":
            ds = PasskeyDataset(tokenizer=tokenizer, seq_len=seq_len,
                              n_samples=config["data"]["n_train_samples"] // len(config["data"]["tasks"]))
        else:
            ds = RulerLiteDataset(tokenizer=tokenizer, task=task, seq_len=seq_len,
                                n_samples=config["data"]["n_train_samples"] // len(config["data"]["tasks"]))
        train_datasets.append(ds)

    # Optimizer
    train_cfg = config["training"]
    optimizer = optim.AdamW(
        scorer.parameters(),
        lr=train_cfg["lr"],
        weight_decay=train_cfg["weight_decay"],
    )

    # Training loop
    print("[4/5] Training scorer...")
    loss_fn = nn.BCEWithLogitsLoss()

    for epoch in range(train_cfg["epochs"]):
        scorer.train()
        epoch_loss = 0
        n_batches = 0

        for dataset in train_datasets:
            loader = torch.utils.data.DataLoader(
                dataset, batch_size=train_cfg["batch_size"], shuffle=True
            )

            for batch in tqdm(loader, desc=f"Epoch {epoch+1}/{train_cfg['epochs']}"):
                input_ids = batch["input_ids"].to(device)
                oracle_mask = batch["oracle_mask"].to(device).float()

                # Get Mamba hidden states (frozen)
                with torch.no_grad():
                    result = backbone(input_ids)
                    hidden = result["hidden_states"].to(dtype)

                # Score with our trainable scorer
                scorer_out = scorer(hidden, return_scores=True)
                scores = scorer_out["scores"]  # (batch, seq_len)

                # Train scorer to predict oracle mask
                loss = loss_fn(scores, oracle_mask)

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(scorer.parameters(), train_cfg["grad_clip"])
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        print(f"  Epoch {epoch+1}: avg_loss = {avg_loss:.4f}")

    # Evaluation: measure alignment with oracle
    print("\n[5/5] Evaluating scorer vs oracle...")
    scorer.eval()

    metrics = {"precision": [], "recall": [], "f1": []}

    for dataset in train_datasets:
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False)

        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            oracle_mask = batch["oracle_mask"].to(device)

            with torch.no_grad():
                result = backbone(input_ids)
                hidden = result["hidden_states"].to(dtype)
                scorer_out = scorer(hidden, return_scores=True)
                pred_mask = scorer_out["anchor_mask"]

            # Compute precision/recall vs oracle per sample
            for b in range(input_ids.shape[0]):
                pred = pred_mask[b]
                oracle = oracle_mask[b]

                tp = (pred & oracle).sum().float()
                fp = (pred & ~oracle).sum().float()
                fn = (~pred & oracle).sum().float()

                precision = tp / (tp + fp + 1e-8)
                recall = tp / (tp + fn + 1e-8)
                f1 = 2 * precision * recall / (precision + recall + 1e-8)

                metrics["precision"].append(precision.item())
                metrics["recall"].append(recall.item())
                metrics["f1"].append(f1.item())

    # Summary
    avg_p = sum(metrics["precision"]) / len(metrics["precision"])
    avg_r = sum(metrics["recall"]) / len(metrics["recall"])
    avg_f1 = sum(metrics["f1"]) / len(metrics["f1"])

    print("\n" + "=" * 60)
    print("  EXPERIMENT 2 SUMMARY")
    print("=" * 60)
    print(f"  Precision vs Oracle: {avg_p:.1%}")
    print(f"  Recall vs Oracle:    {avg_r:.1%}")
    print(f"  F1 vs Oracle:        {avg_f1:.1%}")

    if avg_p > 0.6:
        print("\n  ✓ SCORER LEARNS SALIENCE — Precision >60%. Proceed to Experiment 3.")
    elif avg_p > 0.3:
        print("\n  ~ PARTIAL LEARNING — Some signal but weak. Consider:")
        print("    - More training data or epochs")
        print("    - Better surrogate labels (loss-based instead of norm-based)")
        print("    - Larger scorer (3 layers?)")
    else:
        print("\n  ✗ SCORER FAILS — Hidden states don't carry enough salience info.")
        print("    Investigate: are the oracle masks correct? Is the backbone too small?")

    # Save
    results = {
        "precision": avg_p,
        "recall": avg_r,
        "f1": avg_f1,
        "all_precision": metrics["precision"],
        "all_recall": metrics["recall"],
    }
    output_dir = Path(config["logging"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save scorer weights
    torch.save(scorer.state_dict(), output_dir / "scorer.pt")
    print(f"\n  Results + weights saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp2_scorer.yaml")
    args = parser.parse_args()
    train_scorer(args.config)
