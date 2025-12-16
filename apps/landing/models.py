from django.db import models
from django.utils.translation import gettext_lazy as _

from base_utils.base_models import (
    TimeStampModel,
    ActivableModel,
    StaticalIdentifier,
    DescriptiveModel,
)


class HeroSection(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    بخش هیرو صفحه اصلی
    """
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    subtitle = models.CharField(max_length=300, verbose_name=_("زیرعنوان"))
    description = models.TextField(verbose_name=_("توضیحات"))

    cta_primary_text = models.CharField(max_length=100, verbose_name=_("متن دکمه اصلی"))
    cta_primary_link = models.CharField(max_length=500, verbose_name=_("لینک دکمه اصلی"))

    cta_secondary_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("متن دکمه ثانویه")
    )
    cta_secondary_link = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("لینک دکمه ثانویه")
    )

    background_image = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_backgrounds",
        verbose_name=_("تصویر پس‌زمینه")
    )

    video_url = models.URLField(
        blank=True,
        verbose_name=_("لینک ویدیو")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("بخش هیرو")
        verbose_name_plural = _("بخش‌های هیرو")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class Feature(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    ویژگی‌های پلتفرم
    """
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    description = models.TextField(verbose_name=_("توضیحات"))

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("نام آیکون"),
        help_text=_("نام آیکون از کتابخانه icofont یا lucide")
    )

    image = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feature_images",
        verbose_name=_("تصویر")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("ویژگی")
        verbose_name_plural = _("ویژگی‌ها")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class Testimonial(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    نظرات کاربران
    """
    name = models.CharField(max_length=200, verbose_name=_("نام"))
    role = models.CharField(max_length=200, verbose_name=_("سمت/نقش"))
    content = models.TextField(verbose_name=_("محتوای نظر"))
    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("امتیاز"),
        help_text=_("از 1 تا 5")
    )

    avatar = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="testimonial_avatars",
        verbose_name=_("تصویر پروفایل")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("نظر کاربر")
        verbose_name_plural = _("نظرات کاربران")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.rating}★"


class FAQ(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    سوالات متداول
    """
    question = models.CharField(max_length=300, verbose_name=_("سوال"))
    answer = models.TextField(verbose_name=_("پاسخ"))

    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("دسته‌بندی")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("سوال متداول")
        verbose_name_plural = _("سوالات متداول")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.question


class Pricing(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    پلن‌های قیمت‌گذاری
    """
    name = models.CharField(max_length=200, verbose_name=_("نام پلن"))
    description = models.TextField(verbose_name=_("توضیحات"))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name=_("قیمت")
    )

    price_period = models.CharField(
        max_length=50,
        default="month",
        verbose_name=_("دوره زمانی"),
        help_text=_("مثلاً: ماهانه، سالانه")
    )

    features = models.JSONField(
        default=list,
        verbose_name=_("لیست امکانات"),
        help_text=_("لیستی از امکانات این پلن")
    )

    is_popular = models.BooleanField(
        default=False,
        verbose_name=_("پرطرفدار")
    )

    cta_text = models.CharField(
        max_length=100,
        default="شروع کنید",
        verbose_name=_("متن دکمه")
    )

    cta_link = models.CharField(
        max_length=500,
        verbose_name=_("لینک دکمه")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("پلن قیمت‌گذاری")
        verbose_name_plural = _("پلن‌های قیمت‌گذاری")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.price} تومان"


class Team(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    اعضای تیم
    """
    name = models.CharField(max_length=200, verbose_name=_("نام"))
    role = models.CharField(max_length=200, verbose_name=_("سمت"))
    bio = models.TextField(blank=True, verbose_name=_("بیوگرافی"))

    avatar = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_avatars",
        verbose_name=_("تصویر پروفایل")
    )

    linkedin_url = models.URLField(blank=True, verbose_name=_("لینک لینکدین"))
    twitter_url = models.URLField(blank=True, verbose_name=_("لینک توییتر"))
    email = models.EmailField(blank=True, verbose_name=_("ایمیل"))

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("عضو تیم")
        verbose_name_plural = _("اعضای تیم")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.role}"


