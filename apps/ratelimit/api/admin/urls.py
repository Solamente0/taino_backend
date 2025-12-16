from rest_framework import routers

from . import views as ratelimit_apis

app_name = "ratelimit"

router = routers.DefaultRouter()
router.register(r"ratelimit", ratelimit_apis.RateLimitModelViewSetAPI, basename="admin-ratelimit-api")

urlpatterns = []
urlpatterns += router.urls
