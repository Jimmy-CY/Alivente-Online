# middleware.py - Complete file with both Database and Module Access middleware
import logging
import sys
import time
import threading
import traceback
from django.db import connections, DatabaseError, InterfaceError
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import resolve, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse
from django.shortcuts import render

# Configure logging to handle Unicode
if sys.platform == "win32":
    import io
    # Reconfigure stdout and stderr with UTF-8 encoding
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding='utf-8')

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
            
            # Log request start with Unicode-safe handling
            request_id = getattr(self.local, 'request_id', 'unknown')
            request_method = getattr(self.local, 'request_method', 'unknown')
            request_path = getattr(self.local, 'request_path', 'unknown')
            user = getattr(self.local, 'user', 'unknown')
            
            # Try to encode the path to ASCII to check for special characters
            try:
                request_path.encode('ascii')
                # If successful, log normally
                logger.info(
                    f"Starting request {request_id}: "
                    f"{request_method} {request_path} "
                    f"(user: {user})"
                )
            except (UnicodeEncodeError, AttributeError):
                # If path contains special characters, log simplified version
                logger.info(
                    f"Starting request {request_id}: "
                    f"{request_method} /media/[file with special characters] "
                    f"(user: {user})"
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


class ModuleAccessMiddleware(MiddlewareMixin):
    """
    Global middleware to control access to modules based on user permissions.
    Prevents users from accessing restricted modules via direct URL entry.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        
        # URLs that should always be accessible (login, logout, admin, etc.)
        self.EXEMPT_URL_PATTERNS = [
            'admin/',
            'login/',
            'logout/',
            'accounts/',
            'api/',  # If you have API endpoints
            'media/',  # Media files
            'static/',  # Static files
            # Removed empty string '' that was matching everything
        ]
        
        # URLs that require login but no specific module permission
        self.LOGIN_ONLY_PATTERNS = [
            'my-profile/',
            'help/',
            'personal',              # Landing page — per-tile perms enforce sub-module access
            'notifications/personal',  # Composite — tile/section gates in template
        ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check permissions before view is called
        """
        try:
            # Get the current URL path
            current_path = request.path_info.lstrip('/')
            
            # Check if this URL should be exempt from permission checking
            if self._is_exempt_url(current_path):
                return None
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                logger.info(f"Unauthenticated user tried to access: {current_path}")
                return HttpResponseRedirect(reverse('login') + f'?next={request.path}')
            
            # Check if this is a login-only URL (no specific module permission needed)
            if self._is_login_only_url(current_path):
                return None
            
            # Superusers can access everything
            if request.user.is_superuser:
                return None
            
            # Check module-specific permissions
            required_permission = self._get_required_permission(current_path)
            if required_permission:
                if not request.user.has_perm(required_permission):
                    logger.warning(
                        f"User {request.user.username} denied access to {current_path} "
                        f"(missing permission: {required_permission})"
                    )
                    return self._render_access_denied(request, required_permission)
            
            return None
            
        except Exception as e:
            logger.error(f"ModuleAccessMiddleware error for {request.path}: {e}")
            # Continue processing - don't block on middleware errors
            return None

    def _is_exempt_url(self, path):
        """Check if URL is exempt from permission checking"""
        for exempt_pattern in self.EXEMPT_URL_PATTERNS:
            if path.startswith(exempt_pattern):
                return True
        return False

    def _is_login_only_url(self, path):
        """Check if URL requires only login, no specific module permission"""
        for pattern in self.LOGIN_ONLY_PATTERNS:
            if path.startswith(pattern):
                return True
        return False

    def _get_required_permission(self, path):
        """Determine which permission is required for the given path.

        Checks URL prefixes against module permissions. First match wins,
        so more specific patterns MUST come before more general ones.
        """
        clean_path = path.rstrip('/')

        # Special case: the bare notifications dashboard is available to all
        # authenticated users, but its sub-URLs (notifications/personal,
        # notifications/settings) are module-restricted. Return None here only
        # for the exact path, so the sub-URLs fall through to the loop below.
        if clean_path == 'notifications':
            return None

        # (url_prefix, permission_codename)
        # First match wins — order matters!
        url_permission_map = [

            # ---------- NOTIFICATIONS (two module-restricted sub-pages) ----------
            # Must come FIRST so these specific sub-URLs match before any
            # broader rule could catch them.
            ('notifications/settings', 'auth.can_access_administration'),

            # ---------- ADMINISTRATION ----------
            ('admin_apms', 'auth.can_access_administration'),
            ('admin_clear', 'auth.can_access_administration'),
            ('admin_unpaid', 'auth.can_access_administration'),
            ('admin_renewals', 'auth.can_access_administration'),
            ('admin_invoices', 'auth.can_access_administration'),
            ('user-administration', 'auth.can_access_administration'),
            ('setup-permissions', 'auth.can_access_administration'),

            # ---------- PASSPORTS / DOCUMENTS ----------
            ('passport-management', 'auth.can_access_passports'),

            # ---------- CELEBRATIONS ----------
            ('celebrations', 'auth.can_access_celebrations'),

            # ---------- CRS REPORTING ----------
            ('crs/', 'auth.can_access_crs'),

            # ---------- RECIPES ----------
            ('recipe_management', 'auth.can_access_recipes'),
            ('recipes/', 'auth.can_access_recipes'),
            ('recipe/', 'auth.can_access_recipes'),
            ('view_recipe', 'auth.can_access_recipes'),
            ('create_recipe', 'auth.can_access_recipes'),
            ('import_recipe', 'auth.can_access_recipes'),
            ('preview_imported_recipe', 'auth.can_access_recipes'),
            ('spell-check-instructions', 'auth.can_access_recipes'),
            ('add-recipe-protein', 'auth.can_access_recipes'),
            ('meal_plans', 'auth.can_access_recipes'),
            ('unit_conversions', 'auth.can_access_recipes'),
            ('save_unit_conversion', 'auth.can_access_recipes'),
            ('add_unit_conversion_manual', 'auth.can_access_recipes'),
            ('edit_unit_conversion', 'auth.can_access_recipes'),
            ('delete_unit_conversion', 'auth.can_access_recipes'),
            ('ingredient_base_units', 'auth.can_access_recipes'),
            ('update_ingredient_base_unit', 'auth.can_access_recipes'),
            ('check-ingredient-usage', 'auth.can_access_recipes'),
            ('delete-ingredient', 'auth.can_access_recipes'),
            ('update-ingredient-full', 'auth.can_access_recipes'),
            ('categories-management', 'auth.can_access_recipes'),
            ('add-category', 'auth.can_access_recipes'),
            ('update-category', 'auth.can_access_recipes'),
            ('check-category-usage', 'auth.can_access_recipes'),
            ('delete-category', 'auth.can_access_recipes'),
            ('measurement-units-management', 'auth.can_access_recipes'),
            ('add-measurement-unit', 'auth.can_access_recipes'),
            ('update-measurement-unit', 'auth.can_access_recipes'),
            ('check-unit-usage', 'auth.can_access_recipes'),
            ('delete-measurement-unit', 'auth.can_access_recipes'),
            ('ajax/add_recipe_course', 'auth.can_access_recipes'),
            ('ajax/add_recipe_category', 'auth.can_access_recipes'),
            ('ajax/add_recipe_ingredient', 'auth.can_access_recipes'),
            ('ajax/add_measurement', 'auth.can_access_recipes'),
            ('ajax/add_ingredient', 'auth.can_access_recipes'),
            ('ajax/add_preparation', 'auth.can_access_recipes'),

            # ---------- PROPERTIES ----------
            ('properties', 'auth.can_access_properties'),
            ('properties_add', 'auth.can_access_properties'),
            ('properties_edit', 'auth.can_access_properties'),
            ('properties_commit', 'auth.can_access_properties'),
            ('properties_edit_commit', 'auth.can_access_properties'),
            ('properties_title_deed', 'auth.can_access_properties'),
            ('title_deeds_management', 'auth.can_access_properties'),
            ('property_report', 'auth.can_access_properties'),
            ('property/', 'auth.can_access_properties'),
            ('prop_rep', 'auth.can_access_properties'),
            ('title_deeds', 'auth.can_access_properties'),
            ('upload_title_deed', 'auth.can_access_properties'),
            ('assets/', 'auth.can_access_properties'),
            ('maintenance/', 'auth.can_access_properties'),
            ('ajax/category/', 'auth.can_access_properties'),
            ('ajax/subcategory/', 'auth.can_access_properties'),
            ('ajax/supplier/', 'auth.can_access_properties'),

            # ---------- TENANTS ----------
            ('tenant', 'auth.can_access_tenants'),
            ('tenant_add', 'auth.can_access_tenants'),
            ('tenant_edit', 'auth.can_access_tenants'),
            ('tenant_edit_commit', 'auth.can_access_tenants'),
            ('tenant_commit', 'auth.can_access_tenants'),
            ('tenant_lease_agreement', 'auth.can_access_tenants'),
            ('tenant_rep', 'auth.can_access_tenants'),
            ('tenant_report', 'auth.can_access_tenants'),
            ('lease', 'auth.can_access_tenants'),
            ('lease-timeline', 'auth.can_access_tenants'),
            ('lease_renewal', 'auth.can_access_tenants'),
            ('lease_renewal_report', 'auth.can_access_tenants'),
            ('lease_agreements', 'auth.can_access_tenants'),
            ('upload_lease_agreement', 'auth.can_access_tenants'),
            ('generate-lease-agreement', 'auth.can_access_tenants'),
            ('get-property-tenant-data', 'auth.can_access_tenants'),
            ('open_invoices_report', 'auth.can_access_tenants'),

            # ---------- SUPPLIERS ----------
            ('suppliers', 'auth.can_access_suppliers'),
            ('suppliers_add', 'auth.can_access_suppliers'),
            ('suppliers_edit', 'auth.can_access_suppliers'),
            ('suppliers_commit', 'auth.can_access_suppliers'),
            ('suppliers_edit_commit', 'auth.can_access_suppliers'),
            ('suppliers_rep', 'auth.can_access_suppliers'),
            ('supplier_report', 'auth.can_access_suppliers'),

            # ---------- ISSUES (FSR) ----------
            ('fsr', 'auth.can_access_issues'),
            ('fsr_add', 'auth.can_access_issues'),
            ('fsr_commit', 'auth.can_access_issues'),
            ('fsr_details', 'auth.can_access_issues'),
            ('fsr_commit_status_change', 'auth.can_access_issues'),
            ('fsr_comment_add', 'auth.can_access_issues'),
            ('fsr_notification', 'auth.can_access_issues'),
            ('fsr_rep', 'auth.can_access_issues'),
            ('issues', 'auth.can_access_issues'),
            ('issues_rep', 'auth.can_access_issues'),
            ('issue-details', 'auth.can_access_issues'),
            ('friday_status_report', 'auth.can_access_issues'),
            ('resolved_issues_report', 'auth.can_access_issues'),
            ('comments-report', 'auth.can_access_issues'),
            ('delete-comment', 'auth.can_access_issues'),

            # ---------- PROJECTS ----------
            # 'projects' MUST come before 'project_*' variants since startswith
            # is used. Check more specific patterns first within this block.
            ('projects', 'auth.can_access_projects'),
            ('ajax/projects', 'auth.can_access_projects'),
            ('ajax/tasks', 'auth.can_access_projects'),
            ('ajax/update_project_status', 'auth.can_access_projects'),
            ('ajax/update_task_status', 'auth.can_access_projects'),
            ('ajax/duplicate_project', 'auth.can_access_projects'),
            ('ajax/delete-task', 'auth.can_access_projects'),
            ('translate', 'auth.can_access_projects'),

            # ---------- DASHBOARD ----------
            # Landing page + tile dispatcher: can_access_dashboard required.
            # property_detail further checks each tile's OWNING module internally.
            ('property_management_dashboard', 'auth.can_access_dashboard'),
            ('property_detail', 'auth.can_access_dashboard'),
            ('dashboard_pl', 'auth.can_access_financials'),
            # The following are Finance-page reports, not Dashboard tiles.
            # They are listed here because they originated as dashboard-era
            # reports, but their owning module is Financials.
            ('occupancy-trends', 'auth.can_access_financials'),
            ('vacancy-management', 'auth.can_access_financials'),
            ('forecast', 'auth.can_access_financials'),

            # ---------- INVOICES ----------
            ('invoices', 'auth.can_access_invoices'),
            ('invoices_commit', 'auth.can_access_invoices'),
            ('open_invoices', 'auth.can_access_invoices'),
            # Physical Invoices + Invoice Customers (re-homed from Tenants).
            # All routes live under these two prefixes (see urls.py).
            ('physical-invoices', 'auth.can_access_invoices'),
            ('invoice-customers', 'auth.can_access_invoices'),

            # ---------- EXPENSES ----------
            ('act_expense_all', 'auth.can_access_expenses'),
            ('act_expense_view', 'auth.can_access_expenses'),
            ('act_expense_add', 'auth.can_access_expenses'),
            ('act_expense_commit', 'auth.can_access_expenses'),
            ('act_expense_edit', 'auth.can_access_expenses'),
            ('act_expense_edit_commit', 'auth.can_access_expenses'),
            ('act_expense_manage_document', 'auth.can_access_expenses'),
            ('mark_approved', 'auth.can_access_expenses'),
            ('mark_paid', 'auth.can_access_expenses'),
            ('mark_deleted', 'auth.can_access_expenses'),

            # ---------- PETTY CASH ----------
            ('petty_cash', 'auth.can_access_petty_cash'),
            ('petty_cash_add', 'auth.can_access_petty_cash'),
            ('petty_cash_commit', 'auth.can_access_petty_cash'),
            ('petty_cash_rep', 'auth.can_access_petty_cash'),

            # ---------- FINANCIALS ----------
            ('finance', 'auth.can_access_financials'),
            ('finance_valuations', 'auth.can_access_financials'),
            ('finance_valuations_add', 'auth.can_access_financials'),
            ('finance_valuations_commit', 'auth.can_access_financials'),
            ('finance_valuations_edit', 'auth.can_access_financials'),
            ('finance_valuations_edit_commit', 'auth.can_access_financials'),
            ('finance_revenue', 'auth.can_access_financials'),
            ('finance_revenue_add', 'auth.can_access_financials'),
            ('finance_revenue_commit', 'auth.can_access_financials'),
            ('finance_revenue_edit', 'auth.can_access_financials'),
            ('finance_revenue_edit_commit', 'auth.can_access_financials'),
            ('finance_revenue_types', 'auth.can_access_financials'),
            ('finance_revenue_types_add', 'auth.can_access_financials'),
            ('finance_revenue_types_commit', 'auth.can_access_financials'),
            ('finance_revenue_types_edit', 'auth.can_access_financials'),
            ('finance_revenue_types_edit_commit', 'auth.can_access_financials'),
            ('finance_revenue_line_types', 'auth.can_access_financials'),
            ('finance_revenue_line_types_add', 'auth.can_access_financials'),
            ('finance_revenue_line_types_commit', 'auth.can_access_financials'),
            ('finance_revenue_line_types_edit', 'auth.can_access_financials'),
            ('finance_revenue_line_types_edit_commit', 'auth.can_access_financials'),
            ('finance_expense', 'auth.can_access_financials'),
            ('finance_expense_add', 'auth.can_access_financials'),
            ('finance_expense_commit', 'auth.can_access_financials'),
            ('finance_expense_edit', 'auth.can_access_financials'),
            ('finance_expense_edit_commit', 'auth.can_access_financials'),
            ('finance_expense_types', 'auth.can_access_financials'),
            ('finance_expense_types_add', 'auth.can_access_financials'),
            ('finance_expense_types_commit', 'auth.can_access_financials'),
            ('finance_expense_types_edit', 'auth.can_access_financials'),
            ('finance_expense_types_edit_commit', 'auth.can_access_financials'),
            ('finance_expense_line_types', 'auth.can_access_financials'),
            ('finance_expense_line_types_add', 'auth.can_access_financials'),
            ('finance_expense_line_types_commit', 'auth.can_access_financials'),
            ('finance_expense_line_types_edit', 'auth.can_access_financials'),
            ('finance_expense_line_types_edit_commit', 'auth.can_access_financials'),
            ('finance_expense_line_types_edit_and_recalc_commit', 'auth.can_access_financials'),
            ('finance_pl_act', 'auth.can_access_financials'),
            ('revenue-details', 'auth.can_access_financials'),
            ('budget-expense-details', 'auth.can_access_financials'),
            ('total-expense-details', 'auth.can_access_financials'),
            ('financial-indicators', 'auth.can_access_financials'),
        ]

        for prefix, permission in url_permission_map:
            if (clean_path == prefix
                or clean_path.startswith(prefix + '/')
                or clean_path.startswith(prefix + '_')):
                return permission

        return None

    def _render_access_denied(self, request, required_permission):
        """Render a user-friendly access denied page"""
        try:
            # Try to render a custom template if it exists
            context = {
                'required_permission': required_permission,
                'user': request.user,
                'requested_path': request.path,
            }
            
            # Try to use your custom template
            try:
                return render(request, 'access_denied.html', context, status=403)
            except:
                # Fallback to a simple HTML response if template doesn't exist
                return self._render_simple_access_denied(request, required_permission)
                
        except Exception as e:
            logger.error(f"Error rendering access denied page: {e}")
            return HttpResponseForbidden("Access Denied: Insufficient permissions")

    def _render_simple_access_denied(self, request, required_permission):
        """Render a simple HTML access denied page"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Access Denied - Alivente</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; 
                    text-align: center; 
                    padding: 20px;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .error-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    max-width: 500px;
                    width: 90%;
                }}
                h1 {{ 
                    color: #e74c3c; 
                    margin-top: 0;
                    font-size: 2em;
                }}
                p {{ 
                    color: #555; 
                    line-height: 1.6;
                    margin: 20px 0;
                }}
                .btn {{
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
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                }}
                .user-info {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>🔒 Access Denied</h1>
                <p>You don't have permission to access this module.</p>
                <div class="user-info">
                    <strong>User:</strong> {request.user.username}<br>
                    <strong>Required Permission:</strong> {required_permission.split('.')[-1].replace('_', ' ').title()}
                </div>
                <p>Please contact your administrator if you believe you should have access to this feature.</p>
                <a href="/" class="btn">🏠 Go Home</a>
                <a href="javascript:history.back()" class="btn">← Go Back</a>
            </div>
        </body>
        </html>
        """
        
        return HttpResponseForbidden(html_content)


# Add this function to help create permissions programmatically
def create_module_permissions():
    """
    Helper function to create module permissions.
    Run this in Django shell or create a management command.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import User
    
    # Get content type (you can use any model, or create a custom one)
    content_type = ContentType.objects.get_for_model(User)
    
    permissions = [
        ('can_access_properties', 'Can access Properties module'),
        ('can_access_tenants', 'Can access Tenants module'),
        ('can_access_suppliers', 'Can access Suppliers module'),
        ('can_access_expenses', 'Can access Expenses module'),
        ('can_access_petty_cash', 'Can access Petty Cash module'),
        ('can_access_financials', 'Can access Financials module'),
        ('can_access_invoices', 'Can access Invoices module'),
        ('can_access_projects', 'Can access Projects module'),
        ('can_access_issues', 'Can access Issues module'),
        ('can_access_dashboard', 'Can access Dashboard module'),
    ]
    
    created_permissions = []
    for codename, name in permissions:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type,
        )
        if created:
            created_permissions.append(permission)
            print(f"Created permission: {permission.name}")
        else:
            print(f"Permission already exists: {permission.name}")
    
    return created_permissions