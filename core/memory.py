"""
Memory System — Three-tier memory for JARVIS.

Tiers:
  1. Short-term: Recent conversation buffer (in-memory)
  2. Long-term: Persistent knowledge store (JSON file + keyword indexing)
  3. Episodic: Event/task logging (JSONL file)

All tiers work with ZERO external dependencies (no ChromaDB needed).
When ChromaDB is available, the long-term memory will use vector search instead.
"""

import json
import os
import time
import re
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict, Counter


class ShortTermMemory:
    """Recent conversation history with token management."""

    def __init__(self, max_tokens: int = 6000, max_messages: int = 20):
        self.messages: List[Dict] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages

    def add(self, role: str, content: str):
        """Add a message to the buffer."""
        self.messages.append({"role": role, "content": content})
        self._trim()

    def get_recent(self, count: int = None) -> List[Dict]:
        """Get the most recent messages."""
        if count:
            return self.messages[-count:]
        return self.messages

    def get_formatted(self, count: int = 10) -> str:
        """Get recent messages as a formatted string for LLM injection."""
        recent = self.messages[-count:] if count else self.messages
        if not recent:
            return ""
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "JARVIS"
            # Truncate long messages for the summary
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _trim(self):
        """Remove oldest messages to stay within limits."""
        # Remove by message count
        while len(self.messages) > self.max_messages * 2:
            self.messages.pop(0)
            self.messages.pop(0)

        # Remove by token count (rough: ~4 chars per token)
        total = sum(len(m["content"]) for m in self.messages)
        while total > self.max_tokens * 4 and len(self.messages) > 4:
            self.messages.pop(0)
            self.messages.pop(0)
            total = sum(len(m["content"]) for m in self.messages)

    def clear(self):
        self.messages.clear()

    def __len__(self):
        return len(self.messages)