class HowItWorks(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    مراحل نحوه کار
    """
    step_number = models.PositiveSmallIntegerField(verbose_name=_("شماره مرحله"))
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    description = models.TextField(verbose_name=_("توضیحات"))

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("نام آیکون")
    )

    image = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="how_it_works_images",
        verbose_name=_("تصویر")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("مرحله نحوه کار")
        verbose_name_plural = _("مراحل نحوه کار")
        ordering = ["step_number", "order"]

    def __str__(self):
        return f"مرحله {self.step_number}: {self.title}"


class Statistic(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    آمار و ارقام
    """
    label = models.CharField(max_length=200, verbose_name=_("عنوان"))
    value = models.CharField(max_length=100, verbose_name=_("مقدار"))

    suffix = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("پسوند"),
        help_text=_("مثلاً: +، K، M")
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("نام آیکون")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("آمار")
        verbose_name_plural = _("آمارها")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.label}: {self.value}{self.suffix}"


class BlogPost(TimeStampModel, ActivableModel, StaticalIdentifier, DescriptiveModel):
    """
    پست‌های بلاگ
    """
    title = models.CharField(max_length=300, verbose_name=_("عنوان"))
    slug = models.SlugField(max_length=350, unique=True, verbose_name=_("اسلاگ"))
    excerpt = models.TextField(verbose_name=_("خلاصه"))
    content = models.TextField(verbose_name=_("محتوا"))

    featured_image = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_featured_images",
        verbose_name=_("تصویر شاخص")
    )

    author = models.ForeignKey(
        "authentication.TainoUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="blog_posts",
        verbose_name=_("نویسنده")
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("دسته‌بندی")
    )

    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("برچسب‌ها")
    )

    reading_time = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("زمان مطالعه (دقیقه)")
    )

    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد بازدید")
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ انتشار")
    )

    class Meta:
        verbose_name = _("پست بلاگ")
        verbose_name_plural = _("پست‌های بلاگ")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class ContactMessage(TimeStampModel, StaticalIdentifier):
    """
    پیام‌های تماس
    """
    name = models.CharField(max_length=200, verbose_name=_("نام"))
    email = models.EmailField(verbose_name=_("ایمیل"))
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("تلفن")
    )
    subject = models.CharField(max_length=300, verbose_name=_("موضوع"))
    message = models.TextField(verbose_name=_("پیام"))

    is_read = models.BooleanField(
        default=False,
        verbose_name=_("خوانده شده")
    )

    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ پاسخ")
    )

    class Meta:
        verbose_name = _("پیام تماس")
        verbose_name_plural = _("پیام‌های تماس")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Newsletter(TimeStampModel, StaticalIdentifier):
    """
    اشتراک خبرنامه
    """
    email = models.EmailField(unique=True, verbose_name=_("ایمیل"))

    is_subscribed = models.BooleanField(
        default=True,
        verbose_name=_("مشترک است")
    )

    unsubscribed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ لغو اشتراک")
    )

    class Meta:
        verbose_name = _("خبرنامه")
        verbose_name_plural = _("خبرنامه‌ها")
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class AppScreenshot(TimeStampModel, ActivableModel, StaticalIdentifier):
    """
    اسکرین‌شات‌های اپلیکیشن
    """
    title = models.CharField(max_length=200, verbose_name=_("عنوان"))
    description = models.TextField(blank=True, verbose_name=_("توضیحات"))

    image = models.ForeignKey(
        "document.TainoDocument",
        on_delete=models.CASCADE,
        related_name="app_screenshots",
        verbose_name=_("تصویر")
    )

    order = models.PositiveIntegerField(default=0, verbose_name=_("ترتیب"))

    class Meta:
        verbose_name = _("اسکرین‌شات اپلیکیشن")
        verbose_name_plural = _("اسکرین‌شات‌های اپلیکیشن")
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title
