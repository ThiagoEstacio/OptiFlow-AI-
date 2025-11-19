"""
AI Response Cache - Fast cache for similar queries
Reduces response time from ~8s to <100ms for repeated queries
"""

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AIResponseCache:
    """
    In-memory cache for AI responses.
    Cache TTL: 5 minutes (queries change frequently in industrial context)
    Max size: 100 entries (LRU eviction)
    """

    def __init__(self, ttl_minutes: int = 5, max_size: int = 100):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def _generate_key(self, message: str, available_tags: Optional[list] = None) -> str:
        """
        Generate cache key from query.
        Normalizes: lowercase, strip whitespace, remove punctuation
        """
        # Normalize message
        normalized = message.lower().strip()
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())  # Remove extra spaces

        # Include tag context if provided (first 5 tags only)
        context = ""
        if available_tags:
            tag_ids = sorted([t.get('id', '')[:8] for t in available_tags[:5]])
            context = '_'.join(tag_ids)

        # Generate hash
        cache_str = f"{normalized}_{context}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def get(self, message: str, available_tags: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """Get cached response if exists and not expired"""
        key = self._generate_key(message, available_tags)

        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check if expired
        if datetime.now() > entry['expires_at']:
            del self._cache[key]
            self._misses += 1
            logger.info(f"🗑️ Cache expired for key: {key[:8]}...")
            return None

        self._hits += 1
        hit_rate = (self._hits / (self._hits + self._misses)) * 100
        logger.info(f"✅ Cache HIT! Key: {key[:8]}... (hit rate: {hit_rate:.1f}%)")
        return entry['response']

    def set(self, message: str, response: Dict[str, Any], available_tags: Optional[list] = None):
        """Cache a response"""
        key = self._generate_key(message, available_tags)

        # LRU eviction if cache full
        if len(self._cache) >= self._max_size:
            # Remove oldest entry
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]['cached_at'])
            del self._cache[oldest_key]
            logger.info(f"🗑️ Cache eviction (LRU): {oldest_key[:8]}...")

        self._cache[key] = {
            'response': response,
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + self._ttl
        }

        logger.info(f"💾 Cached response for key: {key[:8]}... (size: {len(self._cache)}/{self._max_size})")

    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("🗑️ Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self._cache),
            "max_size": self._max_size
        }


# Global cache instance
_ai_cache = AIResponseCache(ttl_minutes=5, max_size=100)


def get_ai_cache() -> AIResponseCache:
    """Get global AI cache instance"""
    return _ai_cache


# Pre-defined common queries and responses for warm cache
COMMON_QUERIES = [
    {
        "query": "Olá",
        "response": {
            "response": "## 👋 Bem-vindo ao OptiFlow AI Assistant\n\nSou seu **Analista PCM/PCO** especializado. Como posso ajudá-lo hoje?",
            "widgets": None,
            "suggestions": ["Listar tags disponíveis", "Mostrar alarmes ativos", "Análise de temperatura"]
        }
    },
    {
        "query": "Ajuda",
        "response": {
            "response": "## 🔧 Como posso ajudar\n\n**Análises disponíveis:**\n- Listar tags e sensores\n- Alarmes ativos\n- Estatísticas (média, máx, mín)\n- Tendências e anomalias\n- Cálculo de OEE\n\nExemplo: \"Liste as tags de temperatura\"",
            "widgets": None,
            "suggestions": ["Listar todas as tags", "Mostrar alarmes críticos", "Calcular OEE"]
        }
    },
    {
        "query": "Quais são as principais tags?",
        "response": {
            "response": "## 📊 Tags Principais\n\nPara listar as tags, use: **get_all_tags(limit=20)**\n\nCategorias comuns:\n- 🌡️ Temperatura\n- 📈 Pressão  \n- ⚡ Potência\n- 🔄 Velocidade",
            "widgets": None,
            "suggestions": None
        }
    },
]


async def warm_cache_with_common_queries():
    """
    Pre-populate cache with common queries on startup.
    Reduces initial latency for frequent queries.
    """
    cache = get_ai_cache()

    logger.info("🔥 Warming AI cache with common queries...")

    for item in COMMON_QUERIES:
        try:
            cache.set(
                message=item["query"],
                response=item["response"],
                available_tags=None
            )
            logger.info(f"✅ Pre-cached: '{item['query']}'")
        except Exception as e:
            logger.error(f"❌ Failed to pre-cache '{item['query']}': {e}")

    logger.info(f"🔥 Cache warmed with {len(COMMON_QUERIES)} common queries")
