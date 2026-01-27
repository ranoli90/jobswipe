"""
Redis Caching Service for Job Embeddings

Provides caching layer for job embeddings to reduce compute costs and latency.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    Async Redis-based cache for job embeddings.

    Features:
    - Stores computed embeddings with TTL
    - Supports batch operations
    - Provides cache hit/miss metrics
    """

    # TTL for cached embeddings (7 days)
    DEFAULT_TTL = 7 * 24 * 60 * 60  # 7 days in seconds

    # Key prefixes
    EMBEDDING_PREFIX = "embedding:"
    JOB_EMBEDDINGS_PREFIX = "job_embeddings:"
    POPULAR_JOBS_PREFIX = "popular_jobs:"

    def __init__(
        self,
        redis_url: str = None,
        max_connections: int = 20,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
    ):
        """
        Initialize embedding cache.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Connection timeout in seconds
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self._pool = None
        self._client = None

        # Metrics
        self.hits = 0
        self.misses = 0

    async def connect(self) -> None:
        """Establish connection to Redis"""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_connect_timeout,
                    decode_responses=True,
                )
                # Test connection
                await self._client.ping()
                logger.info("Connected to Redis embedding cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._client = None

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis embedding cache")

    async def _ensure_connection(self) -> bool:
        """Ensure Redis connection is active"""
        if self._client is None:
            await self.connect()
        return self._client is not None

    def _generate_embedding_key(self, text: str) -> str:
        """Generate cache key for embedding"""
        # Normalize text for consistent hashing
        normalized = text.lower().strip()
        hash_value = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"{self.EMBEDDING_PREFIX}{hash_value}"

    def _generate_job_embeddings_key(self, job_id: str) -> str:
        """Generate cache key for job embeddings"""
        return f"{self.JOB_EMBEDDINGS_PREFIX}{job_id}"

    def _generate_popular_jobs_key(self, category: str = "all") -> str:
        """Generate cache key for popular jobs list"""
        return f"{self.POPULAR_JOBS_PREFIX}{category}"

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding for text.

        Args:
            text: Original text to get embedding for

        Returns:
            Cached embedding vector or None if not found
        """
        if not await self._ensure_connection():
            return None

        key = self._generate_embedding_key(text)

        try:
            cached = await self._client.get(key)
            if cached:
                self.hits += 1
                return json.loads(cached)
            else:
                self.misses += 1
                return None
        except Exception as e:
            logger.error(f"Error getting embedding from cache: {e}")
            return None

    async def set_embedding(
        self, text: str, embedding: List[float], ttl: int = None
    ) -> bool:
        """
        Cache embedding for text.

        Args:
            text: Original text
            embedding: Embedding vector
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        if not await self._ensure_connection():
            return False

        key = self._generate_embedding_key(text)
        ttl = ttl or self.DEFAULT_TTL

        try:
            await self._client.setex(key, ttl, json.dumps(embedding))
            return True
        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
            return False

    async def get_job_embedding(self, job_id: str) -> Optional[List[float]]:
        """
        Get cached embedding for a job.

        Args:
            job_id: Job ID

        Returns:
            Cached embedding vector or None
        """
        if not await self._ensure_connection():
            return None

        key = self._generate_job_embeddings_key(job_id)

        try:
            cached = await self._client.get(key)
            if cached:
                self.hits += 1
                return json.loads(cached)
            else:
                self.misses += 1
                return None
        except Exception as e:
            logger.error(f"Error getting job embedding from cache: {e}")
            return None

    async def set_job_embedding(
        self, job_id: str, embedding: List[float], ttl: int = None
    ) -> bool:
        """
        Cache embedding for a job.

        Args:
            job_id: Job ID
            embedding: Embedding vector
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        if not await self._ensure_connection():
            return False

        key = self._generate_job_embeddings_key(job_id)
        ttl = ttl or self.DEFAULT_TTL

        try:
            await self._client.setex(key, ttl, json.dumps(embedding))
            return True
        except Exception as e:
            logger.error(f"Error caching job embedding: {e}")
            return False

    async def get_batch_embeddings(
        self, texts: List[str]
    ) -> Dict[str, Optional[List[float]]]:
        """
        Get multiple embeddings in batch.

        Args:
            texts: List of texts to get embeddings for

        Returns:
            Dict mapping text to cached embedding (or None)
        """
        if not await self._ensure_connection():
            return {text: None for text in texts}

        if not texts:
            return {}

        # Build keys
        keys = [self._generate_embedding_key(text) for text in texts]

        try:
            # Pipeline for batch get
            pipe = self._client.pipeline()
            for key in keys:
                pipe.get(key)
            results = await pipe.execute()

            # Build response
            embeddings = {}
            for i, text in enumerate(texts):
                if results[i]:
                    self.hits += 1
                    embeddings[text] = json.loads(results[i])
                else:
                    self.misses += 1
                    embeddings[text] = None

            return embeddings
        except Exception as e:
            logger.error(f"Error in batch embedding get: {e}")
            return {text: None for text in texts}

    async def set_batch_embeddings(
        self, embeddings: Dict[str, List[float]], ttl: int = None
    ) -> int:
        """
        Cache multiple embeddings in batch.

        Args:
            embeddings: Dict mapping text to embedding vector
            ttl: Time to live in seconds

        Returns:
            Number of embeddings cached
        """
        if not await self._ensure_connection():
            return 0

        if not embeddings:
            return 0

        ttl = ttl or self.DEFAULT_TTL

        try:
            # Pipeline for batch set
            pipe = self._client.pipeline()
            for text, embedding in embeddings.items():
                key = self._generate_embedding_key(text)
                pipe.setex(key, ttl, json.dumps(embedding))
            results = await pipe.execute()

            # Count successful operations
            cached_count = sum(1 for result in results if result)
            logger.info(f"Cached {cached_count}/{len(embeddings)} embeddings")
            return cached_count
        except Exception as e:
            logger.error(f"Error in batch embedding set: {e}")
            return 0

    async def get_popular_jobs(
        self, category: str = "all", limit: int = 100
    ) -> List[str]:
        """
        Get list of popular job IDs.

        Args:
            category: Job category filter
            limit: Maximum number of job IDs to return

        Returns:
            List of job IDs
        """
        if not await self._ensure_connection():
            return []

        key = self._generate_popular_jobs_key(category)

        try:
            jobs = await self._client.lrange(key, 0, limit - 1)
            return jobs
        except Exception as e:
            logger.error(f"Error getting popular jobs from cache: {e}")
            return []

    async def add_popular_job(
        self, job_id: str, category: str = "all", max_size: int = 1000
    ) -> bool:
        """
        Add a job to the popular jobs list.

        Args:
            job_id: Job ID to add
            category: Job category
            max_size: Maximum list size

        Returns:
            True if added successfully
        """
        if not await self._ensure_connection():
            return False

        key = self._generate_popular_jobs_key(category)

        try:
            # Add to left (most recent first) and trim
            await self._client.lpush(key, job_id)
            await self._client.ltrim(key, 0, max_size - 1)
            return True
        except Exception as e:
            logger.error(f"Error adding popular job to cache: {e}")
            return False

    async def invalidate_embedding(self, text: str) -> bool:
        """
        Invalidate cached embedding for text.

        Args:
            text: Text to invalidate

        Returns:
            True if invalidated successfully
        """
        if not await self._ensure_connection():
            return False

        key = self._generate_embedding_key(text)

        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating embedding: {e}")
            return False

    async def invalidate_job_embedding(self, job_id: str) -> bool:
        """
        Invalidate cached embedding for a job.

        Args:
            job_id: Job ID to invalidate

        Returns:
            True if invalidated successfully
        """
        if not await self._ensure_connection():
            return False

        key = self._generate_job_embeddings_key(job_id)

        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error invalidating job embedding: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self._client is not None,
        }

    async def clear_all(self) -> bool:
        """
        Clear all cached embeddings.

        Returns:
            True if cleared successfully
        """
        if not await self._ensure_connection():
            return False

        try:
            # Delete all keys with our prefixes
            patterns = [
                f"{self.EMBEDDING_PREFIX}*",
                f"{self.JOB_EMBEDDINGS_PREFIX}*",
                f"{self.POPULAR_JOBS_PREFIX}*",
            ]

            for pattern in patterns:
                cursor = 0
                while True:
                    cursor, keys = await self._client.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        await self._client.delete(*keys)
                    if cursor == 0:
                        break

            logger.info("Cleared all cached embeddings")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global embedding cache instance
embedding_cache = EmbeddingCache()


# Convenience functions
async def get_cached_embedding(text: str) -> Optional[List[float]]:
    """Get embedding from cache"""
    return await embedding_cache.get_embedding(text)


async def cache_embedding(text: str, embedding: List[float], ttl: int = None) -> bool:
    """Cache embedding"""
    return await embedding_cache.set_embedding(text, embedding, ttl)


async def get_cached_job_embedding(job_id: str) -> Optional[List[float]]:
    """Get job embedding from cache"""
    return await embedding_cache.get_job_embedding(job_id)


async def cache_job_embedding(
    job_id: str, embedding: List[float], ttl: int = None
) -> bool:
    """Cache job embedding"""
    return await embedding_cache.set_job_embedding(job_id, embedding, ttl)


async def cache_batch_embeddings(
    embeddings: Dict[str, List[float]], ttl: int = None
) -> int:
    """Cache multiple embeddings"""
    return await embedding_cache.set_batch_embeddings(embeddings, ttl)
