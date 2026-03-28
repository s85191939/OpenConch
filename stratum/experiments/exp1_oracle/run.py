"""
Experiment 1: Oracle Anchor Proof (~$20, ~4 GPU-hours)

THE QUESTION: If we cheat and tell the model exactly which tokens matter,
does adding attention to those tokens fix the recall problem?

THE METHOD:
1. Load pretrained Mamba-130M
2. Run passkey retrieval and RULER-lite tasks
3. Measure baseline accuracy (pure Mamba, no attention)
4. Inject oracle anchor attention: manually mark the ground-truth
   important tokens and run full attention on just those tokens
5. Measure accuracy again

IF THIS WORKS (oracle anchors >> baseline):
   → The architecture is sound. The ceiling is high. Proceed to Exp 2.

IF THIS FAILS (oracle anchors ≈ baseline):
   → Attention on sparse tokens doesn't help. The architecture is flawed.
   → Save your money, don't run Exp 2 or 3.

This is the cheapest possible test of the core hypothesis.
"""

import argparse
import yaml
import torch
import json
from pathlib import Path
from transformers import AutoTokenizer

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.mamba_backbone import MambaBackbone
from models.anchor_attention import AnchorAttention
from data.passkey import PasskeyDataset
from data.ruler_lite import RulerLiteDataset
from eval.harness import evaluate_model, print_results


class OracleAugmentedMamba(torch.nn.Module):
    """
    Mamba backbone + anchor attention on oracle-selected tokens.

    This is NOT a real model — it's a diagnostic tool. It cheats by
    using the ground-truth oracle mask to select anchor tokens. The
    point is to measure the ceiling: how much does attention help
    when you know exactly where to apply it?
    """

    def __init__(self, backbone, attention, lm_head, use_oracle: bool = True):
        super().__init__()
        self.backbone = backbone
        self.attention = attention
        self.lm_head = lm_head
        self.use_oracle = use_oracle
        self._oracle_mask = None

    def set_oracle_mask(self, mask):
        """Set the oracle mask for the next forward pass."""
        self._oracle_mask = mask

    def forward(self, input_ids):
        # Run Mamba backbone
        result = self.backbone(input_ids)
        hidden = result["hidden_states"]

        if self.use_oracle and self._oracle_mask is not None:
            # Apply attention to oracle-selected tokens
            attn_out = self.attention(hidden, self._oracle_mask)
            # Residual connection: add attention output to Mamba output
            hidden = hidden + attn_out

        # Project to vocab
        logits = self.lm_head(hidden)

        return {"logits": logits}


