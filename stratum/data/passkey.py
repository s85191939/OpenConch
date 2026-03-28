"""
Passkey Retrieval Dataset — the simplest long-context benchmark.

Buries a random 5-digit passkey inside a long sequence of distractor text.
The model must retrieve the passkey when prompted at the end.

This is the standard "needle in a haystack" test. If a model can't pass
this, it fundamentally cannot handle long context.

Structure:
    [distractor text...] The passkey is 83291. [more distractor text...]
    What is the passkey? The passkey is _____

The key variable is WHERE in the sequence the passkey appears:
- Beginning (easy — recency bias helps)
- Middle (hard — "lost in the middle" problem)
- End (easy — still in short-term memory)
"""

import torch
import random
import string
from torch.utils.data import Dataset
from typing import Optional


# Distractor sentences — filler text that the model must ignore
DISTRACTORS = [
    "The weather today is partly cloudy with a chance of rain.",
    "Please remember to submit your report by end of day Friday.",
    "The quarterly earnings exceeded analyst expectations by twelve percent.",
    "Traffic on the main highway is expected to be heavy during rush hour.",
    "The new software update includes several performance improvements.",
    "Annual rainfall in the region averages approximately forty inches.",
    "The committee voted unanimously to approve the proposed amendments.",
    "Research suggests that regular exercise improves cognitive function.",
    "The museum will be closed for renovations starting next month.",
    "Global temperatures have risen by approximately one point five degrees.",
    "The project timeline has been extended by two additional weeks.",
    "Customer satisfaction scores improved by fifteen percent this quarter.",
    "The library now offers digital lending for e-books and audiobooks.",
    "Construction of the new bridge is expected to take eighteen months.",
    "The team successfully completed all milestones ahead of schedule.",
]


class PasskeyDataset(Dataset):
    """
    Generates passkey retrieval samples at specified sequence lengths.

    Each sample contains:
        - input_ids: tokenized sequence with buried passkey
        - passkey: the target string to retrieve
        - passkey_position: where in the sequence the passkey was placed (0-1 normalized)
        - oracle_mask: boolean mask marking the passkey token positions (for Exp 1)
    """

    def __init__(
        self,
        tokenizer,
        seq_len: int = 8192,
        n_samples: int = 1000,
        passkey_positions: Optional[list] = None,
        seed: int = 42,
    ):
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.n_samples = n_samples
        self.passkey_positions = passkey_positions or [0.1, 0.25, 0.5, 0.75, 0.9]
        self.seed = seed

        random.seed(seed)
        self.samples = [self._generate_sample(i) for i in range(n_samples)]

    def _generate_passkey(self) -> str:
        """Generate a random 5-digit passkey."""
        return "".join(random.choices(string.digits, k=5))

    def _generate_sample(self, idx: int):
        """Generate a single passkey retrieval sample."""
        passkey = self._generate_passkey()
        position = self.passkey_positions[idx % len(self.passkey_positions)]

        # Build the passkey sentence
        passkey_sentence = f" The secret passkey is {passkey}. Remember this number."

        # Build distractor text to fill the sequence
        prompt_suffix = f" What is the secret passkey? The secret passkey is"

        # Tokenize the passkey sentence and prompt to know their lengths
        passkey_tokens = self.tokenizer.encode(passkey_sentence, add_special_tokens=False)
        suffix_tokens = self.tokenizer.encode(prompt_suffix, add_special_tokens=False)
        answer_tokens = self.tokenizer.encode(f" {passkey}", add_special_tokens=False)

        # Fill remaining length with distractor text
        target_distractor_len = self.seq_len - len(passkey_tokens) - len(suffix_tokens) - len(answer_tokens)

        # Generate distractor tokens
        distractor_tokens = []
        while len(distractor_tokens) < target_distractor_len:
            sentence = random.choice(DISTRACTORS)
            tokens = self.tokenizer.encode(f" {sentence}", add_special_tokens=False)
            distractor_tokens.extend(tokens)
        distractor_tokens = distractor_tokens[:target_distractor_len]

        # Insert passkey at the target position
        insert_pos = int(len(distractor_tokens) * position)
        full_tokens = (
            distractor_tokens[:insert_pos]
            + passkey_tokens
            + distractor_tokens[insert_pos:]
            + suffix_tokens
        )

        # Trim to exact seq_len (minus answer)
        full_tokens = full_tokens[: self.seq_len - len(answer_tokens)]

        # Build input and target
        input_ids = full_tokens + answer_tokens

        # Build oracle mask: True at passkey token positions
        oracle_mask = [False] * len(input_ids)
        # Mark the passkey tokens
        pk_start = insert_pos
        pk_end = insert_pos + len(passkey_tokens)
        for i in range(pk_start, min(pk_end, len(oracle_mask))):
            oracle_mask[i] = True
        # Also mark the suffix (question) tokens as important
        suffix_start = len(full_tokens) - len(suffix_tokens) - len(answer_tokens)
        for i in range(max(0, suffix_start), min(suffix_start + len(suffix_tokens), len(oracle_mask))):
            oracle_mask[i] = True

        return {
            "input_ids": input_ids[: self.seq_len],
            "passkey": passkey,
            "passkey_position": position,
            "oracle_mask": oracle_mask[: self.seq_len],
            "answer_tokens": answer_tokens,
        }

    def __len__(self):
        return self.n_samples

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return {
            "input_ids": torch.tensor(sample["input_ids"], dtype=torch.long),
            "oracle_mask": torch.tensor(sample["oracle_mask"], dtype=torch.bool),
            "passkey": sample["passkey"],
            "passkey_position": sample["passkey_position"],
        }
