# Tier 3 — Memory System

> **Goal:** JARVIS remembers everything — conversations, facts, preferences, tasks.
> **Est. time:** 6-8 hours · **Depends on:** Tier 2

## ✅ Checklist
- [ ] `core/memory.py` — Three-tier memory architecture
- [ ] Short-term memory: conversation ring buffer with token management
- [ ] Long-term memory: ChromaDB vector database
- [ ] Long-term memory: Embedding generation via sentence-transformers
- [ ] Episodic memory: structured event/task logging
- [ ] Semantic search: query relevant memories before each response
- [ ] Memory consolidation: deduplication and pruning
- [ ] User-facing memory commands (remember, recall, forget)
- [ ] Memory persistence across sessions
- [ ] Memory injection into LLM context
- [ ] Test: "JARVIS remembers something from an earlier conversation"

---

## 📄 core/memory.py — Memory Architecture

### Three-Tier Model

```
┌──────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  SHORT-TERM (Buffer)        LONG-TERM (Vector DB)            │
│  ┌────────────────────┐    ┌──────────────────────┐          │
│  │ Last 20 exchanges  │    │ ChromaDB             │          │
│  │ ~6000 tokens       │    │ ┌────────────────┐   │          │
│  │ Auto-trimmed       │    │ │Embeddings      │   │          │
│  │                    │    │ │Facts           │   │          │
│  │ Active session     │    │ │Preferences     │   │          │
│  └────────────────────┘    │ │Past topics     │   │          │
│                             │ │Skills/tools    │   │          │
│                             │ └────────────────┘   │          │
│                             └──────────────────────┘          │
│                                                               │
│  EPISODIC (Structured Logs)                                   │
│  ┌───────────────────────────┐                                │
│  │ Event: timestamp, action  │                                │
│  │ Task: status, result      │                                │
│  │ Routine: pattern, time    │                                │
│  └───────────────────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

### Implementation

```python
"""
Memory System — Three-tier memory for JARVIS.
"""

import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np


@dataclass
class MemoryItem:
    """A single piece of stored information."""
    id: str
    content: str
    type: str  # "fact", "preference", "summary", "event", "tool"
    timestamp: float
    importance: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = None


class ShortTermMemory:
    """Ring buffer of recent conversation history."""
    
    def __init__(self, max_tokens: int = 6000, max_messages: int = 20):
        self.messages: List[Dict] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._trim()
    
    def get_recent(self, count: int = None) -> List[Dict]:
        if count:
            return self.messages[-count:]
        return self.messages
    
    def _trim(self):
        # Remove oldest pairs if over max_messages
        while len(self.messages) > self.max_messages * 2:
            self.messages.pop(0)
        
        # Token-aware trimming (rough: 4 chars ≈ 1 token)
        total = sum(len(m["content"]) for m in self.messages)
        while total > self.max_tokens * 4:
            self.messages.pop(0)
            self.messages.pop(0)
            total = sum(len(m["content"]) for m in self.messages)
    
    def summarize_for_archive(self) -> str:
        """Generate a summary of recent conversation for long-term storage."""
        if not self.messages:
            return ""
        # In practice, this would call the LLM to generate a summary
        return f"Conversation: {len(self.messages)} messages"


