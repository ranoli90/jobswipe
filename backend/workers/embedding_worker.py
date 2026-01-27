"""
Async Queue for Embedding Calculations

Processes embedding generation tasks asynchronously using Redis Queue.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Status of a queued task"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmbeddingTask:
    """Represents an embedding calculation task"""

    def __init__(
        self,
        task_id: str,
        text: str,
        priority: int = 0,
        metadata: Dict[str, Any] = None,
    ):
        self.task_id = task_id
        self.text = text
        self.priority = priority
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now(timezone.utc)
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dict"""
        return {
            "task_id": self.task_id,
            "text": self.text,
            "priority": self.priority,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingTask":
        """Deserialize task from dict"""
        task = cls(
            task_id=data["task_id"],
            text=data["text"],
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )
        task.status = TaskStatus(data.get("status", "pending"))
        task.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            task.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        task.result = data.get("result")
        task.error = data.get("error")
        return task


class EmbeddingQueue:
    """
    Async Redis-based queue for embedding calculations.

    Features:
    - Priority-based task processing
    - Automatic retry on failure
    - Task status tracking
    - Concurrency control
    """

    # Queue keys
    PENDING_QUEUE = "embedding_tasks:pending"
    PROCESSING_SET = "embedding_tasks:processing"
    COMPLETED_HASH = "embedding_tasks:completed"
    FAILED_QUEUE = "embedding_tasks:failed"

    # Configuration
    DEFAULT_MAX_CONCURRENCY = 5
    DEFAULT_RETRY_DELAY = 60  # seconds
    MAX_RETRIES = 3

    def __init__(
        self,
        redis_url: str = None,
        max_concurrency: int = None,
        retry_delay: int = None,
    ):
        """
        Initialize embedding queue.

        Args:
            redis_url: Redis connection URL
            max_concurrency: Maximum concurrent workers
            retry_delay: Delay before retrying failed tasks
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.max_concurrency = max_concurrency or self.DEFAULT_MAX_CONCURRENCY
        self.retry_delay = retry_delay or self.DEFAULT_RETRY_DELAY
        self._client = None
        self._worker_tasks = []
        self._running = False

    async def connect(self) -> None:
        """Connect to Redis"""
        if self._client is None:
            self._client = redis.from_url(self.redis_url, decode_responses=True)
            await self._client.ping()
            logger.info("Connected to Redis embedding queue")

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._stop_workers()
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis embedding queue")

    async def _ensure_connection(self) -> bool:
        """Ensure Redis connection"""
        if self._client is None:
            await self.connect()
        return self._client is not None

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        import uuid

        return f"emb_{uuid.uuid4().hex[:12]}"

    async def enqueue(
        self,
        text: str,
        priority: int = 0,
        metadata: Dict[str, Any] = None,
        delay: int = 0,
    ) -> str:
        """
        Add a task to the queue.

        Args:
            text: Text to generate embedding for
            priority: Task priority (higher = processed first)
            metadata: Additional metadata
            delay: Delay before task becomes available (seconds)

        Returns:
            Task ID
        """
        if not await self._ensure_connection():
            raise RuntimeError("Not connected to Redis")

        task_id = self._generate_task_id()
        task = EmbeddingTask(
            task_id=task_id, text=text, priority=priority, metadata=metadata
        )

        # Add delay if specified
        if delay > 0:
            await asyncio.sleep(delay)

        # Store task data
        task_data = json.dumps(task.to_dict())
        await self._client.hset(self.PENDING_QUEUE, task_id, task_data)

        # Add to priority-sorted set (higher priority = higher score)
        # Use negative priority so higher values come first (ZADD sorts ascending)
        await self._client.zadd(f"{self.PENDING_QUEUE}:sorted", {task_id: -priority})

        logger.debug("Enqueued embedding task: %s", task_id)
        return task_id

    async def enqueue_batch(
        self, texts: List[str], priority: int = 0, metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        Add multiple tasks to the queue.

        Args:
            texts: List of texts to generate embeddings for
            priority: Task priority
            metadata: Additional metadata

        Returns:
            List of task IDs
        """
        task_ids = []
        for text in texts:
            task_id = await self.enqueue(text, priority, metadata)
            task_ids.append(task_id)
        return task_ids

    async def dequeue(self) -> Optional[EmbeddingTask]:
        """
        Get next task from queue.

        Returns:
            Next task or None if queue is empty
        """
        if not await self._ensure_connection():
            return None

        # Get highest priority task
        result = await self._client.zpopmax(f"{self.PENDING_QUEUE}:sorted")

        if not result:
            return None

        task_id, priority = result[0]

        # Get task data
        task_data = await self._client.hget(self.PENDING_QUEUE, task_id)
        if not task_data:
            return None

        task = EmbeddingTask.from_dict(json.loads(task_data))
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now(timezone.utc)

        # Update task data
        await self._client.hset(self.PENDING_QUEUE, task_id, json.dumps(task.to_dict()))

        # Move to processing set
        await self._client.zadd(
            self.PROCESSING_SET, {task_id: datetime.now(timezone.utc).timestamp()}
        )

        logger.debug("Dequeued embedding task: %s", task_id)
        return task

    async def complete(self, task_id: str, result: List[float]) -> bool:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
            result: Embedding result

        Returns:
            True if successful
        """
        if not await self._ensure_connection():
            return False

        # Get task
        task_data = await self._client.hget(self.PENDING_QUEUE, task_id)
        if not task_data:
            return False

        task = EmbeddingTask.from_dict(json.loads(task_data))
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        task.result = result

        # Remove from processing set
        await self._client.zrem(self.PROCESSING_SET, task_id)

        # Store in completed hash with TTL (7 days)
        await self._client.hset(
            self.COMPLETED_HASH, task_id, json.dumps(task.to_dict())
        )
        await self._client.expire(self.COMPLETED_HASH, 7 * 24 * 60 * 60)

        # Remove from pending queue
        await self._client.hdel(self.PENDING_QUEUE, task_id)

        logger.debug("Completed embedding task: %s", task_id)
        return True

    async def fail(self, task_id: str, error: str, retry: bool = True) -> bool:
        """
        Mark task as failed.

        Args:
            task_id: Task ID
            error: Error message
            retry: Whether to retry the task

        Returns:
            True if queued for retry
        """
        if not await self._ensure_connection():
            return False

        # Get task
        task_data = await self._client.hget(self.PENDING_QUEUE, task_id)
        if not task_data:
            return False

        task = EmbeddingTask.from_dict(json.loads(task_data))
        retry_count = task.metadata.get("retry_count", 0)

        if retry and retry_count < self.MAX_RETRIES:
            # Queue for retry
            task.metadata["retry_count"] = retry_count + 1
            task.status = TaskStatus.PENDING
            task.error = None

            # Update task data
            await self._client.hset(
                self.PENDING_QUEUE, task_id, json.dumps(task.to_dict())
            )

            # Re-add to priority queue with delay
            await self._client.zadd(
                f"{self.PENDING_QUEUE}:sorted", {task_id: -task.priority}
            )

            # Remove from processing set
            await self._client.zrem(self.PROCESSING_SET, task_id)

            logger.debug("Requeued embedding task for retry: %s (attempt %s)" % (task_id, retry_count + 1)
            )
            return True
        

        # Mark as failed
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now(timezone.utc)
        task.error = error

        # Remove from processing set
        await self._client.zrem(self.PROCESSING_SET, task_id)

        # Store in failed queue
        await self._client.hset(
            self.FAILED_QUEUE, task_id, json.dumps(task.to_dict())
        )
            await self._client.expire(self.FAILED_QUEUE, 7 * 24 * 60 * 60)

            # Remove from pending queue
            await self._client.hdel(self.PENDING_QUEUE, task_id)

            logger.error("Embedding task failed: %s - %s", ('task_id', 'error'))
            return False

    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task status dict or None
        """
        # Check pending queue
        task_data = await self._client.hget(self.PENDING_QUEUE, task_id)
        if task_data:
            return json.loads(task_data)

        # Check completed
        task_data = await self._client.hget(self.COMPLETED_HASH, task_id)
        if task_data:
            return json.loads(task_data)

        # Check failed
        task_data = await self._client.hget(self.FAILED_QUEUE, task_id)
        if task_data:
            return json.loads(task_data)

        return None

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.

        Returns:
            Dict with queue stats
        """
        if not await self._ensure_connection():
            return {}

        pending_count = await self._client.hlen(self.PENDING_QUEUE)
        processing_count = await self._client.zcard(self.PROCESSING_SET)
        completed_count = await self._client.hlen(self.COMPLETED_HASH)
        failed_count = await self._client.hlen(self.FAILED_QUEUE)

        return {
            "pending": pending_count,
            "processing": processing_count,
            "completed": completed_count,
            "failed": failed_count,
            "total": pending_count + processing_count + completed_count + failed_count,
        }

    async def _process_task(self, task: EmbeddingTask, embedding_service) -> None:
        """
        Process a single task.

        Args:
            task: Task to process
            embedding_service: Service to generate embeddings
        """
        try:
            # Generate embedding
            result = await embedding_service.generate_embedding(task.text)

            # Mark as completed
            await self.complete(task.task_id, result)

        except Exception as e:
            logger.error("Error processing task %s: %s", ('task.task_id', 'e'))
            await self.fail(task.task_id, str(e))

    async def _worker_loop(self, embedding_service) -> None:
        """Worker task processing loop"""
        while self._running:
            try:
                # Get next task
                task = await self.dequeue()

                if task:
                    await self._process_task(task, embedding_service)
                

                # No tasks available, wait
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Worker error: %s", e)
                await asyncio.sleep(1)

    async def _start_workers(self, embedding_service, num_workers: int = None) -> None:
        """
        Start worker processes.

        Args:
            embedding_service: Service to use for embeddings
            num_workers: Number of worker processes
        """
        num_workers = num_workers or self.max_concurrency
        self._running = True

        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(embedding_service))
            self._worker_tasks.append(worker)
            logger.debug("Started embedding worker %s/%s", ('i + 1', 'num_workers'))

    async def _stop_workers(self) -> None:
        """Stop all worker processes"""
        self._running = False

        for worker in self._worker_tasks:
            worker.cancel()

        self._worker_tasks = []
        logger.debug("Stopped all embedding workers")

    async def start_processing(
        self, embedding_service, num_workers: int = None
    ) -> None:
        """
        Start processing tasks from the queue.

        Args:
            embedding_service: Service to use for embeddings
            num_workers: Number of worker processes
        """
        await self._start_workers(embedding_service, num_workers)
        logger.info("Started embedding queue processing")

    async def stop_processing(self) -> None:
        """Stop processing tasks"""
        await self._stop_workers()
        logger.info("Stopped embedding queue processing")

    async def clear_queue(self) -> Dict[str, int]:
        """
        Clear all queues.

        Returns:
            Dict with counts of cleared items
        """
        if not await self._ensure_connection():
            return {}

        stats = await self.get_queue_stats()

        # Clear all queues
        await self._client.delete(self.PENDING_QUEUE)
        await self._client.delete(f"{self.PENDING_QUEUE}:sorted")
        await self._client.delete(self.PROCESSING_SET)
        await self._client.delete(self.COMPLETED_HASH)
        await self._client.delete(self.FAILED_QUEUE)

        logger.info("Cleared embedding queues: %s", stats)
        return stats


# Global embedding queue instance
embedding_queue = EmbeddingQueue()


# Convenience functions
async def queue_embedding(
    text: str, priority: int = 0, metadata: Dict[str, Any] = None
) -> str:
    """Queue a single embedding task"""
    return await embedding_queue.enqueue(text, priority, metadata)


async def queue_batch_embeddings(texts: List[str], priority: int = 0) -> List[str]:
    """Queue multiple embedding tasks"""
    return await embedding_queue.enqueue_batch(texts, priority)


async def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a task"""
    return await embedding_queue.get_status(task_id)


async def get_queue_status() -> Dict[str, Any]:
    """Get queue statistics"""
    return await embedding_queue.get_queue_stats()
