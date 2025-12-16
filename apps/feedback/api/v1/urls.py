from rest_framework.routers import DefaultRouter

from . import views as feedback_apis

app_name = "feedback"

router = DefaultRouter()

router.register(r"send-feedback", feedback_apis.FeedBackGenericViewSetAPI, basename="send-feedback-api")

urlpatterns = []

urlpatterns += router.urls
