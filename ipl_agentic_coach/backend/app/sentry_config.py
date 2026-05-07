"""Sentry integration for error tracking."""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from .config import settings


def init_sentry():
    """Initialize Sentry for error tracking."""
    if not settings.sentry_enabled:
        return
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=settings.log_level,
                event_level="ERROR",
            ),
        ],
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.sentry_environment,
        debug=settings.debug,
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII
        profiles_sampler=lambda: 0.1,  # 10% profiling
    )


def capture_exception(exc: Exception, context: dict = None):
    """Manually capture exception to Sentry."""
    if settings.sentry_enabled:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_exception(exc)


def capture_message(message: str, level: str = "info", context: dict = None):
    """Manually capture message to Sentry."""
    if settings.sentry_enabled:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            sentry_sdk.capture_message(message, level=level)
