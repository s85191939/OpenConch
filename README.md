# OpenConch

**Episodic memory for AI agents. Remember everything. Retrieve faithfully.**

OpenConch is a memory layer for AI applications that goes beyond vector similarity search. It gives your agents episodic memory — the kind humans have — so they remember *what actually happened* and retrieve it faithfully. No contradictions. No invented memories. No lost context.

## Why Not Just Use mem0?

mem0 stores memories as vector embeddings and retrieves them by cosine similarity. That works for simple cases, but breaks down when:

- **Timing matters**: A preference from last year shouldn't override what the user said 5 minutes ago. mem0 treats them equally.
- **Memory grows unbounded**: Every interaction creates more vectors. At scale, retrieval gets noisy — too many "similar" results, not enough "correct" ones.
- **Relevance is contextual**: Whether a memory matters depends on *what you're doing right now*, not just semantic similarity. "User is allergic to peanuts" is critical when planning dinner, irrelevant when debugging code.

OpenConch solves these with three innovations:

1. **Mamba-powered temporal understanding**: Instead of hardcoded decay formulas, a Mamba language model processes your entire memory history in chronological order and *learns* which memories are relevant to the current query — including temporal context.

2. **Episodic memory store**: A fixed-size memory bank (like human working memory) that compresses and evicts old memories intelligently. Never grows unbounded. The most important memories are always accessible.

3. **Salience scoring**: Every incoming memory is scored for importance. Critical facts (allergies, deadlines, preferences) are stored in the episodic store for fast, reliable retrieval. Noise is filtered out.

## Quick Start

```bash
pip install openconch
```

```python
from openconch import Memory

m = Memory()

# Add memories
m.add("User prefers dark mode", user_id="alice")
m.add("User is allergic to peanuts", user_id="alice")
m.add("Meeting with Bob at 3pm tomorrow", user_id="alice")

# Search — returns the most relevant memories
results = m.search("What should I know about Alice's diet?", user_id="alice")
for r in results:
    print(r["content"], r["score"])
# → "User is allergic to peanuts" 0.92

# Update
m.update(results[0]["id"], "User is allergic to peanuts and tree nuts")

# Delete
m.delete(results[0]["id"])

# History — full audit trail
m.history(results[0]["id"])
```

## With Claude

```python
from openconch import Memory
import anthropic

memory = Memory()
client = anthropic.Anthropic()

# Retrieve relevant memories before calling Claude
relevant = memory.search("user preferences", user_id="alice")
context = "\n".join(f"- {r['content']}" for r in relevant)

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=f"User memories:\n{context}",
    messages=[{"role": "user", "content": "Help me set up my new laptop"}],
)

# Store new facts from the conversation
memory.add(response.content[0].text, user_id="alice")
```

## Architecture

```
                    OpenConch API
        .add()  .search()  .update()  .delete()
                        |
                  Memory Router
         (scores salience, decides storage tier)
                        |
          +-------------+-------------+
          |             |             |
    Salience       Episodic       Vector
    Scorer         Memory         Store
    (Mamba)        (fixed-size,   (ChromaDB/
                   temporal)       Qdrant)
```

**On add**: The salience scorer evaluates importance. High-salience memories (facts, preferences, deadlines) go to both the episodic store and vector store. Medium-salience goes to vector only. Low-salience (noise) is dropped.

**On search**: Both stores are queried. The episodic store uses Mamba to score temporal relevance — it processes memories in chronological order and understands which ones matter *right now*. Results are fused and reranked.

**On eviction**: When the episodic store is full, the least relevant memory is evicted. Relevance considers salience, access frequency, and temporal context. Critical memories survive; noise gets cleaned up automatically.

## Configuration

```python
from openconch import Memory, OpenConchConfig

config = OpenConchConfig(
    # Storage
    vector_store="chromadb",        # or "qdrant"
    persist_directory=".openconch",

    # Episodic Memory (requires GPU for Mamba)
    episodic_enabled=True,
    episodic_slots=256,             # Fixed memory bank size

    # Salience Scoring
    salience_mode="mamba",          # or "heuristic" (CPU-only)

    # LLM for fact extraction
    llm_model="claude-sonnet-4-20250514",

    # Search
    default_top_k=10,
)

m = Memory(config=config)
```

### Modes

| Mode | GPU Required | Best For |
|------|-------------|----------|
| `salience_mode="heuristic"` | No | Development, testing, CPU-only environments |
| `salience_mode="mamba"` | Yes (A100/H100) | Production with temporal understanding |
| `episodic_enabled=False` | No | Simple vector-only mode (like mem0) |
| `episodic_enabled=True` | Yes | Full episodic memory with compression |

## How Temporal Memory Works

Traditional memory systems use hardcoded decay: `relevance = e^(-t/halflife)`. A memory from 6 months ago always scores lower than one from yesterday, regardless of content.

OpenConch uses Mamba — a state-space model that processes sequences in linear time. It reads your memories in chronological order:

```
[T-720h] User started a new job at Acme Corp
[T-168h] User mentioned they're preparing for a board presentation
[T-24h]  User asked about slide design tips
[T-1h]   User said the presentation is tomorrow
[QUERY]  What does Alice need help with?
```

Mamba's hidden state at each position encodes the full temporal context — what came before, what patterns emerged, what's likely relevant now. The salience scorer then reads this state and scores each memory. The result: "board presentation" and "presentation is tomorrow" score highest, even though the job change is more recent than the presentation prep started.

No decay formula could get this right. The model *learns* temporal relevance from data.

## Project Structure

```
OpenConch/
├── openconch/           # The Python package
│   ├── memory.py        # Public API (Memory class)
│   ├── router.py        # Memory routing logic
│   ├── scorer.py        # Salience scoring (heuristic + Mamba)
│   ├── episodic.py      # Episodic memory store
│   ├── vector_store.py  # ChromaDB/Qdrant backend
│   ├── embeddings.py    # Sentence-transformers embeddings
│   ├── llm.py           # Claude integration
│   ├── history.py       # SQLite audit log
│   └── config.py        # Configuration
├── stratum/             # STRATUM neural architecture
│   ├── models/          # Mamba backbone, scorer, attention, memory, fusion
│   ├── experiments/     # Validation experiments
│   └── configs/         # Training configs
├── examples/
│   ├── basic_usage.py
│   └── claude_agent.py
└── tests/
```

## vs mem0

| Feature | mem0 | OpenConch |
|---------|------|-----------|
| Storage | Vector DB only | Vector + Episodic (fixed-size) |
| Retrieval | Cosine similarity | Semantic + temporal (Mamba) |
| Temporal awareness | None (or manual metadata) | Learned from data |
| Memory growth | Unbounded | Fixed-size with smart eviction |
| Salience scoring | LLM-based (expensive) | Learned scorer (fast) + LLM fallback |
| Fact extraction | GPT-4 | Claude |
| Compression | None | Episodic store compresses automatically |
| Audit trail | Basic history | Full SQLite history with diffs |
| CPU-only mode | Yes | Yes (heuristic scorer + ChromaDB) |
| GPU mode | No | Yes (Mamba temporal understanding) |

## License

Apache 2.0
