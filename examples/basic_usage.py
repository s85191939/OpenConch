"""
OpenConch — Basic Usage Example

Shows the core API: add, search, update, delete.
Works without GPU (uses heuristic scorer and ChromaDB).
"""

from openconch import Memory, OpenConchConfig

# Create a memory instance with default config (heuristic scorer, ChromaDB)
config = OpenConchConfig(
    persist_directory=".openconch_demo",
    salience_mode="heuristic",  # No GPU needed
)
m = Memory(config=config)

print("OpenConch Basic Usage Demo")
print("=" * 50)

# Add memories (infer=False stores raw text, no LLM needed)
print("\n1. Adding memories...")
results = m.add("User prefers dark mode in all applications", user_id="alice", infer=False)
print(f"   Added: {results[0]['content']} (salience: {results[0]['salience']:.2f}, tier: {results[0]['tier']})")

results = m.add("User is allergic to peanuts", user_id="alice", infer=False)
print(f"   Added: {results[0]['content']} (salience: {results[0]['salience']:.2f}, tier: {results[0]['tier']})")

results = m.add("User's birthday is March 15, 1995", user_id="alice", infer=False)
print(f"   Added: {results[0]['content']} (salience: {results[0]['salience']:.2f}, tier: {results[0]['tier']})")

results = m.add("The weather is nice today", user_id="alice", infer=False)
print(f"   Added: {results[0]['content']} (salience: {results[0]['salience']:.2f}, tier: {results[0]['tier']})")

results = m.add("Meeting with Bob at 3pm tomorrow to discuss the Q4 budget of $2.5M", user_id="alice", infer=False)
print(f"   Added: {results[0]['content']} (salience: {results[0]['salience']:.2f}, tier: {results[0]['tier']})")

# Search memories
print("\n2. Searching...")
results = m.search("What food allergies does Alice have?", user_id="alice")
print(f"   Query: 'What food allergies does Alice have?'")
for r in results[:3]:
    print(f"   → {r['content']} (score: {r['score']:.3f})")

print()
results = m.search("What's happening with Bob?", user_id="alice")
print(f"   Query: 'What's happening with Bob?'")
for r in results[:3]:
    print(f"   → {r['content']} (score: {r['score']:.3f})")

# Show memory state
print(f"\n3. Memory state: {m}")

# Update a memory
print("\n4. Updating a memory...")
if results:
    mem_id = results[0]["id"]
    m.update(mem_id, "Meeting with Bob rescheduled to 4pm tomorrow, discussing Q4 budget of $3M")
    print(f"   Updated memory {mem_id[:8]}...")

# History
print("\n5. Memory history:")
if results:
    history = m.history(results[0]["id"])
    for h in history[:3]:
        print(f"   [{h['action']}] {h.get('new_content', 'N/A')[:60]}...")

print("\nDone!")
