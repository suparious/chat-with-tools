"""
Memory Tool for Chat with Tools Framework

This tool provides persistent memory capabilities for agents,
allowing them to store and retrieve information across conversations.
Uses a simple JSON-based storage system.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib
from .base_tool import BaseTool


class MemoryStore:
    """Simple memory storage system."""
    
    def __init__(self, storage_path: str = "./agent_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_path / "index.json"
        self.memories_dir = self.storage_path / "memories"
        self.memories_dir.mkdir(exist_ok=True)
        self._load_index()
    
    def _load_index(self):
        """Load the memory index."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {
                "memories": {},
                "tags": {},
                "total_memories": 0
            }
    
    def _save_index(self):
        """Save the memory index."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a memory."""
        timestamp = str(datetime.now().timestamp())
        content_hash = hashlib.md5(f"{content}{timestamp}".encode()).hexdigest()[:8]
        return f"mem_{content_hash}_{int(timestamp)}"
    
    def store(
        self,
        content: str,
        memory_type: str = "fact",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a memory."""
        memory_id = self._generate_id(content)
        
        memory = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "accessed_count": 0,
            "last_accessed": None
        }
        
        # Save memory file
        memory_file = self.memories_dir / f"{memory_id}.json"
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
        
        # Update index
        self.index["memories"][memory_id] = {
            "type": memory_type,
            "tags": tags or [],
            "created_at": memory["created_at"],
            "summary": content[:100] + "..." if len(content) > 100 else content
        }
        
        # Update tag index
        for tag in (tags or []):
            if tag not in self.index["tags"]:
                self.index["tags"][tag] = []
            self.index["tags"][tag].append(memory_id)
        
        self.index["total_memories"] += 1
        self._save_index()
        
        return memory_id
    
    def retrieve(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory."""
        memory_file = self.memories_dir / f"{memory_id}.json"
        
        if not memory_file.exists():
            return None
        
        with open(memory_file, 'r') as f:
            memory = json.load(f)
        
        # Update access stats
        memory["accessed_count"] += 1
        memory["last_accessed"] = datetime.now().isoformat()
        
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
        
        return memory
    
    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories."""
        results = []
        
        for memory_id, info in self.index["memories"].items():
            # Filter by type
            if memory_type and info["type"] != memory_type:
                continue
            
            # Filter by tags
            if tags and not any(tag in info["tags"] for tag in tags):
                continue
            
            # Filter by query
            if query and query.lower() not in info["summary"].lower():
                memory = self.retrieve(memory_id)
                if memory and query.lower() not in memory["content"].lower():
                    continue
            
            results.append({
                "id": memory_id,
                "summary": info["summary"],
                "type": info["type"],
                "tags": info["tags"],
                "created_at": info["created_at"]
            })
        
        # Sort by creation date (newest first)
        results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return results[:limit]
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory."""
        memory_file = self.memories_dir / f"{memory_id}.json"
        
        if not memory_file.exists():
            return False
        
        # Remove file
        memory_file.unlink()
        
        # Update index
        if memory_id in self.index["memories"]:
            info = self.index["memories"][memory_id]
            
            # Remove from tag index
            for tag in info["tags"]:
                if tag in self.index["tags"]:
                    self.index["tags"][tag].remove(memory_id)
                    if not self.index["tags"][tag]:
                        del self.index["tags"][tag]
            
            del self.index["memories"][memory_id]
            self.index["total_memories"] -= 1
            self._save_index()
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        type_counts = {}
        for info in self.index["memories"].values():
            mem_type = info["type"]
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
        
        return {
            "total_memories": self.index["total_memories"],
            "memory_types": type_counts,
            "total_tags": len(self.index["tags"]),
            "popular_tags": sorted(
                [(tag, len(ids)) for tag, ids in self.index["tags"].items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


class MemoryTool(BaseTool):
    """
    Memory tool for storing and retrieving information persistently.
    
    This tool allows agents to build up knowledge over time and
    reference it in future conversations.
    """
    
    def __init__(self, config: dict):
        self.config = config
        storage_path = config.get('memory', {}).get('storage_path', './agent_memory')
        self.store = MemoryStore(storage_path)
    
    @property
    def name(self) -> str:
        return "memory"
    
    @property
    def description(self) -> str:
        return """Store and retrieve information persistently across conversations.
        
        Memory types: 'fact', 'experience', 'preference', 'instruction', 'context'
        
        Actions:
        - store: Save new information
        - retrieve: Get specific memory by ID
        - search: Find memories by query, tags, or type
        - forget: Delete a memory
        - stats: Get memory statistics
        """
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["store", "retrieve", "search", "forget", "stats"],
                    "description": "Action to perform"
                },
                "content": {
                    "type": "string",
                    "description": "Content to store (for 'store' action)"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["fact", "experience", "preference", "instruction", "context"],
                    "default": "fact",
                    "description": "Type of memory"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorizing the memory"
                },
                "memory_id": {
                    "type": "string",
                    "description": "Memory ID (for 'retrieve' and 'forget' actions)"
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for 'search' action)"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results (for 'search' action)"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute memory operations."""
        action = kwargs.get("action")
        
        try:
            if action == "store":
                content = kwargs.get("content")
                if not content:
                    return {"error": "Content is required for storing"}
                
                memory_id = self.store.store(
                    content=content,
                    memory_type=kwargs.get("memory_type", "fact"),
                    tags=kwargs.get("tags", [])
                )
                
                return {
                    "status": "stored",
                    "memory_id": memory_id,
                    "message": f"Memory stored successfully with ID: {memory_id}"
                }
            
            elif action == "retrieve":
                memory_id = kwargs.get("memory_id")
                if not memory_id:
                    return {"error": "Memory ID is required for retrieval"}
                
                memory = self.store.retrieve(memory_id)
                if memory:
                    return {
                        "status": "retrieved",
                        "memory": memory
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": f"Memory with ID {memory_id} not found"
                    }
            
            elif action == "search":
                results = self.store.search(
                    query=kwargs.get("query"),
                    tags=kwargs.get("tags"),
                    memory_type=kwargs.get("memory_type"),
                    limit=kwargs.get("limit", 10)
                )
                
                return {
                    "status": "searched",
                    "results": results,
                    "count": len(results)
                }
            
            elif action == "forget":
                memory_id = kwargs.get("memory_id")
                if not memory_id:
                    return {"error": "Memory ID is required for deletion"}
                
                if self.store.delete(memory_id):
                    return {
                        "status": "forgotten",
                        "message": f"Memory {memory_id} deleted successfully"
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": f"Memory {memory_id} not found"
                    }
            
            elif action == "stats":
                stats = self.store.get_stats()
                return {
                    "status": "stats",
                    "statistics": stats
                }
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": f"Memory operation failed: {str(e)}"}
