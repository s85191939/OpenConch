"""
Evaluation harness for STRATUM experiments.

Runs a model against passkey retrieval and RULER-lite tasks,
reports accuracy at different depth positions, and logs to wandb.
"""

import torch
import json
from tqdm import tqdm
from pathlib import Path
from typing import Optional
from torch.utils.data import DataLoader


def evaluate_model(
    model,
    tokenizer,
    dataset,
    batch_size: int = 4,
    max_new_tokens: int = 10,
    device: str = "cuda",
    output_path: Optional[str] = None,
) -> dict:
    """
    Evaluate a model on a long-context retrieval dataset.

    Args:
        model: the model to evaluate (must have a generate or forward method)
        tokenizer: tokenizer for decoding
        dataset: PasskeyDataset or RulerLiteDataset
        batch_size: evaluation batch size
        max_new_tokens: tokens to generate for answer
        device: cuda or cpu
        output_path: optional path to save detailed results as JSON

    Returns:
        dict with:
            - accuracy: float, overall exact match accuracy
            - accuracy_by_position: dict mapping position -> accuracy
            - total: int, number of samples evaluated
            - correct: int, number of correct answers
            - details: list of per-sample results
    """
    model.eval()
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    results = {
        "correct": 0,
        "total": 0,
        "by_position": {},
        "details": [],
    }

    with torch.no_grad():
        for batch in tqdm(loader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            answers = batch.get("answer") or batch.get("passkey")

            # Generate predictions
            if hasattr(model, "generate"):
                output_ids = model.generate(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=0.0,
                    do_sample=False,
                )
                # Extract only the new tokens
                pred_ids = output_ids[:, input_ids.shape[1]:]
            else:
                # For models without generate, use greedy decoding
                pred_ids = greedy_decode(model, input_ids, max_new_tokens)

            # Decode and compare
            for i in range(input_ids.shape[0]):
                pred_text = tokenizer.decode(pred_ids[i], skip_special_tokens=True).strip()
                target_text = answers[i] if isinstance(answers[i], str) else answers[i].item()
                target_text = str(target_text).strip()

                correct = pred_text.startswith(target_text) or target_text in pred_text

                # Track by position if available
                position = None
                if "passkey_position" in batch:
                    position = batch["passkey_position"][i].item()
                elif "position" in batch:
                    position = batch["position"][i].item() if torch.is_tensor(batch["position"][i]) else batch["position"][i]

                if position is not None:
                    pos_key = f"{position:.2f}"
                    if pos_key not in results["by_position"]:
                        results["by_position"][pos_key] = {"correct": 0, "total": 0}
                    results["by_position"][pos_key]["total"] += 1
                    if correct:
                        results["by_position"][pos_key]["correct"] += 1

                results["total"] += 1
                if correct:
                    results["correct"] += 1

                results["details"].append({
                    "predicted": pred_text,
                    "target": target_text,
                    "correct": correct,
                    "position": position,
                })

    # Compute accuracies
    results["accuracy"] = results["correct"] / max(results["total"], 1)
    results["accuracy_by_position"] = {
        pos: data["correct"] / max(data["total"], 1)
        for pos, data in results["by_position"].items()
    }

    # Save detailed results
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

    return results


def greedy_decode(model, input_ids, max_new_tokens):
    """Simple greedy decoding for models without a generate method."""
    generated = input_ids
    for _ in range(max_new_tokens):
        outputs = model(generated)
        if isinstance(outputs, dict):
            logits = outputs.get("logits") or outputs.get("output")
        else:
            logits = outputs

        next_token = logits[:, -1, :].argmax(dim=-1, keepdim=True)
        generated = torch.cat([generated, next_token], dim=-1)

    return generated[:, input_ids.shape[1]:]


def print_results(results: dict, experiment_name: str = ""):
    """Pretty-print evaluation results."""
    print(f"\n{'=' * 60}")
    print(f"  {experiment_name or 'Evaluation'} Results")
    print(f"{'=' * 60}")
    print(f"  Overall Accuracy: {results['accuracy']:.1%} ({results['correct']}/{results['total']})")

    if results.get("accuracy_by_position"):
        print(f"\n  Accuracy by Position:")
        for pos in sorted(results["accuracy_by_position"].keys()):
            acc = results["accuracy_by_position"][pos]
            bar = "█" * int(acc * 20)
            print(f"    Position {pos}: {acc:.1%} {bar}")

    print(f"{'=' * 60}\n")
