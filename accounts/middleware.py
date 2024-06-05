import logging
from datetime import datetime
import requests

logger = logging.getLogger("user_activity")


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user if request.user.is_authenticated else "Anonymous"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get(
            "REMOTE_ADDR"
        )
        location = self.get_location(ip_address)
        logger.debug(
            f"{timestamp} - User:{user.email if request.user.is_authenticated else 'Anonymous'} - {request.method} - {request.path} - {ip_address} - {location} - Status Code: {response.status_code}"
        )
        return response

    def process_exception(self, request, exception):
        user = request.user if request.user.is_authenticated else "Anonymous"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_address = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get(
            "REMOTE_ADDR"
        )
        location = self.get_location(ip_address)
        logger.error(
            f"{timestamp} - User:{user.email if request.user.is_authenticated else 'Anonymous'} - {request.method} - {request.path} - {ip_address} - {location} - Exception: {exception}"
        )
        return None

    def get_location(self, ip_address):
        response = requests.get(f"https://freegeoip.app/json/{ip_address}")
        data = response.json()
        return f"{data['city']}, {data['country_name']}"
