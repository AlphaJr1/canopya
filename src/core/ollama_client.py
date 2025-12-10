"""
Ollama Client Wrapper dengan Full Hyperparameter Control
Untuk fine-tuning generation quality RAG system

"""

from typing import Optional, Dict, List
import ollama
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaConfig:
    
    def __init__(
        self,
        # Model selection
        model: str = "qwen3:8b",  # Upgraded to Qwen 3 (57% faster!)
        
        # Core generation parameters
        temperature: float = 0.3,        # 0.0-1.0: Creativity (lower = more focused)
        top_p: float = 0.9,              # 0.0-1.0: Nucleus sampling
        top_k: int = 40,                 # Top-k sampling
        
        # Repetition control
        repeat_penalty: float = 1.1,     # 1.0+ : Penalize repetition
        repeat_last_n: int = 64,         # Look back N tokens for repetition
        
        # Length control
        num_predict: int = 512,          # Max tokens to generate
        
        # Context
        num_ctx: int = 2048,             # Context window size
        
        # Stop sequences
        stop: Optional[List[str]] = None,
        
        # Misc
        seed: Optional[int] = None,      # For reproducibility
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repeat_penalty = repeat_penalty
        self.repeat_last_n = repeat_last_n
        self.num_predict = num_predict
        self.num_ctx = num_ctx
        self.stop = stop or []
        self.seed = seed
    
    def to_dict(self) -> Dict:
        options = {
            'temperature': self.temperature,
            'top_p': self.top_p,
            'top_k': self.top_k,
            'repeat_penalty': self.repeat_penalty,
            'repeat_last_n': self.repeat_last_n,
            'num_predict': self.num_predict,
            'num_ctx': self.num_ctx,
        }
        
        if self.seed is not None:
            options['seed'] = self.seed
        
        return options
    
    def __repr__(self):
        return f"OllamaConfig(model={self.model}, temp={self.temperature}, top_p={self.top_p})"

class OllamaClient:
    """
    Wrapper untuk Ollama dengan hyperparameter control
    
    Usage:
        # Default config
        client = OllamaClient()
        
        # Custom config
        config = OllamaConfig(temperature=0.5, top_p=0.95)
        client = OllamaClient(config)
        
        # Generate
        response = client.generate("Your prompt here")
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        self.config = config or OllamaConfig()
        self._verify_connection()
        logger.info(f"✅ Ollama client initialized: {self.config}")
    
    def _verify_connection(self):
        """Verify Ollama connection"""
        try:
            ollama.list()
            logger.info("✅ Ollama connection verified")
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            raise ConnectionError("Ollama is not running. Start with: ollama serve")
    
    def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        override_config: Optional[Dict] = None,
        stream: bool = False
    ) -> Dict:
        """
        Generate response from Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            override_config: Temporary config overrides
            stream: Enable streaming (for future)
            
        Returns:
            Dict with 'response', 'tokens', 'duration', etc.
        """
        # Build full prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Get options
        options = self.config.to_dict()
        if override_config:
            options.update(override_config)
        
        # Add stop sequences
        if self.config.stop:
            options['stop'] = self.config.stop
        
        # Generate
        start = time.time()
        
        try:
            ollama_response = ollama.generate(
                model=self.config.model,
                prompt=full_prompt,
                options=options,
                stream=stream
            )
            
            elapsed = time.time() - start
            
            # Convert to dict and add timing info
            response = {
                'response': ollama_response['response'],
                'model': ollama_response.get('model', self.config.model),
                'created_at': ollama_response.get('created_at'),
                'done': ollama_response.get('done', True),
                'total_duration': ollama_response.get('total_duration'),
                'load_duration': ollama_response.get('load_duration'),
                'prompt_eval_count': ollama_response.get('prompt_eval_count'),
                'prompt_eval_duration': ollama_response.get('prompt_eval_duration'),
                'eval_count': ollama_response.get('eval_count'),
                'eval_duration': ollama_response.get('eval_duration'),
                'generation_time': elapsed,
                'tokens_per_second': ollama_response.get('eval_count', 0) / elapsed if elapsed > 0 else 0
            }
            
            logger.info(f"Generated in {elapsed:.2f}s ({response['tokens_per_second']:.1f} tok/s)")
            
            return response
            
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        override_config: Optional[Dict] = None
    ) -> Dict:
        """
        Chat completion (multi-turn conversation)
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            override_config: Temporary config overrides
            
        Returns:
            Response dict
        """
        options = self.config.to_dict()
        if override_config:
            options.update(override_config)
        
        try:
            response = ollama.chat(
                model=self.config.model,
                messages=messages,
                options=options
            )
            return response
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    def update_config(self, **kwargs):
        """Update configuration parameters dynamically"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")

