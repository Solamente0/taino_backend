from django.db import models

from apps.document.models import TainoDocument
from base_utils.base_models import (
    TimeStampModel,
    DescriptiveModel,
    BaseModel,
    AdminStatusModel,
    ActivableModel,
    StaticalIdentifier,
)


class Banner(TimeStampModel, ActivableModel, StaticalIdentifier):
    BANNER_TYPE_CHOICES = [
        ("image", "تصویر"),
        ("iframe", "iframe"),
        ("embed", "کد Embed"),
    ]

    order = models.PositiveIntegerField(default=0)

    # نوع بنر
    banner_type = models.CharField(max_length=20, choices=BANNER_TYPE_CHOICES, default="image", verbose_name="نوع بنر")

    # آدرس صفحه - استاتیک نیم برای فیلتر کردن
    # مثال: /dashboard/path یا root برای صفحه اصلی
    where_to_place = models.CharField(
        max_length=255, null=True, blank=True, db_index=True, verbose_name="محل نمایش (آدرس صفحه)"  # برای سرعت جستجو
    )

    # فیلدهای متنی
    header_text = models.CharField(max_length=255, null=True, blank=True)
    bold_text = models.CharField(max_length=255, null=True, blank=True)
    footer_text = models.CharField(max_length=255, null=True, blank=True)
    link_title = models.CharField(max_length=255, null=True, blank=True)
    link = models.CharField(max_length=1000, null=True, blank=True)

    # فایل تصویر - فقط برای تایپ image
    file = models.ForeignKey(TainoDocument, on_delete=models.CASCADE, null=True, blank=True, verbose_name="فایل تصویر")

    # کد iframe/embed - برای تایپ iframe و embed
    iframe_code = models.TextField(null=True, blank=True, verbose_name="کد iframe یا embed")

    # ارتفاع iframe (اختیاری)
    iframe_height = models.PositiveIntegerField(default=150, verbose_name="ارتفاع iframe (پیکسل)")

    # مدت زمان نمایش هر اسلایدر (به میلی‌ثانیه)
    display_duration = models.PositiveIntegerField(
        default=5000,
        verbose_name="مدت زمان نمایش (میلی‌ثانیه)",
        help_text="مدت زمان نمایش این بنر به میلی‌ثانیه (1000 = 1 ثانیه). پیش‌فرض: 5000 (5 ثانیه)",
    )

    class Meta:
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["where_to_place", "is_active"]),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        # اعتبارسنجی: برای تایپ image باید file داشته باشیم
        if self.banner_type == "image" and not self.file:
            raise ValidationError({"file": "برای بنر تصویری، فایل الزامی است."})

        # اعتبارسنجی: برای تایپ iframe/embed باید کد داشته باشیم
        if self.banner_type in ["iframe", "embed"] and not self.iframe_code:
            raise ValidationError({"iframe_code": "برای بنر iframe/embed، کد الزامی است."})
