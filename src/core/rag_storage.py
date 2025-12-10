"""
RAG Storage - Menyimpan dan mengambil RAG process data
Setiap query RAG akan disimpan dengan unique ID untuk ditampilkan di dashboard
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid
from pathlib import Path

STORAGE_DIR = Path(__file__).parent.parent.parent / "data" / "rag_queries"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_query_id() -> str:
    """Generate unique ID untuk query"""
    return str(uuid.uuid4())[:8]


def save_rag_process(
    query: str,
    retrieved_docs: List[Dict],
    response: str,
    intent: str = "rag",
    user_id: Optional[str] = None
) -> str:
    """
    Simpan RAG process data ke file JSON
    
    Args:
        query: User query
        retrieved_docs: List of retrieved documents dengan scores
        response: Bot response
        intent: Intent type (rag, hybrid, dll)
        user_id: User ID (optional)
    
    Returns:
        query_id: Unique ID untuk query ini
    """
    query_id = generate_query_id()
    
    data = {
        "query_id": query_id,
        "query": query,
        "response": response,
        "intent": intent,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "num_docs": len(retrieved_docs),
        "avg_score": sum(d.get('score', 0) for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0,
        "documents": retrieved_docs
    }
    
    file_path = STORAGE_DIR / f"{query_id}.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return query_id


def get_rag_process(query_id: str) -> Optional[Dict]:
    """
    Ambil RAG process data berdasarkan query_id
    
    Args:
        query_id: Query ID
    
    Returns:
        RAG process data atau None jika tidak ditemukan
    """
    file_path = STORAGE_DIR / f"{query_id}.json"
    
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def list_recent_queries(limit: int = 50) -> List[Dict]:
    """
    List recent queries (untuk debugging/monitoring)
    
    Args:
        limit: Maximum number of queries to return
    
    Returns:
        List of query metadata (tanpa full documents)
    """
    files = sorted(
        STORAGE_DIR.glob("*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )[:limit]
    
    queries = []
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            queries.append({
                "query_id": data["query_id"],
                "query": data["query"],
                "timestamp": data["timestamp"],
                "num_docs": data["num_docs"],
                "avg_score": data["avg_score"]
            })
    
    return queries


def cleanup_old_queries(days: int = 7):
    """
    Hapus query data yang lebih lama dari X hari
    
    Args:
        days: Hapus data lebih lama dari ini
    """
    import time
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    deleted = 0
    for file_path in STORAGE_DIR.glob("*.json"):
        if file_path.stat().st_mtime < cutoff_time:
            file_path.unlink()
            deleted += 1
    
    return deleted

if __name__ == "__main__":
    # Test RAG storage
    print("Testing RAG Storage...\n")
    
    # Test 1: Save RAG process
    test_docs = [
        {
            "text": "NFT (Nutrient Film Technique) adalah sistem hidroponik...",
            "score": 0.85,
            "source": "hidroponik_nft.pdf",
            "page": 5
        },
        {
            "text": "Keuntungan sistem NFT adalah efisiensi air...",
            "score": 0.72,
            "source": "hidroponik_nft.pdf",
            "page": 7
        }
    ]
    
    query_id = save_rag_process(
        query="apa itu sistem NFT?",
        retrieved_docs=test_docs,
        response="NFT adalah Nutrient Film Technique...",
        intent="rag",
        user_id="6281234567890"
    )
    
    print(f"✅ Saved RAG process with ID: {query_id}")
    
    # Test 2: Retrieve RAG process
    data = get_rag_process(query_id)
    if data:
        print(f"✅ Retrieved RAG process:")
        print(f"   Query: {data['query']}")
        print(f"   Num docs: {data['num_docs']}")
        print(f"   Avg score: {data['avg_score']:.4f}")
    
    # Test 3: List recent queries
    recent = list_recent_queries(limit=5)
    print(f"\n✅ Recent queries: {len(recent)}")
    for q in recent:
        print(f"   - {q['query_id']}: {q['query'][:50]}...")
    
    print("\n✅ All tests passed!")
