# A simple, in-memory cache for storing large querysets.
# This is a temporary solution to facilitate the new architecture.
# In a production environment, this would be replaced by a more robust
# caching backend like Redis or Memcached.

class SimpleInMemoryCache:
    def __init__(self):
        self._cache = {}

    def get(self, key):
        """
        Retrieves an item from the cache. Returns None if the key is not found.
        """
        return self._cache.get(key)

    def set(self, key, value):
        """
        Adds an item to the cache, overwriting any existing item with the same key.
        """
        self._cache[key] = value

    def clear(self):
        """
        Clears the entire cache.
        """
        self._cache = {}

# Create a global instance of the cache to be used by the application
product_list_cache = SimpleInMemoryCache()
