"""
Quick Wins untuk Improve RAG Canopya
Alternative yang lebih ringan dari GEPA/DSPy

1. Hybrid Search (BM25 + Vector)
2. Query Expansion (Domain-specific synonyms)
3. Better Prompting

Total effort: 2-3 hari
Expected improvement: 30-40%
"""

from typing import List, Dict, Optional
import logging
import re

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    logging.warning("rank-bm25 not installed. Hybrid Search will fallback to vector search only.")

logger = logging.getLogger(__name__)


class QueryExpander:
    """
    Expand user queries dengan domain-specific synonyms
    untuk improve retrieval tanpa re-indexing
    """
    
    def __init__(self):
        # Domain dictionary untuk hidroponik
        self.synonyms = {
            # Sistem hidroponik
            "nft": ["nft", "nutrient film technique", "film nutrisi", "sistem nft"],
            "dft": ["dft", "deep flow technique", "deep water culture", "dwc"],
            "wick": ["wick", "sistem sumbu", "sumbu"],
            "drip": ["drip", "tetes", "sistem tetes", "drip irrigation"],
            
            # Parameter
            "ph": ["ph", "keasaman", "tingkat keasaman", "derajat keasaman"],
            "ec": ["ec", "electrical conductivity", "konduktivitas", "tds"],
            "ppm": ["ppm", "parts per million", "kepekatan"],
            
            # Nutrisi
            "nutrisi": ["nutrisi", "pupuk", "hara", "unsur hara", "larutan nutrisi"],
            "nitrogen": ["nitrogen", "n", "unsur n"],
            "fosfor": ["fosfor", "p", "phosphorus", "unsur p"],
            "kalium": ["kalium", "k", "potassium", "unsur k"],
            "npk": ["npk", "nitrogen fosfor kalium"],
            
            # Tanaman
            "selada": ["selada", "lettuce", "salad"],
            "kangkung": ["kangkung", "water spinach", "kangkong"],
            "bayam": ["bayam", "spinach"],
            "tomat": ["tomat", "tomato"],
            "cabai": ["cabai", "chili", "cabe", "pepper"],
            
            # Masalah
            "busuk": ["busuk", "rot", "pembusukan", "decay"],
            "layu": ["layu", "wilt", "wilting", "kering"],
            "kuning": ["kuning", "yellow", "yellowing", "klorosis", "chlorosis"],
            "hama": ["hama", "pest", "serangga"],
            "penyakit": ["penyakit", "disease", "sakit"],
            
            # Action words
            "cara": ["cara", "bagaimana", "how", "metode", "langkah"],
            "atur": ["atur", "setting", "adjust", "kontrol", "maintain"],
            "jaga": ["jaga", "maintain", "keep", "pertahankan"],
            "atasi": ["atasi", "solve", "fix", "perbaiki", "handle"],
        }
        
        # Stopwords yang tidak perlu di-expand
        self.stopwords = {
            "yang", "untuk", "dari", "di", "ke", "pada", "dengan", "adalah",
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and"
        }
    
    def expand(self, query: str, max_expansions: int = 3) -> str:
        """
        Expand query dengan synonyms
        
        Args:
            query: Original user query
            max_expansions: Max synonyms per term
        
        Returns:
            Expanded query
        """
        query_lower = query.lower()
        words = query_lower.split()
        
        # Collect expansions
        expansions = []
        
        for word in words:
            # Skip stopwords
            if word in self.stopwords:
                continue
            
            # Clean word dari punctuation
            clean_word = word.strip('.,!?;:⚠️')
            
            # Check if word has synonyms (exact match only)
            if clean_word in self.synonyms:
                # Add synonyms (limit to max_expansions)
                expansions.extend(self.synonyms[clean_word][:max_expansions])
        
        # Combine original + expansions
        if expansions:
            expanded = f"{query} {' '.join(set(expansions))}"
            logger.info(f"Expanded query: '{query}' → '{expanded}'")
            return expanded
        
        return query
    
    def add_synonym(self, term: str, synonyms: List[str]):
        """Add custom synonym mapping"""
        self.synonyms[term.lower()] = [s.lower() for s in synonyms]


