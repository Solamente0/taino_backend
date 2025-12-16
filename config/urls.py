from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import path, include, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.permissions import AllowAny
from django.contrib import admin


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
@throttle_classes([])
def health_check_view(request, **kwargs):
    from rest_framework.response import Response

    return Response("pong")


urlpatterns = [
    path("api/ping", health_check_view, name="health_check"),
    path("api/auth/", include("apps.authentication.api.urls", namespace="authentication"), name="authentication"),
    path("api/country/", include("apps.country.api.urls"), name="country"),
    path("api/document/", include("apps.document.api.urls"), name="documents"),
    path("api/banner/", include("apps.banner.api.urls"), name="banner"),
    path("api/social-media/", include("apps.social_media.api.urls"), name="social_media"),
    path("api/version/", include("apps.version.api.urls"), name="version"),
    path("api/feedback/", include("apps.feedback.api.urls"), name="feedback"),
    path("api/ratelimit/", include("apps.ratelimit.api.urls"), name="ratelimit"),
    path("api/address/", include("apps.address.api.urls"), name="address"),
    path("api/user/", include("apps.user.api.urls"), name="user"),
    path("api/wallet/", include("apps.wallet.api.urls"), name="wallet"),
    path("api/referral/", include("apps.referral.api.urls"), name="referral"),
    path("api/setting/", include("apps.setting.api.urls"), name="setting"),
    path("api/notification/", include("apps.notification.api.urls"), name="notification"),
    path("api/common/", include("apps.common.api.urls"), name="common"),
    path("api/payment/", include("apps.payment.api.urls"), name="payment"),
    path("api/subscription/", include("apps.subscription.api.urls"), name="subscription"),
    path("api/chat/", include("apps.chat.api.urls"), name="chat"),
    path("api/ai-chat/", include("apps.ai_chat.api.urls"), name="ai-chat"),
    path("api/permissions/", include("apps.permissions.api.urls"), name="permissions"),
    path("api/messaging/", include("apps.messaging.api.urls"), name="messaging"),
    path("api/analyzer/", include("apps.analyzer.api.urls"), name="analyzer"),
    path("api/activity-log/", include("apps.activity_log.api.urls"), name="activity_log"),
    path("api/crm-hub/", include("apps.crm_hub.api.urls"), name="crm_hub"),
    path("api/ai-support/", include("apps.ai_support.api.urls"), name="ai-support"),
    path("api/file-to-text/", include("apps.file_to_text.api.urls"), name="file_to_text"),
    path("api/case/", include("apps.case.api.urls"), name="case"),
]

if settings.DEBUG or settings.TESTING:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns.extend(
        [
            # path("material-admin/", include("admin_material.urls")),
            # path("admin/", admin.site.urls),
            path("api/drf-auth/", include("rest_framework.urls")),
            path("api/schema/download/", SpectacularAPIView.as_view(), name="schema"),
            path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
            path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
        ]
    )

urlpatterns += [re_path(r"^i18n/", include("django.conf.urls.i18n"))]

# if settings.DEBUG:
# urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]
urlpatterns += i18n_patterns(re_path(r"^taino/admin/", admin.site.urls))
# else:
#     urlpatterns += i18n_patterns(re_path(r"^taino/admin/", admin.site.urls))
