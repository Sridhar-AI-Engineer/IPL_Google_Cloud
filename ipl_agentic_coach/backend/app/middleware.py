"""Rate limiting and request throttling middleware."""
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class RateLimiter:
    """In-memory rate limiter using token bucket algorithm."""

    def __init__(self, requests: int = 100, window: int = 3600):
        """
        Args:
            requests: Number of requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.clients: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Check if client can make a request."""
        now = time.time()
        
        # Clean old requests
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if now - req_time < self.window
        ]
        
        # Check limit
        if len(self.clients[client_id]) >= self.requests:
            return False
        
        self.clients[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        now = time.time()
        self.clients[client_id] = [
            req_time for req_time in self.clients[client_id]
            if now - req_time < self.window
        ]
        return max(0, self.requests - len(self.clients[client_id]))


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests=settings.rate_limit_requests,
    window=settings.rate_limit_window_seconds,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting."""
        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Extract client identifier
        client_id = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check rate limit
        if not rate_limiter.is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        # Add rate limit headers
        response = await call_next(request)
        remaining = rate_limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + settings.rate_limit_window_seconds
        )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers."""
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.googleapis.com; "
            "connect-src 'self' https:"
        )
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response
