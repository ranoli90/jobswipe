"""
A/B Testing Framework

Implements feature flags and A/B testing for the platform.
"""

import hashlib
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from backend.db.database import async_session
from backend.db.models import ABTest, FeatureFlag, User

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExperimentStatus(str, Enum):
    """Experiment status"""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class UserGroup(str, Enum):
    """User groups for A/B testing"""

    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"
    VARIANT_D = "variant_d"


@dataclass
class ExperimentConfig:
    """A/B test configuration"""

    experiment_id: str
    name: str
    description: str
    variants: Dict[str, float]  # variant_name -> weight
    start_date: datetime
    end_date: Optional[datetime] = None
    target_filter: Optional[Dict[str, Any]] = None
    primary_metric: Optional[str] = None
    status: ExperimentStatus = ExperimentStatus.DRAFT


@dataclass
class ExperimentResult:
    """Result of an A/B test variant"""

    variant: str
    users_count: int
    conversions: int
    conversion_rate: float
    revenue: float = 0.0


class FeatureFlagService:
    """
    Service for managing feature flags
    """

    # In-memory cache of feature flags
    _flags_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    async def is_enabled(
        cls,
        flag_name: str,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a feature flag is enabled

        Args:
            flag_name: Name of the feature flag
            user_id: User ID for user-specific flags

        Returns:
            True if flag is enabled
        """
        # Check cache first
        if flag_name in cls._flags_cache:
            flag = cls._flags_cache[flag_name]

            # Check if flag is global
            if flag.get("global_enabled", False):
                return True

            # Check user-specific
            if user_id and "users" in flag:
                return user_id in flag["users"]

            return False

        # Try to load from database
        try:
            async with async_session() as session:
                result = await session.execute(
                    FeatureFlag.__table__.select().where(FeatureFlag.name == flag_name)
                )
                flag_row = result.fetchone()

            if flag_row:
                flag_data = {
                    "id": flag_row.id,
                    "name": flag_row.name,
                    "enabled": flag_row.enabled,
                    "global_enabled": flag_row.global_enabled,
                    "users": set() if not flag_row.user_ids else flag_row.user_ids,
                }
                cls._flags_cache[flag_name] = flag_data

                if flag_data.get("global_enabled", False):
                    return True

                if user_id and "users" in flag_data:
                    return user_id in flag_data["users"]

                return False
        except Exception as e:
            logger.error("Failed to check feature flag %s: %s", ('flag_name', 'e'))

        return False

    @classmethod
    async def set_flag(
        cls,
        flag_name: str,
        enabled: bool = False,
        global_enabled: bool = False,
        user_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Set a feature flag

        Args:
            flag_name: Name of the feature flag
            enabled: Whether the flag is enabled
            global_enabled: Whether the flag is enabled for all users
            user_ids: List of user IDs for user-specific flags
        """
        # Update cache
        cls._flags_cache[flag_name] = {
            "name": flag_name,
            "enabled": enabled,
            "global_enabled": global_enabled,
            "users": set(user_ids) if user_ids else set(),
        }

        # Update database
        try:
            async with async_session() as session:
                # Check if flag exists
                result = await session.execute(
                    FeatureFlag.__table__.select().where(FeatureFlag.name == flag_name)
                )
                existing = result.fetchone()

                if existing:
                    await session.execute(
                        FeatureFlag.__table__.update()
                        .where(FeatureFlag.id == existing.id)
                        .values(
                            enabled=enabled,
                            global_enabled=global_enabled,
                            user_ids=user_ids or [],
                            updated_at=datetime.now(timezone.utc),
                        )
                    )
                

                flag = FeatureFlag(
                    name=flag_name,
                    enabled=enabled,
                    global_enabled=global_enabled,
                    user_ids=user_ids or [],
                )
                session.add(flag)

            await session.commit()
        except Exception as e:
            logger.error("Failed to set feature flag %s: %s", ('flag_name', 'e'))

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the feature flags cache"""
        cls._flags_cache.clear()


class ABTestService:
    """
    A/B Testing Service

    Manages experiments, assigns users to variants, and tracks results.
    """

    def __init__(self):
        self._experiments: Dict[str, ExperimentConfig] = {}

    async def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        variants: Dict[str, float],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        target_filter: Optional[Dict[str, Any]] = None,
        primary_metric: Optional[str] = None,
    ) -> str:
        """
        Create a new A/B test experiment

        Args:
            experiment_id: Unique experiment ID
            name: Experiment name
            description: Experiment description
            variants: Dictionary of variant names and their weights
            start_date: Experiment start date
            end_date: Experiment end date (optional)
            target_filter: Filter for target users (optional)
            primary_metric: Primary metric to measure (optional)

        Returns:
            Experiment ID
        """
        config = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=variants,
            start_date=start_date,
            end_date=end_date,
            target_filter=target_filter,
            primary_metric=primary_metric,
        )

        self._experiments[experiment_id] = config

        # Save to database
        try:
            async with async_session() as session:
                test = ABTest(
                    experiment_id=experiment_id,
                    name=name,
                    description=description,
                    variants=variants,
                    start_date=start_date,
                    end_date=end_date,
                    target_filter=target_filter,
                    primary_metric=primary_metric,
                    status=ExperimentStatus.DRAFT.value,
                )
                session.add(test)
                await session.commit()
        except Exception as e:
            logger.error("Failed to save experiment: %s", e)

        return experiment_id

    def assign_variant(
        self,
        experiment_id: str,
        user_id: str,
    ) -> Optional[str]:
        """
        Assign a user to a variant for an experiment

        Uses deterministic assignment based on user ID hash

        Args:
            experiment_id: Experiment ID
            user_id: User ID

        Returns:
            Variant name or None if experiment not found
        """
        config = self._experiments.get(experiment_id)
        if not config:
            return None

        # Use hash for deterministic assignment
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)

        # Determine variant based on weight
        random.seed(hash_value)
        rand = random.random()

        cumulative = 0.0
        for variant, weight in config.variants.items():
            cumulative += weight
            if rand <= cumulative:
                return variant

        # Fallback to first variant
        return list(config.variants.keys())[0] if config.variants else None

    async def start_experiment(self, experiment_id: str) -> bool:
        """
        Start an experiment

        Args:
            experiment_id: Experiment ID

        Returns:
            True if experiment was started
        """
        if experiment_id not in self._experiments:
            return False

        config = self._experiments[experiment_id]
        config.status = ExperimentStatus.RUNNING

        # Update database
        try:
            async with async_session() as session:
                await session.execute(
                    ABTest.__table__.update()
                    .where(ABTest.experiment_id == experiment_id)
                    .values(
                        status=ExperimentStatus.RUNNING.value,
                        started_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
        except Exception as e:
            logger.error("Failed to start experiment: %s", e)

        return True

    async def record_conversion(
        self,
        experiment_id: str,
        user_id: str,
        variant: str,
        metric_name: str,
        value: float = 1.0,
    ) -> None:
        """
        Record a conversion for an experiment

        Args:
            experiment_id: Experiment ID
            user_id: User ID
            variant: Variant name
            metric_name: Name of the metric
            value: Value of the conversion
        """
        # In production, this would store to a metrics/analytics database
        logger.info("Conversion: experiment=%s, " % (experiment_id)
            f"user={user_id}, variant={variant}, "
            f"metric={metric_name}, value={value}"
        )

    async def get_experiment_results(
        self,
        experiment_id: str,
    ) -> Optional[List[ExperimentResult]]:
        """
        Get results for an experiment

        Args:
            experiment_id: Experiment ID

        Returns:
            List of experiment results by variant
        """
        config = self._experiments.get(experiment_id)
        if not config:
            return None

        results = []
        for variant in config.variants.keys():
            # In production, fetch actual data from analytics
            result = ExperimentResult(
                variant=variant,
                users_count=0,
                conversions=0,
                conversion_rate=0.0,
            )
            results.append(result)

        return results

    async def stop_experiment(
        self,
        experiment_id: str,
    ) -> bool:
        """
        Stop an experiment

        Args:
            experiment_id: Experiment ID

        Returns:
            True if experiment was stopped
        """
        if experiment_id not in self._experiments:
            return False

        config = self._experiments[experiment_id]
        config.status = ExperimentStatus.COMPLETED

        try:
            async with async_session() as session:
                await session.execute(
                    ABTest.__table__.update()
                    .where(ABTest.experiment_id == experiment_id)
                    .values(
                        status=ExperimentStatus.COMPLETED.value,
                        ended_at=datetime.now(timezone.utc),
                    )
                )
                await session.commit()
        except Exception as e:
            logger.error("Failed to stop experiment: %s", e)

        return True


class Feature(ABC, Generic[T]):
    """
    Base class for feature implementations with A/B testing
    """

    def __init__(
        self,
        flag_name: str,
        experiment_id: Optional[str] = None,
        default_value: Optional[T] = None,
    ):
        self.flag_name = flag_name
        self.experiment_id = experiment_id
        self.default_value = default_value

    async def get_value(
        self,
        user_id: Optional[str] = None,
    ) -> T:
        """
        Get the value of this feature for a user

        Args:
            user_id: User ID

        Returns:
            Feature value
        """
        # Check if feature flag is enabled
        if await FeatureFlagService.is_enabled(self.flag_name, user_id):
            return self._get_enabled_value(user_id)

        # Check if in experiment
        if self.experiment_id and user_id:
            ab_service = ABTestService()
            variant = ab_service.assign_variant(self.experiment_id, user_id)
            if variant:
                return self._get_variant_value(variant, user_id)

        return self.default_value or self._get_default_value()

    @abstractmethod
    def _get_enabled_value(self, user_id: Optional[str]) -> T:
        """Get value when feature is enabled"""
        pass

    def _get_variant_value(self, variant: str, user_id: Optional[str]) -> T:
        """Get value based on variant (override in subclasses)"""
        return (
            self._get_enabled_value(user_id)
            if variant == "control"
            else self.default_value
        )

    def _get_default_value(self) -> T:
        """Get default value"""
        return self.default_value


# Example feature implementations


class NewOnboardingFlow(Feature[bool]):
    """Feature flag for new onboarding flow"""

    def __init__(self):
        super().__init__(
            flag_name="new_onboarding_flow",
            experiment_id="exp_onboarding_v2",
            default_value=False,
        )

    def _get_enabled_value(self, user_id: Optional[str]) -> bool:
        return True


class JobMatchAlgorithmV2(Feature[float]):
    """Feature flag for new job match algorithm with custom threshold"""

    def __init__(self):
        super().__init__(
            flag_name="job_match_v2",
            experiment_id="exp_match_algorithm",
            default_value=0.7,
        )

    def _get_enabled_value(self, user_id: Optional[str]) -> float:
        return 0.85  # Higher threshold for new algorithm


# Global instances
feature_flag_service = FeatureFlagService()
ab_test_service = ABTestService()