class LongTermMemory:
    """
    Persistent knowledge store.

    Stores facts, preferences, and past conversation summaries.
    Uses keyword-based indexing (no external dependencies needed).
    Can be upgraded to use ChromaDB vector search when available.
    """

    def __init__(self, storage_path: str = "./memory_store"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Files
        self._facts_file = self.storage_path / "facts.json"
        self._index_file = self.storage_path / "keyword_index.json"

        # In-memory cache
        self._facts: List[Dict] = []
        self._keyword_index: Dict[str, List[int]] = defaultdict(list)  # word -> fact indices

        # Lock for thread safety
        self._lock = threading.Lock()

        # Load existing data
        self._load()

    def _load(self):
        """Load facts and index from disk."""
        if self._facts_file.exists():
            with open(self._facts_file) as f:
                self._facts = json.load(f)

        if self._index_file.exists():
            with open(self._index_file) as f:
                self._keyword_index = defaultdict(list, json.load(f))

    def _save(self):
        """Save facts and index to disk."""
        with self._lock:
            with open(self._facts_file, "w") as f:
                json.dump(self._facts, f, indent=2)
            with open(self._index_file, "w") as f:
                json.dump(dict(self._keyword_index), f, indent=2)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Lowercase and split
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'shall', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'about',
            'also', 'and', 'but', 'or', 'if', 'because', 'while', 'that',
            'this', 'these', 'those', 'it', 'its', 'you', 'your', 'i',
            'me', 'my', 'we', 'our', 'they', 'them', 'he', 'she', 'him',
            'her', 'his', 'what', 'which', 'who', 'whom',
        }
        return [w for w in words if w not in stop_words]

    def _update_index(self, fact_idx: int, content: str):
        """Update the keyword index for a fact."""
        keywords = self._extract_keywords(content)
        for word in keywords:
            if fact_idx not in self._keyword_index[word]:
                self._keyword_index[word].append(fact_idx)

    def store(self, content: str, category: str = "general",
              importance: float = 0.5, source: str = "conversation"):
        """Store a fact in long-term memory.

        Args:
            content: The fact/knowledge to remember
            category: 'fact', 'preference', 'summary', 'user_info', 'general'
            importance: 0.0 (trivial) to 1.0 (critical)
            source: Where this came from
        """
        fact = {
            "id": f"mem_{int(time.time() * 1000)}_{len(self._facts)}",
            "content": content,
            "category": category,
            "importance": importance,
            "source": source,
            "created": datetime.now().isoformat(),
            "access_count": 0,
        }

        with self._lock:
            idx = len(self._facts)
            self._facts.append(fact)
            self._update_index(idx, content)

        self._save()

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search memory by keyword matching with scoring."""
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []

        with self._lock:
            # Score each fact
            scores = Counter()
            for word in query_keywords:
                for fact_idx in self._keyword_index.get(word, []):
                    scores[fact_idx] += 1

            # Get top results
            results = []
            for fact_idx, score in scores.most_common(max_results):
                if fact_idx < len(self._facts):
                    fact = dict(self._facts[fact_idx])
                    fact["relevance"] = score / len(query_keywords)
                    fact["age_hours"] = self._age_hours(fact["created"])
                    results.append(fact)
                    self._facts[fact_idx]["access_count"] += 1

        self._save()
        return results

    def recall(self, query: str, max_results: int = 5) -> str:
        """Search memory and return formatted string for LLM injection.

        Args:
            query: What to search for
            max_results: Max results

        Returns:
            Formatted string with relevant memories, or empty string
        """
        results = self.search(query, max_results)
        if not results:
            return ""

        lines = ["## Relevant Memories:"]
        for r in results:
            age = r["age_hours"]
            age_str = f"{age:.0f}h ago" if age < 24 else f"{age/24:.0f}d ago"
            lines.append(f"- [{r['category']}] {r['content']} ({age_str})")

        return "\n".join(lines)

    def get_all(self, category: str = None) -> List[Dict]:
        """Get all stored facts, optionally filtered by category."""
        if category:
            return [f for f in self._facts if f["category"] == category]
        return list(self._facts)

    def forget(self, fact_id: str) -> bool:
        """Delete a specific fact by ID."""
        with self._lock:
            for i, f in enumerate(self._facts):
                if f["id"] == fact_id:
                    self._facts.pop(i)
                    self._rebuild_index()
                    self._save()
                    return True
        return False

    def forget_all(self, category: str = None):
        """Clear memories, optionally by category."""
        with self._lock:
            if category:
                self._facts = [f for f in self._facts if f["category"] != category]
            else:
                self._facts.clear()
            self._rebuild_index()
        self._save()

    def _rebuild_index(self):
        """Rebuild the keyword index from scratch."""
        self._keyword_index.clear()
        for i, fact in enumerate(self._facts):
            self._update_index(i, fact["content"])

    def _age_hours(self, created_str: str) -> float:
        """Calculate age of a memory in hours."""
        try:
            created = datetime.fromisoformat(created_str)
            return (datetime.now() - created).total_seconds() / 3600
        except Exception:
            return 0

    def count(self) -> int:
        """Number of stored facts."""
        return len(self._facts)


class EpisodicMemory:
    """Event and task logging (JSONL format)."""

    def __init__(self, log_path: str = "./logs/episodic.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: str, description: str,
            success: bool = True, details: dict = None):
        """Log a significant event.

        Args:
            event_type: 'task', 'error', 'command', 'milestone', 'interaction'
            description: Human-readable description
            success: Whether it succeeded
            details: Optional structured data
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "success": success,
            "details": details or {},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent(self, count: int = 10) -> List[Dict]:
        """Get most recent events."""
        events = []
        try:
            with open(self.log_path) as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except FileNotFoundError:
            pass
        return events[-count:]

    def get_recent_formatted(self, count: int = 5) -> str:
        """Get recent events as formatted string for LLM injection."""
        events = self.get_recent(count)
        if not events:
            return ""
        lines = ["## Recent Events:"]
        for e in events:
            icon = "✅" if e["success"] else "❌"
            lines.append(f"- {icon} {e['description']} ({e['type']})")
        return "\n".join(lines)