class HybridRetriever:
    """
    Hybrid retrieval: Vector search + BM25 Keyword search
    Menggunakan Reciprocal Rank Fusion (RRF) untuk combine results
    """
    
    def __init__(self, qdrant_client, embedder, collection_name: str):
        self.qdrant = qdrant_client
        self.embedder = embedder
        self.collection_name = collection_name
        self.bm25_index = None
        self.documents_cache = []
        self._build_bm25_index()
    
    def _build_bm25_index(self):
        """Build BM25 index from all documents in Qdrant"""
        if not HAS_BM25:
            logger.warning("rank-bm25 not available, skipping BM25 index building")
            return
        
        try:
            from rank_bm25 import BM25Okapi
            import re
            
            # Get actual Qdrant client (handle HybridQdrantClient wrapper)
            qdrant_client = getattr(self.qdrant, 'active_client', self.qdrant)
            
            # Fetch all documents from Qdrant
            scroll_result = qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            points = scroll_result[0]
            
            # Extract texts and build corpus
            corpus = []
            self.documents_cache = []
            
            for point in points:
                text = point.payload.get('text', '')
                # Tokenize for BM25
                tokens = re.findall(r'\w+', text.lower())
                corpus.append(tokens)
                self.documents_cache.append({
                    'id': point.id,
                    'text': text,
                    'payload': point.payload
                })
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(corpus)
            logger.info(f"✅ BM25 index built with {len(corpus)} documents")
            
        except Exception as e:
            logger.warning(f"Failed to build BM25 index: {e}")
            self.bm25_index = None
    
    def _bm25_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """BM25 keyword search"""
        if self.bm25_index is None:
            return []
        
        import re
        
        # Tokenize query
        query_tokens = re.findall(r'\w+', query.lower())
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                doc = self.documents_cache[idx].copy()
                doc['score'] = float(scores[idx])
                doc['method'] = 'bm25'
                results.append(doc)
        
        return results
    
    def _vector_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Vector semantic search"""
        query_embedding = self.embedder.encode(
            f"query: {query}", 
            normalize_embeddings=True
        ).tolist()
        
        vector_results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        results = []
        for hit in vector_results:
            doc = {
                'id': hit.id,
                'text': hit.payload.get('text', ''),
                'score': hit.score,
                'payload': hit.payload,
                'method': 'vector'
            }
            results.append(doc)
        
        return results
    
    def _reciprocal_rank_fusion(
        self, 
        bm25_results: List[Dict], 
        vector_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion (RRF) untuk combine BM25 + Vector results
        
        RRF Score = sum(1 / (k + rank))
        k = 60 adalah default yang bagus (dari paper)
        """
        
        # Build score dict
        doc_scores = {}
        doc_data = {}
        
        # Add BM25 scores
        for rank, doc in enumerate(bm25_results, start=1):
            doc_id = doc['id']
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
        
        # Add Vector scores
        for rank, doc in enumerate(vector_results, start=1):
            doc_id = doc['id']
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score
            if doc_id not in doc_data:
                doc_data[doc_id] = doc
        
        # Sort by RRF score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Build final results
        results = []
        for doc_id, rrf_score in sorted_docs:
            doc = doc_data[doc_id].copy()
            doc['rrf_score'] = rrf_score
            doc['method'] = 'hybrid'
            results.append(doc)
        
        return results
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Dict]:
        """
        Hybrid retrieval dengan BM25 + Vector search + RRF
        
        Args:
            query: User query
            top_k: Number of final results
            use_hybrid: If False, use vector search only
        
        Returns:
            List of retrieved documents
        """
        
        if not use_hybrid or self.bm25_index is None:
            # Fallback to vector search only
            vector_results = self._vector_search(query, top_k)
            return self._format_results(vector_results[:top_k])
        
        # Hybrid search: BM25 + Vector + RRF
        bm25_results = self._bm25_search(query, top_k * 2)
        vector_results = self._vector_search(query, top_k * 2)
        
        # Combine with RRF
        hybrid_results = self._reciprocal_rank_fusion(bm25_results, vector_results)
        
        # Return top-k
        return self._format_results(hybrid_results[:top_k])
    
    def _format_results(self, results: List[Dict]) -> List[Dict]:
        """Format results untuk compatibility dengan RAGEngine"""
        if not results:
            return []
        
        # Scale RRF scores ke range yang comparable dengan vector scores (0.5-1.0)
        # Vector scores biasanya 0.7-0.9, jadi kita scale RRF ke range yang mirip
        rrf_scores = [doc.get('rrf_score', doc.get('score', 0)) for doc in results]
        
        if rrf_scores and max(rrf_scores) > 0:
            max_score = max(rrf_scores)
            
            # Scale: normalize by max, then map to range [0.5, 1.0]
            # Formula: 0.5 + (score / max_score) * 0.5
            # Ini membuat top result = 1.0, dan results lain scaled proportionally
            normalized_scores = [0.5 + (s / max_score) * 0.5 for s in rrf_scores]
        else:
            # Fallback: use original scores
            normalized_scores = rrf_scores
        
        formatted = []
        for i, doc in enumerate(results):
            payload = doc.get('payload', {})
            formatted_doc = {
                'text': doc.get('text', ''),
                'score': normalized_scores[i],  # Use scaled score
                'raw_rrf_score': doc.get('rrf_score', doc.get('score', 0)),  # Keep original for debugging
                'source_title': payload.get('source_title', 'Unknown'),
                'source_file': payload.get('source_file', ''),
                'source': payload.get('source', ''),
                'page': payload.get('page'),
                'section': payload.get('section'),
                'images': payload.get('images', []),
                'has_table': payload.get('has_table', False),
                'type': payload.get('type', 'unknown'),
                'method': doc.get('method', 'unknown')
            }
            formatted.append(formatted_doc)
        
        return formatted




