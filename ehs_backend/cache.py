from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json

def cache_key_generator(*args, **kwargs):
    """Generate a unique cache key based on arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_response(timeout=300):
    """Cache decorator for API responses"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_generator(
                view_func.__name__,
                *args,
                **kwargs
            )
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Generate response and cache it
            response = view_func(*args, **kwargs)
            cache.set(cache_key, response, timeout)
            return response
        return wrapped_view
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching a pattern"""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(pattern)
    else:
        # Fallback for cache backends that don't support pattern deletion
        cache.clear()