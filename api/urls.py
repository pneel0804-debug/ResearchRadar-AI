from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    PaperViewSet, ResearchGapViewSet, ProjectIdeaViewSet,
    LiteratureReviewViewSet, ExperimentalPlanViewSet
)

router = DefaultRouter()
router.register(r'papers', PaperViewSet, basename='paper')
router.register(r'gaps', ResearchGapViewSet, basename='gap')
router.register(r'ideas', ProjectIdeaViewSet, basename='idea')
router.register(r'literature', LiteratureReviewViewSet, basename='literature')
router.register(r'experiments', ExperimentalPlanViewSet, basename='experiment')

urlpatterns = [
    path('', include(router.urls)),
]
