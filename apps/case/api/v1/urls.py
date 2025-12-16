from rest_framework.routers import DefaultRouter
from apps.case.api.v1.views import (
    CaseViewSet,
    SessionViewSet,
    AssessmentViewSet,
    TreatmentPlanViewSet,
    DailyLogViewSet,
    CaseDocumentViewSet,
    CaseReportViewSet,
)

app_name = "case"

router = DefaultRouter()
router.register("cases", CaseViewSet, basename="case")
router.register("sessions", SessionViewSet, basename="session")
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("treatment-plans", TreatmentPlanViewSet, basename="treatment-plan")
router.register("daily-logs", DailyLogViewSet, basename="daily-log")
router.register("documents", CaseDocumentViewSet, basename="document")
router.register("reports", CaseReportViewSet, basename="report")

urlpatterns = []

urlpatterns += router.urls
