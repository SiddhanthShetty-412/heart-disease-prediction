# Heart Disease Prediction – Django REST API

A production-ready Django REST backend that serves an **Artificial Neural Network (ANN)**  
trained on the UCI Heart-Statlog dataset to predict the likelihood of heart disease.

---

## Project Structure

```
heart_disease_api/
├── heart_disease_api/          # Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── predictor/                  # Core app
│   ├── management/
│   │   └── commands/
│   │       └── train_model.py  # `python manage.py train_model`
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── ml_model.py             # Singleton model loader & predict()
│   ├── models.py               # PredictionRecord DB model
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── model_artifacts/            # Auto-created by train_model
│   ├── ann_model.keras
│   └── scaler.joblib
├── manage.py
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Create & activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply database migrations

```bash
python manage.py migrate
```

### 4. Train the ANN model

This fetches the Heart-Statlog dataset from OpenML, trains the ANN, and saves  
`model_artifacts/ann_model.keras` and `model_artifacts/scaler.joblib`.

```bash
python manage.py train_model
```

Optional flags:

```bash
python manage.py train_model --epochs 300 --batch 32 --test-size 0.25
```

### 5. Start the development server

```bash
python manage.py runserver
```

The API is now live at `http://127.0.0.1:8000/`.

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/predict/` | Run a heart-disease prediction |
| `GET`  | `/api/predictions/` | List all past predictions |
| `GET`  | `/api/predictions/<id>/` | Retrieve one prediction record |
| `GET`  | `/api/health/` | Liveness + model-load check |
| `GET`  | `/api/model-info/` | Feature metadata for frontend forms |

---

## POST /api/predict/

### Request

```json
{
    "age": 52,
    "gender": 1,
    "chest_pain": 0,
    "rest_bps": 125,
    "cholestrol": 212,
    "fasting_blood_sugar": 0,
    "rest_ecg": 1,
    "thalach": 168,
    "exer_angina": 0,
    "old_peak": 1.0,
    "slope": 2,
    "ca": 2,
    "thalassemia": 3
}
```

### Field Reference

| Field | Description | Range |
|-------|-------------|-------|
| `age` | Age in years | 1–120 |
| `gender` | 0 = Female, 1 = Male | 0–1 |
| `chest_pain` | 0=Typical Angina, 1=Atypical, 2=Non-anginal, 3=Asymptomatic | 0–3 |
| `rest_bps` | Resting blood pressure (mm Hg) | 50–300 |
| `cholestrol` | Serum cholesterol (mg/dl) | 100–600 |
| `fasting_blood_sugar` | Fasting BS > 120 mg/dl: 1=Yes, 0=No | 0–1 |
| `rest_ecg` | 0=Normal, 1=ST-T abnormality, 2=LV hypertrophy | 0–2 |
| `thalach` | Maximum heart rate achieved | 60–250 |
| `exer_angina` | Exercise-induced angina: 1=Yes, 0=No | 0–1 |
| `old_peak` | ST depression (exercise vs rest) | 0.0–10.0 |
| `slope` | 0=Upsloping, 1=Flat, 2=Downsloping | 0–2 |
| `ca` | Major vessels coloured by fluoroscopy | 0–4 |
| `thalassemia` | 3=Normal, 6=Fixed defect, 7=Reversible defect | 0–7 |

### Response (200 OK)

```json
{
    "prediction": "Heart Disease Detected",
    "probability": 0.873412,
    "record_id": 1
}
```

---

## GET /api/predictions/

Returns the full prediction history (most recent first).

Optional query parameters:
- `?limit=10` — cap results
- `?prediction=true` or `?prediction=false` — filter by outcome

---

## GET /api/health/

```json
{
    "status": "ok",
    "model": "ok"
}
```

---

## GET /api/model-info/

Returns JSON with feature names, types, ranges and option labels — useful  
for building dynamic frontend forms without hardcoding metadata.

---

## Django Admin

Create a superuser then visit `http://127.0.0.1:8000/admin/` to browse  
and filter all prediction records through the built-in admin interface.

```bash
python manage.py createsuperuser
```

---

## ANN Architecture

```
Input  (13 features)
  ↓
Dense(64, relu) → BatchNorm → Dropout(0.3)
  ↓
Dense(32, relu) → BatchNorm → Dropout(0.2)
  ↓
Dense(16, relu)
  ↓
Dense(1, sigmoid)   →   P(heart disease)
```

Trained with:
- Optimiser: Adam (lr=0.001)
- Loss: Binary cross-entropy
- Early stopping: patience=20, restores best weights

---

## Example cURL Requests

```bash
# Predict
curl -X POST http://127.0.0.1:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"age":52,"gender":1,"chest_pain":0,"rest_bps":125,"cholestrol":212,
       "fasting_blood_sugar":0,"rest_ecg":1,"thalach":168,"exer_angina":0,
       "old_peak":1.0,"slope":2,"ca":2,"thalassemia":3}'

# Health check
curl http://127.0.0.1:8000/api/health/

# Prediction history (last 5, disease-positive only)
curl "http://127.0.0.1:8000/api/predictions/?limit=5&prediction=true"
```

---

## Production Notes

- Set `SECRET_KEY` via environment variable and `DEBUG=False`  
- Replace SQLite with PostgreSQL (`psycopg2-binary`)  
- Serve with **Gunicorn** + **Nginx**  
- Lock down `CORS_ALLOWED_ORIGINS` to your frontend domain  
- Consider model versioning (MLflow / DVC) for tracking retrained models  
