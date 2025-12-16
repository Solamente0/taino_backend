import logging
from django.db import connection, reset_queries
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class ConnectionMonitorMiddleware(MiddlewareMixin):
    def process_request(self, request):
        connection.queries_log.clear()
        
    def process_response(self, request, response):
        # Log if too many queries
        if len(connection.queries) > 50:
            logger.warning(
                f"High query count: {len(connection.queries)} queries for {request.path}"
            )
        
        # Check for unclosed connections
        if hasattr(connection, 'connection') and connection.connection:
            if not connection.is_usable():
                logger.error(f"Connection unusable after {request.path}")
                connection.close()
        
        reset_queries()
        return response
