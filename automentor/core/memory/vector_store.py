import os
import json
import uuid
import faiss
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer
from ..models import MemoryEntry, User


class VectorMemoryStore:
    """
    Vector-based memory store using FAISS for efficient similarity search
    and long-term context retention.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 store_path: str = "./data/vector_store"):
        self.model_name = model_name
        self.store_path = store_path
        self.encoder = SentenceTransformer(model_name)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        
        # Create storage directory
        os.makedirs(store_path, exist_ok=True)
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Memory storage
        self.memories: Dict[str, MemoryEntry] = {}
        self.user_memories: Dict[str, List[str]] = {}  # user_id -> list of memory_ids
        
        # Load existing data
        self._load_store()
    
    def _load_store(self):
        """Load existing vector store and memories from disk"""
        index_path = os.path.join(self.store_path, "faiss_index.bin")
        memories_path = os.path.join(self.store_path, "memories.json")
        
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
        
        if os.path.exists(memories_path):
            with open(memories_path, 'r') as f:
                data = json.load(f)
                # Reconstruct MemoryEntry objects
                for mem_id, mem_data in data['memories'].items():
                    mem_data['created_at'] = datetime.fromisoformat(mem_data['created_at'])
                    self.memories[mem_id] = MemoryEntry(**mem_data)
                self.user_memories = data['user_memories']
    
    def _save_store(self):
        """Save vector store and memories to disk"""
        index_path = os.path.join(self.store_path, "faiss_index.bin")
        memories_path = os.path.join(self.store_path, "memories.json")
        
        faiss.write_index(self.index, index_path)
        
        # Convert memories to serializable format
        serializable_memories = {}
        for mem_id, memory in self.memories.items():
            mem_dict = memory.dict()
            mem_dict['created_at'] = mem_dict['created_at'].isoformat()
            serializable_memories[mem_id] = mem_dict
        
        data = {
            'memories': serializable_memories,
            'user_memories': self.user_memories
        }
        
        with open(memories_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_memory(self, user_id: str, content: str, memory_type: str = "conversation",
                   metadata: Optional[Dict[str, Any]] = None, importance: float = 0.5) -> str:
        """Add a new memory to the store"""
        memory_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = self.encoder.encode([content])[0].tolist()
        
        # Create memory entry
        memory = MemoryEntry(
            id=memory_id,
            user_id=user_id,
            content=content,
            type=memory_type,
            metadata=metadata or {},
            embedding=embedding,
            importance=importance
        )
        
        # Store memory
        self.memories[memory_id] = memory
        
        # Add to user's memory list
        if user_id not in self.user_memories:
            self.user_memories[user_id] = []
        self.user_memories[user_id].append(memory_id)
        
        # Add to FAISS index
        embedding_array = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(embedding_array)  # Normalize for cosine similarity
        self.index.add(embedding_array)
        
        # Save to disk
        self._save_store()
        
        return memory_id
    
    def search_memories(self, user_id: str, query: str, top_k: int = 5, 
                       memory_types: Optional[List[str]] = None) -> List[MemoryEntry]:
        """Search for relevant memories based on semantic similarity"""
        if user_id not in self.user_memories or not self.user_memories[user_id]:
            return []
        
        # Generate query embedding
        query_embedding = self.encoder.encode([query])[0]
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_array, min(top_k * 3, len(self.memories)))
        
        # Filter results by user and memory type
        user_memory_ids = set(self.user_memories[user_id])
        results = []
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
            
            # Find memory by index (this is a simplified approach)
            # In a production system, you'd maintain an index mapping
            memory_id = list(self.memories.keys())[idx] if idx < len(self.memories) else None
            
            if memory_id and memory_id in user_memory_ids:
                memory = self.memories[memory_id]
                
                # Filter by memory type if specified
                if memory_types and memory.type not in memory_types:
                    continue
                
                results.append(memory)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_user_context(self, user_id: str, context_window: int = 20) -> List[MemoryEntry]:
        """Get recent context for a user"""
        if user_id not in self.user_memories:
            return []
        
        user_memory_ids = self.user_memories[user_id]
        user_memories = [self.memories[mid] for mid in user_memory_ids if mid in self.memories]
        
        # Sort by recency and importance
        user_memories.sort(key=lambda m: (m.created_at, m.importance), reverse=True)
        
        return user_memories[:context_window]
    
    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by ID"""
        return self.memories.get(memory_id)
    
    def update_memory_importance(self, memory_id: str, importance: float):
        """Update the importance score of a memory"""
        if memory_id in self.memories:
            self.memories[memory_id].importance = importance
            self._save_store()
    
    def delete_memory(self, memory_id: str, user_id: str):
        """Delete a memory from the store"""
        if memory_id in self.memories and memory_id in self.user_memories.get(user_id, []):
            del self.memories[memory_id]
            self.user_memories[user_id].remove(memory_id)
            # Note: FAISS doesn't support efficient deletion, so we keep the vector
            # In production, you'd rebuild the index periodically
            self._save_store()
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's memories"""
        if user_id not in self.user_memories:
            return {"total_memories": 0, "memory_types": {}}
        
        user_memory_ids = self.user_memories[user_id]
        user_memories = [self.memories[mid] for mid in user_memory_ids if mid in self.memories]
        
        memory_types = {}
        for memory in user_memories:
            memory_types[memory.type] = memory_types.get(memory.type, 0) + 1
        
        return {
            "total_memories": len(user_memories),
            "memory_types": memory_types,
            "oldest_memory": min(m.created_at for m in user_memories) if user_memories else None,
            "newest_memory": max(m.created_at for m in user_memories) if user_memories else None,
            "average_importance": sum(m.importance for m in user_memories) / len(user_memories) if user_memories else 0
        }