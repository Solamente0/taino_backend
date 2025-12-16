from django.utils import timezone


class CaseNumberGenerator:
    """
    تولیدکننده شماره یکتا برای پرونده‌ها
    فرمت: CNS-YYYY-NNNNN
    مثال: CNS-2024-00123
    """
    
    @staticmethod
    def generate():
        from apps.case.models import Case
        
        current_year = timezone.now().year
        prefix = f"CNS-{current_year}"
        
        # پیدا کردن آخرین شماره در این سال
        last_case = Case.objects.filter(
            case_number__startswith=prefix
        ).order_by('-case_number').first()
        
        if last_case:
            # استخراج شماره از آخرین پرونده
            last_number = int(last_case.case_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        
        # فرمت‌بندی با 5 رقم
        return f"{prefix}-{new_number:05d}"