# Preset configurations untuk different use cases
class OllamaPresets:
    
    @staticmethod
    def factual() -> OllamaConfig:
        return OllamaConfig(
            temperature=0.1,
            top_p=0.9,
            top_k=20,
            repeat_penalty=1.2
        )
    
    @staticmethod
    def balanced() -> OllamaConfig:
        return OllamaConfig(
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1
        )
    
    @staticmethod
    def creative() -> OllamaConfig:
        return OllamaConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=80,
            repeat_penalty=1.05
        )
    
    @staticmethod
    def precise() -> OllamaConfig:
        return OllamaConfig(
            temperature=0.0,
            top_p=0.85,
            top_k=10,
            repeat_penalty=1.3
        )

# TESTING & EXAMPLES

def test_different_configs():
    """Test different Ollama configurations"""
    prompt = "Jelaskan apa itu hidroponik NFT dalam 2 kalimat."
    
    configs = {
        "Factual (RAG)": OllamaPresets.factual(),
        "Balanced": OllamaPresets.balanced(),
        "Creative": OllamaPresets.creative(),
        "Precise": OllamaPresets.precise(),
    }
    
    print("="*80)
    print("🧪 Testing Different Ollama Configurations")
    print("="*80)
    print(f"\nPrompt: {prompt}\n")
    
    for name, config in configs.items():
        print(f"\n{'='*80}")
        print(f"Config: {name}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Top-P: {config.top_p}")
        print(f"  Top-K: {config.top_k}")
        print(f"{'='*80}")
        
        client = OllamaClient(config)
        response = client.generate(prompt)
        
        print(f"\nResponse:")
        print(response['response'])
        print(f"\nTokens: {response.get('eval_count', 0)}")
        print(f"Speed: {response['tokens_per_second']:.1f} tok/s")

def test_rag_configuration():
    """Test RAG-optimized configuration"""
    print("\n" + "="*80)
    print("🔍 Testing RAG-Optimized Configuration")
    print("="*80)
    
    config = OllamaPresets.factual()
    client = OllamaClient(config)
    
    system_prompt = "Jawab berdasarkan informasi yang diberikan saja."
    context = """
    NFT (Nutrient Film Technique) adalah sistem hidroponik di mana 
    larutan nutrisi mengalir dalam lapisan tipis melalui saluran miring.
    Akar tanaman menyentuh aliran nutrisi tipis ini.
    """
    prompt = f"Context: {context}\n\nQuestion: Apa itu NFT?"
    
    response = client.generate(prompt, system_prompt=system_prompt)
    
    print(f"\nResponse:")
    print(response['response'])
    print(f"\nPerformance:")
    print(f"  Time: {response['generation_time']:.2f}s")
    print(f"  Speed: {response['tokens_per_second']:.1f} tok/s")
    print(f"  Tokens: {response.get('eval_count', 0)}")

if __name__ == "__main__":
    print("🚀 Ollama Client Wrapper Test\n")
    
    # Test 1: Different configs
    test_different_configs()
    
    # Test 2: RAG-optimized
    test_rag_configuration()
    
    print("\n" + "="*80)
    print("✅ All tests complete!")
    print("="*80)
