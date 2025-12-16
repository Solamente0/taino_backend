# apps/ai_chat/middleware/rate_limiting.py
"""
Middleware برای محدودسازی درخواست‌های قیمت‌گذاری
"""
import time
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status


class AIPricingRateLimitMiddleware:
    """
    محدودسازی تعداد درخواست‌های قیمت‌گذاری
    برای جلوگیری از سوء استفاده
    """
    
    # تنظیمات Rate Limiting
    RATE_LIMIT_PATHS = [
        '/api/v1/ai_chat/pricing/preview',
        '/api/v1/ai_chat/pricing/calculate',
        '/api/v1/ai_chat/pricing/charge',
        '/api/v1/ai_chat/pricing/realtime-preview',
    ]
    
    # محدودیت‌های مختلف بر اساس endpoint
    LIMITS = {
        'realtime-preview': (60, 60),  # 60 درخواست در 60 ثانیه
        'preview': (30, 60),            # 30 درخواست در 60 ثانیه
        'calculate': (20, 60),          # 20 درخواست در 60 ثانیه
        'charge': (10, 60),             # 10 درخواست در 60 ثانیه
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # بررسی اینکه آیا این درخواست نیاز به Rate Limiting دارد
        if any(path in request.path for path in self.RATE_LIMIT_PATHS):
            # بررسی Rate Limit
            is_allowed, remaining, reset_time = self._check_rate_limit(request)
            
            if not is_allowed:
                return JsonResponse(
                    {
                        'error': 'تعداد درخواست‌های شما از حد مجاز بیشتر است',
                        'rate_limit': {
                            'remaining': remaining,
                            'reset_in_seconds': reset_time
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        response = self.get_response(request)
        return response
    
    def _check_rate_limit(self, request):
        """بررسی محدودیت درخواست"""
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated:
            # برای کاربران ناشناس، از IP استفاده کنیم
            identifier = self._get_client_ip(request)
        else:
            identifier = str(user.pid)
        
        # تشخیص نوع endpoint
        endpoint_type = self._get_endpoint_type(request.path)
        max_requests, window_seconds = self.LIMITS.get(
            endpoint_type, 
            (30, 60)  # پیش‌فرض
        )
        
        # کلید cache
        cache_key = f"rate_limit:{endpoint_type}:{identifier}"
        
        # دریافت تعداد درخواست‌های فعلی
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= max_requests:
            # محاسبه زمان باقی‌مانده تا reset
            ttl = cache.ttl(cache_key)
            return False, 0, ttl if ttl > 0 else window_seconds
        
        # افزایش تعداد درخواست‌ها
        if current_requests == 0:
            cache.set(cache_key, 1, window_seconds)
        else:
            cache.incr(cache_key)
        
        remaining = max_requests - (current_requests + 1)
        return True, remaining, window_seconds
    
    def _get_endpoint_type(self, path):
        """تشخیص نوع endpoint از مسیر"""
        if 'realtime-preview' in path:
            return 'realtime-preview'
        elif 'preview' in path:
            return 'preview'
        elif 'calculate' in path:
            return 'calculate'
        elif 'charge' in path:
            return 'charge'
        return 'default'
    
    @staticmethod
    def _get_client_ip(request):
        """دریافت IP کلاینت"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
