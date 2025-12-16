from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.common.api.v1.views import (
    HomePageView,
    FrequentlyAskedQuestionViewSet,
    TermsOfUseViewSet,
    ContactUsAPIView,
    NewsletterSubscribeAPIView,
    NewsletterUnsubscribeAPIView,
    ServiceItemViewSet,
    AboutUsAPIView,
    AboutUsTeamMemberViewSet,
    EnsureCookieAPIView, TutorialVideoViewSet, ServiceCategoryViewSet,
)

app_name = "common"

router = DefaultRouter()
router.register(r"frequently-questions", FrequentlyAskedQuestionViewSet, basename="frequently-questions")
router.register(r"terms-of-use", TermsOfUseViewSet, basename="terms-of-use")
router.register(r"about-us/team-member", AboutUsTeamMemberViewSet, basename="about-us-team-member")
router.register(r"tutorial-videos", TutorialVideoViewSet, basename="tutorial-videos")  # Add this line
router.register(r"service-categories", ServiceCategoryViewSet, basename="service-categories")
router.register(r"service-items", ServiceItemViewSet, basename="service-items")

urlpatterns = [
    path("home/", HomePageView.as_view(), name="home"),
    path("contact-us/", ContactUsAPIView.as_view(), name="contact-us"),
    path("newsletter/subscribe/", NewsletterSubscribeAPIView.as_view(), name="newsletter-subscribe"),
    path("newsletter/unsubscribe/", NewsletterUnsubscribeAPIView.as_view(), name="newsletter-unsubscribe"),
    path("about-us/", AboutUsAPIView.as_view(), name="about-us"),
    path("ensure-cookie/", EnsureCookieAPIView.as_view(), name="ensure-cookie"),  # Add this route
]

urlpatterns += router.urls
