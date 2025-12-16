from rest_framework import routers

from . import views as feedback_apis

app_name = "feedback"

router = routers.DefaultRouter()
router.register(r"feedback", feedback_apis.FeedbackModelViewSetAPI, basename="admin-feedback-api")

urlpatterns = []
urlpatterns += router.urls
