"""
Security middleware to prevent scraping and automation
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
import re
import time


class AntiScrapingMiddleware(MiddlewareMixin):
    """
    Middleware to prevent scraping and automation tools
    """
    async_mode = False
    
    def process_request(self, request):
        """
        Check for suspicious user agents and block them
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # List of suspicious user agents and patterns
        blocked_patterns = [
            # Common scrapers
            r'ahrefsbot',
            r'mj12bot',
            r'dotbot',
            r'semrushbot',
            r'screaming frog',
            r'blexbot',
            r'backlinkcrawler',
            r'linkdexbot',
            r'grapeshotcrawler',
            r'baiduspider',
            r'yandexbot',
            
            # Automation tools
            r'selenium',
            r'webdriver',
            r'phantomjs',
            r'headlesschrome',
            r'headlessfirefox',
            r'puppeteer',
            r'playwright',
            r'curl',
            r'wget',
            r'postman',
            r'insomnia',
            
            # Data extraction tools
            r'dataforseobot',
            r'netpeakspider',
            r'serpstatbot',
            r'scrapy',
            r'beautifulsoup',
            r'mechanize',
            r'python-requests',
            
            # Generic bot patterns
            r'bot',
            r'crawler',
            r'spider',
            r'scraper',
            r'harvest',
            r'extract',
            r'fetch',
        ]
        
        # Check if user agent matches any blocked pattern
        for pattern in blocked_patterns:
            if re.search(pattern, user_agent):
                return HttpResponseForbidden(
                    "Access denied. Automated scraping and bots are not allowed."
                )
        
        # Check for suspicious headers
        suspicious_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_ORIGINATING_IP',
        ]
        
        # Block requests with too many forwarded headers (common in proxies)
        forwarded_count = sum(1 for header in suspicious_headers 
                            if request.META.get(header))
        if forwarded_count > 2:
            return HttpResponseForbidden(
                "Access denied. Proxy usage is restricted."
            )
        
        return None
    
    def process_response(self, request, response):
        """
        Add security headers to prevent scraping
        """
        # Add anti-scraping headers
        response['X-Robots-Tag'] = 'noindex, nofollow, nosnippet, noarchive'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware to prevent rapid requests
    """
    async_mode = False
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        
    def process_request(self, request):
        """
        Implement basic rate limiting
        """
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Simple rate limiting: max 100 requests per hour per IP
        current_time = int(time.time())
        hour_key = f"{ip_address}_{current_time // 3600}"
        
        if hour_key not in self.request_counts:
            self.request_counts[hour_key] = 0
        
        self.request_counts[hour_key] += 1
        
        if self.request_counts[hour_key] > 100:
            return HttpResponseForbidden(
                "Rate limit exceeded. Please try again later."
            )
        
        return None
    
    def get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
