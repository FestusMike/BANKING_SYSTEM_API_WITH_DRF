import logging
from datetime import datetime

logger = logging.getLogger("user_activity")


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user if request.user.is_authenticated else "Anonymous"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(
            f"{timestamp} - User:{user.id if request.user.is_authenticated else 'Anonymous'} - {request.method} - {request.path} - {request.META.get('REMOTE_ADDR')} - Status Code: {response.status_code}"
        )
        return response

    def process_exception(self, request, exception):
        user = request.user if request.user.is_authenticated else "Anonymous"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.error(
            f"{timestamp} - User:{user.id if request.user.is_authenticated else 'Anonymous'} - {request.method} - {request.path} - {request.META.get('REMOTE_ADDR')} - Exception: {exception}"
        )
        return None
