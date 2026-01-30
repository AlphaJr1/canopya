"""
Hybrid Multimodal Hydroponic Chatbot
Combines RAG Engine (knowledge-based + multimodal) + Rule-Based Engine (sensor diagnostics)
Supports text, images, tables, and page references
Fokus: Sistem Hidroponik
"""

from typing import Dict, Optional, List
import re
import logging
import requests

from src.core.rag_engine import RAGEngine
from src.core.rule_engine import RuleBasedEngine, SensorReading, GrowthStage
from src.core.simulator_client import get_simulator_client
from src.services.ph_service import get_ph_service
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridChatbot:
    """
    Intelligent chatbot that routes queries to appropriate engine:
    - RAG Engine: Knowledge-based questions
    - Rule Engine: Sensor diagnostics
    - Hybrid: Both combined
    """
    
    def __init__(self):
        """Initialize both engines"""
        logger.info("Initializing Hybrid Chatbot...")
        
        self.rag_engine = RAGEngine()
        self.rule_engine = RuleBasedEngine()
        self.simulator_client = get_simulator_client()
        self.ph_service = get_ph_service()
        
        # Check simulator availability
        if self.simulator_client.check_health():
            logger.info("✅ Simulator connected")
        else:
            logger.warning("⚠️ Simulator not available (will use manual sensor input)")
        
        logger.info("✅ Hybrid Chatbot ready!")
    
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
    
    
    def _extract_sensor_data(self, message: str) -> Optional[SensorReading]:
        """Extract sensor values from user message"""
        sensor_data = SensorReading()
        
        ph_patterns = [
            r'pH\s*[:=]?\s*([0-9.]+)',          # pH: 6.0 or pH 6.0
            r'pH\s+saya\s+([0-9.]+)',            # pH saya 6.0
            r'ph\s*[:=]?\s*([0-9.]+)',          # ph: 6.0 (lowercase)
        ]
        for pattern in ph_patterns:
            ph_match = re.search(pattern, message, re.IGNORECASE)
            if ph_match:
                sensor_data.ph = float(ph_match.group(1))
                break
        
        tds_patterns = [
            r'(?:TDS|EC)\s*[:=]?\s*([0-9.]+)',      # TDS: 1000 or TDS 1000
            r'(?:TDS|EC)\s+saya\s+([0-9.]+)',       # TDS saya 1000
            r'tds\s*[:=]?\s*([0-9.]+)',             # tds: 1000 (lowercase)
        ]
        for pattern in tds_patterns:
            tds_match = re.search(pattern, message, re.IGNORECASE)
            if tds_match:
                sensor_data.tds = float(tds_match.group(1))
                break
        
        temp_patterns = [
            r'(?:suhu|temp(?:eratur)?)\s*[:=]?\s*([0-9.]+)',
            r'([0-9.]+)\s*°?C'
        ]
        for pattern in temp_patterns:
            temp_match = re.search(pattern, message, re.IGNORECASE)
            if temp_match:
                sensor_data.temperature = float(temp_match.group(1))
                break
        
        humid_match = re.search(r'(?:kelembapan|humidity|RH)\s*[:=]?\s*([0-9.]+)', message, re.IGNORECASE)
        if humid_match:
            sensor_data.humidity = float(humid_match.group(1))
        
        growth_keywords = {
            'seedling': ['seedling', 'bibit', 'biji', 'semai', 'seed'],
            'vegetative': ['vegetatif', 'vegetative', 'daun', 'leaf', 'tumbuh'],
            'fruiting': ['fruiting', 'berbuah', 'bunga', 'flower', 'buah', 'fruit']
        }
        
        detected_stage = None
        for stage, keywords in growth_keywords.items():
            if any(kw in message.lower() for kw in keywords):
                detected_stage = stage
                break
        
        if detected_stage == 'seedling':
            sensor_data.growth_stage = GrowthStage.SEEDLING
        elif detected_stage == 'fruiting':
            sensor_data.growth_stage = GrowthStage.FRUITING
        else:
            sensor_data.growth_stage = GrowthStage.VEGETATIVE
        
        if any([sensor_data.ph, sensor_data.tds, sensor_data.temperature, sensor_data.humidity]):
            return sensor_data
        
        return None
    
    def _detect_action_intent(self, message: str) -> Optional[Dict]:
        """
        Detect if user wants to perform an action (add nutrient, water, etc)
        Returns dict with action_type and confidence, or None
        """
        message_lower = message.lower()
        
        # CRITICAL: Exclude knowledge-seeking queries
        # These are NOT action requests, they're asking HOW to do something
        knowledge_excludes = [
            'cara ',  # "cara mengatasi", "cara menambah"
            'bagaimana ',  # "bagaimana mengatasi"
            'gimana ',  # "gimana mengatasi"
            'kapan ',  # "kapan harus"
            'kenapa ',  # "kenapa perlu"
            'mengapa ',  # "mengapa harus"
            'apa yang harus',  # "apa yang harus dilakukan"
        ]
        
        # If message contains knowledge-seeking words, NOT an action
        for exclude in knowledge_excludes:
            if exclude in message_lower:
                return None
        
        # Action patterns - must be EXPLICIT action requests
        action_patterns = {
            'add_nutrient': [
                r'\btambah\s+nutrisi\b',
                r'\bkasih\s+nutrisi\b',
                r'\bberi\s+nutrisi\b',
                r'\bmau\s+tambah\s+nutrisi\b',
                r'\btolong\s+tambah\s+nutrisi\b'
            ],
            'add_water': [
                r'\btambah\s+air\b',
                r'\bkasih\s+air\b',
                r'\bberi\s+air\b',
                r'\bmau\s+tambah\s+air\b',
                r'\btolong\s+tambah\s+air\b'
            ],
            'add_ph_down': [
                r'\bturunkan\s+ph\b',
                r'\bph\s+down\b',
                r'\btambah\s+asam\b',
                r'\bmau\s+turunkan\s+ph\b',
                r'\btolong\s+turunkan\s+ph\b'
            ],
            'add_ph_up': [
                r'\bnaikkan\s+ph\b',
                r'\bph\s+up\b',
                r'\btambah\s+basa\b',
                r'\bmau\s+naikkan\s+ph\b',
                r'\btolong\s+naikkan\s+ph\b'
            ]
        }
        
        for action_type, patterns in action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return {
                        'action_type': action_type,
                        'confidence': 0.8
                    }
        
        return None
    
    def _execute_simulator_action(self, action_type: str, amount: float = 1.0) -> Dict:
        """
        Execute action di simulator
        Returns dict dengan success status dan before/after values
        """
        try:
            response = requests.post(
                f"{self.simulator_client.base_url}/action",
                json={
                    'action_type': action_type,
                    'amount': amount
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'message': 'Gagal melakukan aksi'}
        
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {'success': False, 'message': str(e)}
    
    def _detect_intent(self, message: str, has_sensor_data: bool) -> tuple[str, float]:
        """
        Detect user intent with confidence scoring
        
        Args:
            message: User message
            has_sensor_data: Whether sensor data was extracted
            
        Returns:
            Tuple of (intent, confidence) where intent is "rule_based", "rag", or "hybrid"
            and confidence is 0.0-1.0
        """
        message_lower = message.lower()
        
        # PRIORITY 1: Check if it's a greeting first
        if self._is_greeting(message):
            return "greeting", 1.0
        
        # Sensor-related keywords
        sensor_keywords = [
            'ph', 'tds', 'ec', 'suhu', 'temp', 'kelembapan', 'humidity',
            'sensor', 'bacaan', 'reading', 'monitor', 'ppm'
        ]
        sensor_matches = sum(1 for kw in sensor_keywords if kw in message_lower)
        has_sensor_keywords = sensor_matches > 0
        
        # Knowledge-seeking keywords
        knowledge_keywords = [
            'cara', 'bagaimana', 'how', 'apa', 'what', 'mengapa', 'why',
            'panduan', 'guide', 'tutorial', 'jenis', 'type', 'kelebihan',
            'advantages', 'manfaat', 'sistem', 'setup', 'install', 'perbedaan',
            'jelaskan', 'explain'
        ]
        knowledge_matches = sum(1 for kw in knowledge_keywords if kw in message_lower)
        has_knowledge_keywords = knowledge_matches > 0
        
        # Action keywords (suggests wanting to fix something)
        action_keywords = ['perbaiki', 'fix', 'atasi', 'solve', 'lakukan', 'do', 'harus']
        has_action_keywords = any(kw in message_lower for kw in action_keywords)
        
        # Decision logic with confidence scoring
        if has_sensor_data:
            if has_knowledge_keywords or has_action_keywords:
                # e.g., "pH saya 4.5, bagaimana cara memperbaikinya?"
                confidence = 0.9 if (knowledge_matches >= 2 or has_action_keywords) else 0.7
                return "hybrid", confidence
            else:
                # e.g., "pH saya 4.5, apakah normal?"
                return "rule_based", 0.85
        elif has_sensor_keywords and has_knowledge_keywords:
            # e.g., "bagaimana cara mengukur pH yang benar?"
            return "rag", 0.8
        elif has_sensor_keywords:
            # e.g., "apa range pH yang ideal?" - knowledge question
            return "rag", 0.75
        elif has_knowledge_keywords:
            confidence = min(0.9, 0.6 + (knowledge_matches * 0.1))
            return "rag", confidence
        else:
            # Default to RAG for general questions (lower confidence)
            return "rag", 0.5
    
    def _should_include_images(self, query: str, rag_response: Dict) -> bool:
        """Determine if images should be included in response"""
        # Always include if RAG found relevant images
        if rag_response.get('num_images', 0) > 0:
            return True
        return False
    
    def _format_image_references(self, images: List[str], scores: List[float]) -> str:
        """Format image references for display"""
        if not images:
            return ""
        
        # Simple, non-intrusive format
        num_images = len(images)
        if num_images == 1:
            return f"\n\n📸 Ada 1 diagram yang bisa membantu visualisasi"
        else:
            return f"\n\n📸 Ada {num_images} diagram yang bisa membantu visualisasi"
    
    def _enrich_rule_response_with_rag(self, rule_response: Dict, query: str) -> str:
        """Enrich rule-based response with RAG context"""
        # Get brief RAG context for the issue
        try:
            rag_response = self.rag_engine.query(query, top_k=2, language="id")
            # Extract just the first 2 sentences for context
            rag_answer = rag_response.get('answer', '')
            sentences = rag_answer.split('. ')
            brief_context = '. '.join(sentences[:2]) + '.' if sentences else ''
            return brief_context
        except Exception as e:
            logger.warning(f"Failed to get RAG context: {e}")
            return None
    
    def _is_sensor_status_query(self, query: str) -> bool:
        """Detect if user is asking about sensor status or plant condition"""
        query_lower = query.lower()
        
        # Keywords yang menunjukkan user bertanya tentang kondisi/status
        status_keywords = [
            'kondisi', 'status', 'bagaimana', 'gimana', 'keadaan',
            'baik', 'sehat', 'normal', 'aman', 'ok', 'oke',
            'cek', 'periksa', 'lihat', 'monitor'
        ]
        
        # Keywords yang menunjukkan user bertanya tentang cara/metode
        method_keywords = [
            'cara', 'bagaimana cara', 'gimana cara', 'how to',
            'langkah', 'metode', 'teknik', 'tips'
        ]
        
        has_status_keyword = any(kw in query_lower for kw in status_keywords)
        has_method_keyword = any(kw in query_lower for kw in method_keywords)
        
        # Jika ada method keyword, prioritaskan sebagai method query (bukan status query)
        if has_method_keyword:
            return False
        
        return has_status_keyword
    
    def _is_greeting(self, message: str) -> bool:
        """Detect if message is a greeting"""
        greeting_keywords = [
            'halo', 'hai', 'hello', 'hi', 'hey', 'selamat pagi', 
            'selamat siang', 'selamat sore', 'selamat malam', 'pagi', 'siang', 'sore', 'malam'
        ]
        message_lower = message.lower().strip()
        
        # Check if message is ONLY a greeting (or very short with greeting)
        return any(message_lower == kw or message_lower.startswith(kw) for kw in greeting_keywords) and len(message.split()) <= 3
    
    def _is_rag_response_useless(self, rag_answer: str) -> bool:
        """
        Detect if RAG response is not helpful (e.g., "Dokumen tidak memberikan...")
        
        Args:
            rag_answer: RAG response text
            
        Returns:
            True if response is useless and should be skipped
        """
        if not rag_answer:
            return True
        
        answer_lower = rag_answer.lower().strip()
        
        # Patterns yang indicate RAG tidak menemukan info berguna
        useless_patterns = [
            'dokumen tidak',
            'tidak ada informasi',
            'tidak menyebutkan',
            'tidak memberikan',
            'tidak menjelaskan',
            'tidak disebutkan',
            'data yang tersedia',
            'tidak terdapat',
            'maaf, aku tidak punya info',
            'maaf, saya tidak punya info',
            'informasi tidak tersedia'
        ]
        
        # Check if response starts with useless pattern (first 100 chars)
        answer_start = answer_lower[:100]
        
        for pattern in useless_patterns:
            if pattern in answer_start:
                return True
        
        return False
    
    def _should_fetch_ph_data(self, message: str, sensor_data: Optional[SensorReading]) -> Dict[str, bool]:
        """
        LLM-based detection: Determine if pH data is needed for this query
        
        Args:
            message: User query
            sensor_data: Extracted sensor data (if any)
            
        Returns:
            Dict with:
            {
                "needs_current_ph": bool,
                "needs_prediction": bool,
                "reason": str
            }
        """
        # If user already provided pH data, don't fetch
        if sensor_data and sensor_data.ph:
            return {
                "needs_current_ph": False,
                "needs_prediction": False,
                "reason": "User provided pH data manually"
            }
        
        message_lower = message.lower()
        
        # Keywords yang SANGAT JELAS butuh pH data
        explicit_ph_keywords = [
            'ph sekarang', 'ph saat ini', 'berapa ph', 'cek ph', 'nilai ph',
            'monitoring ph', 'ph air', 'ph sistem', 'kondisi ph'
        ]
        
        # Keywords untuk prediksi
        prediction_keywords = [
            'prediksi', 'predict', 'trend', 'akan', 'nanti', 'besok',
            'ke depan', 'future', 'forecast'
        ]
        
        # Keywords umum monitoring/status - KEEP SPECIFIC, avoid false positives
        monitoring_keywords = [
            'kondisi sistem', 'status sistem', 'monitoring', 'cek sistem',
            'keadaan sistem', 'sistem saya', 'air saya bagaimana',
            'ph sekarang', 'ph saat ini', 'tds sekarang', 'suhu sekarang'
        ]
        
        # Check explicit pH query
        if any(kw in message_lower for kw in explicit_ph_keywords):
            needs_prediction = any(kw in message_lower for kw in prediction_keywords)
            return {
                "needs_current_ph": True,
                "needs_prediction": needs_prediction,
                "reason": "Explicit pH query detected"
            }
        
        # Check if asking about predictions specifically
        if any(kw in message_lower for kw in prediction_keywords):
            if 'ph' in message_lower:
                return {
                    "needs_current_ph": True,
                    "needs_prediction": True,
                    "reason": "pH prediction query detected"
                }
        
        # Check SPECIFIC monitoring query (must be explicit about system status)
        if any(kw in message_lower for kw in monitoring_keywords):
            # Ambil data untuk context
            return {
                "needs_current_ph": True,
                "needs_prediction": False,
                "reason": "Specific system monitoring query detected"
            }
        
        # Default: tidak perlu
        return {
            "needs_current_ph": False,
            "needs_prediction": False,
            "reason": "No pH data needed for this query"
        }
    
    def _format_ph_response(self, ph_data: Dict, message: str) -> str:
        """
        Format pH data menjadi response yang natural dan informatif
        Urutan: 1) Prediksi, 2) pH Realtime, 3) Tips berdasarkan pH realtime
        
        Args:
            ph_data: Data dari ph_service.get_ph_with_predictions()
            message: Original user query
            
        Returns:
            Formatted response string
        """
        current = ph_data.get('current', {})
        predictions = ph_data.get('predictions', [])
        trend = ph_data.get('trend', 'unknown')
        avg_prediction = ph_data.get('avg_prediction')
        ph_value = current.get('ph')
        
        response = ""
        
        # 1. HASIL PREDIKSI (jika ada)
        if predictions:
            response += "📈 Prediksi Trend\n"
            
            trend_label = {
                "rising": "📈 Turun perlahan",
                "falling": "📉 Turun perlahan",
                "stable": "➡️ Stabil"
            }
            response += f"• Trend: {trend_label.get(trend, 'Unknown')}\n"
            
            if avg_prediction:
                response += f"• Rata-rata prediksi: {avg_prediction:.2f}\n"
            
            response += f"• Prediksi {len(predictions)} periode ke depan:\n"
            for i, pred in enumerate(predictions[:3], 1):
                response += f"  {i}. pH {pred['ph']}\n"
            
            response += "\n"
        
        # 2. pH REALTIME
        response += "📊 Status pH Real-Time\n"
        response += f"• Nilai: {current.get('ph')}\n"
        response += f"• Waktu: {current.get('timestamp')}\n"
        
        if ph_value:
            if 5.5 <= ph_value <= 6.5:
                response += f"• Status: ✅ Optimal\n"
            elif 5.0 <= ph_value < 5.5:
                response += f"• Status: ⚠️ Agak Asam\n"
            elif 6.5 < ph_value <= 7.0:
                response += f"• Status: ⚠️ Agak Basa\n"
            elif ph_value < 5.0:
                response += f"• Status: 🚨 Terlalu Asam (Critical)\n"
            else:
                response += f"• Status: 🚨 Terlalu Basa (Critical)\n"
        
        # 3. TIPS DAN SARAN BERDASARKAN pH REALTIME
        if ph_value:
            response += "\n💡 Tips Umum Hidroponik\n"
            
            if 5.5 <= ph_value <= 6.5:
                response += "• Penjelasan: pH-mu ideal untuk hidroponik. Tanaman bisa serap nutrisi dengan maksimal!\n"
                response += "• Saran: Pertahankan pH di range ini dengan monitoring rutin setiap hari. Jika mulai naik/turun, segera sesuaikan dengan pH up/down secara bertahap.\n"
            
            elif 5.0 <= ph_value < 5.5:
                response += "• Penjelasan: pH sedikit di bawah ideal (5.5-6.5). Tanaman masih bisa tumbuh tapi penyerapan nutrisi tidak optimal.\n"
                response += "• Saran: Naikkan pH secara bertahap dengan menambahkan:\n"
                response += "  - Potassium hydroxide (KOH), atau\n"
                response += "  - Potassium carbonate (K2CO3)\n"
                response += "  Tambahkan sedikit demi sedikit, cek setiap 15-30 menit hingga mencapai 5.5-6.5.\n"
            
            elif 6.5 < ph_value <= 7.0:
                response += "• Penjelasan: pH sedikit di atas ideal (5.5-6.5). Beberapa nutrisi mikro seperti besi (Fe) jadi susah diserap tanaman.\n"
                response += "• Saran: Turunkan pH secara bertahap dengan menambahkan:\n"
                response += "  - Asam sitrat (lebih aman untuk pemula), atau\n"
                response += "  - pH down komersial\n"
                response += "  Tambahkan sedikit demi sedikit, cek setiap 15-30 menit hingga mencapai 5.5-6.5.\n"
            
            elif ph_value < 5.0:
                response += "• Penjelasan: pH terlalu rendah! Ini bisa stress tanaman susah serap nutrisi mikro (Fe, Mn, Zn). Tanaman susah serap nutrisi mikro (Fe, Mn, Zn).\n"
                response += "• Saran: SEGERA naikkan pH dengan:\n"
                response += "  1. Tambahkan potassium hydroxide atau potassium carbonate secara bertahap\n"
                response += "  2. Cek pH setiap 10-15 menit\n"
                response += "  3. Target: bawa ke range 5.5-6.5\n"
                response += "  4. Jangan terburu-buru, perubahan drastis bisa shock tanaman\n"
            
            else:
                response += "• Penjelasan: pH terlalu tinggi! Tanaman susah serap nutrisi mikro (Fe, Mn, Zn). Daun bisa menguning (klorosis).\n"
                response += "• Saran: SEGERA turunkan pH dengan:\n"
                response += "  1. Tambahkan asam nitrat atau asam fosfat secara bertahap\n"
                response += "  2. Cek pH setiap 10-15 menit\n"
                response += "  3. Target: bawa ke range 5.5-6.5\n"
                response += "  4. Jangan terburu-buru, perubahan drastis bisa shock tanaman\n"
        
        return response
    
    def _format_response(self, intent: str, rag_response: Optional[Dict], rule_response: Optional[Dict], 
                        query: str, include_images: bool = True, user_name: Optional[str] = None,
                        ph_data: Optional[Dict] = None) -> str:
        """Format final response based on intent - natural and conversational"""
        
        # Check if this is a greeting
        is_greeting = self._is_greeting(query)
        
        if intent == "rule_based" and rule_response:
            # Start with conversational diagnostic
            response = f"{rule_response['summary']}"
            
            # Add specific issues with natural formatting at the end
            issues = [d for d in rule_response['diagnostics'] 
                     if d['severity'] in ['critical', 'warning']]
            
            if issues:
                # Add warning at the end in a natural way
                for d in issues:
                    icon = "🚨" if d['severity'] == 'critical' else ""
                    param_name = d['parameter'].lower()
                    value = d['value']
                    optimal = d['optimal_range']
                    action = d['action']
                    
                    response += f" Saya lihat {param_name} kamu sedang tidak baik-baik saja {icon}, saat ini {value} dan idealnya {optimal}, maka {action.lower()}"
            
            # Try to enrich with RAG context (subtle)
            if not rule_response.get('has_rag_context'):
                rag_context = self._enrich_rule_response_with_rag(rule_response, query)
                if rag_context:
                    response += f"\n\n💡 Info Tambahan: {rag_context}"
            
            # Clean markdown formatting before returning
            return self._clean_markdown_formatting(response)
        
        elif intent == "rag" and rag_response:
            # For greetings, use special format
            if is_greeting:
                greeting = f"Halo{' ' + user_name if user_name else ''}! 👋"
                offer = "\n\nApakah kamu ingin saya bantu mengecek sesuatu atau ada pertanyaan tentang sistem hidroponik?"
                response = greeting + offer
            else:
                # Deteksi jika ini pertanyaan tentang prediksi pH
                query_lower = query.lower()
                is_ph_prediction_query = ph_data and any(kw in query_lower for kw in [
                    'prediksi', 'predict', 'trend', 'kedepan', 'ke depan', 'akan', 'nanti'
                ]) and 'ph' in query_lower
                
                # Jika pertanyaan tentang prediksi pH dan ada pH data, SKIP RAG answer
                if is_ph_prediction_query:
                    response = self._format_ph_response(ph_data, query)
                else:
                    # Check if RAG response is useless
                    rag_answer = rag_response.get('answer', '')
                    is_useless = self._is_rag_response_useless(rag_answer)
                    
                    # Jika RAG useless tapi ada pH data, HANYA tampilkan pH data (skip apology)
                    if is_useless and ph_data:
                        response = self._format_ph_response(ph_data, query)
                    # Jika RAG useless dan ga ada pH data, kasih generic response
                    elif is_useless and not ph_data:
                        response = "Maaf, saya tidak menemukan informasi spesifik untuk pertanyaan Anda. Bisa tolong lebih spesifik?"
                    # RAG response berguna, tampilkan normal
                    else:
                        response = f"{rag_answer}"
                        
                        # Add pH data if available (SEBELUM sources)
                        if ph_data:
                            response += f"\n\n{self._format_ph_response(ph_data, query)}"
                        
                        # Add image references if available (non-intrusive)
                        if include_images and rag_response.get('num_images', 0) > 0:
                            img_ref = self._format_image_references(
                                rag_response.get('images', []),
                                rag_response.get('image_scores', [])
                            )
                            response += img_ref
                        
                        # Add indicator: sources for doc-based, general tips for fallback
                        if rag_response.get('used_fallback'):
                            response += f"\n\n💡 Tips Umum Hidroponik"
                        elif rag_response.get('sources'):
                            sources = rag_response['sources'][:2]
                            response += f"\n\n📚 Sumber: {', '.join(sources)}"
            
            # Clean markdown formatting before returning
            return self._clean_markdown_formatting(response)
        
        elif intent == "hybrid" and rule_response and rag_response:
            # Smooth hybrid: answer first, then subtle warning ONLY if relevant
            response = f"{rag_response['answer']}"
            
            # Only add sensor warning if user is asking about status/condition
            is_status_query = self._is_sensor_status_query(query)
            
            if is_status_query:
                # Add critical/warning details at the end in natural way
                issues = [d for d in rule_response['diagnostics'] 
                         if d['severity'] in ['critical', 'warning']]
                
                if issues:
                    for d in issues:
                        icon = "🚨" if d['severity'] == 'critical' else ""
                        param_name = d['parameter'].lower()
                        value = d['value']
                        optimal = d['optimal_range']
                        
                        response += f" Saya lihat {param_name} kamu sedang tidak baik-baik saja {icon}, saat ini {value} dan idealnya {optimal}, maka coba kamu sesuaikan seperti yang saya jelaskan di atas."
            
            # Add images if available
            if include_images and rag_response.get('num_images', 0) > 0:
                img_ref = self._format_image_references(
                    rag_response.get('images', []),
                    rag_response.get('image_scores', [])
                )
                response += img_ref
            
            # Clean markdown formatting before returning
            return self._clean_markdown_formatting(response)
        
        else:
            return "Maaf, saya tidak dapat memproses pertanyaan Anda. Bisa tolong diulang dengan lebih spesifik?"
    
    def chat(self, message: str, language: str = "id", include_images: bool = True, 
             user_id: Optional[str] = None, onboarding_completed: bool = False, 
             conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Main chat function - processes user message and returns response
        
        Args:
            message: User message
            language: Response language ("id" or "en")
            include_images: Whether to include images in response
            user_id: User ID untuk generate dashboard URL (optional)
            onboarding_completed: Flag jika user baru selesai onboarding
            conversation_history: List of previous messages for context (optional)
            
        Returns:
            Response dict with answer, metadata, and optional images
        """
        logger.info(f"Processing message: {message}")
        
        # Get user context from database if user_id provided
        user_context = None
        if user_id:
            try:
                from src.database.base import get_db
                from src.database.operations import DatabaseOperations
                
                db = next(get_db())
                db_ops = DatabaseOperations(db)
                
                # Get user and plants
                user = db_ops.get_or_create_user(user_id)
                plants = db_ops.get_active_plants(user_id)
                
                user_context = {
                    'name': user.name,
                    'plants': [
                        {
                            'name': p.plant_name,
                            'type': p.plant_type,
                            'stage': p.growth_stage
                        }
                        for p in plants
                    ]
                }
                
                logger.info(f"User context loaded: {user_context}")
                
            except Exception as e:
                logger.warning(f"Failed to load user context: {e}")
                user_context = None
        
        # Check for action intent first
        action_intent = self._detect_action_intent(message)
        if action_intent:
            logger.info(f"Action detected: {action_intent['action_type']}")
            
            # Execute action
            action_result = self._execute_simulator_action(action_intent['action_type'])
            
            if action_result.get('success'):
                before = action_result['before']
                after = action_result['after']
                improved = action_result.get('improved', False)
                
                action_labels = {
                    'add_nutrient': 'Menambah Nutrisi',
                    'add_water': 'Menambah Air',
                    'add_ph_down': 'Menambah pH Down',
                    'add_ph_up': 'Menambah pH Up'
                }
                action_label = action_labels.get(action_intent['action_type'], action_intent['action_type'])
                
                answer = f"✅ {action_label} Berhasil!\n\n"
                answer += f"Sebelum:\n"
                answer += f"• pH: {before['ph']}\n"
                answer += f"• TDS: {before['tds']} ppm\n"
                answer += f"• Status: {before['status'].upper()}\n\n"
                answer += f"Sesudah:\n"
                answer += f"• pH: {after['ph']}\n"
                answer += f"• TDS: {after['tds']} ppm\n"
                answer += f"• Status: {after['status'].upper()}\n"
                
                if improved:
                    answer += "\n🎉 Kondisi tanaman membaik!"
                
                return {
                    'answer': answer,
                    'intent': 'action',
                    'action_type': action_intent['action_type'],
                    'action_result': action_result,
                    'confidence': action_intent['confidence'],
                    'has_sensor_data': True,
                    'sensor_data': after
                }
            else:
                return {
                    'answer': f"❌ Gagal melakukan aksi: {action_result.get('message', 'Unknown error')}",
                    'intent': 'action',
                    'confidence': 0.5,
                    'has_sensor_data': False
                }
        
        # Get sensor data from simulator if not in message
        sensor_data = self._extract_sensor_data(message)
        if not sensor_data:
            # Try to get from simulator
            simulator_data = self.simulator_client.get_current_sensor_data()
            if simulator_data:
                sensor_data = SensorReading(
                    ph=simulator_data.get('ph'),
                    tds=simulator_data.get('tds'),
                    temperature=simulator_data.get('temperature')
                )
                logger.info("Using sensor data from simulator")
        
        # Detect intent with confidence
        intent, confidence = self._detect_intent(message, has_sensor_data=sensor_data is not None)
        logger.info(f"Detected intent: {intent} (confidence: {confidence:.2f})")
        
        # AUTO-FETCH pH DATA jika diperlukan (LLM-based detection)
        ph_data = None
        should_fetch = self._should_fetch_ph_data(message, sensor_data)
        
        if should_fetch['needs_current_ph']:
            logger.info(f"🌡️ Fetching pH data: {should_fetch['reason']}")
            try:
                if should_fetch['needs_prediction']:
                    ph_data = self.ph_service.get_ph_with_predictions(prediction_limit=3)
                else:
                    current_ph = self.ph_service.get_current_ph()
                    ph_data = {
                        'current': current_ph,
                        'predictions': [],
                        'trend': 'unknown'
                    }
                logger.info(f"✅ pH data fetched: current={ph_data['current']['ph']}")
                
                # Jika tidak ada sensor_data manual, gunakan pH dari API untuk sensor_data
                if not sensor_data:
                    sensor_data = SensorReading(ph=ph_data['current']['ph'])
            except Exception as e:
                logger.error(f"❌ Failed to fetch pH data: {e}")
                ph_data = None
        
        # Process based on intent
        rag_response = None
        rule_response = None
        rag_context_for_rule = None
        
        # GREETING: Skip RAG entirely
        if intent == "greeting":
            logger.info("Greeting detected - skipping RAG process")
            user_name = user_context.get('name') if user_context else None
            greeting = f"Halo{' ' + user_name if user_name else ''}! 👋"
            offer = "\n\nApakah kamu ingin saya bantu mengecek sesuatu atau ada pertanyaan tentang sistem hidroponik?"
            
            return {
                'answer': greeting + offer,
                'intent': intent,
                'confidence': 1.0,
                'has_sensor_data': False,
                'metadata': {
                    'intent': intent,
                    'confidence': 1.0,
                    'rag_used': False,
                    'rule_based_used': False
                }
            }
        
        if intent in ["rag", "hybrid"]:
            # Enrich message dengan user context untuk RAG
            enriched_message = message
            if user_context and user_context.get('plants'):
                plant_info = user_context['plants'][0]
                context_prefix = f"[Context: User {user_context.get('name', 'ini')} menanam {plant_info['name']} ({plant_info['type']}) di tahap {plant_info['stage']}] "
                enriched_message = context_prefix + message
                logger.info(f"Enriched message with user context: {enriched_message[:100]}...")
            
            rag_response = self.rag_engine.query(enriched_message, language=language, conversation_history=conversation_history, user_id=user_id)
            
            # Extract brief context for rule engine if hybrid
            if intent == "hybrid" and rag_response:
                sentences = rag_response.get('answer', '').split('. ')
                rag_context_for_rule = '. '.join(sentences[:2]) + '.' if sentences else None
        
        if intent in ["rule_based", "hybrid"]:
            if sensor_data:
                rule_response = self.rule_engine.diagnose_all(sensor_data, rag_context=rag_context_for_rule)
        
        # Format final response with user name
        user_name = user_context.get('name') if user_context else None
        answer = self._format_response(intent, rag_response, rule_response, message, include_images, user_name, ph_data)
        
        # Add RAG dashboard link if RAG was used AND response includes RAG content
        # Skip if response is pH-only (starts with 📊)
        rag_dashboard_url = None
        if intent in ['rag', 'hybrid'] and rag_response and rag_response.get('query_id'):
            # Skip dashboard link jika response hanya pH data (no RAG content used)
            if not answer.startswith('📊'):
                query_id = rag_response['query_id']
            
                # Get dashboard base URL from environment or file
                dashboard_base_url = os.getenv('RAG_DASHBOARD_URL')
            
                # If not in env, try to read from .ports.info file
                if not dashboard_base_url:
                    try:
                        from pathlib import Path
                        ports_file = Path(__file__).parent.parent.parent / '.ports.info'
                        if ports_file.exists():
                            with open(ports_file, 'r') as f:
                                for line in f:
                                    if line.startswith('RAG_DASHBOARD_URL='):
                                        dashboard_base_url = line.split('=', 1)[1].strip()
                                        break
                    except Exception as e:
                        logger.warning(f"Failed to read RAG_DASHBOARD_URL from .ports.info: {e}")
            
                # Fallback to production URL
                if not dashboard_base_url:
                    dashboard_base_url = 'https://rag.canopya.cloud'
                
                rag_dashboard_url = f"{dashboard_base_url}/?query_id={query_id}"
                
                # Append RAG dashboard link to answer
                answer += f"\n\nLihat detail RAG process: {rag_dashboard_url}"
                
                logger.info(f"RAG dashboard link added: {rag_dashboard_url}")
        
        # Return comprehensive response
        result = {
            'answer': answer,
            'intent': intent,
            'confidence': confidence,
            'has_sensor_data': sensor_data is not None,
            'sensor_data': sensor_data,
            'rag_dashboard_url': rag_dashboard_url,
        }
        
        # Add RAG metadata if available
        if rag_response:
            result['rag_confidence'] = rag_response.get('confidence', 0)
            result['sources'] = rag_response.get('sources', [])
            result['images'] = rag_response.get('images', []) if include_images else []
            result['image_scores'] = rag_response.get('image_scores', []) if include_images else []
            result['num_images'] = rag_response.get('num_images', 0) if include_images else 0
            result['pages'] = rag_response.get('pages', [])
            result['has_visual_support'] = rag_response.get('has_visual_support', False)
        
        return result


# Helper function for quick testing
def ask(message: str) -> str:
    """
    Quick helper to ask chatbot
    
    Usage:
        from src.core.hybrid_chatbot import ask
        response = ask("pH saya 4.5, bagaimana?")
        print(response)
    """
    bot = HybridChatbot()
    result = bot.chat(message)
    return result['answer']


if __name__ == "__main__":
    """Test hybrid chatbot"""
    
    print("Hybrid Chatbot Test\n")
    
    bot = HybridChatbot()
    
    test_messages = [
        "pH saya 4.2, TDS 1500, suhu 28°C",
        "apa kelebihan hidroponik dibanding tanah biasa?",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        response = bot.chat(message)
        print(f"Intent: {response['intent']}")
        print(f"Response: {response['answer'][:100]}...\n")
    
    print("✅ Test complete")

