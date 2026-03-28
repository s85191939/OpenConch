"""
RULER-Lite — simplified version of NVIDIA's RULER benchmark.

RULER tests effective context length across 4 task types:
1. Single needle retrieval (NIAH) — find one fact in noise
2. Multi-needle retrieval — find multiple facts scattered across context
3. Variable tracking — track value changes across the sequence
4. Aggregation — combine information from multiple positions

We implement lightweight versions of each for validation under budget.
"""

import torch
import random
from torch.utils.data import Dataset
from typing import Optional


# Entity names for variable tracking
ENTITIES = [
    "Alice", "Bob", "Charlie", "Diana", "Edward",
    "Fiona", "George", "Hannah", "Ivan", "Julia",
]

CITIES = [
    "London", "Paris", "Tokyo", "Berlin", "Sydney",
    "Cairo", "Mumbai", "Toronto", "Seoul", "Rome",
]

COLORS = [
    "red", "blue", "green", "yellow", "purple",
    "orange", "white", "black", "silver", "gold",
]


class RulerLiteDataset(Dataset):
    """
    Generates RULER-inspired long-context evaluation samples.

    Task types:
        - 'single_niah': Single needle in a haystack
        - 'multi_niah': Multiple needles scattered in haystack
        - 'variable_track': Track entity state changes across context
        - 'aggregate': Count/combine information from multiple positions
    """

    def __init__(
        self,
        tokenizer,
        task: str = "single_niah",
        seq_len: int = 8192,
        n_samples: int = 500,
        seed: int = 42,
    ):
        self.tokenizer = tokenizer
        self.task = task
        self.seq_len = seq_len
        self.n_samples = n_samples

        random.seed(seed)

        generators = {
            "single_niah": self._gen_single_niah,
            "multi_niah": self._gen_multi_niah,
            "variable_track": self._gen_variable_track,
            "aggregate": self._gen_aggregate,
        }

        if task not in generators:
            raise ValueError(f"Unknown task: {task}. Choose from {list(generators.keys())}")

        self.generator = generators[task]
        self.samples = [self.generator(i) for i in range(n_samples)]

    def _pad_with_distractors(self, tokens_before, key_tokens, tokens_after, suffix_tokens):
        """Build a full sequence with distractor padding."""
        filler_sentences = [
            "The morning meeting was rescheduled to three PM.",
            "Sales figures for the western region exceeded targets.",
            "The updated policy takes effect at the start of next quarter.",
            "Maintenance has been completed on all server clusters.",
            "The training program will run for six consecutive weeks.",
        ]

        # Generate enough distractor tokens
        all_distractor = []
        while len(all_distractor) < self.seq_len * 2:
            s = random.choice(filler_sentences)
            all_distractor.extend(self.tokenizer.encode(f" {s}", add_special_tokens=False))

        target_before = tokens_before
        target_after = self.seq_len - target_before - len(key_tokens) - len(suffix_tokens)
        target_after = max(0, target_after)

        full = (
            all_distractor[:target_before]
            + key_tokens
            + all_distractor[target_before : target_before + target_after]
            + suffix_tokens
        )

        return full[: self.seq_len]

    def _gen_single_niah(self, idx):
        """Single needle: one fact buried, one question at end."""
        entity = random.choice(ENTITIES)
        city = random.choice(CITIES)

        needle = f" {entity} lives in {city}."
        question = f" Where does {entity} live? {entity} lives in"
        answer = f" {city}"

        needle_tok = self.tokenizer.encode(needle, add_special_tokens=False)
        question_tok = self.tokenizer.encode(question, add_special_tokens=False)
        answer_tok = self.tokenizer.encode(answer, add_special_tokens=False)

        # Place needle at varying positions
        position = [0.1, 0.25, 0.5, 0.75, 0.9][idx % 5]
        insert_at = int((self.seq_len - len(needle_tok) - len(question_tok)) * position)

        full = self._pad_with_distractors(insert_at, needle_tok, 0, question_tok + answer_tok)

        # Oracle mask: needle + question positions
        oracle_mask = [False] * len(full)
        for i in range(insert_at, min(insert_at + len(needle_tok), len(full))):
            oracle_mask[i] = True

        return {
            "input_ids": full,
            "answer": city,
            "answer_tokens": answer_tok,
            "oracle_mask": oracle_mask,
            "position": position,
            "task": "single_niah",
        }

    def _gen_multi_niah(self, idx):
        """Multiple needles: several facts scattered, question about one."""
        entities = random.sample(ENTITIES, 4)
        cities = random.sample(CITIES, 4)

        # Target is the first entity
        target_idx = 0
        needles = [f" {e} lives in {c}." for e, c in zip(entities, cities)]
        question = f" Where does {entities[target_idx]} live? {entities[target_idx]} lives in"
        answer = f" {cities[target_idx]}"

        question_tok = self.tokenizer.encode(question, add_special_tokens=False)
        answer_tok = self.tokenizer.encode(answer, add_special_tokens=False)

        # Scatter needles at 20%, 40%, 60%, 80%
        needle_positions = [0.2, 0.4, 0.6, 0.8]

        # Build sequence with multiple insertions
        filler = []
        while len(filler) < self.seq_len * 2:
            filler.extend(self.tokenizer.encode(
                " The committee reviewed all pending proposals carefully.",
                add_special_tokens=False
            ))

        available = self.seq_len - len(question_tok) - len(answer_tok)
        full = []
        oracle_mask = []

        for i, pos in enumerate(needle_positions):
            n_tok = self.tokenizer.encode(needles[i], add_special_tokens=False)
            insert_at = int(available * pos)
            # Fill up to insert point
            while len(full) < insert_at:
                if len(filler) > len(full):
                    full.append(filler[len(full)])
                    oracle_mask.append(False)
                else:
                    break
            # Insert needle
            is_target = (i == target_idx)
            for t in n_tok:
                full.append(t)
                oracle_mask.append(is_target)  # Only mark target needle

        # Fill remaining
        while len(full) < available:
            if len(filler) > len(full):
                full.append(filler[len(full)])
                oracle_mask.append(False)
            else:
                break

        # Add question + answer
        full = full[:available] + question_tok + answer_tok
        oracle_mask = oracle_mask[:available] + [True] * len(question_tok) + [False] * len(answer_tok)

        full = full[: self.seq_len]
        oracle_mask = oracle_mask[: self.seq_len]

        return {
            "input_ids": full,
            "answer": cities[target_idx],
            "answer_tokens": answer_tok,
            "oracle_mask": oracle_mask,
            "task": "multi_niah",
        }

    def _gen_variable_track(self, idx):
        """Variable tracking: entity changes state, must report final state."""
        entity = random.choice(ENTITIES)
        states = random.sample(COLORS, 3)  # 3 state changes

        # Build state change sentences
        changes = [f" {entity} now has a {color} hat." for color in states]
        question = f" What color is {entity}'s hat? {entity}'s hat is"
        answer = f" {states[-1]}"  # Last state is correct

        question_tok = self.tokenizer.encode(question, add_special_tokens=False)
        answer_tok = self.tokenizer.encode(answer, add_special_tokens=False)

        # Scatter changes at 30%, 50%, 70%
        positions = [0.3, 0.5, 0.7]

        filler = []
        while len(filler) < self.seq_len * 2:
            filler.extend(self.tokenizer.encode(
                " Regular updates were provided throughout the process.",
                add_special_tokens=False
            ))

        available = self.seq_len - len(question_tok) - len(answer_tok)
        full = []
        oracle_mask = []

        for i, pos in enumerate(positions):
            c_tok = self.tokenizer.encode(changes[i], add_special_tokens=False)
            insert_at = int(available * pos)
            while len(full) < insert_at:
                if len(filler) > len(full):
                    full.append(filler[len(full)])
                    oracle_mask.append(False)
                else:
                    break
            # All state changes are important for tracking
            for t in c_tok:
                full.append(t)
                oracle_mask.append(True)

        while len(full) < available:
            if len(filler) > len(full):
                full.append(filler[len(full)])
                oracle_mask.append(False)
            else:
                break

        full = full[:available] + question_tok + answer_tok
        oracle_mask = oracle_mask[:available] + [True] * len(question_tok) + [False] * len(answer_tok)

        full = full[: self.seq_len]
        oracle_mask = oracle_mask[: self.seq_len]

        return {
            "input_ids": full,
            "answer": states[-1],
            "answer_tokens": answer_tok,
            "oracle_mask": oracle_mask,
            "task": "variable_track",
        }

    def _gen_aggregate(self, idx):
        """Aggregation: count how many entities are in a specific city."""
        target_city = random.choice(CITIES)
        all_entities = random.sample(ENTITIES, 8)

        # Randomly assign cities — some go to target
        n_target = random.randint(2, 5)
        assignments = []
        for i, entity in enumerate(all_entities):
            city = target_city if i < n_target else random.choice([c for c in CITIES if c != target_city])
            assignments.append((entity, city))
        random.shuffle(assignments)

        statements = [f" {e} lives in {c}." for e, c in assignments]
        question = f" How many people live in {target_city}? The answer is"
        answer = f" {n_target}"

        question_tok = self.tokenizer.encode(question, add_special_tokens=False)
        answer_tok = self.tokenizer.encode(answer, add_special_tokens=False)

        # Scatter statements evenly
        filler = []
        while len(filler) < self.seq_len * 2:
            filler.extend(self.tokenizer.encode(
                " Various data points were collected and analyzed.",
                add_special_tokens=False
            ))

        available = self.seq_len - len(question_tok) - len(answer_tok)
        full = []
        oracle_mask = []

        for i, (entity, city) in enumerate(assignments):
            s_tok = self.tokenizer.encode(statements[i], add_special_tokens=False)
            insert_at = int(available * (i + 1) / (len(assignments) + 1))
            while len(full) < insert_at:
                if len(filler) > len(full):
                    full.append(filler[len(full)])
                    oracle_mask.append(False)
                else:
                    break
            # Mark statements about target city as oracle-important
            is_target = (city == target_city)
            for t in s_tok:
                full.append(t)
                oracle_mask.append(is_target)

        while len(full) < available:
            if len(filler) > len(full):
                full.append(filler[len(full)])
                oracle_mask.append(False)
            else:
                break

        full = full[:available] + question_tok + answer_tok
        oracle_mask = oracle_mask[:available] + [True] * len(question_tok) + [False] * len(answer_tok)

        full = full[: self.seq_len]
        oracle_mask = oracle_mask[: self.seq_len]

        return {
            "input_ids": full,
            "answer": str(n_target),
            "answer_tokens": answer_tok,
            "oracle_mask": oracle_mask,
            "task": "aggregate",
        }

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return {
            "input_ids": torch.tensor(sample["input_ids"], dtype=torch.long),
            "oracle_mask": torch.tensor(sample["oracle_mask"], dtype=torch.bool),
            "answer": sample["answer"],
            "task": sample["task"],
        }