def run_experiment(config_path: str):
    """Run the oracle anchor proof experiment."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    device = config["hardware"]["device"]
    dtype = getattr(torch, config["hardware"]["dtype"])

    print("=" * 60)
    print("  Experiment 1: Oracle Anchor Proof")
    print("=" * 60)

    # Load tokenizer
    print("\n[1/5] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
    tokenizer.pad_token = tokenizer.eos_token

    # Load Mamba backbone
    print("[2/5] Loading Mamba-130M backbone...")
    backbone = MambaBackbone.from_pretrained(
        config["model"]["backbone"],
        freeze=True,
    )
    backbone = backbone.to(device)

    # Get LM head from the pretrained model
    from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel
    pretrained = MambaLMHeadModel.from_pretrained(
        config["model"]["backbone"], device=device, dtype=dtype
    )
    lm_head = pretrained.lm_head

    # Create anchor attention module
    print("[3/5] Creating anchor attention module...")
    attention = AnchorAttention(
        d_model=config["attention"]["d_model"],
        n_heads=config["attention"]["n_heads"],
        dropout=config["attention"]["dropout"],
    ).to(device).to(dtype)

    # Initialize attention weights (Xavier)
    for p in attention.parameters():
        if p.dim() > 1:
            torch.nn.init.xavier_uniform_(p)

    # Create evaluation datasets
    print("[4/5] Generating evaluation datasets...")
    all_results = {}

    for seq_len in config["data"]["seq_lengths"]:
        for task_name in config["data"]["tasks"]:
            print(f"\n--- Task: {task_name}, Seq Length: {seq_len} ---")

            if task_name == "passkey":
                dataset = PasskeyDataset(
                    tokenizer=tokenizer,
                    seq_len=seq_len,
                    n_samples=config["data"]["n_samples_per_task"],
                    passkey_positions=config["data"]["passkey_positions"],
                )
            else:
                dataset = RulerLiteDataset(
                    tokenizer=tokenizer,
                    task=task_name,
                    seq_len=seq_len,
                    n_samples=config["data"]["n_samples_per_task"],
                )

            # --- Run 1: Baseline (pure Mamba, no attention) ---
            print(f"  Running baseline (pure Mamba)...")
            baseline_model = OracleAugmentedMamba(
                backbone, attention, lm_head, use_oracle=False
            )
            baseline_results = evaluate_model(
                baseline_model, tokenizer, dataset,
                batch_size=config["eval"]["batch_size"],
                device=device,
            )
            print_results(baseline_results, f"Baseline Mamba ({task_name} @ {seq_len})")

            # --- Run 2: Oracle attention (cheat with ground-truth mask) ---
            print(f"  Running oracle-augmented Mamba...")
            oracle_model = OracleAugmentedMamba(
                backbone, attention, lm_head, use_oracle=True
            )

            # Custom eval loop that sets oracle masks
            oracle_correct = 0
            oracle_total = 0
            for i in range(len(dataset)):
                sample = dataset[i]
                input_ids = sample["input_ids"].unsqueeze(0).to(device)
                oracle_mask = sample["oracle_mask"].unsqueeze(0).to(device)

                oracle_model.set_oracle_mask(oracle_mask)

                with torch.no_grad():
                    output = oracle_model(input_ids)
                    logits = output["logits"]
                    pred_token = logits[0, -1, :].argmax().item()
                    pred_text = tokenizer.decode([pred_token]).strip()

                target = sample.get("passkey") or sample.get("answer", "")
                if pred_text.startswith(str(target)[:3]):  # Partial match
                    oracle_correct += 1
                oracle_total += 1

            oracle_acc = oracle_correct / max(oracle_total, 1)
            print(f"  Oracle Accuracy: {oracle_acc:.1%} ({oracle_correct}/{oracle_total})")

            # Record results
            key = f"{task_name}_{seq_len}"
            all_results[key] = {
                "baseline_accuracy": baseline_results["accuracy"],
                "oracle_accuracy": oracle_acc,
                "delta": oracle_acc - baseline_results["accuracy"],
                "baseline_by_position": baseline_results.get("accuracy_by_position", {}),
            }

    # --- Summary ---
    print("\n" + "=" * 60)
    print("  EXPERIMENT 1 SUMMARY")
    print("=" * 60)

    for key, res in all_results.items():
        delta_str = f"+{res['delta']:.1%}" if res['delta'] > 0 else f"{res['delta']:.1%}"
        print(f"  {key:30s}  Baseline: {res['baseline_accuracy']:.1%}  Oracle: {res['oracle_accuracy']:.1%}  Delta: {delta_str}")

    avg_delta = sum(r["delta"] for r in all_results.values()) / len(all_results)
    print(f"\n  Average improvement from oracle anchors: {avg_delta:+.1%}")

    if avg_delta > 0.15:
        print("\n  ✓ HYPOTHESIS SUPPORTED — Oracle anchors significantly improve recall.")
        print("    Proceed to Experiment 2 (scorer learnability).")
    elif avg_delta > 0.05:
        print("\n  ~ MARGINAL — Some improvement but may not justify the architecture.")
        print("    Consider adjusting anchor ratio or attention capacity before Exp 2.")
    else:
        print("\n  ✗ HYPOTHESIS NOT SUPPORTED — Anchored attention doesn't help enough.")
        print("    Investigate whether the issue is attention init, task design, or fundamental.")

    # Save results
    output_dir = Path(config["logging"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to {output_dir / 'results.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp1_oracle.yaml")
    args = parser.parse_args()
    run_experiment(args.config)
