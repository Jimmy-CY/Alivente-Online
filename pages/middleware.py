# middleware.py - Complete Database Connection Management
import logging
import time
import threading
from django.db import connections
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Advanced middleware for managing database connections and preventing timeouts
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.connection_stats = {}
        self.cleanup_threshold = getattr(settings, 'DB_CLEANUP_THRESHOLD', 100)
        self.max_connection_age = getattr(settings, 'DB_MAX_CONNECTION_AGE', 300)  # 5 minutes
        self.force_cleanup_interval = getattr(settings, 'DB_FORCE_CLEANUP_INTERVAL', 50)
        
        # Thread-local storage for tracking request connections
        self.local = threading.local()
        
        logger.info(f"DatabaseConnectionMiddleware initialized with threshold={self.cleanup_threshold}")

    def __call__(self, request):
        """Main middleware entry point"""
        # Initialize request tracking
        self.local.request_start_time = time.time()
        self.local.initial_connection_count = self._count_active_connections()
        self.local.request_id = getattr(request, 'META', {}).get('HTTP_X_REQUEST_ID', f'req_{int(time.time())}')
        
        try:
            # Pre-request connection health check
            self._pre_request_cleanup()
            
            # Process the request
            response = self.get_response(request)
            
            # Log connection usage for this request
            self._log_request_stats(request)
            
            return response
            
        except Exception as e:
            # Handle exceptions by ensuring connections are cleaned up
            logger.error(f"Exception in request {self.local.request_id}: {e}")
            self._emergency_cleanup()
            raise
            
        finally:
            # Always run post-request cleanup
            self._post_request_cleanup()

    def _pre_request_cleanup(self):
        """Run before processing request"""
        try:
            # Increment request counter
            self.request_count += 1
            
            # Check if we need periodic cleanup
            if self.request_count % self.force_cleanup_interval == 0:
                logger.info(f"Running periodic cleanup after {self.request_count} requests")
                self._force_cleanup_all()
                
        except Exception as e:
            logger.warning(f"Pre-request cleanup error: {e}")

    def _post_request_cleanup(self):
        """Run after processing request"""
        try:
            # Calculate request duration
            request_duration = time.time() - self.local.request_start_time
            
            # If request took too long, force cleanup
            if request_duration > 30:  # 30 seconds
                logger.warning(f"Long request ({request_duration:.2f}s) - forcing connection cleanup")
                self._force_cleanup_all()
            else:
                # Normal cleanup
                self.cleanup_connections()
                
        except Exception as e:
            logger.warning(f"Post-request cleanup error: {e}")

    def cleanup_connections(self):
        """Smart connection cleanup based on usage patterns"""
        try:
            cleaned_connections = []
            
            for alias in connections:
                conn = connections[alias]
                
                if not conn.connection:
                    continue
                    
                should_close = False
                reason = ""
                
                # Check query count threshold
                if hasattr(conn, 'queries') and len(conn.queries) > self.cleanup_threshold:
                    should_close = True
                    reason = f"query_count={len(conn.queries)}"
                
                # Check connection age (for MySQL connections)
                if hasattr(conn, 'connection') and hasattr(conn.connection, '_connection_time'):
                    age = time.time() - conn.connection._connection_time
                    if age > self.max_connection_age:
                        should_close = True
                        reason = f"age={age:.1f}s"
                
                # Check if connection is unusable
                if not conn.is_usable():
                    should_close = True
                    reason = "unusable"
                
                # Close connection if criteria met
                if should_close:
                    try:
                        conn.close()
                        cleaned_connections.append(f"{alias}({reason})")
                    except Exception as e:
                        logger.error(f"Error closing connection {alias}: {e}")
            
            if cleaned_connections:
                logger.info(f"Cleaned connections: {', '.join(cleaned_connections)}")
                
        except Exception as e:
            logger.error(f"Connection cleanup error: {e}")

    def _force_cleanup_all(self):
        """Force close all connections - use sparingly"""
        try:
            # Get connection stats before cleanup
            before_count = self._count_active_connections()
            
            # Close all connections
            connections.close_all()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Log the cleanup
            after_count = self._count_active_connections()
            logger.info(f"Force cleanup: {before_count} -> {after_count} connections")
            
        except Exception as e:
            logger.error(f"Force cleanup error: {e}")

    def _emergency_cleanup(self):
        """Emergency cleanup when exceptions occur"""
        try:
            logger.warning("Running emergency database cleanup")
            
            # Close all connections immediately
            for alias in connections:
                try:
                    connections[alias].close()
                except:
                    pass
            
            # Clear the connection cache
            connections.close_all()
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def _count_active_connections(self):
        """Count currently active database connections"""
        count = 0
        for alias in connections:
            if connections[alias].connection is not None:
                count += 1
        return count

    def _log_request_stats(self, request):
        """Log detailed connection statistics for monitoring"""
        try:
            final_count = self._count_active_connections()
            request_duration = time.time() - self.local.request_start_time
            
            # Log if connection count changed significantly
            count_change = final_count - self.local.initial_connection_count
            
            if count_change > 2 or request_duration > 10:
                logger.info(
                    f"Request {self.local.request_id}: "
                    f"duration={request_duration:.2f}s, "
                    f"connections={self.local.initial_connection_count}->{final_count}, "
                    f"path={request.path}"
                )
                
        except Exception as e:
            logger.warning(f"Stats logging error: {e}")

    def process_exception(self, request, exception):
        """Handle exceptions by cleaning up connections"""
        try:
            logger.error(f"Exception in request {getattr(self.local, 'request_id', 'unknown')}: {exception}")
            self._emergency_cleanup()
        except Exception as e:
            logger.error(f"Exception handling failed: {e}")
        
        return None  # Don't interfere with exception propagation


