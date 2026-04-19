"""
Timeout Guard - Prevents runaway agent tasks.

Provides timeout functionality for orchestrator skill invocation.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Callable


# Default timeout: 5 minutes
DEFAULT_TIMEOUT = 300


@dataclass
class TimeoutResult:
    """Result of a timeout-guarded operation."""
    completed: bool
    timed_out: bool
    duration_seconds: float
    error: str | None = None


class TimeoutGuard:
    """
    Guards operations with a timeout.
    
    Usage:
        guard = TimeoutGuard(timeout=10)
        if guard.is_expired():
            # Handle timeout
            pass
    """
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """
        Initialize the timeout guard.
        
        Args:
            timeout: Maximum seconds before expiration (default: 300)
        """
        self.timeout = timeout
        self._start_time = time.monotonic()
        self._end_time = self._start_time + timeout
    
    def get_remaining_seconds(self) -> float:
        """Return remaining seconds before timeout."""
        remaining = self._end_time - time.monotonic()
        return max(0.0, remaining)
    
    def is_expired(self) -> bool:
        """Check if timeout has expired."""
        return time.monotonic() >= self._end_time
    
    def get_elapsed_seconds(self) -> float:
        """Return elapsed seconds since start."""
        return time.monotonic() - self._start_time
    
    def __enter__(self) -> "TimeoutGuard":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - checks timeout."""
        if self.is_expired():
            raise TimeoutError(f"Operation exceeded {self.timeout} second timeout")
    
    def run_with_timeout(
        self,
        func: Callable[[], any],
        on_timeout: Callable[[], any] | None = None,
    ) -> TimeoutResult:
        """
        Run a function with timeout protection.
        
        Args:
            func: Function to execute
            on_timeout: Optional callback when timeout occurs
        
        Returns:
            TimeoutResult with completion status
        """
        start = time.monotonic()
        result: any = None
        error: str | None = None
        
        try:
            result = func()
            duration = time.monotonic() - start
            return TimeoutResult(
                completed=True,
                timed_out=False,
                duration_seconds=duration,
            )
        except TimeoutError as e:
            duration = time.monotonic() - start
            if on_timeout:
                on_timeout()
            return TimeoutResult(
                completed=False,
                timed_out=True,
                duration_seconds=duration,
                error=str(e),
            )
        except Exception as e:
            duration = time.monotonic() - start
            return TimeoutResult(
                completed=False,
                timed_out=False,
                duration_seconds=duration,
                error=str(e),
            )


def with_timeout(timeout: int = DEFAULT_TIMEOUT):
    """
    Decorator to add timeout to a function.
    
    Usage:
        @with_timeout(timeout=10)
        def my_function():
            # Do work
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> TimeoutResult:
            guard = TimeoutGuard(timeout=timeout)
            
            def run_func() -> any:
                return func(*args, **kwargs)
            
            return guard.run_with_timeout(run_func)
        
        return wrapper
    return decorator
