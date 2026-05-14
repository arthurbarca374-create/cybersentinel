import logging

logger = logging.getLogger(__name__)

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    HAS_LIMITER = True
except ImportError:
    from unittest.mock import MagicMock
    limiter = MagicMock()
    limiter.limit = lambda x: (lambda f: f)
    HAS_LIMITER = False
    logger.warning("slowapi not installed — rate limiting is DISABLED. Install with: pip install slowapi")
