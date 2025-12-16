from django.db.models import QuerySet

from apps.landing.models import (
    HeroSection,
    Feature,
    Testimonial,
    FAQ,
    Pricing,
    Team,
    HowItWorks,
    Statistic,
    BlogPost,
    AppScreenshot,
)
from base_utils.services import AbstractBaseQuery


class LandingQuery(AbstractBaseQuery):
    """
    کوئری‌های صفحه فرود
    """

    @staticmethod
    def get_active_hero_sections() -> QuerySet[HeroSection]:
        """دریافت بخش‌های هیرو فعال"""
        return HeroSection.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_features() -> QuerySet[Feature]:
        """دریافت ویژگی‌های فعال"""
        return Feature.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_testimonials() -> QuerySet[Testimonial]:
        """دریافت نظرات کاربران فعال"""
        return Testimonial.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_faqs(category: str = None) -> QuerySet[FAQ]:
        """دریافت سوالات متداول فعال"""
        queryset = FAQ.objects.filter(is_active=True)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.order_by('order', '-created_at')

    @staticmethod
    def get_active_pricing() -> QuerySet[Pricing]:
        """دریافت پلن‌های قیمت‌گذاری فعال"""
        return Pricing.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_team() -> QuerySet[Team]:
        """دریافت اعضای تیم فعال"""
        return Team.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_how_it_works() -> QuerySet[HowItWorks]:
        """دریافت مراحل نحوه کار فعال"""
        return HowItWorks.objects.filter(is_active=True).order_by('step_number', 'order')

    @staticmethod
    def get_active_statistics() -> QuerySet[Statistic]:
        """دریافت آمارهای فعال"""
        return Statistic.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_active_screenshots() -> QuerySet[AppScreenshot]:
        """دریافت اسکرین‌شات‌های فعال"""
        return AppScreenshot.objects.filter(is_active=True).order_by('order', '-created_at')

    @staticmethod
    def get_published_blog_posts() -> QuerySet[BlogPost]:
        """دریافت پست‌های بلاگ منتشر شده"""
        return BlogPost.objects.filter(
            is_active=True,
            published_at__isnull=False
        ).order_by('-published_at', '-created_at')

    @staticmethod
    def get_blog_post_by_slug(slug: str) -> BlogPost:
        """دریافت پست بلاگ با اسلاگ"""
        return BlogPost.objects.get(
            slug=slug,
            is_active=True,
            published_at__isnull=False
        )

    @staticmethod
    def get_faq_categories() -> list:
        """دریافت لیست دسته‌بندی‌های سوالات متداول"""
        return (
            FAQ.objects
            .filter(is_active=True, category__isnull=False)
            .values_list('category', flat=True)
            .distinct()
            .order_by('category')
        )
