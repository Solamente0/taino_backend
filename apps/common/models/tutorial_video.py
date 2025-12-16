from django.db import models
from django.core.validators import URLValidator

from base_utils.base_models import TimeStampModel, ActivableModel, DescriptiveModel


class TutorialVideo(TimeStampModel, ActivableModel, DescriptiveModel):
    """
    Model for storing tutorial videos for frontend routes
    """
    
    route_path = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="مسیر صفحه",
        help_text="Frontend route path (e.g., /dashboard, /services/tax-filing)"
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name="عنوان آموزش"
    )
    
    video = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.CASCADE,
        related_name="tutorial_videos",
        verbose_name="ویدیو آموزشی",
        null=True,
        blank=True,
        help_text="Upload video file"
    )
    
    video_url = models.URLField(
        max_length=500,
        verbose_name="لینک ویدیو",
        null=True,
        blank=True,
        validators=[URLValidator()],
        help_text="External video URL (YouTube, Vimeo, etc.)"
    )
    
    thumbnail = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        related_name="tutorial_thumbnails",
        verbose_name="تصویر پیش‌نمایش",
        null=True,
        blank=True
    )
    
    duration = models.CharField(
        max_length=20,
        verbose_name="مدت زمان",
        null=True,
        blank=True,
        help_text="e.g., '5:30' or '2 minutes'"
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    
    show_on_first_visit = models.BooleanField(
        default=False,
        verbose_name="نمایش در اولین بازدید",
        help_text="Automatically show tutorial on user's first visit to this route"
    )
    
    tags = models.CharField(
        max_length=255,
        verbose_name="برچسب‌ها",
        null=True,
        blank=True,
        help_text="Comma-separated tags for categorization"
    )

    class Meta:
        verbose_name = "ویدیو آموزشی"
        verbose_name_plural = "ویدیوهای آموزشی"
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["route_path", "is_active"]),
            models.Index(fields=["is_active", "order"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.route_path}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure at least one video source is provided
        if not self.video and not self.video_url:
            raise ValidationError("Either video file or video URL must be provided")
        
        super().clean()
    
    def get_video_source(self):
        """
        Returns the appropriate video source (uploaded file or external URL)
        """
        if self.video:
            return {
                "type": "file",
                "url": self.video.file.url if self.video.file else None
            }
        elif self.video_url:
            return {
                "type": "url",
                "url": self.video_url
            }
        return None
