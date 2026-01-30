"""
Hybrid Qdrant Client - Support Local (Docker) dan Cloud (Qdrant Cloud)
Strategy: Local-first dengan auto-fallback ke cloud + bi-directional sync
"""

import os
import logging
from typing import Optional, List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridQdrantClient:
    """
    Hybrid Qdrant Client dengan strategi:
    1. Primary: Local (Docker) - low latency
    2. Fallback: Cloud (Qdrant Cloud) - high availability
    3. Auto-sync: Bi-directional synchronization
    """
    
    def __init__(
        self,
        mode: str = None,
        local_host: str = None,
        local_port: int = None,
        cloud_url: str = None,
        cloud_api_key: str = None,
        collection_name: str = None,
        auto_sync: bool = True
    ):
        self.mode = mode or os.getenv("QDRANT_MODE", "hybrid")
        self.local_host = local_host or os.getenv("QDRANT_LOCAL_HOST", "localhost")
        self.local_port = int(local_port or os.getenv("QDRANT_LOCAL_PORT", 6333))
        self.cloud_url = cloud_url or os.getenv("QDRANT_CLOUD_URL")
        self.cloud_api_key = cloud_api_key or os.getenv("QDRANT_CLOUD_API_KEY")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION_NAME", "aquaponics_knowledge")
        self.auto_sync = auto_sync
        
        self.local_client: Optional[QdrantClient] = None
        self.cloud_client: Optional[QdrantClient] = None
        self.active_client: Optional[QdrantClient] = None
        self.is_local_available = False
        self.is_cloud_available = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize local dan cloud clients berdasarkan mode"""
        logger.info(f"🔧 Initializing Hybrid Qdrant Client (mode: {self.mode})")
        
        if self.mode in ["local", "hybrid"]:
            self._init_local_client()
        
        if self.mode in ["cloud", "hybrid"]:
            self._init_cloud_client()
        
        self._set_active_client()
        
        if self.mode == "hybrid" and self.auto_sync:
            self._initial_sync()
    
    def _init_local_client(self):
        """Initialize local Qdrant client (Docker)"""
        try:
            self.local_client = QdrantClient(
                host=self.local_host,
                port=self.local_port,
                timeout=5
            )
            self.local_client.get_collections()
            self.is_local_available = True
            logger.info(f"✅ Local Qdrant connected: {self.local_host}:{self.local_port}")
        except Exception as e:
            self.is_local_available = False
            logger.warning(f"⚠️ Local Qdrant unavailable: {e}")
    
    def _init_cloud_client(self):
        """Initialize cloud Qdrant client (Qdrant Cloud)"""
        try:
            if not self.cloud_url or not self.cloud_api_key:
                raise ValueError("Cloud URL and API Key required for cloud mode")
            
            self.cloud_client = QdrantClient(
                url=self.cloud_url,
                api_key=self.cloud_api_key,
                timeout=60  # Increased for slow network
            )
            self.cloud_client.get_collections()
            self.is_cloud_available = True
            logger.info(f"✅ Cloud Qdrant connected: {self.cloud_url[:50]}...")
        except Exception as e:
            self.is_cloud_available = False
            logger.warning(f"⚠️ Cloud Qdrant unavailable: {e}")
    
    def _set_active_client(self):
        """Set active client berdasarkan availability (local-first)"""
        if self.mode == "local":
            if self.is_local_available:
                self.active_client = self.local_client
                logger.info("🎯 Active client: LOCAL")
            else:
                raise ConnectionError("Local Qdrant not available")
        
        elif self.mode == "cloud":
            if self.is_cloud_available:
                self.active_client = self.cloud_client
                logger.info("🎯 Active client: CLOUD")
            else:
                raise ConnectionError("Cloud Qdrant not available")
        
        elif self.mode == "hybrid":
            if self.is_local_available:
                self.active_client = self.local_client
                logger.info("🎯 Active client: LOCAL (primary)")
            elif self.is_cloud_available:
                self.active_client = self.cloud_client
                logger.info("🎯 Active client: CLOUD (fallback)")
            else:
                raise ConnectionError("No Qdrant instance available")
    
    def _initial_sync(self):
        """Initial sync saat startup (cloud → local jika local kosong)"""
        if not (self.is_local_available and self.is_cloud_available):
            logger.info("⏭️ Skipping initial sync (not all clients available)")
            return
        
        try:
            local_count = self._safe_count(self.local_client)
            cloud_count = self._safe_count(self.cloud_client)
            
            logger.info(f"📊 Vector count - Local: {local_count}, Cloud: {cloud_count}")
            
            if local_count == 0 and cloud_count > 0:
                logger.info("🔄 Syncing from cloud to local...")
                self.sync_cloud_to_local()
            elif cloud_count == 0 and local_count > 0:
                logger.info("🔄 Syncing from local to cloud...")
                self.sync_local_to_cloud()
            else:
                logger.info("✅ Both instances have data, no initial sync needed")
        
        except Exception as e:
            logger.error(f"❌ Initial sync failed: {e}")
    
    def _safe_count(self, client: QdrantClient) -> int:
        """Safe count dengan error handling"""
        try:
            result = client.count(collection_name=self.collection_name)
            return result.count
        except Exception:
            return 0
    
    def _execute_with_fallback(self, operation: str, *args, **kwargs):
        """Execute operation dengan auto-fallback"""
        try:
            result = getattr(self.active_client, operation)(*args, **kwargs)
            
            if self.mode == "hybrid" and self.auto_sync:
                self._async_sync_to_backup(operation, args, kwargs)
            
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
        backup_client = self.cloud_client if self.active_client == self.local_client else self.local_client
        
        if backup_client is None:
            raise ConnectionError("No backup client available")
        
        try:
            result = getattr(backup_client, operation)(*args, **kwargs)
            logger.info(f"✅ Fallback successful using {'cloud' if backup_client == self.cloud_client else 'local'}")
            
            self.active_client = backup_client
            
            return result
        except Exception as e:
            logger.error(f"❌ Fallback also failed: {e}")
            raise
    
    def _async_sync_to_backup(self, operation: str, args, kwargs):
        """Async sync ke backup client (non-blocking)"""
        import threading
        
        def sync_task():
            try:
                backup_client = self.cloud_client if self.active_client == self.local_client else self.local_client
                if backup_client:
                    getattr(backup_client, operation)(*args, **kwargs)
                    logger.debug(f"🔄 Synced {operation} to backup")
            except Exception as e:
                logger.debug(f"⚠️ Backup sync failed: {e}")
        
        thread = threading.Thread(target=sync_task, daemon=True)
        thread.start()
    
    def sync_local_to_cloud(self):
        """Manual sync: local → cloud"""
        if not (self.is_local_available and self.is_cloud_available):
            logger.warning("⚠️ Cannot sync: both clients must be available")
            return
        
        try:
            logger.info("🔄 Starting local → cloud sync...")
            
            local_points = self.local_client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=True
            )[0]
            
            if local_points:
                self.cloud_client.upsert(
                    collection_name=self.collection_name,
                    points=local_points
                )
                logger.info(f"✅ Synced {len(local_points)} points to cloud")
            else:
                logger.info("ℹ️ No points to sync")
        
        except Exception as e:
            logger.error(f"❌ Local → Cloud sync failed: {e}")

    
    def sync_cloud_to_local(self):
        """Manual sync: cloud → local"""
        if not (self.is_local_available and self.is_cloud_available):
            logger.warning("⚠️ Cannot sync: both clients must be available")
            return
        
        try:
            logger.info("🔄 Starting cloud → local sync...")
            
            cloud_points = self.cloud_client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=True
            )[0]
            
            if cloud_points:
                self.local_client.upsert(
                    collection_name=self.collection_name,
                    points=cloud_points
                )
                logger.info(f"✅ Synced {len(cloud_points)} points to local")
            else:
                logger.info("ℹ️ No points to sync")
        
        except Exception as e:
            logger.error(f"❌ Cloud → Local sync failed: {e}")
    
    
    def search(self, collection_name: str, query_vector, limit: int = 5, **kwargs):
        """Search - wrapper untuk backward compatibility"""
        from qdrant_client.models import QueryRequest
        
        # Use query_points for newer Qdrant client
        return self.active_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            **kwargs
        ).points
    
    def upsert(self, *args, **kwargs):
        """Upsert - direct pass-through"""
        return self.active_client.upsert(*args, **kwargs)
    
    def count(self, *args, **kwargs):
        """Count - direct pass-through"""
        return self.active_client.count(*args, **kwargs)
    
    def get_collections(self):
        """Get collections - direct pass-through"""
        return self.active_client.get_collections()

    
    def create_collection(self, *args, **kwargs):
        """Create collection di semua available clients"""
        results = {}
        
        if self.is_local_available:
            try:
                self.local_client.create_collection(*args, **kwargs)
                results['local'] = 'success'
                logger.info("✅ Collection created in local")
            except Exception as e:
                results['local'] = f'failed: {e}'
                logger.error(f"❌ Local collection creation failed: {e}")
        
        if self.is_cloud_available:
            try:
                self.cloud_client.create_collection(*args, **kwargs)
                results['cloud'] = 'success'
                logger.info("✅ Collection created in cloud")
            except Exception as e:
                results['cloud'] = f'failed: {e}'
                logger.error(f"❌ Cloud collection creation failed: {e}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get status dari semua clients"""
        status = {
            'mode': self.mode,
            'local': {
                'available': self.is_local_available,
                'active': self.active_client == self.local_client,
                'count': self._safe_count(self.local_client) if self.is_local_available else 0
            },
            'cloud': {
                'available': self.is_cloud_available,
                'active': self.active_client == self.cloud_client,
                'count': self._safe_count(self.cloud_client) if self.is_cloud_available else 0
            }
        }
        return status
    
    def reconnect_local(self):
        """Reconnect ke local Qdrant dan sync dari cloud jika perlu"""
        logger.info("🔄 Attempting to reconnect to local Qdrant...")
        self._init_local_client()
        
        if self.is_local_available:
            logger.info("✅ Local Qdrant reconnected")
            
            if self.mode == "hybrid" and self.is_cloud_available:
                local_count = self._safe_count(self.local_client)
                cloud_count = self._safe_count(self.cloud_client)
                
                if cloud_count > local_count:
                    logger.info("🔄 Syncing from cloud to local after reconnect...")
                    self.sync_cloud_to_local()
            
            self.active_client = self.local_client
            logger.info("🎯 Switched active client to LOCAL")
        else:
            logger.warning("⚠️ Local Qdrant still unavailable")


if __name__ == "__main__":
    print("🧪 Testing Hybrid Qdrant Client\n")
    
    client = HybridQdrantClient()
    
    status = client.get_status()
    print(f"Status: {status}\n")
    
    try:
        count = client.count(collection_name=client.collection_name)
        print(f"✅ Vector count: {count.count}")
    except Exception as e:
        print(f"❌ Error: {e}")