class Memory:
    """Unified memory interface combining all three tiers.

    Usage:
        memory = Memory()
        memory.remember("User likes coffee")
        context = memory.recall("coffee preferences")
        memory.log_event("task", "Searched the web", True)
    """

    def __init__(self, settings=None):
        self.settings = settings or {}
        storage_path = self.settings.get("memory.storage_path", "./memory_store")
        log_path = self.settings.get("memory.log_path", "./logs")

        self.short_term = ShortTermMemory(
            max_tokens=self.settings.get("memory.max_history_tokens", 6000),
            max_messages=self.settings.get("memory.max_history_messages", 20),
        )
        self.long_term = LongTermMemory(storage_path=str(Path(storage_path)))
        self.episodic = EpisodicMemory(log_path=str(Path(log_path) / "episodic.jsonl"))

        self._enabled = self.settings.get("memory.enabled", True)
        print(f"💾 Memory ready | {self.long_term.count()} facts stored")

    # ── Short-term ──

    def add_conversation(self, role: str, content: str):
        """Add to conversation buffer."""
        if self._enabled:
            self.short_term.add(role, content)

    def get_recent_conversation(self, count: int = 10) -> str:
        """Get recent conversation as formatted string."""
        return self.short_term.get_formatted(count)

    # ── Long-term ──

    def remember(self, content: str, category: str = "general",
                 importance: float = 0.5):
        """Store something in long-term memory.

        Examples:
            memory.remember("User prefers dark mode", "preference", 0.8)
            memory.remember("JARVIS can control smart home devices", "capability", 0.6)
        """
        if self._enabled:
            self.long_term.store(content, category, importance)

    def recall(self, query: str, max_results: int = 5) -> str:
        """Search memory for relevant context.

        Returns formatted string for LLM context injection.
        """
        if not self._enabled:
            return ""
        return self.long_term.recall(query, max_results)

    def get_all_facts(self, category: str = None) -> List[Dict]:
        """Get all stored facts."""
        return self.long_term.get_all(category)

    def forget(self, fact_id: str) -> bool:
        """Delete a specific memory."""
        return self.long_term.forget(fact_id)

    def forget_all(self, category: str = None):
        """Clear memories."""
        self.long_term.forget_all(category)

    # ── Episodic ──

    def log_event(self, event_type: str, description: str,
                  success: bool = True, details: dict = None):
        """Log a significant event."""
        if self._enabled:
            self.episodic.log(event_type, description, success, details)

    def get_recent_events(self, count: int = 5) -> str:
        """Get recent events as formatted string."""
        return self.episodic.get_recent_formatted(count)

    # ── Context Injection (for Brain) ──

    def build_context(self, user_input: str) -> str:
        """Build full context string for LLM prompt injection.

        Combines relevant memories + recent events + recent conversation.
        Called by Brain before each API call.
        """
        if not self._enabled:
            return ""

        parts = []

        # 1. Relevant long-term memories
        memories = self.recall(user_input, max_results=5)
        if memories:
            parts.append(memories)

        # 2. Recent events
        events = self.get_recent_events(3)
        if events:
            parts.append(events)

        # 3. Recent conversation (last few exchanges)
        conversation = self.get_recent_conversation(count=4)
        if conversation and self.short_term.messages:
            parts.append("## Recent Conversation:\n" + conversation)

        if not parts:
            return ""

        return "\n\n".join(parts)

    # ── Stats ──

    def stats(self) -> str:
        """Get memory statistics."""
        return (
            f"  Short-term: {len(self.short_term)} messages\n"
            f"  Long-term:  {self.long_term.count()} facts\n"
            f"  Enabled:    {self._enabled}"
        )

    @property
    def is_enabled(self) -> bool:
        return self._enabled
