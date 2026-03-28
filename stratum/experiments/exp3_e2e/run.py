"""
Experiment 3: End-to-End Tiny STRATUM (~$80, ~16 GPU-hours)

THE QUESTION: Does the full STRATUM architecture (Mamba + scorer + anchor
attention + episodic memory + fusion gate) outperform pure Mamba and pure
transformer baselines at the same parameter count on long-context tasks?

THE METHOD:
1. Train STRATUM-130M end-to-end on synthetic long-context data
2. Train Mamba-130M baseline on the same data
3. Train Transformer-160M (Pythia) baseline on the same data
4. Evaluate all three on RULER-lite tasks at 8K-16K tokens
5. Compare recall accuracy, especially at mid-sequence positions

This is the full proof. If STRATUM wins here, it validates the architecture.
If it doesn't, the individual components from Exp 1-2 still stand as contributions.
"""

import argparse
import yaml
import torch
import torch.nn as nn
import torch.optim as optim
import json
from pathlib import Path
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.mamba_backbone import MambaBackbone
from models.salience_scorer import SalienceScorer
from models.anchor_attention import AnchorAttention
from models.episodic_memory import EpisodicMemory
from models.fusion import FusionGate
from data.passkey import PasskeyDataset
from data.ruler_lite import RulerLiteDataset
from eval.harness import evaluate_model, print_results


class StratumModel(nn.Module):
    """
    Full STRATUM: Mamba backbone + salience scorer + anchor attention
    + episodic memory + fusion gate + LM head.

    This is the complete architecture described in the README.
    """

    def __init__(self, backbone, scorer, attention, memory, fusion, lm_head):
        super().__init__()
        self.backbone = backbone
        self.scorer = scorer
        self.attention = attention
        self.memory = memory
        self.fusion = fusion
        self.lm_head = lm_head

    def forward(self, input_ids, labels=None):
        # S2: Mamba backbone
        backbone_out = self.backbone(input_ids)
        hidden = backbone_out["hidden_states"]  # (batch, seq, d_model)

        # Salience scoring
        scorer_out = self.scorer(hidden, return_scores=True)
        anchor_mask = scorer_out["anchor_mask"]

        # S3: Anchor attention (only on flagged tokens)
        attn_out = self.attention(hidden, anchor_mask)

        # S1: Episodic memory
        mem_out = self.memory(hidden)
        mem_hidden = mem_out["output"]

        # Fusion: combine all three strata
        fused = self.fusion(
            s1_memory=mem_hidden,
            s2_mamba=hidden,
            s3_attention=attn_out,
        )
        output = fused["output"]

        # LM head
        logits = self.lm_head(output)

        result = {"logits": logits, "gate_weights": fused["gate_weights"]}

        if labels is not None:
            loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
            loss = loss_fn(logits.view(-1, logits.size(-1)), labels.view(-1))
            result["loss"] = loss

        return result


def build_stratum(config, device, dtype):
    """Build the full STRATUM model from config."""
    backbone = MambaBackbone.from_pretrained(
        config["model"]["backbone"], freeze=False
    ).to(device)

    # Get LM head
    from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel
    pretrained = MambaLMHeadModel.from_pretrained(
        config["model"]["backbone"], device=device, dtype=dtype
    )
    lm_head = pretrained.lm_head

    scorer = SalienceScorer(
        d_model=config["scorer"]["d_model"],
        d_inner=config["scorer"]["d_inner"],
        dropout=config["scorer"]["dropout"],
        anchor_ratio=config["scorer"]["anchor_ratio"],
    ).to(device).to(dtype)

    attention = AnchorAttention(
        d_model=config["attention"]["d_model"],
        n_heads=config["attention"]["n_heads"],
        dropout=config["attention"]["dropout"],
    ).to(device).to(dtype)

    memory = EpisodicMemory(
        d_model=config["memory"]["d_model"],
        n_slots=config["memory"]["n_slots"],
        chunk_size=config["memory"]["chunk_size"],
    ).to(device).to(dtype)

    fusion = FusionGate(
        d_model=config["fusion"]["d_model"],
        temperature=config["fusion"]["temperature"],
    ).to(device).to(dtype)

    return StratumModel(backbone, scorer, attention, memory, fusion, lm_head)


