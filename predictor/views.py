import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, ListAPIView

from .models import PredictionRecord
from .serializers import (
    PredictRequestSerializer,
    PredictResponseSerializer,
    PredictionRecordSerializer,
)
from . import ml_model

logger = logging.getLogger(__name__)


class PredictView(APIView):
    """
    POST /api/predict/

    Accept patient vitals and return a heart-disease prediction.

    Request body (JSON):
    {
        "age": 52, "gender": 1, "chest_pain": 0, "rest_bps": 125,
        "cholestrol": 212, "fasting_blood_sugar": 0, "rest_ecg": 1,
        "thalach": 168, "exer_angina": 0, "old_peak": 1.0,
        "slope": 2, "ca": 2, "thalassemia": 3
    }

    Response (200):
    {
        "prediction": "Heart Disease Detected",
        "probability": 0.8734,
        "record_id": 1
    }
    """

    def post(self, request):
        req_serializer = PredictRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        features = req_serializer.to_feature_array()

        try:
            result = ml_model.predict(features)
        except FileNotFoundError as exc:
            logger.error('Model artefact missing: %s', exc)
            return Response(
                {'error': str(exc), 'hint': 'Run `python manage.py train_model` to generate artefacts.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as exc:
            logger.exception('Prediction failed')
            return Response({'error': 'Prediction failed.', 'detail': str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Persist record
        data = req_serializer.validated_data
        record = PredictionRecord.objects.create(
            **data,
            probability=result['probability'],
            prediction=result['prediction'],
        )

        resp_serializer = PredictResponseSerializer({
            'prediction':  result['label'],
            'probability': result['probability'],
            'record_id':   record.pk,
        })
        return Response(resp_serializer.data, status=status.HTTP_200_OK)


class PredictionHistoryView(ListAPIView):
    """
    GET /api/predictions/

    Returns all past predictions, most recent first.
    Supports optional query params:
      ?limit=10   — page size
      ?prediction=true|false  — filter by outcome
    """
    serializer_class = PredictionRecordSerializer

    def get_queryset(self):
        qs = PredictionRecord.objects.all()
        prediction_filter = self.request.query_params.get('prediction')
        if prediction_filter is not None:
            qs = qs.filter(prediction=(prediction_filter.lower() == 'true'))
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                qs = qs[:int(limit)]
            except ValueError:
                pass
        return qs


class PredictionDetailView(RetrieveAPIView):
    """
    GET /api/predictions/<id>/

    Returns the full record for a single past prediction.
    """
    queryset = PredictionRecord.objects.all()
    serializer_class = PredictionRecordSerializer


class HealthCheckView(APIView):
    """
    GET /api/health/

    Lightweight liveness probe.  Also verifies model artefacts are loadable.
    """

    def get(self, request):
        try:
            ml_model.get_model_and_scaler()
            model_status = 'ok'
        except FileNotFoundError as exc:
            model_status = f'not_loaded: {exc}'

        return Response({
            'status': 'ok',
            'model': model_status,
        })


class ModelInfoView(APIView):
    """
    GET /api/model-info/

    Returns feature metadata so frontends can build dynamic forms.
    """

    FEATURE_META = [
        {'name': 'age',                 'label': 'Age',                         'type': 'int',   'min': 1,   'max': 120},
        {'name': 'gender',              'label': 'Gender',                       'type': 'int',   'min': 0,   'max': 1,   'options': {0: 'Female', 1: 'Male'}},
        {'name': 'chest_pain',          'label': 'Chest Pain Type',              'type': 'int',   'min': 0,   'max': 3,   'options': {0: 'Typical Angina', 1: 'Atypical Angina', 2: 'Non-Anginal', 3: 'Asymptomatic'}},
        {'name': 'rest_bps',            'label': 'Resting Blood Pressure',       'type': 'int',   'min': 50,  'max': 300, 'unit': 'mm Hg'},
        {'name': 'cholestrol',          'label': 'Serum Cholesterol',            'type': 'int',   'min': 100, 'max': 600, 'unit': 'mg/dl'},
        {'name': 'fasting_blood_sugar', 'label': 'Fasting Blood Sugar > 120 mg/dl', 'type': 'int', 'min': 0, 'max': 1,  'options': {0: 'No', 1: 'Yes'}},
        {'name': 'rest_ecg',            'label': 'Resting ECG Results',          'type': 'int',   'min': 0,   'max': 2,   'options': {0: 'Normal', 1: 'ST-T Wave Abnormality', 2: 'Left Ventricular Hypertrophy'}},
        {'name': 'thalach',             'label': 'Max Heart Rate Achieved',      'type': 'int',   'min': 60,  'max': 250},
        {'name': 'exer_angina',         'label': 'Exercise-Induced Angina',      'type': 'int',   'min': 0,   'max': 1,   'options': {0: 'No', 1: 'Yes'}},
        {'name': 'old_peak',            'label': 'ST Depression (Old Peak)',     'type': 'float', 'min': 0.0, 'max': 10.0},
        {'name': 'slope',               'label': 'Slope of Peak ST Segment',     'type': 'int',   'min': 0,   'max': 2,   'options': {0: 'Upsloping', 1: 'Flat', 2: 'Downsloping'}},
        {'name': 'ca',                  'label': 'Major Vessels (Fluoroscopy)',  'type': 'int',   'min': 0,   'max': 4},
        {'name': 'thalassemia',         'label': 'Thalassemia',                  'type': 'int',   'min': 0,   'max': 7,   'options': {3: 'Normal', 6: 'Fixed Defect', 7: 'Reversible Defect'}},
    ]

    def get(self, request):
        return Response({
            'model':    'ANN – Heart Disease Classifier',
            'features': self.FEATURE_META,
            'output':   {
                'field': 'prediction',
                'values': {'true': 'Heart Disease Detected', 'false': 'No Heart Disease'},
            },
        })
