from django.urls import path
from .views import (
    PredictView,
    PredictionHistoryView,
    PredictionDetailView,
    HealthCheckView,
    ModelInfoView,
)

urlpatterns = [
    # Core prediction
    path('predict/',               PredictView.as_view(),          name='predict'),

    # History / detail
    path('predictions/',           PredictionHistoryView.as_view(), name='prediction-list'),
    path('predictions/<int:pk>/',  PredictionDetailView.as_view(),  name='prediction-detail'),

    # Utility
    path('health/',                HealthCheckView.as_view(),       name='health-check'),
    path('model-info/',            ModelInfoView.as_view(),         name='model-info'),
]