class ImprovedRAGEngine:
    """
    RAG Engine dengan quick wins:
    - Query Expansion
    - Hybrid Search
    - Better Prompting
    """
    
    def __init__(
        self,
        qdrant_client,
        embedder,
        ollama_client,
        collection_name: str = "aquaponics_knowledge"
    ):
        self.query_expander = QueryExpander()
        self.hybrid_retriever = HybridRetriever(
            qdrant_client, 
            embedder, 
            collection_name
        )
        self.ollama = ollama_client
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        use_expansion: bool = True
    ) -> List[Dict]:
        """
        Retrieve dengan query expansion + hybrid search
        """
        
        # Expand query
        if use_expansion:
            expanded_query = self.query_expander.expand(query)
        else:
            expanded_query = query
        
        # Hybrid retrieval
        documents = self.hybrid_retriever.retrieve(
            expanded_query, 
            top_k=top_k
        )
        
        logger.info(f"Retrieved {len(documents)} documents for: {query}")
        
        return documents
    
    def generate(
        self, 
        query: str, 
        context_docs: List[Dict],
        language: str = "id"
    ) -> Dict:
        """
        Generate dengan improved prompt
        """
        
        # Build context
        context = "\n\n".join([
            f"[Dokumen {i+1} - {doc['source_title']}]\n{doc['text']}"
            for i, doc in enumerate(context_docs[:3])
        ])
        
        # Improved prompt (hasil manual engineering)
        if language == "id":
            system_prompt = """Kamu adalah asisten ahli hidroponik yang membantu petani Indonesia.

TUGAS:
Jawab pertanyaan dengan jelas, praktis, dan mudah dipahami.

ATURAN PENTING:
1. Gunakan bahasa Indonesia yang NATURAL dan CONVERSATIONAL (seperti ngobrol dengan teman)
2. Berikan jawaban yang ACTIONABLE (bisa langsung dipraktikkan)
3. Gunakan HANYA informasi dari dokumen yang diberikan
4. Kalau ada angka/range (pH, EC, dll), SEBUTKAN dengan jelas
5. Kalau perlu langkah-langkah, gunakan numbering sederhana
6. JANGAN gunakan markdown formatting (*, **, _, dll)
7. Untuk penekanan, gunakan HURUF KAPITAL atau kata seperti "penting:", "catatan:"

FORMAT JAWABAN:
- Mulai dengan jawaban langsung (jangan bertele-tele)
- Kalau perlu detail, baru kasih penjelasan
- Kalau ada tips praktis, tambahkan di akhir

CONTOH BAGUS:
"pH ideal untuk NFT adalah 5.5-6.5.

Cara cek:
1. Pakai pH meter digital (lebih akurat)
2. Cek 2 kali sehari (pagi & sore)
3. Kalau di luar range, adjust pakai pH down/up

Catatan: pH terlalu tinggi bikin nutrisi susah diserap tanaman."

CONTOH JELEK:
"Berdasarkan dokumen yang tersedia, untuk sistem NFT direkomendasikan..."
(Terlalu formal dan bertele-tele!)
"""
        else:
            system_prompt = """You are a hydroponics expert helping farmers.

TASK:
Answer questions clearly, practically, and easy to understand.

IMPORTANT RULES:
1. Use NATURAL and CONVERSATIONAL English
2. Provide ACTIONABLE answers (can be directly applied)
3. Use ONLY information from provided documents
4. If there are numbers/ranges (pH, EC, etc), STATE them clearly
5. If steps needed, use simple numbering
6. DO NOT use markdown formatting (*, **, _, etc)
7. For emphasis, use CAPITAL LETTERS or words like "important:", "note:"

ANSWER FORMAT:
- Start with direct answer (don't beat around the bush)
- Add details if needed
- Add practical tips at the end if relevant
"""
        
        prompt = f"""{system_prompt}

DOKUMEN:
{context}

PERTANYAAN: {query}

JAWABAN:"""
        
        response = self.ollama.generate(
            prompt=prompt,
            options={"temperature": 0.3, "top_p": 0.9}
        )
        
        return {
            'answer': response['response'].strip(),
            'sources': [doc['source_title'] for doc in context_docs[:3]],
            'confidence': sum(doc['score'] for doc in context_docs[:3]) / 3,
            'num_sources': len(context_docs),
        }
    
    def query(
        self, 
        user_query: str, 
        top_k: int = 5,
        language: str = "id",
        use_expansion: bool = True
    ) -> Dict:
        """
        Complete RAG pipeline dengan improvements
        """
        
        # Retrieve
        documents = self.retrieve(
            user_query, 
            top_k=top_k,
            use_expansion=use_expansion
        )
        
        if not documents:
            return {
                'answer': "Maaf, informasi tidak ditemukan dalam knowledge base.",
                'sources': [],
                'confidence': 0.0,
                'num_sources': 0,
            }
        
        # Generate
        result = self.generate(user_query, documents, language=language)
        
        return result


if __name__ == "__main__":
    
    # Test Query Expander
    print("="*60)
    print("QUERY EXPANSION TEST")
    print("="*60)
    
    expander = QueryExpander()
    
    test_queries = [
        "Berapa pH untuk NFT?",
        "Gimana cara ngatur nutrisi selada?",
        "Kenapa kangkung saya kuning?",
        "Cara atasi hama pada tomat",
    ]
    
    for query in test_queries:
        expanded = expander.expand(query)
        print(f"\nOriginal: {query}")
        print(f"Expanded: {expanded}")
    
    print("\n" + "="*60)
    print("✅ Query expansion test complete")
