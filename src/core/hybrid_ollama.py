"""
Hybrid Ollama Client - Support Local dan Cloud (Ollama Cloud)
Strategy: Local-first dengan auto-fallback ke cloud
"""

import os
import logging
from typing import Optional, Dict, List, Any
import ollama
import httpx
from dotenv import load_dotenv
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridOllamaClient:
    """
    Hybrid Ollama Client dengan strategi:
    1. Primary: Local (localhost:11434) - low latency, privacy
    2. Fallback: Cloud (ollama.com) - high availability
    3. Auto-fallback: Seamless switching saat local unavailable
    """
    
    def __init__(
        self,
        mode: str = None,
        local_host: str = None,
        cloud_host: str = None,
        cloud_api_key: str = None,
        model: str = None,
        cloud_model: str = None
    ):
        self.mode = mode or os.getenv("OLLAMA_MODE", "hybrid")
        self.local_host = local_host or os.getenv("OLLAMA_LOCAL_HOST", "http://localhost:11434")
        self.cloud_host = cloud_host or os.getenv("OLLAMA_CLOUD_HOST", "https://ollama.com")
        self.cloud_api_key = cloud_api_key or os.getenv("OLLAMA_CLOUD_API_KEY")
        self.model = model or os.getenv("OLLAMA_MODEL", "ministral-3:3b")
        self.cloud_model = cloud_model or os.getenv("OLLAMA_CLOUD_MODEL", "gpt-oss:120b")
        
        self.local_client: Optional[ollama.Client] = None
        self.cloud_client: Optional[ollama.Client] = None
        self.active_client: Optional[ollama.Client] = None
        self.active_model: str = self.model
        self.is_local_available = False
        self.is_cloud_available = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize local dan cloud clients berdasarkan mode"""
        logger.info(f"🔧 Initializing Hybrid Ollama Client (mode: {self.mode})")
        
        if self.mode in ["local", "hybrid"]:
            self._init_local_client()
        
        if self.mode in ["cloud", "hybrid"]:
            self._init_cloud_client()
        
        self._set_active_client()
    
    def _init_local_client(self):
        """Initialize local Ollama client"""
        try:
            self.local_client = ollama.Client(host=self.local_host)
            self.local_client.list()
            self.is_local_available = True
            logger.info(f"✅ Local Ollama connected: {self.local_host}")
        except Exception as e:
            self.is_local_available = False
            logger.warning(f"⚠️ Local Ollama unavailable: {e}")
    
    def _init_cloud_client(self):
        """Initialize cloud Ollama client (ollama.com) dengan retry logic"""
        try:
            if not self.cloud_api_key:
                raise ValueError("Cloud API Key required for cloud mode")
            
            # Initialize dengan basic config
            self.cloud_client = ollama.Client(
                host=self.cloud_host,
                headers={'Authorization': f'Bearer {self.cloud_api_key}'}
            )
            
            # Test connection dengan retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    self.cloud_client.list()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Cloud list() attempt {attempt+1} failed: {e}, retrying...")
                        time.sleep(1)
                    else:
                        logger.warning(f"Cloud list() failed after {max_retries} attempts, but will try on first request")
            
            self.is_cloud_available = True
            logger.info(f"✅ Cloud Ollama connected: {self.cloud_host}")
        except Exception as e:
            self.is_cloud_available = False
            logger.warning(f"⚠️ Cloud Ollama unavailable: {e}")
    
    def _set_active_client(self):
        """Set active client berdasarkan availability (local-first)"""
        if self.mode == "local":
            if self.is_local_available:
                self.active_client = self.local_client
                self.active_model = self.model
                logger.info(f"🎯 Active client: LOCAL ({self.model})")
            else:
                raise ConnectionError("Local Ollama not available")
        
        elif self.mode == "cloud":
            if self.is_cloud_available:
                self.active_client = self.cloud_client
                self.active_model = self.cloud_model
                logger.info(f"🎯 Active client: CLOUD ({self.cloud_model})")
            else:
                raise ConnectionError("Cloud Ollama not available")
        
        elif self.mode == "hybrid":
            if self.is_local_available:
                self.active_client = self.local_client
                self.active_model = self.model
                logger.info(f"🎯 Active client: LOCAL (primary) - {self.model}")
            elif self.is_cloud_available:
                self.active_client = self.cloud_client
                self.active_model = self.cloud_model
                logger.info(f"🎯 Active client: CLOUD (fallback) - {self.cloud_model}")
            else:
                raise ConnectionError("No Ollama instance available")
    
    def _execute_with_fallback(self, operation: str, *args, **kwargs):
        """Execute operation dengan auto-fallback"""
        try:
            result = getattr(self.active_client, operation)(*args, **kwargs)
            return result
        
        except Exception as e:
            logger.error(f"❌ {operation} failed on active client: {e}")
            
            if self.mode == "hybrid":
                logger.info("🔄 Attempting fallback...")
                return self._fallback_execute(operation, args, kwargs)
            else:
                raise
    
    def _fallback_execute(self, operation: str, args, kwargs):
        """Execute pada backup client"""
        if self.active_client == self.local_client:
            backup_client = self.cloud_client
            backup_model = self.cloud_model
            backup_name = "cloud"
        else:
            backup_client = self.local_client
            backup_model = self.model
            backup_name = "local"
        
        if backup_client is None:
            raise ConnectionError("No backup client available")
        
        try:
            if 'model' in kwargs:
                kwargs['model'] = backup_model
            
            result = getattr(backup_client, operation)(*args, **kwargs)
            logger.info(f"✅ Fallback successful using {backup_name}")
            
            self.active_client = backup_client
            self.active_model = backup_model
            
            return result
        except Exception as e:
            logger.error(f"❌ Fallback also failed: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        model: str = None,
        options: Dict = None,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        Generate response dari Ollama
        
        Args:
            prompt: User prompt
            model: Model name (optional, uses active_model by default)
            options: Generation options (temperature, top_p, etc)
            stream: Enable streaming
            **kwargs: Additional parameters
            
        Returns:
            Response dict
        """
        model = model or self.active_model
        
        try:
            start = time.time()
            
            response = self._execute_with_fallback(
                'generate',
                model=model,
                prompt=prompt,
                options=options,
                stream=stream,
                **kwargs
            )
            
            elapsed = time.time() - start
            
            if isinstance(response, dict):
                response['generation_time'] = elapsed
                if response.get('eval_count'):
                    response['tokens_per_second'] = response['eval_count'] / elapsed
            
            logger.info(f"Generated in {elapsed:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        options: Dict = None,
        stream: bool = False,
        **kwargs
    ) -> Dict:
        """
        Chat completion (multi-turn conversation)
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            model: Model name (optional)
            options: Generation options
            stream: Enable streaming
            **kwargs: Additional parameters
            
        Returns:
            Response dict
        """
        model = model or self.active_model
        
        try:
            start = time.time()
            
            response = self._execute_with_fallback(
                'chat',
                model=model,
                messages=messages,
                options=options,
                stream=stream,
                **kwargs
            )
            
            elapsed = time.time() - start
            
            if isinstance(response, dict):
                response['generation_time'] = elapsed
            
            logger.info(f"Chat completed in {elapsed:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    def list(self) -> Dict:
        """List available models"""
        try:
            return self._execute_with_fallback('list')
        except Exception as e:
            logger.error(f"List error: {e}")
            raise
    
    def pull(self, model: str) -> Dict:
        """Pull model (only works on local)"""
        if not self.is_local_available:
            raise ConnectionError("Pull only available on local Ollama")
        
        try:
            return self.local_client.pull(model)
        except Exception as e:
            logger.error(f"Pull error: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get status dari semua clients"""
        status = {
            'mode': self.mode,
            'local': {
                'available': self.is_local_available,
                'active': self.active_client == self.local_client,
                'host': self.local_host,
                'model': self.model
            },
            'cloud': {
                'available': self.is_cloud_available,
                'active': self.active_client == self.cloud_client,
                'host': self.cloud_host,
                'model': self.cloud_model
            },
            'active_model': self.active_model
        }
        return status
    
    def reconnect_local(self):
        """Reconnect ke local Ollama"""
        logger.info("🔄 Attempting to reconnect to local Ollama...")
        self._init_local_client()
        
        if self.is_local_available:
            logger.info("✅ Local Ollama reconnected")
            self.active_client = self.local_client
            self.active_model = self.model
            logger.info(f"🎯 Switched active client to LOCAL ({self.model})")
        else:
            logger.warning("⚠️ Local Ollama still unavailable")
    
    def switch_to_cloud(self):
        """Manually switch to cloud"""
        if not self.is_cloud_available:
            raise ConnectionError("Cloud Ollama not available")
        
        self.active_client = self.cloud_client
        self.active_model = self.cloud_model
        logger.info(f"🎯 Switched to CLOUD ({self.cloud_model})")
    
    def switch_to_local(self):
        """Manually switch to local"""
        if not self.is_local_available:
            raise ConnectionError("Local Ollama not available")
        
        self.active_client = self.local_client
        self.active_model = self.model
        logger.info(f"🎯 Switched to LOCAL ({self.model})")


if __name__ == "__main__":
    print("🧪 Testing Hybrid Ollama Client\n")
    
    client = HybridOllamaClient()
    
    status = client.get_status()
    print(f"Status: {status}\n")
    
    try:
        response = client.generate("Jelaskan apa itu hidroponik dalam 1 kalimat.")
        print(f"✅ Response: {response.get('response', '')[:100]}...")
        print(f"⏱️ Time: {response.get('generation_time', 0):.2f}s")
    except Exception as e:
        print(f"❌ Error: {e}")