class LongTermMemory:
    """Vector database for semantic memory retrieval."""
    
    def __init__(self, storage_path: str = "./memory_store"):
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        self.client = chromadb.PersistentClient(path=storage_path)
        self.collection = self.client.get_or_create_collection(
            name="jarvis_memory",
            metadata={"hnsw:space": "cosine"}
        )
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
    
    def store(self, item: MemoryItem):
        """Store a memory item with embedding."""
        embedding = self.encoder.encode(item.content).tolist()
        
        self.collection.add(
            ids=[item.id],
            embeddings=[embedding],
            documents=[item.content],
            metadatas=[{
                "type": item.type,
                "timestamp": item.timestamp,
                "importance": item.importance,
                "metadata": json.dumps(item.metadata or {}),
            }]
        )
    
    def query(self, query: str, n_results: int = 5, 
              type_filter: str = None) -> List[MemoryItem]:
        """Search memory by semantic similarity."""
        query_embedding = self.encoder.encode(query).tolist()
        
        where = {}
        if type_filter:
            where = {"type": type_filter}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where if where else None,
        )
        
        items = []
        for i in range(len(results["ids"][0])):
            items.append(MemoryItem(
                id=results["ids"][0][i],
                content=results["documents"][0][i],
                type=results["metadatas"][0][i].get("type", "unknown"),
                timestamp=results["metadatas"][0][i].get("timestamp", 0),
                importance=results["metadatas"][0][i].get("importance", 0.5),
                metadata=json.loads(
                    results["metadatas"][0][i].get("metadata", "{}")
                ),
            ))
        
        return items
    
    def forget(self, item_id: str):
        """Delete a specific memory."""
        self.collection.delete(ids=[item_id])
    
    def forget_all(self, type_filter: str = None):
        """Clear memories, optionally filtered by type."""
        if type_filter:
            self.collection.delete(where={"type": type_filter})
        else:
            self.collection.delete(where={})


class EpisodicMemory:
    """Structured logging of events, tasks, and routines."""
    
    def __init__(self, log_path: str = "./logs/episodic.jsonl"):
        self.log_path = log_path
    
    def log_event(self, event_type: str, description: str, 
                  success: bool = True, details: dict = None):
        """Log a significant event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "success": success,
            "details": details or {},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_recent_events(self, count: int = 10) -> List[Dict]:
        """Get most recent events."""
        events = []
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except FileNotFoundError:
            pass
        return events[-count:]
    
    def find_events(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search events by description keywords."""
        results = []
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        if query.lower() in event.get("description", "").lower():
                            results.append(event)
        except FileNotFoundError:
            pass
        return results[:max_results]


class Memory:
    """Unified memory interface combining all three tiers."""
    
    def __init__(self, settings):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(
            settings.get("memory_storage_path", "./memory_store")
        )
        self.episodic = EpisodicMemory(
            settings.get("memory_log_path", "./logs/episodic.jsonl")
        )
    
    def add_conversation(self, role: str, content: str):
        """Add to short-term memory."""
        self.short_term.add(role, content)
    
    def remember_fact(self, fact: str, importance: float = 0.5, 
                      metadata: dict = None):
        """Store an important fact in long-term memory."""
        item = MemoryItem(
            id=f"fact_{time.time_ns()}",
            content=fact,
            type="fact",
            timestamp=time.time(),
            importance=importance,
            metadata=metadata,
        )
        self.long_term.store(item)
    
    def recall(self, query: str, n_results: int = 5) -> str:
        """
        Search all memory for context relevant to the query.
        Returns a formatted string for LLM context injection.
        """
        memories = self.long_term.query(query, n_results)
        recent_events = self.episodic.get_recent_events(3)
        
        if not memories and not recent_events:
            return ""
        
        context = "## Relevant Memories:\n"
        for m in memories:
            context += f"- [{m.type}] {m.content}\n"
        
        if recent_events:
            context += "\n## Recent Events:\n"
            for e in recent_events:
                context += f"- {e['description']} ({'✅' if e['success'] else '❌'})\n"
        
        return context
    
    def inject_into_context(self, user_input: str) -> str:
        """
        Query memory and return context string for LLM prompt injection.
        Called by Brain before sending to LLM.
        """
        return self.recall(user_input)
```

### Memory Commands (Voice)

These special phrases trigger memory operations:

- *"JARVIS, remember that..."* → `memory.remember_fact(...)`
- *"JARVIS, what do you know about [X]?"* → `memory.recall("X")`
- *"JARVIS, forget [X]"* → `memory.forget(...)`
- *"JARVIS, remind me to [do X] at [time]"* → Scheduled reminder

---

## 🔧 Settings Keys

```yaml
memory:
  storage_path: ./memory_store
  log_path: ./logs
  max_history_tokens: 6000
  max_history_messages: 20
  embedding_model: all-MiniLM-L6-v2
  memory_injection: true           # Auto-inject memories into context
  auto_summarize: true             # Summarize old conversations
  importance_threshold: 0.3        # Minimum importance to keep
```

## 🔗 Next Agent

When complete → move to `.agent/tier4-tools.agent.md`
