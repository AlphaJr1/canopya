"""
RAG Engine for Multimodal Hydroponic Knowledge Base
Supports text + images + tables from PDF and web sources
"""

import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from src.core.hybrid_qdrant import HybridQdrantClient
from src.core.hybrid_ollama import HybridOllamaClient
from src.core.quick_wins_rag import QueryExpander, HybridRetriever
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation Engine"""
    
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        cache_folder: str = None,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "aquaponics_knowledge",
        ollama_model: str = "ministral-3:3b",
        use_query_expansion: bool = True,
        use_hybrid_search: bool = True  # ENABLED by default: +4% diversity, -8% bias, -10% latency
    ):
        # Load E5-base model from local cache (no HuggingFace checks)
        import os
        import glob
        
        # Set default cache_folder to project root/models
        if cache_folder is None:
            # Get the project root (3 levels up from this file: src/core/rag_engine.py)
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            cache_folder = os.path.join(project_root, "models")
        
        # Convert cache_folder to absolute path
        if not os.path.isabs(cache_folder):
            cache_folder = os.path.abspath(cache_folder)
        
        try:
            # First try: direct model name with local_files_only
            self.embedder = SentenceTransformer(
                model_name, 
                cache_folder=cache_folder,
                local_files_only=True,
                trust_remote_code=False
            )
            logger.info(f"✅ Loaded model from cache: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load with model name, trying snapshot path: {e}")
            # Fallback: try loading from HF cache snapshot directory
            cache_path = os.path.join(cache_folder, f"models--{model_name.replace('/', '--')}", "snapshots")
            logger.info(f"Looking for model in: {cache_path}")
            if os.path.exists(cache_path):
                # Find the snapshot directory (usually a hash)
                snapshots = glob.glob(os.path.join(cache_path, "*"))
                if snapshots:
                    snapshot_path = snapshots[0]  # Use the first (usually only one)
                    logger.info(f"Loading from snapshot: {snapshot_path}")
                    self.embedder = SentenceTransformer(snapshot_path, local_files_only=True)
                    logger.info(f"✅ Loaded model from snapshot")
                else:
                    raise RuntimeError(f"No snapshots found in: {cache_path}")
            else:
                raise RuntimeError(f"Model cache not found: {cache_path}")
        
        self.qdrant = HybridQdrantClient(
            local_host=qdrant_host,
            local_port=qdrant_port,
            collection_name=collection_name
        )
        self.collection_name = collection_name
        self.ollama_model = ollama_model
        
        # Initialize Hybrid Ollama Client with auto-fallback
        self.ollama = HybridOllamaClient()
        
        # Initialize Query Expander
        self.use_query_expansion = use_query_expansion
        if self.use_query_expansion:
            self.query_expander = QueryExpander()
            logger.info("✅ Query Expansion enabled")
        else:
            self.query_expander = None
            logger.info("⚠️ Query Expansion disabled")
        
        # Initialize Hybrid Search
        self.use_hybrid_search = use_hybrid_search
        if self.use_hybrid_search:
            self.hybrid_retriever = HybridRetriever(
                self.qdrant,
                self.embedder,
                self.collection_name
            )
            logger.info("✅ Hybrid Search enabled (BM25 + Vector + RRF)")
        else:
            self.hybrid_retriever = None
            logger.info("⚠️ Hybrid Search disabled (Vector only)")
        
        self._verify_setup()
    
    def _verify_setup(self):
        """Verify Qdrant and Ollama connections"""
        try:
            count = self.qdrant.count(collection_name=self.collection_name)
            logger.info(f"✅ Qdrant connected - {count.count} vectors")
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
            raise
        
        try:
            status = self.ollama.get_status()
            active = "local" if status['local']['active'] else "cloud"
            logger.info(f"✅ Ollama connected ({active} mode)")
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            raise
    
    def _clean_markdown_formatting(self, text: str) -> str:
        """
        Remove all markdown formatting from text to make it more natural for WhatsApp
        Removes: **, *, _, ~~, etc.
        """
        import re
        
        # Remove double asterisk (bold)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        
        # Remove single asterisk (italic) 
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove underscore (italic/bold)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        
        # Remove strikethrough
        text = re.sub(r'~~([^~]+)~~', r'\1', text)
        
        return text
    
    def _generate_fallback_answer(self, query: str, language: str = "id") -> Optional[str]:
        """
        Generate helpful fallback answer using general hydroponics knowledge
        when RAG docs tidak punya info spesifik
        
        Args:
            query: User query
            language: Response language
        
        Returns:
            Fallback answer atau None jika generation failed
        """
        try:
            if language == "id":
                fallback_prompt = f"""Kamu adalah ahli hidroponik yang berpengalaman. 

