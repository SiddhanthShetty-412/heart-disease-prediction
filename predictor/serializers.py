from rest_framework import serializers
from .models import PredictionRecord


FEATURE_FIELDS = [
    'age', 'gender', 'chest_pain', 'rest_bps', 'cholestrol',
    'fasting_blood_sugar', 'rest_ecg', 'thalach', 'exer_angina',
    'old_peak', 'slope', 'ca', 'thalassemia',
]


class PredictRequestSerializer(serializers.Serializer):
    """Validates a single-patient prediction request."""
    age                = serializers.IntegerField(min_value=1, max_value=120)
    gender             = serializers.IntegerField(min_value=0, max_value=1)
    chest_pain         = serializers.IntegerField(min_value=0, max_value=3)
    rest_bps           = serializers.IntegerField(min_value=50, max_value=300)
    cholestrol         = serializers.IntegerField(min_value=100, max_value=600)
    fasting_blood_sugar = serializers.IntegerField(min_value=0, max_value=1)
    rest_ecg           = serializers.IntegerField(min_value=0, max_value=2)
    thalach            = serializers.IntegerField(min_value=60, max_value=250)
    exer_angina        = serializers.IntegerField(min_value=0, max_value=1)
    old_peak           = serializers.FloatField(min_value=0.0, max_value=10.0)
    slope              = serializers.IntegerField(min_value=0, max_value=2)
    ca                 = serializers.IntegerField(min_value=0, max_value=4)
    thalassemia        = serializers.IntegerField(min_value=0, max_value=7)

    def to_feature_array(self):
        """Return a list of feature values in training order."""
        data = self.validated_data
        return [data[f] for f in FEATURE_FIELDS]


class PredictResponseSerializer(serializers.Serializer):
    """Shape of a prediction response."""
    prediction  = serializers.CharField()
    probability = serializers.FloatField()
    record_id   = serializers.IntegerField()


class PredictionRecordSerializer(serializers.ModelSerializer):
    """Full DB record serializer for history / detail endpoints."""
    prediction_label = serializers.SerializerMethodField()

    class Meta:
        model = PredictionRecord
        fields = '__all__'

    def get_prediction_label(self, obj):
        return 'Heart Disease Detected' if obj.prediction else 'No Heart Disease'
