"""
RAG Engine for Multimodal Hydroponic/Aquaponic Knowledge Base
Supports text + images + tables from PDF and web sources
"""

import os
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import ollama
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval-Augmented Generation Engine"""
    
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        cache_folder: str = None,  # Will be set to project root/models
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "aquaponics_knowledge",
        ollama_model: str = "qwen3:8b"  # Upgraded to Qwen 3 for faster generation
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
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        self.ollama_model = ollama_model
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
            ollama.list()
            logger.info("✅ Ollama connected")
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
        # Enrich query with conversation history if provided
        enriched_query = query
        if conversation_history and len(conversation_history) > 0:
            # Get last 3 messages for context
            recent_messages = conversation_history[-3:]
            context = " ".join([f"{msg.get('role', 'user')}: {msg.get('message', '')}" 
                              for msg in recent_messages])
            enriched_query = f"{context} {query}"
            logger.info(f"Enriched query with conversation history: {enriched_query[:100]}...")
        
        # Encode query
        # Use E5 query prefix for better cross-lingual retrieval
        query_embedding = self.embedder.encode(f"query: {enriched_query}", normalize_embeddings=True).tolist()
        
        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        # Format results
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
                'scored_images': self._score_image_relevance(
                    query, 
                    hit.payload.get('images', []), 
                    hit.score
                )
            }
            documents.append(doc)
        
        avg_score = sum(d['score'] for d in documents) / len(documents) if documents else 0
        logger.info(f"Retrieved {len(documents)} documents (avg score: {avg_score:.4f})")
        
        return documents
    
    def generate(self, query: str, context_docs: List[Dict], language: str = "id", include_images: bool = True, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """Generate response using LLM with retrieved context"""
        # Build text context
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc['text']}"
            for i, doc in enumerate(context_docs[:3])
        ])
        
        # Collect and filter images
        all_scored_images = []
        for doc in context_docs[:3]:
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
        
        # Build conversation history context
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            # Get last 3 messages for context
            recent_history = conversation_history[-6:]  # Last 3 exchanges (user + assistant)
            history_lines = []
            for msg in recent_history:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                history_lines.append(f"{role}: {msg.get('message', '')}")
            history_context = "\n\nPercakapan Sebelumnya:\n" + "\n".join(history_lines)
        
        if language == "id":
            system_prompt = """Anda adalah asisten ahli untuk sistem hidroponik. 
        Jawab pertanyaan dengan akurat berdasarkan dokumen yang diberikan.

        Aturan:
        1. Jawab dalam Bahasa Indonesia yang natural dan mudah dipahami
        2. Gunakan HANYA informasi dari dokumen yang diberikan
        3. Jika informasi tidak lengkap, katakan apa yang tersedia
        4. Berikan jawaban yang praktis dan actionable
        5. Jika ada diagram/gambar, sebutkan secara natural dalam penjelasan (contoh: "seperti terlihat pada diagram...")
        6. Jangan terlalu formal - gunakan bahasa yang conversational
        7. PENTING: JANGAN gunakan formatting markdown (*, **, _, dll). Tulis dalam teks biasa saja. Untuk penekanan, gunakan HURUF KAPITAL atau kata-kata seperti "penting:", "catatan:", dll.
        8. PERHATIKAN konteks percakapan sebelumnya jika ada - jawab pertanyaan follow-up dengan mempertimbangkan topik yang sedang dibahas
        """
        else:
            system_prompt = """You are an expert assistant for hydroponic systems.
        Answer questions accurately based on the provided documents.

        Rules:
        1. Answer in natural and clear English
        2. Use ONLY information from the provided documents
        3. If information is incomplete, state what is available
        4. Provide practical and actionable answers
        5. If there are diagrams/images, mention them naturally in your explanation
        6. Keep it conversational, not too formal
        7. IMPORTANT: DO NOT use markdown formatting (*, **, _, etc). Write in plain text only. For emphasis, use CAPITAL LETTERS or words like "important:", "note:", etc.
        8. PAY ATTENTION to previous conversation context if available - answer follow-up questions considering the topic being discussed
        """
                
        prompt = f"""{system_prompt}

        Context:
        {context}{image_context}{history_context}

        Question: {query}

        Answer:"""
        
        response = ollama.generate(
            model=self.ollama_model,
            prompt=prompt,
            options={"temperature": 0.3, "top_p": 0.9}
        )
        
        # Clean markdown formatting from LLM response
        cleaned_answer = self._clean_markdown_formatting(response['response'].strip())
        
        # Build structured response
        result = {
            'answer': cleaned_answer,
            'sources': [doc['source_title'] for doc in context_docs[:3]],
            'confidence': sum(doc['score'] for doc in context_docs[:3]) / 3 if context_docs else 0,
            'num_sources': len(context_docs),
            'has_visual_support': len(relevant_images) > 0,
            'pages': [doc.get('page') for doc in context_docs[:3] if doc.get('page')]
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
        logger.info(f"Processing query: {user_query}")
        
        documents = self.retrieve(user_query, top_k=top_k, conversation_history=conversation_history)
        
        if not documents:
            return {
                'answer': "Maaf, informasi tidak ditemukan dalam knowledge base.",
                'sources': [],
                'confidence': 0.0,
                'num_sources': 0,
                'query_id': None
            }
        
        result = self.generate(user_query, documents, language=language, conversation_history=conversation_history)
        
        # Save RAG process to storage
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
            
            logger.info(f"RAG process saved with ID: {query_id}")
            
        except Exception as e:
            logger.warning(f"Failed to save RAG process: {e}")
        
        # Add query_id to result
        result['query_id'] = query_id
        
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
