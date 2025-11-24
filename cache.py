import time
from functools import wraps

class SimpleCache:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        if key in self.cache:
            data, expiry = self.cache[key]
            if time.time() < expiry:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key, data, ttl=300):  # 5 minutes default
        self.cache[key] = (data, time.time() + ttl)

# Global cache instance
cache = SimpleCache()

def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator