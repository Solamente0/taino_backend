# apps/ai_chat/services/pricing_exceptions.py
"""
کلاس‌های Exception سفارشی برای مدیریت بهتر خطاهای قیمت‌گذاری
"""

class PricingException(Exception):
    """کلاس پایه برای خطاهای قیمت‌گذاری"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InsufficientBalanceError(PricingException):
    """خطای موجودی ناکافی"""
    def __init__(self, required, available):
        message = f"موجودی ناکافی: نیاز {required} سکه، موجود {available} سکه"
        details = {
            'required': required,
            'available': available,
            'shortage': required - available
        }
        super().__init__(message, details)


class CharacterMismatchError(PricingException):
    """خطای عدم تطابق تعداد کاراکترها"""
    def __init__(self, frontend_count, backend_count, tolerance):
        diff = abs(frontend_count - backend_count)
        message = f"عدم تطابق تعداد کاراکترها: فرانت={frontend_count}, بک={backend_count}, اختلاف={diff}"
        details = {
            'frontend_count': frontend_count,
            'backend_count': backend_count,
            'difference': diff,
            'tolerance': tolerance
        }
        super().__init__(message, details)


class InvalidTokenRangeError(PricingException):
    """خطای محدوده نامعتبر توکن"""
    def __init__(self, requested, min_allowed, max_allowed):
        message = f"مقدار توکن نامعتبر: درخواست={requested}, محدوده={min_allowed}-{max_allowed}"
        details = {
            'requested': requested,
            'min_allowed': min_allowed,
            'max_allowed': max_allowed
        }
        super().__init__(message, details)


class ConfigNotFoundError(PricingException):
    """خطای یافت نشدن کانفیگ"""
    def __init__(self, static_name):
        message = f"کانفیگ هوش مصنوعی یافت نشد: {static_name}"
        details = {'static_name': static_name}
        super().__init__(message, details)


class SessionReadOnlyError(PricingException):
    """خطای جلسه فقط خواندنی"""
    def __init__(self, session_pid, reason):
        message = f"جلسه {session_pid} قفل است: {reason}"
        details = {
            'session_pid': session_pid,
            'reason': reason
        }
        super().__init__(message, details)

