"""
Request/Response Logging Middleware
Logs all incoming requests and their responses to a file.
"""
import json
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger('api_requests')


class RequestResponseLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses.
    Only logs requests to /api/ endpoints.
    """
    
    def process_request(self, request):
        """Store request start time and log request details"""
        # Only log API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Skip Swagger/ReDoc endpoints
        if request.path.startswith('/api/docs/') or request.path.startswith('/api/redoc/') or request.path.startswith('/api/schema/'):
            return None
        
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log request and response details"""
        # Only log API requests
        if not request.path.startswith('/api/'):
            return response
        
        # Skip Swagger/ReDoc endpoints
        if request.path.startswith('/api/docs/') or request.path.startswith('/api/redoc/') or request.path.startswith('/api/schema/'):
            return response
        
        # Calculate request duration
        duration = 0
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # Convert to milliseconds
        
        # Prepare request data
        request_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'user': None,
            'ip_address': self._get_client_ip(request),
        }
        
        # Add user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            request_data['user'] = {
                'id': request.user.id,
                'username': request.user.username,
            }
        
        # Add request body for POST/PUT/PATCH requests
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.body.decode('utf-8')
                if body:
                    try:
                        request_data['body'] = json.loads(body)
                    except json.JSONDecodeError:
                        # If not JSON, store as string (truncated if too long)
                        request_data['body'] = body[:500] if len(body) <= 500 else body[:500] + '...'
            except Exception:
                request_data['body'] = '<unable to decode>'
        
        # Prepare response data
        response_data = {
            'status_code': response.status_code,
            'duration_ms': round(duration, 2),
        }
        
        # Add response body for JSON responses (truncated if too large)
        if isinstance(response, JsonResponse):
            try:
                response_body = json.loads(response.content.decode('utf-8'))
                # Truncate large responses
                if isinstance(response_body, dict):
                    response_data['body'] = self._truncate_dict(response_body, max_depth=3)
                else:
                    response_str = json.dumps(response_body)
                    response_data['body'] = response_str[:500] if len(response_str) <= 500 else response_str[:500] + '...'
            except Exception:
                response_data['body'] = '<unable to decode>'
        
        # Log the request/response
        log_entry = {
            'request': request_data,
            'response': response_data,
        }
        
        logger.info(json.dumps(log_entry, default=str))
        
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _truncate_dict(self, data, max_depth=3, current_depth=0):
        """Recursively truncate dictionary to prevent huge log entries"""
        if current_depth >= max_depth:
            return '...'
        
        if isinstance(data, dict):
            result = {}
            for key, value in list(data.items())[:10]:  # Limit to 10 items
                if isinstance(value, (dict, list)):
                    result[key] = self._truncate_dict(value, max_depth, current_depth + 1)
                else:
                    value_str = str(value)
                    result[key] = value_str[:200] if len(value_str) <= 200 else value_str[:200] + '...'
            if len(data) > 10:
                result['...'] = f'{len(data) - 10} more items'
            return result
        elif isinstance(data, list):
            result = []
            for item in data[:10]:  # Limit to 10 items
                if isinstance(item, (dict, list)):
                    result.append(self._truncate_dict(item, max_depth, current_depth + 1))
                else:
                    item_str = str(item)
                    result.append(item_str[:200] if len(item_str) <= 200 else item_str[:200] + '...')
            if len(data) > 10:
                result.append(f'... {len(data) - 10} more items')
            return result
        else:
            return data