User bertanya: "{query}"

Dokumen knowledge base tidak punya info spesifik untuk pertanyaan ini. Berikan jawaban helpful berdasarkan prinsip UMUM hidroponik yang kamu tahu.

Aturan:
1. Gunakan bahasa natural dan conversational ("kamu" bukan "Anda")
2. Mulai dengan disclaimer: "Berdasarkan prinsip umum hidroponik..." atau "Secara umum dalam hidroponik..."
3. Berikan tips praktis dan actionable
4. Keep it concise (max 3-4 kalimat)
5. Jangan gunakan markdown formatting
6. Jika pertanyaan terlalu spesifik dan kamu tidak yakin, bilang jujur

Answer:"""
            else:
                fallback_prompt = f"""You are an experienced hydroponics expert.

User asked: "{query}"

The knowledge base doesn't have specific info for this question. Provide a helpful answer based on GENERAL hydroponics principles you know.

Rules:
1. Use natural conversational language
2. Start with disclaimer: "Based on general hydroponics principles..." or "Generally in hydroponics..."
3. Give practical and actionable tips
4. Keep it concise (max 3-4 sentences)  
5. No markdown formatting
6. If question is too specific and you're unsure, be honest

Answer:"""
            
            logger.info("🔄 Generating fallback answer...")
            response = self.ollama.generate(
                model=self.ollama.active_model,
                prompt=fallback_prompt,
                options={"temperature": 0.7, "top_p": 0.9},  # Higher temperature for creativity
                stream=False
            )
            
            fallback_answer = response.get('response', '').strip()
            fallback_answer = self._clean_markdown_formatting(fallback_answer)
            
            return fallback_answer if fallback_answer else None
            
        except Exception as e:
            logger.error(f"❌ Fallback generation failed: {e}")
            return None
    
    
    def _score_image_relevance(self, query: str, images: List[str], doc_score: float) -> List[Dict]:
        """Score and filter images based on relevance to query"""
        if not images:
            return []
        
        # Simple heuristic: images from high-scoring documents are more relevant
        # Future: could use CLIP model for semantic image-text matching
        scored_images = []
        for img_path in images:
            # Base score from document relevance
            img_score = doc_score
            
            # Boost score if query contains visual keywords
            visual_keywords = ['cara', 'setup', 'diagram', 'gambar', 'bentuk', 'struktur', 'sistem']
            if any(kw in query.lower() for kw in visual_keywords):
                img_score *= 1.2
            
            scored_images.append({
                'path': img_path,
                'score': min(img_score, 1.0),  # Cap at 1.0
                'source': 'document'
            })
        
        return scored_images
    
    def retrieve(self, query: str, top_k: int = 5, conversation_history: Optional[List[Dict]] = None) -> List[Dict]:
        """Retrieve relevant documents from vector database"""
        # Apply Query Expansion if enabled
        processed_query = query
        if self.use_query_expansion and self.query_expander:
            processed_query = self.query_expander.expand(query)
            logger.info(f"Query expanded: '{query}' → '{processed_query}'")
        
        # Enrich query with conversation history if provided
        enriched_query = processed_query
        if conversation_history and len(conversation_history) > 0:
            recent_messages = conversation_history[-3:]
            context = " ".join([f"{msg.get('role', 'user')}: {msg.get('message', '')}" 
                              for msg in recent_messages])
            enriched_query = f"{context} {processed_query}"
            logger.info(f"Enriched query with conversation history: {enriched_query[:100]}...")
        
        # Use Hybrid Search if enabled, otherwise fallback to vector search
        if self.use_hybrid_search and self.hybrid_retriever:
            documents = self.hybrid_retriever.retrieve(
                enriched_query,
                top_k=top_k,
                use_hybrid=True
            )
            logger.info(f"Retrieved {len(documents)} documents via Hybrid Search")
        else:
            # Fallback: Vector search only
            query_embedding = self.embedder.encode(f"query: {enriched_query}", normalize_embeddings=True).tolist()
            
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            
            documents = []
            for hit in results:
                doc = {
                    'text': hit.payload.get('text', ''),
                    'score': hit.score,
                    'source_title': hit.payload.get('source_title', 'Unknown'),
                    'source_file': hit.payload.get('source_file', ''),
                    'source': hit.payload.get('source', ''),
                    'page': hit.payload.get('page'),
                    'section': hit.payload.get('section'),
                    'images': hit.payload.get('images', []),
                    'has_table': hit.payload.get('has_table', False),
                    'type': hit.payload.get('type', 'unknown'),
                }
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents via Vector Search")
        
        # Add scored images to all documents
        for doc in documents:
            doc['scored_images'] = self._score_image_relevance(
                query,
                doc.get('images', []),
                doc.get('score', 0)
            )
        
        avg_score = sum(d['score'] for d in documents) / len(documents) if documents else 0
        logger.info(f"Avg score: {avg_score:.4f}")
        
        return documents
    
    def generate(self, query: str, context_docs: List[Dict], language: str = "id", include_images: bool = True, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Generate response using LLM with retrieved context"""
        logger.info("🔄 Building context from documents...")
        # Build text context - REDUCED to 2 docs for cloud compatibility
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc['text']}"
            for i, doc in enumerate(context_docs[:2])  # ← Changed from [:3] to [:2]
        ])
        logger.info(f"✅ Context built from {len(context_docs[:2])} documents")
        
        # Collect and filter images
        all_scored_images = []
        for doc in context_docs[:2]:  # ← Changed from [:3] to [:2]
            all_scored_images.extend(doc.get('scored_images', []))
        
        # Filter by relevance threshold and limit to top 3
        IMAGE_RELEVANCE_THRESHOLD = 0.7
        MAX_IMAGES = 3
        relevant_images = [
            img for img in all_scored_images 
            if img['score'] >= IMAGE_RELEVANCE_THRESHOLD
        ]
        relevant_images = sorted(relevant_images, key=lambda x: x['score'], reverse=True)[:MAX_IMAGES]
        
        # Add image context to prompt if images are available
        image_context = ""
        if relevant_images and include_images:
            image_context = f"\n\n[Tersedia {len(relevant_images)} diagram/gambar relevan untuk visualisasi]"
        
        # Build conversation history context - REDUCED to 2 exchanges
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            # Get last 2 exchanges (4 messages) instead of 3
            recent_history = conversation_history[-4:]  # ← Changed from [-6:] to [-4:]
            history_lines = []
            for msg in recent_history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                history_lines.append(f"{role}: {msg.get('message', '')}")
            history_context = "\n\nPercakapan Sebelumnya:\n" + "\n".join(history_lines)
        
        # SHORTENED system prompt for cloud compatibility
        if language == "id":
            system_prompt = """Kamu adalah asisten hidroponik yang ramah dan helpful.

Aturan penting:
1. Jawab langsung dan to the point, jangan mulai dengan "Dokumen menyebutkan..." atau "Dokumen tidak..."
2. Gunakan bahasa natural dan conversational, seolah chat dengan teman
3. Jawab HANYA berdasarkan info dari dokumen yang diberikan
4. Jika dokumen tidak punya info yang diminta, bilang "Maaf, aku tidak punya info spesifik untuk itu" - jangan jelaskan tentang dokumen
5. Berikan tips praktis dan actionable
6. Jangan gunakan markdown formatting (*, **, _)
7. Perhatikan konteks percakapan sebelumnya
        """
        else:
            system_prompt = """You are a friendly and helpful hydroponic assistant.

Important rules:
1. Answer directly and to the point, don't start with "The document mentions..." or "The document doesn't..."
2. Use natural and conversational language, like chatting with a friend
3. Answer ONLY based on info from provided documents
4. If documents lack requested info, say "Sorry, I don't have specific info for that" - don't explain about documents
5. Give practical and actionable tips
6. No markdown formatting (*, **, _)
7. Consider previous conversation context
        """
                
        prompt = f"""{system_prompt}

        Context:
        {context}{image_context}{history_context}

        Question: {query}

        Answer:"""
        
        logger.info("🤖 Generating response from LLM...")
        import time
        gen_start = time.time()
        
        # Use active_model from ollama client (auto-selects based on mode)
        response = self.ollama.generate(
            model=self.ollama.active_model,  # ← Use active_model instead of ollama_model
            prompt=prompt,
            options={"temperature": 0.3, "top_p": 0.9},
            stream=False
        )
        
        gen_time = time.time() - gen_start
        logger.info(f"✅ LLM response generated in {gen_time:.2f}s")
        
        # Clean markdown formatting from LLM response
        cleaned_answer = self._clean_markdown_formatting(response['response'].strip())
        
        # Calculate confidence from retrieved documents
        avg_confidence = sum(doc['score'] for doc in context_docs[:2]) / 2 if context_docs else 0
        
        # Detect if RAG response is useless (low confidence or "Maaf" message)
        is_low_confidence = avg_confidence < 0.5 or len(context_docs) == 0
        answer_is_apology = cleaned_answer.lower().startswith('maaf')
        
        # FALLBACK: If RAG tidak punya info, generate helpful general answer
        used_fallback = False
        if is_low_confidence or answer_is_apology:
            logger.info("⚠️ Low confidence RAG response detected, using fallback generation...")
            fallback_answer = self._generate_fallback_answer(query, language)
            if fallback_answer:
                cleaned_answer = fallback_answer
                used_fallback = True
                logger.info("✅ Fallback answer generated")
        
        # Build structured response
        result = {
            'answer': cleaned_answer,
            'sources': [doc['source_title'] for doc in context_docs[:2]] if not used_fallback else [],
            'confidence': avg_confidence,
            'num_sources': len(context_docs) if not used_fallback else 0,
            'has_visual_support': len(relevant_images) > 0,
            'pages': [doc.get('page') for doc in context_docs[:2] if doc.get('page')] if not used_fallback else [],
            'used_fallback': used_fallback
        }
        
        # Add image metadata if available
        if relevant_images and include_images:
            result['images'] = [img['path'] for img in relevant_images]
            result['image_scores'] = [img['score'] for img in relevant_images]
            result['num_images'] = len(relevant_images)
        else:
            result['images'] = []
            result['image_scores'] = []
            result['num_images'] = 0
        
        return result
    
    def query(self, user_query: str, top_k: int = 5, language: str = "id", conversation_history: Optional[List[Dict]] = None, user_id: Optional[str] = None) -> Dict:
        """Complete RAG pipeline: Retrieve + Generate"""
        import time
        total_start = time.time()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 Processing query: {user_query}")
        logger.info(f"{'='*60}")
        
        logger.info("🔍 Step 1/3: Retrieving relevant documents...")
        retrieve_start = time.time()
        documents = self.retrieve(user_query, top_k=top_k, conversation_history=conversation_history)
        retrieve_time = time.time() - retrieve_start
        logger.info(f"✅ Retrieved {len(documents)} documents in {retrieve_time:.2f}s")
        
        if not documents:
            logger.warning("⚠️ No documents found")
            return {
                'answer': "Maaf, informasi tidak ditemukan dalam knowledge base.",
                'sources': [],
                'confidence': 0.0,
                'num_sources': 0,
                'query_id': None
            }
        
        logger.info("🤖 Step 2/3: Generating response...")
        gen_start = time.time()
        result = self.generate(user_query, documents, language=language, conversation_history=conversation_history)
        gen_time = time.time() - gen_start
        logger.info(f"✅ Response generated in {gen_time:.2f}s")
        
        # Save RAG process to storage
        logger.info("💾 Step 3/3: Saving RAG process...")
        query_id = None
        try:
            from src.core.rag_storage import save_rag_process
            
            query_id = save_rag_process(
                query=user_query,
                retrieved_docs=documents,
                response=result.get('answer', ''),
                intent='rag',
                user_id=user_id
            )
            
            logger.info(f"✅ RAG process saved with ID: {query_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save RAG process: {e}")
        
        # Add query_id to result
        result['query_id'] = query_id
        
        total_time = time.time() - total_start
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Query completed in {total_time:.2f}s")
        logger.info(f"{'='*60}\n")
        
        return result


def ask(question: str, language: str = "id") -> str:
    """Quick helper to ask questions"""
    engine = RAGEngine()
    response = engine.query(question, language=language)
    return response['answer']


if __name__ == "__main__":
    print("RAG Engine Test\n")
    
    rag = RAGEngine()
    
    test_queries = [
        "berapa pH yang ideal untuk sistem NFT?",
        "apa kelebihan hidroponik dibanding tanah biasa?",
    ]
    
    for query in test_queries:
        print(f"Query: {query}")
        response = rag.query(query)
        print(f"Answer: {response['answer']}\n")
    
    print("✅ Test complete")
