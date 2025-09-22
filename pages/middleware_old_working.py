# middleware.py - Enhanced version with error handling
import logging
import time
import threading
import traceback
from django.db import connections, DatabaseError, InterfaceError
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Enhanced middleware with detailed query tracking, request correlation, and error handling
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        self.cleanup_threshold = getattr(settings, 'DB_CLEANUP_THRESHOLD', 100)
        self.max_connection_age = getattr(settings, 'DB_MAX_CONNECTION_AGE', 300)
        self.force_cleanup_interval = getattr(settings, 'DB_FORCE_CLEANUP_INTERVAL', 50)
        
        # Enhanced tracking
        self.connection_history = {}  # Track connection usage history
        self.local = threading.local()
        
        logger.info(f"Enhanced DatabaseConnectionMiddleware initialized with threshold={self.cleanup_threshold}")

    def __call__(self, request):
        # Generate unique request ID and store request info
        self.local.request_start_time = time.time()
        self.local.request_id = f"req_{int(time.time())}_{threading.get_ident()}"
        self.local.request_path = request.path
        self.local.request_method = request.method
        self.local.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:100]
        self.local.user = str(request.user) if hasattr(request, 'user') else 'anonymous'
        
        # Record initial query counts for each connection
        self.local.initial_query_counts = {}
        for alias in connections:
            conn = connections[alias]
            if hasattr(conn, 'queries'):
                self.local.initial_query_counts[alias] = len(conn.queries)
            else:
                self.local.initial_query_counts[alias] = 0

        try:
            # Pre-request cleanup
            self._pre_request_cleanup()
            
            # Process the request
            response = self.get_response(request)
            
            # Log detailed request stats
            self._log_detailed_request_stats()
            
            return response
            
        except (DatabaseError, InterfaceError) as e:
            # Handle database connection errors gracefully
            logger.error(
                f"Database connection error in request {self.local.request_id}: {e}\n"
                f"Path: {self.local.request_path}\n"
                f"User: {self.local.user}\n"
                f"Error type: {type(e).__name__}"
            )
            self._emergency_cleanup()
            return self._render_connectivity_error(request)
            
        except Exception as e:
            # Enhanced exception logging for other errors
            self._log_exception_with_context(e)
            self._emergency_cleanup()
            raise
            
        finally:
            # Enhanced post-request cleanup
            self._enhanced_post_request_cleanup()

    def process_exception(self, request, exception):
        """Process exceptions that occur during request processing"""
        if isinstance(exception, (DatabaseError, InterfaceError)):
            logger.error(
                f"Database exception caught: {exception}\n"
                f"Path: {request.path}\n"
                f"Method: {request.method}\n"
                f"User: {getattr(request, 'user', 'unknown')}"
            )
            self._emergency_cleanup()
            return self._render_connectivity_error(request)
        return None

    def _render_connectivity_error(self, request):
        """Render user-friendly connectivity error page"""
        try:
            return render(request, 'error_pages/connectivity_error.html', status=503)
        except Exception:
            # Fallback if template rendering fails
            return HttpResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Connection Issue</title>
                    <style>
                        body { 
                            font-family: Arial, sans-serif; 
                            text-align: center; 
                            padding: 50px; 
                            background-color: #f8f9fa;
                        }
                        .error-container {
                            background: white;
                            padding: 40px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            max-width: 500px;
                            margin: 0 auto;
                        }
                        h1 { color: #dc3545; }
                        p { color: #6c757d; }
                        .btn {
                            background-color: #17a2b8;
                            color: white;
                            padding: 12px 24px;
                            border: none;
                            border-radius: 4px;
                            text-decoration: none;
                            display: inline-block;
                            margin: 10px;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-container">
                        <h1>Connection Issue</h1>
                        <p>There seems to be an issue with your connectivity or your internet bandwidth. Please try again later.</p>
                        <a href="javascript:history.back()" class="btn">Go Back</a>
                        <a href="/" class="btn">Home</a>
                    </div>
                </body>
                </html>
                """,
                status=503
            )

    def _pre_request_cleanup(self):
        """Enhanced pre-request cleanup with tracking"""
        try:
            self.request_count += 1
            
            # Log request start
            logger.info(
                f"Starting request {self.local.request_id}: "
                f"{self.local.request_method} {self.local.request_path} "
                f"(user: {self.local.user})"
            )
            
            if self.request_count % self.force_cleanup_interval == 0:
                logger.info(f"Running periodic cleanup after {self.request_count} requests")
                self._force_cleanup_all()
                
        except Exception as e:
            logger.warning(f"Pre-request cleanup error: {e}")

    def _enhanced_post_request_cleanup(self):
        """Enhanced cleanup with detailed connection tracking"""
        try:
            request_duration = time.time() - self.local.request_start_time
            
            # Calculate query usage per connection for this request
            query_usage = {}
            total_queries_this_request = 0
            
            for alias in connections:
                conn = connections[alias]
                if hasattr(conn, 'queries'):
                    current_count = len(conn.queries)
                    initial_count = self.local.initial_query_counts.get(alias, 0)
                    queries_this_request = current_count - initial_count
                    query_usage[alias] = {
                        'initial': initial_count,
                        'final': current_count,
                        'this_request': queries_this_request
                    }
                    total_queries_this_request += queries_this_request
            
            # Enhanced cleanup decision
            self.enhanced_cleanup_connections(query_usage, request_duration)
            
        except Exception as e:
            logger.warning(f"Enhanced post-request cleanup error: {e}")

    def enhanced_cleanup_connections(self, query_usage, request_duration):
        """Enhanced cleanup with detailed logging"""
        try:
            cleaned_connections = []
            
            for alias in connections:
                conn = connections[alias]
                
                if not conn.connection:
                    continue
                    
                should_close = False
                reasons = []
                
                # Get query info for this connection
                usage = query_usage.get(alias, {})
                current_queries = usage.get('final', 0)
                request_queries = usage.get('this_request', 0)
                
                # Check query count threshold
                if current_queries > self.cleanup_threshold:
                    should_close = True
                    reasons.append(f"total_queries={current_queries}")
                
                # Check if this single request used too many queries
                if request_queries > 50:  # Flag requests with >50 queries
                    reasons.append(f"request_queries={request_queries}")
                    logger.warning(
                        f"HIGH QUERY REQUEST {self.local.request_id}: "
                        f"{request_queries} queries for {alias} connection - "
                        f"Path: {self.local.request_path}, "
                        f"User: {self.local.user}, "
                        f"Duration: {request_duration:.2f}s"
                    )
                
                # Check connection age
                if hasattr(conn, 'connection') and hasattr(conn.connection, '_connection_time'):
                    age = time.time() - conn.connection._connection_time
                    if age > self.max_connection_age:
                        should_close = True
                        reasons.append(f"age={age:.1f}s")
                
                # Check if connection is unusable
                if not conn.is_usable():
                    should_close = True
                    reasons.append("unusable")
                
                # Long request cleanup
                if request_duration > 30:
                    should_close = True
                    reasons.append(f"long_request={request_duration:.1f}s")
                
                # Close connection if criteria met
                if should_close:
                    try:
                        # Log detailed connection info before closing
                        self._log_connection_details(alias, conn, usage, reasons)
                        
                        # Track in connection history
                        self._record_connection_closure(alias, usage, reasons)
                        
                        conn.close()
                        cleaned_connections.append(f"{alias}({', '.join(reasons)})")
                        
                    except Exception as e:
                        logger.error(f"Error closing connection {alias}: {e}")
            
            if cleaned_connections:
                logger.info(
                    f"Request {self.local.request_id} - Cleaned connections: {', '.join(cleaned_connections)}"
                )
                
        except Exception as e:
            logger.error(f"Enhanced connection cleanup error: {e}")

    def _log_connection_details(self, alias, conn, usage, reasons):
        """Log detailed information about a connection being closed"""
        try:
            # Get recent queries if available
            recent_queries = []
            if hasattr(conn, 'queries') and conn.queries:
                # Get last 5 queries
                recent_queries = [
                    q.get('sql', 'unknown')[:100] + '...' if len(q.get('sql', '')) > 100 
                    else q.get('sql', 'unknown')
                    for q in conn.queries[-5:]
                ]
            
            logger.warning(
                f"CLOSING CONNECTION {alias} for request {self.local.request_id}:\n"
                f"  Reasons: {', '.join(reasons)}\n"
                f"  Request: {self.local.request_method} {self.local.request_path}\n"
                f"  User: {self.local.user}\n"
                f"  Query counts: {usage}\n"
                f"  Recent queries: {recent_queries}\n"
                f"  Request duration: {time.time() - self.local.request_start_time:.2f}s\n"
                f"  User agent: {self.local.user_agent}"
            )
            
        except Exception as e:
            logger.error(f"Error logging connection details: {e}")

    def _record_connection_closure(self, alias, usage, reasons):
        """Record connection closure in history for pattern analysis"""
        try:
            if alias not in self.connection_history:
                self.connection_history[alias] = []
            
            self.connection_history[alias].append({
                'timestamp': time.time(),
                'request_id': self.local.request_id,
                'request_path': self.local.request_path,
                'user': self.local.user,
                'usage': usage,
                'reasons': reasons,
            })
            
            # Keep only last 50 entries per connection
            if len(self.connection_history[alias]) > 50:
                self.connection_history[alias] = self.connection_history[alias][-50:]
                
        except Exception as e:
            logger.error(f"Error recording connection closure: {e}")

    def _log_detailed_request_stats(self):
        """Log detailed statistics for each request"""
        try:
            request_duration = time.time() - self.local.request_start_time
            
            # Calculate total queries for this request
            total_queries = 0
            query_breakdown = {}
            
            for alias in connections:
                conn = connections[alias]
                if hasattr(conn, 'queries'):
                    current_count = len(conn.queries)
                    initial_count = self.local.initial_query_counts.get(alias, 0)
                    queries_this_request = current_count - initial_count
                    query_breakdown[alias] = queries_this_request
                    total_queries += queries_this_request
            
            # Log if request used many queries or took long time
            if total_queries > 20 or request_duration > 5:
                logger.info(
                    f"Request {self.local.request_id} stats: "
                    f"duration={request_duration:.2f}s, "
                    f"total_queries={total_queries}, "
                    f"breakdown={query_breakdown}, "
                    f"path={self.local.request_path}, "
                    f"user={self.local.user}"
                )
                
        except Exception as e:
            logger.warning(f"Stats logging error: {e}")

    def _log_exception_with_context(self, exception):
        """Enhanced exception logging with request context"""
        try:
            logger.error(
                f"EXCEPTION in request {self.local.request_id}:\n"
                f"  Exception: {exception}\n"
                f"  Request: {self.local.request_method} {self.local.request_path}\n"
                f"  User: {self.local.user}\n"
                f"  Duration so far: {time.time() - self.local.request_start_time:.2f}s\n"
                f"  Traceback: {traceback.format_exc()}"
            )
        except Exception as e:
            logger.error(f"Exception logging failed: {e}")

    def _force_cleanup_all(self):
        """Enhanced force cleanup with better logging"""
        try:
            before_counts = {}
            for alias in connections:
                conn = connections[alias]
                if hasattr(conn, 'queries'):
                    before_counts[alias] = len(conn.queries)
                else:
                    before_counts[alias] = 0
            
            # Close all connections
            connections.close_all()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info(f"Force cleanup completed. Previous query counts: {before_counts}")
            
        except Exception as e:
            logger.error(f"Force cleanup error: {e}")

    def _emergency_cleanup(self):
        """Enhanced emergency cleanup"""
        try:
            logger.error(
                f"EMERGENCY CLEANUP for request {self.local.request_id}: "
                f"{self.local.request_method} {self.local.request_path}"
            )
            
            # Close all connections immediately
            for alias in connections:
                try:
                    connections[alias].close()
                except:
                    pass
            
            connections.close_all()
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def get_connection_history_summary(self):
        """Get summary of connection closure patterns (for debugging)"""
        summary = {}
        for alias, history in self.connection_history.items():
            summary[alias] = {
                'total_closures': len(history),
                'recent_paths': list(set([h['request_path'] for h in history[-10:]])),
                'recent_users': list(set([h['user'] for h in history[-10:]])),
                'common_reasons': {}
            }
            
            # Count reasons
            for h in history:
                for reason in h['reasons']:
                    summary[alias]['common_reasons'][reason] = summary[alias]['common_reasons'].get(reason, 0) + 1
        
        return summary