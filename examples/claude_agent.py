"""
OpenConch + Claude Agent SDK Integration

Shows how to use OpenConch as a memory backend for a Claude agent.
The agent automatically stores and retrieves memories across conversations.

Requires: pip install anthropic
Set ANTHROPIC_API_KEY environment variable.
"""

import anthropic
from openconch import Memory, OpenConchConfig

# Initialize OpenConch
config = OpenConchConfig(
    persist_directory=".openconch_agent",
    salience_mode="heuristic",
    llm_model="claude-sonnet-4-20250514",
)
memory = Memory(config=config)

# Initialize Claude client
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a helpful assistant with persistent memory.

You have access to a memory system that remembers things about the user
across conversations. Before answering, check if you have relevant memories.
After the conversation, store any new facts you learn.

Current memories about this user:
{memories}

Instructions:
- Reference memories naturally in conversation ("I remember you mentioned...")
- If memories contradict the user, trust the user (they may have changed their mind)
- Store new facts, preferences, and important details
"""


def chat_with_memory(user_message: str, user_id: str = "default"):
    """
    Chat with Claude, augmented by OpenConch memory.
    """
    # 1. Retrieve relevant memories
    relevant = memory.search(user_message, user_id=user_id, top_k=5)
    memory_context = "\n".join(
        f"- {r['content']}" for r in relevant
    ) if relevant else "No memories yet."

    # 2. Build system prompt with memories
    system = SYSTEM_PROMPT.format(memories=memory_context)

    # 3. Call Claude
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    assistant_reply = response.content[0].text

    # 4. Store the conversation as new memories
    conversation = f"User: {user_message}\nAssistant: {assistant_reply}"
    memory.add(conversation, user_id=user_id, infer=True)

    return assistant_reply


# Demo conversation
if __name__ == "__main__":
    print("OpenConch + Claude Agent Demo")
    print("=" * 50)
    print("(Type 'quit' to exit, 'memories' to see stored memories)\n")

    user_id = "demo_user"

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "quit":
            break
        elif user_input.lower() == "memories":
            all_mem = memory.get_all(user_id=user_id)
            print(f"\n--- Stored Memories ({len(all_mem)}) ---")
            for m in all_mem[:10]:
                print(f"  [{m.get('score', '?'):.2f}] {m['content'][:80]}")
            print()
            continue

        reply = chat_with_memory(user_input, user_id=user_id)
        print(f"Assistant: {reply}\n")