def train_and_evaluate(config_path: str):
    """Full end-to-end training and evaluation."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    device = config["hardware"]["device"]
    dtype = getattr(torch, config["hardware"]["dtype"])

    print("=" * 60)
    print("  Experiment 3: End-to-End STRATUM")
    print("=" * 60)

    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
    tokenizer.pad_token = tokenizer.eos_token

    # Build STRATUM
    print("\n[1/6] Building STRATUM model...")
    model = build_stratum(config, device, dtype)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Total params: {total_params / 1e6:.1f}M")
    print(f"  Trainable params: {trainable_params / 1e6:.1f}M")

    # Build training data
    print("[2/6] Generating training data...")
    seq_len = config["data"]["seq_lengths"][0]
    n_per_task = config["data"]["n_train_samples"] // len(config["data"]["train_tasks"])

    train_datasets = []
    for task in config["data"]["train_tasks"]:
        if task == "passkey":
            ds = PasskeyDataset(tokenizer=tokenizer, seq_len=seq_len, n_samples=n_per_task)
        else:
            ds = RulerLiteDataset(tokenizer=tokenizer, task=task, seq_len=seq_len, n_samples=n_per_task)
        train_datasets.append(ds)

    train_data = torch.utils.data.ConcatDataset(train_datasets)
    train_loader = torch.utils.data.DataLoader(
        train_data, batch_size=config["training"]["batch_size"], shuffle=True
    )

    # Optimizer with separate LR for scorer
    train_cfg = config["training"]
    scorer_params = list(model.scorer.parameters())
    other_params = [p for n, p in model.named_parameters()
                    if "scorer" not in n and p.requires_grad]

    optimizer = optim.AdamW([
        {"params": other_params, "lr": train_cfg["lr"]},
        {"params": scorer_params, "lr": train_cfg["lr"] * train_cfg["scorer_lr_multiplier"]},
    ], weight_decay=train_cfg["weight_decay"])

    # Training loop
    print("[3/6] Training STRATUM...")
    model.train()
    global_step = 0

    for epoch in range(train_cfg["epochs"]):
        epoch_loss = 0
        n_batches = 0

        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{train_cfg['epochs']}"):
            input_ids = batch["input_ids"].to(device)

            # Create labels: predict next token (shift by 1)
            labels = input_ids[:, 1:].contiguous()
            input_for_model = input_ids[:, :-1].contiguous()

            output = model(input_for_model, labels=labels)
            loss = output["loss"]

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), train_cfg["grad_clip"])
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1
            global_step += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        print(f"  Epoch {epoch+1}: loss = {avg_loss:.4f}")

    # Evaluate STRATUM
    print("\n[4/6] Evaluating STRATUM...")
    model.eval()

    eval_results = {"stratum": {}}
    for task in config["data"]["eval_tasks"]:
        for sl in config["data"]["seq_lengths"]:
            if task == "passkey":
                eval_ds = PasskeyDataset(tokenizer=tokenizer, seq_len=sl,
                                        n_samples=config["data"]["n_eval_samples"])
            else:
                eval_ds = RulerLiteDataset(tokenizer=tokenizer, task=task, seq_len=sl,
                                          n_samples=config["data"]["n_eval_samples"])

            res = evaluate_model(model, tokenizer, eval_ds,
                               batch_size=config["eval"]["batch_size"], device=device)
            key = f"{task}_{sl}"
            eval_results["stratum"][key] = res["accuracy"]
            print_results(res, f"STRATUM ({task} @ {sl})")

    # Baselines
    if config["baselines"]["run_mamba_baseline"]:
        print("\n[5/6] Running Mamba baseline...")
        from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel
        mamba_base = MambaLMHeadModel.from_pretrained(
            config["model"]["backbone"], device=device, dtype=dtype
        )
        eval_results["mamba"] = {}
        for task in config["data"]["eval_tasks"]:
            for sl in config["data"]["seq_lengths"]:
                if task == "passkey":
                    eval_ds = PasskeyDataset(tokenizer=tokenizer, seq_len=sl,
                                            n_samples=config["data"]["n_eval_samples"])
                else:
                    eval_ds = RulerLiteDataset(tokenizer=tokenizer, task=task, seq_len=sl,
                                              n_samples=config["data"]["n_eval_samples"])
                res = evaluate_model(mamba_base, tokenizer, eval_ds,
                                   batch_size=config["eval"]["batch_size"], device=device)
                key = f"{task}_{sl}"
                eval_results["mamba"][key] = res["accuracy"]
        del mamba_base

    if config["baselines"]["run_transformer_baseline"]:
        print("[6/6] Running Transformer baseline...")
        transformer = AutoModelForCausalLM.from_pretrained(
            config["baselines"]["transformer_model"],
            torch_dtype=dtype,
        ).to(device)
        eval_results["transformer"] = {}
        for task in config["data"]["eval_tasks"]:
            for sl in config["data"]["seq_lengths"]:
                if task == "passkey":
                    eval_ds = PasskeyDataset(tokenizer=tokenizer, seq_len=sl,
                                            n_samples=config["data"]["n_eval_samples"])
                else:
                    eval_ds = RulerLiteDataset(tokenizer=tokenizer, task=task, seq_len=sl,
                                              n_samples=config["data"]["n_eval_samples"])
                res = evaluate_model(transformer, tokenizer, eval_ds,
                                   batch_size=config["eval"]["batch_size"], device=device)
                key = f"{task}_{sl}"
                eval_results["transformer"][key] = res["accuracy"]
        del transformer

    # Final comparison
    print("\n" + "=" * 60)
    print("  EXPERIMENT 3: FINAL COMPARISON")
    print("=" * 60)
    print(f"\n  {'Task':<25s} {'STRATUM':>10s} {'Mamba':>10s} {'Transformer':>12s}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*12}")

    for key in sorted(eval_results["stratum"].keys()):
        s = eval_results["stratum"].get(key, 0)
        m = eval_results.get("mamba", {}).get(key, 0)
        t = eval_results.get("transformer", {}).get(key, 0)
        winner = "★" if s > m and s > t else " "
        print(f"  {key:<25s} {s:>9.1%} {m:>9.1%} {t:>11.1%}  {winner}")

    # Save everything
    output_dir = Path(config["logging"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "results.json", "w") as f:
        json.dump(eval_results, f, indent=2)
    torch.save(model.state_dict(), output_dir / "stratum_model.pt")
    print(f"\n  Results + model saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/exp3_e2e.yaml")
    args = parser.parse_args()
    train_and_evaluate(args.config)
