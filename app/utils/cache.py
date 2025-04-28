from functools import wraps
from typing import Any, Optional, Callable
import json
from datetime import datetime, timedelta
import redis
from flask import current_app

class Cache:
    """Redis cache implementation"""
    
    def __init__(self, redis_url: str):
        """
        Initialize Redis connection
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis = redis.from_url(redis_url)
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Any: Cached value if exists, None otherwise
        """
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            current_app.logger.error(f"Cache get error: {str(e)}")
            return None
            
    def set(self, key: str, value: Any, expires_in: int = 3600) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expires_in: Expiration time in seconds (default: 1 hour)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.redis.setex(
                key,
                expires_in,
                json.dumps(value)
            )
        except Exception as e:
            current_app.logger.error(f"Cache set error: {str(e)}")
            return False
            
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {str(e)}")
            return False
            
    def clear(self) -> bool:
        """
        Clear all cached values
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return self.redis.flushdb()
        except Exception as e:
            current_app.logger.error(f"Cache clear error: {str(e)}")
            return False

def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Generated cache key
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)

def cached(expires_in: int = 3600):
    """
    Cache decorator
    
    Args:
        expires_in: Cache expiration time in seconds (default: 1 hour)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__module__}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Get cache instance
            cache = current_app.cache
            
            # Try to get cached value
            cached_value = cache.get(key)
            if cached_value is not None:
                current_app.logger.debug(f"Cache hit for key: {key}")
                return cached_value
            
            # If not cached, execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(key, result, expires_in)
            current_app.logger.debug(f"Cached value for key: {key}")
            
            return result
        return wrapper
    return decorator

def cache_weather(location: dict, days: int = 7) -> str:
    """
    Generate cache key for weather data
    
    Args:
        location: Location dictionary with lat/lon
        days: Number of forecast days
        
    Returns:
        str: Cache key
    """
    return f"weather:{location['latitude']}:{location['longitude']}:{days}"

def invalidate_weather_cache(location: dict):
    """
    Invalidate weather cache for a location
    
    Args:
        location: Location dictionary with lat/lon
    """
    try:
        pattern = f"weather:{location['latitude']}:{location['longitude']}:*"
        keys = current_app.cache.redis.keys(pattern)
        if keys:
            current_app.cache.redis.delete(*keys)
            current_app.logger.info(f"Invalidated weather cache for location: {location}")
    except Exception as e:
        current_app.logger.error(f"Failed to invalidate weather cache: {str(e)}")

def should_refresh_weather(cached_data: dict) -> bool:
    """
    Check if weather data should be refreshed
    
    Args:
        cached_data: Cached weather data
        
    Returns:
        bool: True if data should be refreshed
    """
    if not cached_data or 'timestamp' not in cached_data:
        return True
        
    # Convert timestamp string to datetime
    cached_time = datetime.fromisoformat(cached_data['timestamp'])
    
    # Weather data should be refreshed every 3 hours
    return datetime.utcnow() - cached_time > timedelta(hours=3)
