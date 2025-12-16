from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.landing.api.v1.serializers import (
    HeroSectionSerializer,
    FeatureSerializer,
    TestimonialSerializer,
    FAQSerializer,
    PricingSerializer,
    TeamSerializer,
    HowItWorksSerializer,
    StatisticSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    ContactMessageCreateSerializer,
    NewsletterSubscribeSerializer,
    AppScreenshotSerializer,
    LandingPageDataSerializer,
)
from apps.landing.models import BlogPost
from apps.landing.services.query import LandingQuery
from base_utils.views.mobile import (
    TainoMobileGenericViewSet,
    TainoMobileReadOnlyModelViewSet,
)


class LandingPageViewSet(TainoMobileGenericViewSet):
    """
    ViewSet برای داده‌های صفحه فرود
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: LandingPageDataSerializer},
        description="دریافت تمام داده‌های صفحه فرود"
    )
    @action(detail=False, methods=['GET'], url_path='all-data')
    def all_data(self, request):
        """
        دریافت تمام داده‌های صفحه فرود در یک درخواست
        """
        data = {
            'hero_sections': LandingQuery.get_active_hero_sections(),
            'features': LandingQuery.get_active_features(),
            'testimonials': LandingQuery.get_active_testimonials(),
            'faqs': LandingQuery.get_active_faqs(),
            'pricing': LandingQuery.get_active_pricing(),
            'team': LandingQuery.get_active_team(),
            'how_it_works': LandingQuery.get_active_how_it_works(),
            'statistics': LandingQuery.get_active_statistics(),
            'screenshots': LandingQuery.get_active_screenshots(),
            'blog_posts': LandingQuery.get_published_blog_posts()[:3],  # 3 پست آخر
        }

        serializer = LandingPageDataSerializer(data, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: HeroSectionSerializer(many=True)},
        description="دریافت بخش‌های هیرو"
    )
    @action(detail=False, methods=['GET'], url_path='hero-sections')
    def hero_sections(self, request):
        """دریافت بخش‌های هیرو"""
        queryset = LandingQuery.get_active_hero_sections()
        serializer = HeroSectionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: FeatureSerializer(many=True)},
        description="دریافت ویژگی‌ها"
    )
    @action(detail=False, methods=['GET'], url_path='features')
    def features(self, request):
        """دریافت ویژگی‌ها"""
        queryset = LandingQuery.get_active_features()
        serializer = FeatureSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: TestimonialSerializer(many=True)},
        description="دریافت نظرات کاربران"
    )
    @action(detail=False, methods=['GET'], url_path='testimonials')
    def testimonials(self, request):
        """دریافت نظرات کاربران"""
        queryset = LandingQuery.get_active_testimonials()
        serializer = TestimonialSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: FAQSerializer(many=True)},
        description="دریافت سوالات متداول"
    )
    @action(detail=False, methods=['GET'], url_path='faqs')
    def faqs(self, request):
        """دریافت سوالات متداول"""
        category = request.query_params.get('category')
        queryset = LandingQuery.get_active_faqs(category)
        serializer = FAQSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: dict},
        description="دریافت دسته‌بندی‌های سوالات متداول"
    )
    @action(detail=False, methods=['GET'], url_path='faq-categories')
    def faq_categories(self, request):
        """دریافت دسته‌بندی‌های سوالات متداول"""
        categories = LandingQuery.get_faq_categories()
        return Response({'categories': list(categories)})

    @extend_schema(
        responses={200: PricingSerializer(many=True)},
        description="دریافت پلن‌های قیمت‌گذاری"
    )
    @action(detail=False, methods=['GET'], url_path='pricing')
    def pricing(self, request):
        """دریافت پلن‌های قیمت‌گذاری"""
        queryset = LandingQuery.get_active_pricing()
        serializer = PricingSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: TeamSerializer(many=True)},
        description="دریافت اعضای تیم"
    )
    @action(detail=False, methods=['GET'], url_path='team')
    def team(self, request):
        """دریافت اعضای تیم"""
        queryset = LandingQuery.get_active_team()
        serializer = TeamSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: HowItWorksSerializer(many=True)},
        description="دریافت مراحل نحوه کار"
    )
    @action(detail=False, methods=['GET'], url_path='how-it-works')
    def how_it_works(self, request):
        """دریافت مراحل نحوه کار"""
        queryset = LandingQuery.get_active_how_it_works()
        serializer = HowItWorksSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: StatisticSerializer(many=True)},
        description="دریافت آمارها"
    )
    @action(detail=False, methods=['GET'], url_path='statistics')
    def statistics(self, request):
        """دریافت آمارها"""
        queryset = LandingQuery.get_active_statistics()
        serializer = StatisticSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        responses={200: AppScreenshotSerializer(many=True)},
        description="دریافت اسکرین‌شات‌های اپلیکیشن"
    )
    @action(detail=False, methods=['GET'], url_path='screenshots')
    def screenshots(self, request):
        """دریافت اسکرین‌شات‌های اپلیکیشن"""
        queryset = LandingQuery.get_active_screenshots()
        serializer = AppScreenshotSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        request=ContactMessageCreateSerializer,
        responses={201: dict},
        description="ارسال پیام تماس"
    )
    @action(detail=False, methods=['POST'], url_path='contact')
    def contact(self, request):
        """ارسال پیام تماس"""
        serializer = ContactMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'پیام شما با موفقیت ارسال شد. به زودی با شما تماس می‌گیریم.'},
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        request=NewsletterSubscribeSerializer,
        responses={201: dict},
        description="اشتراک در خبرنامه"
    )
    @action(detail=False, methods=['POST'], url_path='newsletter/subscribe')
    def newsletter_subscribe(self, request):
        """اشتراک در خبرنامه"""
        serializer = NewsletterSubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'message': 'شما با موفقیت در خبرنامه مشترک شدید.'},
            status=status.HTTP_201_CREATED
        )


class BlogViewSet(TainoMobileReadOnlyModelViewSet):
    """
    ViewSet برای بلاگ
    """
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return LandingQuery.get_published_blog_posts()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BlogPostDetailSerializer
        return BlogPostListSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        دریافت جزئیات پست و افزایش تعداد بازدید
        """
        instance = self.get_object()

        # افزایش تعداد بازدید
        BlogPost.objects.filter(pid=instance.pid).update(
            views_count=instance.views_count + 1
        )
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        responses={200: BlogPostListSerializer(many=True)},
        description="دریافت پست‌های پرطرفدار"
    )
    @action(detail=False, methods=['GET'], url_path='popular')
    def popular(self, request):
        """دریافت پست‌های پرطرفدار بر اساس تعداد بازدید"""
        queryset = self.get_queryset().order_by('-views_count')[:5]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: BlogPostListSerializer(many=True)},
        description="دریافت پست‌های یک دسته‌بندی"
    )
    @action(detail=False, methods=['GET'], url_path='category/(?P<category>[^/.]+)')
    def by_category(self, request, category=None):
        """دریافت پست‌های یک دسته‌بندی خاص"""
        queryset = self.get_queryset().filter(category=category)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
