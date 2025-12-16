from rest_framework import serializers

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
    ContactMessage,
    Newsletter,
    AppScreenshot,
)
from base_utils.serializers.base import TainoBaseModelSerializer, TainoBaseSerializer


class HeroSectionSerializer(TainoBaseModelSerializer):
    """سریالایزر بخش هیرو"""
    background_image_url = serializers.SerializerMethodField()

    class Meta:
        model = HeroSection
        fields = [
            'pid',
            'title',
            'subtitle',
            'description',
            'cta_primary_text',
            'cta_primary_link',
            'cta_secondary_text',
            'cta_secondary_link',
            'background_image_url',
            'video_url',
            'order',
        ]

    def get_background_image_url(self, obj):
        if obj.background_image and hasattr(obj.background_image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.background_image.file.url)
            return obj.background_image.file.url
        return None


class FeatureSerializer(TainoBaseModelSerializer):
    """سریالایزر ویژگی‌ها"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Feature
        fields = [
            'pid',
            'title',
            'description',
            'icon',
            'image_url',
            'order',
        ]

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.file.url)
            return obj.image.file.url
        return None


class TestimonialSerializer(TainoBaseModelSerializer):
    """سریالایزر نظرات کاربران"""
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Testimonial
        fields = [
            'pid',
            'name',
            'role',
            'content',
            'rating',
            'avatar_url',
            'order',
        ]

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.file.url)
            return obj.avatar.file.url
        return None


class FAQSerializer(TainoBaseModelSerializer):
    """سریالایزر سوالات متداول"""

    class Meta:
        model = FAQ
        fields = [
            'pid',
            'question',
            'answer',
            'category',
            'order',
        ]


class PricingSerializer(TainoBaseModelSerializer):
    """سریالایزر قیمت‌گذاری"""

    class Meta:
        model = Pricing
        fields = [
            'pid',
            'name',
            'description',
            'price',
            'price_period',
            'features',
            'is_popular',
            'cta_text',
            'cta_link',
            'order',
        ]


class TeamSerializer(TainoBaseModelSerializer):
    """سریالایزر اعضای تیم"""
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'pid',
            'name',
            'role',
            'bio',
            'avatar_url',
            'linkedin_url',
            'twitter_url',
            'email',
            'order',
        ]

    def get_avatar_url(self, obj):
        if obj.avatar and hasattr(obj.avatar, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.file.url)
            return obj.avatar.file.url
        return None


class HowItWorksSerializer(TainoBaseModelSerializer):
    """سریالایزر مراحل نحوه کار"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HowItWorks
        fields = [
            'pid',
            'step_number',
            'title',
            'description',
            'icon',
            'image_url',
            'order',
        ]

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.file.url)
            return obj.image.file.url
        return None


class StatisticSerializer(TainoBaseModelSerializer):
    """سریالایزر آمارها"""

    class Meta:
        model = Statistic
        fields = [
            'pid',
            'label',
            'value',
            'suffix',
            'icon',
            'order',
        ]


class BlogPostListSerializer(TainoBaseModelSerializer):
    """سریالایزر لیست پست‌های بلاگ"""
    featured_image_url = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'pid',
            'title',
            'slug',
            'excerpt',
            'featured_image_url',
            'author_name',
            'category',
            'tags',
            'reading_time',
            'views_count',
            'published_at',
        ]

    def get_featured_image_url(self, obj):
        if obj.featured_image and hasattr(obj.featured_image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.file.url)
            return obj.featured_image.file.url
        return None


class BlogPostDetailSerializer(TainoBaseModelSerializer):
    """سریالایزر جزئیات پست بلاگ"""
    featured_image_url = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'pid',
            'title',
            'slug',
            'excerpt',
            'content',
            'featured_image_url',
            'author_name',
            'category',
            'tags',
            'reading_time',
            'views_count',
            'published_at',
            'created_at',
        ]

    def get_featured_image_url(self, obj):
        if obj.featured_image and hasattr(obj.featured_image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.file.url)
            return obj.featured_image.file.url
        return None


class ContactMessageCreateSerializer(TainoBaseModelSerializer):
    """سریالایزر ایجاد پیام تماس"""

    class Meta:
        model = ContactMessage
        fields = [
            'name',
            'email',
            'phone',
            'subject',
            'message',
        ]


class NewsletterSubscribeSerializer(TainoBaseModelSerializer):
    """سریالایزر اشتراک خبرنامه"""

    class Meta:
        model = Newsletter
        fields = ['email']

    def create(self, validated_data):
        email = validated_data['email']
        newsletter, created = Newsletter.objects.get_or_create(
            email=email,
            defaults={'is_subscribed': True}
        )

        if not created and not newsletter.is_subscribed:
            newsletter.is_subscribed = True
            newsletter.unsubscribed_at = None
            newsletter.save()

        return newsletter


class AppScreenshotSerializer(TainoBaseModelSerializer):
    """سریالایزر اسکرین‌شات‌های اپلیکیشن"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AppScreenshot
        fields = [
            'pid',
            'title',
            'description',
            'image_url',
            'order',
        ]

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'file'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.file.url)
            return obj.image.file.url
        return None


class LandingPageDataSerializer(TainoBaseSerializer):
    """سریالایزر کامل داده‌های صفحه فرود"""
    hero_sections = HeroSectionSerializer(many=True)
    features = FeatureSerializer(many=True)
    testimonials = TestimonialSerializer(many=True)
    faqs = FAQSerializer(many=True)
    pricing = PricingSerializer(many=True)
    team = TeamSerializer(many=True)
    how_it_works = HowItWorksSerializer(many=True)
    statistics = StatisticSerializer(many=True)
    screenshots = AppScreenshotSerializer(many=True)
    blog_posts = BlogPostListSerializer(many=True)
