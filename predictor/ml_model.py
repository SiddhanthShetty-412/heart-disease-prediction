"""
ml_model.py
-----------
Singleton that loads the Keras ANN model and StandardScaler once at
startup and exposes a simple predict() interface to the views.

Artefacts expected in settings.MODEL_DIR:
  - ann_model.keras   (saved with model.save())
  - scaler.joblib     (saved with joblib.dump(scaler, ...))

Run  `python manage.py train_model`  to generate them from scratch.
"""

import logging
import threading
import numpy as np

logger = logging.getLogger(__name__)

_lock   = threading.Lock()
_model  = None
_scaler = None


def _load_artifacts():
    """Load (or reload) model + scaler from disk."""
    global _model, _scaler

    from django.conf import settings
    import joblib

    model_dir = settings.MODEL_DIR
    model_path  = model_dir / 'ann_model.keras'
    scaler_path = model_dir / 'scaler.joblib'

    if not model_path.exists():
        raise FileNotFoundError(
            f'Model not found at {model_path}. '
            'Run `python manage.py train_model` first.'
        )
    if not scaler_path.exists():
        raise FileNotFoundError(
            f'Scaler not found at {scaler_path}. '
            'Run `python manage.py train_model` first.'
        )

    # Import here so Django can start even without TF installed in CI
    from keras.models import load_model

    _model  = load_model(str(model_path))
    _scaler = joblib.load(str(scaler_path))
    logger.info('ANN model and scaler loaded successfully.')


def get_model_and_scaler():
    """Return (model, scaler), loading them lazily on first call."""
    global _model, _scaler
    if _model is None or _scaler is None:
        with _lock:
            if _model is None or _scaler is None:
                _load_artifacts()
    return _model, _scaler


def predict(feature_list: list) -> dict:
    """
    Run a single-patient prediction.

    Parameters
    ----------
    feature_list : list of 13 numeric values in training-column order:
        [age, gender, chest_pain, rest_bps, cholestrol, fasting_blood_sugar,
         rest_ecg, thalach, exer_angina, old_peak, slope, ca, thalassemia]

    Returns
    -------
    dict with keys:
        probability : float  (0–1)
        prediction  : bool   (True = disease)
        label       : str
    """
    model, scaler = get_model_and_scaler()

    X = np.array([feature_list], dtype=float)
    X_scaled = scaler.transform(X)

    probability = float(model.predict(X_scaled, verbose=0)[0][0])
    prediction  = probability >= 0.5

    return {
        'probability': round(probability, 6),
        'prediction':  prediction,
        'label':       'Heart Disease Detected' if prediction else 'No Heart Disease',
    }