class ConnectionHealthMiddleware(MiddlewareMixin):
    """
    Simpler middleware focused on connection health monitoring
    Use this if the full middleware above is too aggressive
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.unhealthy_threshold = 3
        self.consecutive_failures = {}

    def process_request(self, request):
        """Check connection health before processing request"""
        try:
            for alias in connections:
                conn = connections[alias]
                
                if not conn.is_usable():
                    # Track consecutive failures
                    self.consecutive_failures[alias] = self.consecutive_failures.get(alias, 0) + 1
                    
                    if self.consecutive_failures[alias] >= self.unhealthy_threshold:
                        logger.warning(f"Connection {alias} unhealthy, forcing reconnect")
                        conn.close()
                        self.consecutive_failures[alias] = 0
                else:
                    # Reset failure counter on successful connection
                    self.consecutive_failures[alias] = 0
                    
        except Exception as e:
            logger.warning(f"Connection health check failed: {e}")

    def process_response(self, request, response):
        """Clean up after successful responses"""
        try:
            # Light cleanup after each request
            for alias in connections:
                conn = connections[alias]
                if hasattr(conn, 'queries') and len(conn.queries) > 50:
                    conn.close()
        except Exception as e:
            logger.warning(f"Response cleanup failed: {e}")
        
        return response

    def process_exception(self, request, exception):
        """Handle database-related exceptions"""
        try:
            # Check if it's a database-related exception
            if 'database' in str(exception).lower() or 'connection' in str(exception).lower():
                logger.error(f"Database exception detected: {exception}")
                connections.close_all()
        except Exception as e:
            logger.error(f"Exception processing failed: {e}")
        
        return None


# Optional: Database Connection Pool Manager
class ConnectionPoolManager:
    """
    Standalone connection pool manager that can be used independently
    """
    
    def __init__(self):
        self.pool_stats = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def get_pool_status(self):
        """Get current status of all connection pools"""
        status = {}
        
        for alias in connections:
            conn = connections[alias]
            status[alias] = {
                'vendor': conn.vendor,
                'is_usable': conn.is_usable(),
                'has_connection': conn.connection is not None,
                'query_count': len(conn.queries) if hasattr(conn, 'queries') else 0,
                'last_used': getattr(conn, '_last_used', 'unknown'),
            }
            
        return status

    def cleanup_if_needed(self):
        """Perform cleanup if interval has passed"""
        now = time.time()
        
        if now - self.last_cleanup > self.cleanup_interval:
            self.force_cleanup()
            self.last_cleanup = now

    def force_cleanup(self):
        """Force cleanup of all connection pools"""
        logger.info("ConnectionPoolManager: Force cleanup initiated")
        
        for alias in connections:
            try:
                conn = connections[alias]
                if conn.connection and not conn.is_usable():
                    conn.close()
                    logger.info(f"Closed unusable connection: {alias}")
            except Exception as e:
                logger.error(f"Error cleaning connection {alias}: {e}")

# Initialize global pool manager
pool_manager = ConnectionPoolManager()