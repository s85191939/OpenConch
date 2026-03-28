"""
LLM integration — Claude API for fact extraction and memory management.

Uses the Anthropic Python SDK to:
1. Extract structured facts from conversations
2. Decide what's worth remembering (before salience scorer refinement)
3. Generate memory summaries for compression
"""

import os
import json
from typing import List, Dict, Optional


FACT_EXTRACTION_PROMPT = """You are a memory extraction system. Given a conversation, extract the key facts, preferences, and information worth remembering long-term.

Rules:
- Extract only factual statements, preferences, and important context
- Each fact should be a single, self-contained statement
- Include WHO the fact is about (user, agent, or a third party)
- Prefer specific details over vague ones
- Skip pleasantries, acknowledgments, and filler

Conversation:
{conversation}

Return a JSON array of extracted facts. Each fact should be a string.
Example: ["User prefers Python over JavaScript", "User's birthday is March 15", "User is working on a machine learning project"]

Extracted facts:"""

MEMORY_SUMMARY_PROMPT = """Summarize these related memories into a single, concise memory that preserves all key information:

Memories:
{memories}

Write a single summary sentence that captures everything important:"""


class LLMEngine:
    """
    Claude-powered fact extraction and memory management.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy-load the Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def extract_facts(self, conversation: str) -> List[str]:
        """
        Extract memorable facts from a conversation.

        Args:
            conversation: The conversation text to extract from

        Returns:
            List of fact strings worth remembering
        """
        client = self._get_client()

        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": FACT_EXTRACTION_PROMPT.format(conversation=conversation),
            }],
        )

        # Parse the JSON response
        text = response.content[0].text.strip()

        # Handle both raw JSON and markdown-wrapped JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            facts = json.loads(text)
            if isinstance(facts, list):
                return [str(f) for f in facts]
        except json.JSONDecodeError:
            # If JSON parsing fails, split by newlines
            return [line.strip().lstrip("- ") for line in text.split("\n") if line.strip()]

        return []

    def summarize_memories(self, memories: List[str]) -> str:
        """
        Compress multiple related memories into one summary.

        Used when the episodic store needs to free up slots —
        instead of just deleting, we compress related memories.
        """
        client = self._get_client()

        memories_text = "\n".join(f"- {m}" for m in memories)

        response = client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": MEMORY_SUMMARY_PROMPT.format(memories=memories_text),
            }],
        )

        return response.content[0].text.strip()

    def should_remember(self, text: str) -> bool:
        """
        Quick LLM check: is this text worth storing as a memory?

        Cheaper than full fact extraction. Used as a pre-filter.
        """
        client = self._get_client()

        response = client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": f"Does this text contain a fact, preference, or information worth remembering long-term? Answer only YES or NO.\n\nText: {text}",
            }],
        )

        answer = response.content[0].text.strip().upper()
        return answer.startswith("YES")
