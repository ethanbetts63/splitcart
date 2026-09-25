"""The project's default throttle class.

DRF's `SimpleRateThrottle` counts into the `default` cache. Here that cache is
also the whole-site page cache: 1000 entries, one-hour timeout. Ordinary browse
traffic would evict an attacker's attempt count long before the window closed,
which is a rate limit that quietly stops limiting under exactly the load that
makes it matter. Counting into a cache of its own is the fix.

Counters are still per worker process and still reset on deploy. That is
acceptable only because rate limiting here is a cost control -- what actually
has to stop a password guess is account lockout, which arrives with the session
migration and is a database row.
"""

from django.core.cache import caches
from rest_framework.throttling import ScopedRateThrottle


class ScopedRequestThrottle(ScopedRateThrottle):
    """Applies whatever scope a view declares, into the throttling cache."""

    cache = caches["throttling"]
