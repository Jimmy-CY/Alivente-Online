# middleware.py - Fixed version
import logging
import time
import threading
import traceback
from django.db import connections, DatabaseError, InterfaceError
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Enhanced middleware with detailed query tracking, request correlation, and error handling
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_count = 0
        
        # Use getattr with defaults instead of accessing settings directly
        self.cleanup_threshold = getattr(self._get_settings(), 'DB_CLEANUP_THRESHOLD', 100)
        self.max_connection_age = getattr(self._get_settings(), 'DB_MAX_CONNECTION_AGE', 300)
        self.force_cleanup_interval = getattr(self._get_settings(), 'DB_FORCE_CLEANUP_INTERVAL', 50)
        
        # Enhanced tracking
        self.connection_history = {}  # Track connection usage history
        self.local = threading.local()
        
        logger.info(f"Enhanced DatabaseConnectionMiddleware initialized with threshold={self.cleanup_threshold}")

    def _get_settings(self):
        """Safely get Django settings to avoid circular imports"""
        try:
            from django.conf import settings
            return settings
        except ImportError:
            return None

    def __call__(self, request):
        # Initialize local storage safely
        try:
            self._init_request_context(request)
        except Exception as e:
            logger.warning(f"Failed to initialize request context: {e}")
            # Continue without detailed tracking
            return self._simple_request_processing(request)

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
                f"Database connection error in request {getattr(self.local, 'request_id', 'unknown')}: {e}\n"
                f"Path: {getattr(self.local, 'request_path', 'unknown')}\n"
                f"User: {getattr(self.local, 'user', 'unknown')}\n"
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

    def _init_request_context(self, request):
        """Safely initialize request context"""
        self.local.request_start_time = time.time()
        self.local.request_id = f"req_{int(time.time())}_{threading.get_ident()}"
        self.local.request_path = getattr(request, 'path', 'unknown')
        self.local.request_method = getattr(request, 'method', 'unknown')
        self.local.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')[:100]
        self.local.user = str(getattr(request, 'user', 'anonymous'))
        
        # Record initial query counts for each connection
        self.local.initial_query_counts = {}
        try:
            for alias in connections:
                conn = connections[alias]
                if hasattr(conn, 'queries') and conn.queries is not None:
                    self.local.initial_query_counts[alias] = len(conn.queries)
                else:
                    self.local.initial_query_counts[alias] = 0
        except Exception as e:
            logger.warning(f"Failed to get initial query counts: {e}")
            self.local.initial_query_counts = {}

    def _simple_request_processing(self, request):
        """Fallback simple request processing without detailed tracking"""
        try:
            response = self.get_response(request)
            # Simple cleanup
            self.request_count += 1
            if self.request_count % self.force_cleanup_interval == 0:
                connections.close_all()
            return response
        except (DatabaseError, InterfaceError):
            connections.close_all()
            return self._render_connectivity_error(request)

    def process_exception(self, request, exception):
        """Process exceptions that occur during request processing"""
        if isinstance(exception, (DatabaseError, InterfaceError)):
            logger.error(
                f"Database exception caught: {exception}\n"
                f"Path: {getattr(request, 'path', 'unknown')}\n"
                f"Method: {getattr(request, 'method', 'unknown')}\n"
                f"User: {getattr(request, 'user', 'unknown')}"
            )
            self._emergency_cleanup()
            return self._render_connectivity_error(request)
        return None

    def _render_connectivity_error(self, request):
        """Render user-friendly connectivity error page"""
        # Always return the HTML fallback to avoid template issues
        return HttpResponse(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Connection Issue</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                        text-align: center; 
                        padding: 20px;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .error-container {
                        background: white;
                        padding: 40px;
                        border-radius: 12px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        max-width: 500px;
                        width: 90%;
                    }
                    h1 { 
                        color: #e74c3c; 
                        margin-top: 0;
                        font-size: 2em;
                    }
                    p { 
                        color: #555; 
                        line-height: 1.6;
                        margin: 20px 0;
                    }
                    .btn {
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 6px;
                        text-decoration: none;
                        display: inline-block;
                        margin: 10px;
                        transition: transform 0.2s;
                        font-weight: 500;
                    }
                    .btn:hover {
                        transform: translateY(-2px);
                    }
                    .error-code {
                        color: #999;
                        font-size: 0.9em;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>⚠️ Connection Issue</h1>
                    <p>We're experiencing temporary connectivity issues. This usually resolves quickly.</p>
                    <p>Please try refreshing the page or check back in a few moments.</p>
                    <a href="javascript:location.reload()" class="btn">🔄 Refresh Page</a>
                    <a href="/" class="btn">🏠 Go Home</a>
                    <div class="error-code">Error Code: DB_CONNECTION_503</div>
                </div>
            </body>
            </html>
            """,
            status=503,
            content_type='text/html'
        )

    def _pre_request_cleanup(self):
        """Enhanced pre-request cleanup with tracking"""
        try:
            self.request_count += 1
            
            # Log request start
            logger.info(
                f"Starting request {getattr(self.local, 'request_id', 'unknown')}: "
                f"{getattr(self.local, 'request_method', 'unknown')} {getattr(self.local, 'request_path', 'unknown')} "
                f"(user: {getattr(self.local, 'user', 'unknown')})"
            )
            
            if self.request_count % self.force_cleanup_interval == 0:
                logger.info(f"Running periodic cleanup after {self.request_count} requests")
                self._force_cleanup_all()
                
        except Exception as e:
            logger.warning(f"Pre-request cleanup error: {e}")

    def _enhanced_post_request_cleanup(self):
        """Enhanced cleanup with detailed connection tracking"""
        try:
            request_start_time = getattr(self.local, 'request_start_time', time.time())
            request_duration = time.time() - request_start_time
            
            # Calculate query usage per connection for this request
            query_usage = {}
            total_queries_this_request = 0
            
            try:
                for alias in connections:
                    conn = connections[alias]
                    if hasattr(conn, 'queries') and conn.queries is not None:
                        current_count = len(conn.queries)
                        initial_count = getattr(self.local, 'initial_query_counts', {}).get(alias, 0)
                        queries_this_request = max(0, current_count - initial_count)
                        query_usage[alias] = {
                            'initial': initial_count,
                            'final': current_count,
                            'this_request': queries_this_request
                        }
                        total_queries_this_request += queries_this_request
            except Exception as e:
                logger.warning(f"Error calculating query usage: {e}")
                query_usage = {}
            
            # Enhanced cleanup decision
            self.enhanced_cleanup_connections(query_usage, request_duration)
            
        except Exception as e:
            logger.warning(f"Enhanced post-request cleanup error: {e}")

    def enhanced_cleanup_connections(self, query_usage, request_duration):
        """Enhanced cleanup with detailed logging"""
        try:
            cleaned_connections = []
            
            for alias in connections:
                try:
                    conn = connections[alias]
                    
                    if not hasattr(conn, 'connection') or not conn.connection:
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
                            f"HIGH QUERY REQUEST {getattr(self.local, 'request_id', 'unknown')}: "
                            f"{request_queries} queries for {alias} connection - "
                            f"Path: {getattr(self.local, 'request_path', 'unknown')}, "
                            f"User: {getattr(self.local, 'user', 'unknown')}, "
                            f"Duration: {request_duration:.2f}s"
                        )
                    
                    # Check if connection is unusable
                    try:
                        if not conn.is_usable():
                            should_close = True
                            reasons.append("unusable")
                    except Exception:
                        should_close = True
                        reasons.append("check_failed")
                    
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
                            
                except Exception as e:
                    logger.error(f"Error processing connection {alias}: {e}")
            
            if cleaned_connections:
                logger.info(
                    f"Request {getattr(self.local, 'request_id', 'unknown')} - Cleaned connections: {', '.join(cleaned_connections)}"
                )
                
        except Exception as e:
            logger.error(f"Enhanced connection cleanup error: {e}")

    def _log_connection_details(self, alias, conn, usage, reasons):
        """Log detailed information about a connection being closed"""
        try:
            # Get recent queries if available
            recent_queries = []
            try:
                if hasattr(conn, 'queries') and conn.queries:
                    # Get last 3 queries (reduced from 5)
                    recent_queries = [
                        q.get('sql', 'unknown')[:100] + '...' if len(q.get('sql', '')) > 100 
                        else q.get('sql', 'unknown')
                        for q in conn.queries[-3:]
                    ]
            except Exception:
                recent_queries = ['query_access_failed']
            
            request_start_time = getattr(self.local, 'request_start_time', time.time())
            
            logger.warning(
                f"CLOSING CONNECTION {alias} for request {getattr(self.local, 'request_id', 'unknown')}:\n"
                f"  Reasons: {', '.join(reasons)}\n"
                f"  Request: {getattr(self.local, 'request_method', 'unknown')} {getattr(self.local, 'request_path', 'unknown')}\n"
                f"  User: {getattr(self.local, 'user', 'unknown')}\n"
                f"  Query counts: {usage}\n"
                f"  Recent queries: {recent_queries[:2]}\n"  # Limit to 2 queries
                f"  Request duration: {time.time() - request_start_time:.2f}s"
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
                'request_id': getattr(self.local, 'request_id', 'unknown'),
                'request_path': getattr(self.local, 'request_path', 'unknown'),
                'user': getattr(self.local, 'user', 'unknown'),
                'usage': usage,
                'reasons': reasons,
            })
            
            # Keep only last 20 entries per connection (reduced from 50)
            if len(self.connection_history[alias]) > 20:
                self.connection_history[alias] = self.connection_history[alias][-20:]
                
        except Exception as e:
            logger.error(f"Error recording connection closure: {e}")

    def _log_detailed_request_stats(self):
        """Log detailed statistics for each request"""
        try:
            request_start_time = getattr(self.local, 'request_start_time', time.time())
            request_duration = time.time() - request_start_time
            
            # Calculate total queries for this request
            total_queries = 0
            query_breakdown = {}
            
            try:
                for alias in connections:
                    conn = connections[alias]
                    if hasattr(conn, 'queries') and conn.queries is not None:
                        current_count = len(conn.queries)
                        initial_count = getattr(self.local, 'initial_query_counts', {}).get(alias, 0)
                        queries_this_request = max(0, current_count - initial_count)
                        query_breakdown[alias] = queries_this_request
                        total_queries += queries_this_request
            except Exception as e:
                logger.warning(f"Error getting request stats: {e}")
            
            # Log if request used many queries or took long time
            if total_queries > 20 or request_duration > 5:
                logger.info(
                    f"Request {getattr(self.local, 'request_id', 'unknown')} stats: "
                    f"duration={request_duration:.2f}s, "
                    f"total_queries={total_queries}, "
                    f"breakdown={query_breakdown}, "
                    f"path={getattr(self.local, 'request_path', 'unknown')}, "
                    f"user={getattr(self.local, 'user', 'unknown')}"
                )
                
        except Exception as e:
            logger.warning(f"Stats logging error: {e}")

    def _log_exception_with_context(self, exception):
        """Enhanced exception logging with request context"""
        try:
            request_start_time = getattr(self.local, 'request_start_time', time.time())
            logger.error(
                f"EXCEPTION in request {getattr(self.local, 'request_id', 'unknown')}:\n"
                f"  Exception: {exception}\n"
                f"  Request: {getattr(self.local, 'request_method', 'unknown')} {getattr(self.local, 'request_path', 'unknown')}\n"
                f"  User: {getattr(self.local, 'user', 'unknown')}\n"
                f"  Duration so far: {time.time() - request_start_time:.2f}s\n"
                f"  Traceback: {traceback.format_exc()}"
            )
        except Exception as e:
            logger.error(f"Exception logging failed: {e}")

    def _force_cleanup_all(self):
        """Enhanced force cleanup with better logging"""
        try:
            before_counts = {}
            try:
                for alias in connections:
                    conn = connections[alias]
                    if hasattr(conn, 'queries') and conn.queries is not None:
                        before_counts[alias] = len(conn.queries)
                    else:
                        before_counts[alias] = 0
            except Exception as e:
                logger.warning(f"Error getting pre-cleanup counts: {e}")
                before_counts = {}
            
            # Close all connections
            connections.close_all()
            
            # Force garbage collection
            try:
                import gc
                gc.collect()
            except Exception as e:
                logger.warning(f"GC failed: {e}")
            
            logger.info(f"Force cleanup completed. Previous query counts: {before_counts}")
            
        except Exception as e:
            logger.error(f"Force cleanup error: {e}")

    def _emergency_cleanup(self):
        """Enhanced emergency cleanup"""
        try:
            logger.error(
                f"EMERGENCY CLEANUP for request {getattr(self.local, 'request_id', 'unknown')}: "
                f"{getattr(self.local, 'request_method', 'unknown')} {getattr(self.local, 'request_path', 'unknown')}"
            )
            
            # Close all connections immediately
            try:
                for alias in connections:
                    try:
                        connections[alias].close()
                    except Exception:
                        pass
                
                connections.close_all()
            except Exception as e:
                logger.error(f"Emergency connection close failed: {e}")
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")

    def get_connection_history_summary(self):
        """Get summary of connection closure patterns (for debugging)"""
        try:
            summary = {}
            for alias, history in self.connection_history.items():
                if not history:
                    continue
                    
                summary[alias] = {
                    'total_closures': len(history),
                    'recent_paths': list(set([h.get('request_path', 'unknown') for h in history[-10:]])),
                    'recent_users': list(set([h.get('user', 'unknown') for h in history[-10:]])),
                    'common_reasons': {}
                }
                
                # Count reasons
                for h in history:
                    for reason in h.get('reasons', []):
                        summary[alias]['common_reasons'][reason] = summary[alias]['common_reasons'].get(reason, 0) + 1
            
            return summary
        except Exception as e:
            logger.error(f"Error generating connection history summary: {e}")
            return {}