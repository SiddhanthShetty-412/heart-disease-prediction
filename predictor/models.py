from django.db import models


class PredictionRecord(models.Model):
    """Stores every prediction request and its result for auditing / history."""

    # ── Input features ──────────────────────────────────────────────────────
    age = models.PositiveIntegerField()
    gender = models.IntegerField(help_text='0 = Female, 1 = Male')
    chest_pain = models.IntegerField(
        help_text='0=typical angina, 1=atypical angina, 2=non-anginal, 3=asymptomatic'
    )
    rest_bps = models.PositiveIntegerField(help_text='Resting blood pressure (mm Hg)')
    cholestrol = models.PositiveIntegerField(help_text='Serum cholesterol (mg/dl)')
    fasting_blood_sugar = models.IntegerField(help_text='1 = fasting BS > 120 mg/dl, else 0')
    rest_ecg = models.IntegerField(
        help_text='0=normal, 1=ST-T wave abnormality, 2=left ventricular hypertrophy'
    )
    thalach = models.PositiveIntegerField(help_text='Maximum heart rate achieved')
    exer_angina = models.IntegerField(help_text='Exercise-induced angina: 1=yes, 0=no')
    old_peak = models.FloatField(help_text='ST depression induced by exercise relative to rest')
    slope = models.IntegerField(help_text='Slope of peak exercise ST segment: 0/1/2')
    ca = models.IntegerField(help_text='Number of major vessels (0–3) coloured by fluoroscopy')
    thalassemia = models.IntegerField(help_text='3=normal, 6=fixed defect, 7=reversible defect')

    # ── Output ───────────────────────────────────────────────────────────────
    probability = models.FloatField()
    prediction = models.BooleanField(help_text='True = Heart Disease Detected')

    # ── Metadata ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        label = 'Disease' if self.prediction else 'No Disease'
        return f'[{self.created_at:%Y-%m-%d %H:%M}] Age {self.age} → {label} ({self.probability:.2%})'
