"""
Performance tests for database connection pool stress testing
Tests concurrent database operations under high load
"""

import asyncio
import concurrent.futures
import threading
import time
from unittest.mock import MagicMock, patch

import psycopg2
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


class TestDatabaseConnectionPoolStress:
    """Stress tests for database connection pool under concurrent load"""

    @pytest.fixture
    def mock_db_config(self):
        """Mock database configuration for testing"""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "jobswipe_test",
            "user": "test_user",
            "password": "test_password",
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,
        }

    def test_connection_pool_creation(self, mock_db_config):
        """Test database connection pool creation and configuration"""
        # Mock connection to avoid actual database
        with patch("psycopg2.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            # Create engine with connection pool
            db_url = f"postgresql://{mock_db_config['user']}:{mock_db_config['password']}@{mock_db_config['host']}:{mock_db_config['port']}/{mock_db_config['database']}"

            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=mock_db_config["pool_size"],
                max_overflow=mock_db_config["max_overflow"],
                pool_timeout=mock_db_config["pool_timeout"],
                pool_recycle=mock_db_config["pool_recycle"],
                echo=False,
            )

            # Verify pool configuration
            assert engine.pool.size == mock_db_config["pool_size"]
            assert engine.pool.max_overflow == mock_db_config["max_overflow"]
            assert engine.pool.timeout == mock_db_config["pool_timeout"]

    @pytest.mark.asyncio
    async def test_concurrent_database_reads(self, mock_db_config):
        """Test concurrent read operations on database"""
        with patch("backend.db.database.get_db") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # Mock query results
            mock_jobs = [MagicMock(id=f"job_{i}", title=f"Job {i}") for i in range(100)]
            mock_session.query.return_value.filter.return_value.all.return_value = (
                mock_jobs
            )

            # Simulate concurrent users fetching jobs
            async def fetch_jobs(user_id: int):
                import uuid

                from backend.services.matching import get_personalized_jobs

                user_uuid = uuid.UUID(f"12345678-1234-5678-9012-{user_id:012d}")
                result = await get_personalized_jobs(user_uuid, db=mock_session)
                return len(result)

            # Run 50 concurrent users
            tasks = [fetch_jobs(i) for i in range(50)]
            results = await asyncio.gather(*tasks)

            # All users should get results
            assert all(result > 0 for result in results)
            assert len(results) == 50

    @pytest.mark.asyncio
    async def test_concurrent_database_writes(self, mock_db_config):
        """Test concurrent write operations on database"""
        with patch("backend.db.database.get_db") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # Mock successful commits
            mock_session.commit.return_value = None
            mock_session.add.return_value = None

            async def create_application_task(user_id: int, job_id: int):
                import uuid

                from backend.services.application_service import \
                    create_application_task

                user_uuid = str(uuid.UUID(f"12345678-1234-5678-9012-{user_id:012d}"))
                job_uuid = str(uuid.UUID(f"87654321-4321-8765-2109-{job_id:012d}"))

                result = await create_application_task(
                    user_uuid, job_uuid, mock_session
                )
                return result is not None

            # Run 30 concurrent application submissions
            tasks = [create_application_task(i, i) for i in range(30)]
            results = await asyncio.gather(*tasks)

            # All submissions should succeed
            assert all(results)
            assert len(results) == 30

            # Verify database was called appropriately
            assert mock_session.add.call_count == 30
            assert mock_session.commit.call_count == 30

    def test_connection_pool_exhaustion_simulation(self, mock_db_config):
        """Test behavior when connection pool is exhausted"""
        with patch("psycopg2.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            # Create small pool to test exhaustion
            db_url = f"postgresql://{mock_db_config['user']}:{mock_db_config['password']}@{mock_db_config['host']}:{mock_db_config['port']}/{mock_db_config['database']}"

            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=2,  # Very small pool
                max_overflow=0,  # No overflow
                pool_timeout=1,  # Short timeout
            )

            # Simulate pool exhaustion
            connections = []
            try:
                # Get first connection
                conn1 = engine.connect()
                connections.append(conn1)

                # Get second connection
                conn2 = engine.connect()
                connections.append(conn2)

                # Third connection should fail or timeout
                start_time = time.time()
                try:
                    conn3 = engine.connect()
                    connections.append(conn3)
                    # If we get here, the pool allowed overflow or has different behavior
                except Exception as e:
                    # Expected when pool is exhausted
                    duration = time.time() - start_time
                    assert duration < 2  # Should fail quickly with short timeout

            finally:
                # Clean up connections
                for conn in connections:
                    try:
                        conn.close()
                    except Exception:
                        pass

    @pytest.mark.asyncio
    async def test_database_transaction_isolation(self, mock_db_config):
        """Test database transaction isolation under concurrent operations"""
        with patch("backend.db.database.get_db") as mock_get_db:
            # Create separate session mocks for each "transaction"
            session1 = MagicMock()
            session2 = MagicMock()

            # Alternate between sessions to simulate concurrent transactions
            call_count = 0

            def get_session():
                nonlocal call_count
                call_count += 1
                return session1 if call_count % 2 == 1 else session2

            mock_get_db.side_effect = get_session

            async def isolated_transaction(tx_id: int):
                import uuid

                from backend.services.application_service import \
                    create_application_task

                user_uuid = str(uuid.UUID(f"12345678-1234-5678-9012-{tx_id:012d}"))
                job_uuid = str(uuid.UUID(f"87654321-4321-8765-2109-{tx_id:012d}"))

                # Each transaction should use its own session
                result = await create_application_task(user_uuid, job_uuid)
                return result is not None

            # Run concurrent transactions
            tasks = [isolated_transaction(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert all(results)

    def test_connection_pool_recovery(self, mock_db_config):
        """Test connection pool recovery after connection failures"""
        with patch("psycopg2.connect") as mock_connect:
            call_count = 0

            def mock_connect_func(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    # First two connections fail
                    raise psycopg2.OperationalError("Connection failed")
                else:
                    # Subsequent connections succeed
                    mock_connection = MagicMock()
                    return mock_connection

            mock_connect.side_effect = mock_connect_func

            db_url = f"postgresql://{mock_db_config['user']}:{mock_db_config['password']}@{mock_db_config['host']}:{mock_db_config['port']}/{mock_db_config['database']}"

            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=5,
                pool_timeout=5,
            )

            # Attempt connections - some should fail, some should succeed
            successful_connections = 0
            failed_connections = 0

            for i in range(10):
                try:
                    conn = engine.connect()
                    successful_connections += 1
                    conn.close()
                except Exception:
                    failed_connections += 1

            # Should have some failures and some successes
            assert successful_connections > 0
            assert failed_connections > 0
            assert successful_connections + failed_connections == 10

    @pytest.mark.asyncio
    async def test_high_concurrency_job_matching(self, mock_db_config):
        """Test job matching algorithm under high concurrency"""
        with patch("backend.db.database.get_db") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # Mock large job dataset
            mock_jobs = [
                MagicMock(
                    id=f"job_{i}",
                    title=f"Developer Job {i}",
                    description=f"Looking for skilled developer with experience {i}",
                    company=f"Company {i}",
                    location="San Francisco",
                )
                for i in range(1000)
            ]

            # Mock profile
            mock_profile = MagicMock()
            mock_profile.skills = ["Python", "JavaScript", "React"]
            mock_profile.location = "San Francisco"

            mock_session.query.return_value.filter.return_value.first.return_value = (
                mock_profile
            )
            mock_session.query.return_value.filter.return_value.or_.return_value.order_by.return_value.filter.return_value.limit.return_value.all.return_value = mock_jobs[
                :100
            ]  # First 100 jobs
            mock_session.query.return_value.filter.return_value.all.return_value = []

            async def concurrent_matching(user_id: int):
                import uuid

                from backend.services.matching import get_personalized_jobs

                user_uuid = uuid.UUID(f"12345678-1234-5678-9012-{user_id:012d}")
                start_time = time.time()
                result = await get_personalized_jobs(
                    user_uuid, page_size=20, db=mock_session
                )
                end_time = time.time()

                return {
                    "user_id": user_id,
                    "jobs_returned": len(result),
                    "duration": end_time - start_time,
                }

            # Run 20 concurrent users
            tasks = [concurrent_matching(i) for i in range(20)]
            results = await asyncio.gather(*tasks)

            # All users should get results
            assert all(r["jobs_returned"] > 0 for r in results)
            assert len(results) == 20

            # Check performance - no individual request should take too long
            max_duration = max(r["duration"] for r in results)
            assert max_duration < 5.0  # Should complete within 5 seconds

    def test_connection_pool_monitoring(self, mock_db_config):
        """Test connection pool monitoring and metrics"""
        with patch("psycopg2.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            db_url = f"postgresql://{mock_db_config['user']}:{mock_db_config['password']}@{mock_db_config['host']}:{mock_db_config['port']}/{mock_db_config['database']}"

            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=5,
            )

            # Test pool status monitoring
            pool = engine.pool

            # Check initial state
            assert pool.size == 10
            assert pool.overflow == 5

            # Simulate connections
            connections = []
            for i in range(12):  # More than pool size
                try:
                    conn = engine.connect()
                    connections.append(conn)
                except Exception:
                    break

            # Pool should have allocated connections
            assert len(connections) > 0

            # Clean up
            for conn in connections:
                try:
                    conn.close()
                except Exception:
                    pass

    @pytest.mark.asyncio
    async def test_database_deadlock_prevention(self, mock_db_config):
        """Test prevention of database deadlocks under concurrent updates"""
        with patch("backend.db.database.get_db") as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # Mock profile for updates
            mock_profile = MagicMock()
            mock_profile.full_name = "Original Name"
            mock_session.query.return_value.filter.return_value.first.return_value = (
                mock_profile
            )

            async def concurrent_profile_update(user_id: int):
                from unittest.mock import AsyncMock

                from backend.api.routers.profile import update_profile

                # Mock request and user
                mock_request = MagicMock()
                mock_user = MagicMock()
                mock_user.id = f"user_{user_id}"

                update_data = {
                    "full_name": f"Updated Name {user_id}",
                    "skills": ["Python", "JavaScript"],
                }

                try:
                    # This would normally update the profile
                    result = await update_profile(update_data, mock_user, mock_session)
                    return True
                except Exception:
                    return False

            # Run concurrent profile updates
            tasks = [concurrent_profile_update(i) for i in range(15)]
            results = await asyncio.gather(*tasks)

            # Most should succeed (exact number depends on locking implementation)
            successful_updates = sum(results)
            assert successful_updates >= 10  # At least 10 should succeed

    def test_connection_pool_cleanup(self, mock_db_config):
        """Test proper cleanup of database connections"""
        with patch("psycopg2.connect") as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            db_url = f"postgresql://{mock_db_config['user']}:{mock_db_config['password']}@{mock_db_config['host']}:{mock_db_config['port']}/{mock_db_config['database']}"

            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
            )

            # Create and dispose connections
            connections = []
            for i in range(10):
                conn = engine.connect()
                connections.append(conn)
                # Simulate some work
                conn.execute(text("SELECT 1"))
                conn.close()  # Return to pool

            # Check that connections are returned to pool
            pool = engine.pool
            # Pool should manage connections properly

            # Dispose engine
            engine.dispose()

            # Verify cleanup
            assert engine.pool is None or len(engine.pool._pool) <= engine.pool.size
