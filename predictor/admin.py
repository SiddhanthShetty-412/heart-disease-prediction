from django.contrib import admin
from .models import PredictionRecord


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display   = ('id', 'age', 'gender', 'probability', 'prediction', 'created_at')
    list_filter    = ('prediction', 'gender')
    readonly_fields = (
        'age', 'gender', 'chest_pain', 'rest_bps', 'cholestrol',
        'fasting_blood_sugar', 'rest_ecg', 'thalach', 'exer_angina',
        'old_peak', 'slope', 'ca', 'thalassemia',
        'probability', 'prediction', 'created_at',
    )
    ordering       = ('-created_at',)

    def has_add_permission(self, request):
        # Records are created only via POST /api/predict/ — not manually
        return False