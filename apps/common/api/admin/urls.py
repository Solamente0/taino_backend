from rest_framework.routers import DefaultRouter

from apps.common.api.admin.views import (
    HomePageAdminViewSet,
    HeroSectionImageAdminViewSet,
    PartnerShipAdminViewSet,
    WayToFileTaxAdminViewSet,
    ServiceAdminViewSet,
    TeamMemberAdminViewSet,
    TestimonialAdminViewSet,
    FrequentlyAskedQuestionAdminViewSet,
    TermsOfUseAdminViewSet,
    ContactUsAdminViewSet,
    NewsletterAdminViewSet,
    ServiceItemAdminViewSet,
    TutorialVideoAdminViewSet,
    ServiceCategoryAdminViewSet,
)

app_name = "common"

router = DefaultRouter()
router.register("homepages", HomePageAdminViewSet, basename="homepages")
router.register("hero-section-images", HeroSectionImageAdminViewSet, basename="hero-section-images")
router.register("partnerships", PartnerShipAdminViewSet, basename="partnerships")
router.register("ways-to-file-tax", WayToFileTaxAdminViewSet, basename="ways-to-file-tax")
router.register("services", ServiceAdminViewSet, basename="services")
router.register("team-members", TeamMemberAdminViewSet, basename="team-members")
router.register("testimonials", TestimonialAdminViewSet, basename="testimonials")
router.register("frequently-questions", FrequentlyAskedQuestionAdminViewSet, basename="frequently-questions")
router.register("terms-of-use", TermsOfUseAdminViewSet, basename="terms-of-use")
router.register("contact-us", ContactUsAdminViewSet, basename="contact-us")
router.register("newsletter", NewsletterAdminViewSet, basename="newsletter")
router.register("tutorial-videos", TutorialVideoAdminViewSet, basename="tutorial-videos")  # Add this line
router.register("service-categories", ServiceCategoryAdminViewSet, basename="service-categories")
router.register("service-items", ServiceItemAdminViewSet, basename="service-items")

urlpatterns = []
urlpatterns += router.urls
