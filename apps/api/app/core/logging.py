from __future__ import annotations

import logging

try:
    import structlog  # type: ignore
except Exception:  # pragma: no cover - fallback for minimal test runtimes
    structlog = None


def configure_logging():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    if structlog is not None:
        structlog.configure(
            processors=[structlog.processors.TimeStamper(fmt='iso'), structlog.processors.add_log_level, structlog.processors.JSONRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        )


class _FallbackLog:
    def __getattr__(self, name):
        logger = logging.getLogger('privacy-toolbox')
        return getattr(logger, name if hasattr(logger, name) else 'info')


log = structlog.get_logger('privacy-toolbox') if structlog is not None else _FallbackLog()
