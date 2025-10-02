"""
Error handling middleware.
"""

import traceback
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.logger import logger 

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logger
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle errors in request processing.
        
        Args:
            request: HTTP request
            call_next: Next middleware function
            
        Returns:
            Response: HTTP response or error response
        """
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Get request ID if available
            request_id = getattr(request.state, "request_id", "unknown")
            
            self.logger.error(
                f"Unhandled error - ID: {request_id}, Error: {str(exc)}"
            )
            self.logger.debug(traceback.format_exc())
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )
            