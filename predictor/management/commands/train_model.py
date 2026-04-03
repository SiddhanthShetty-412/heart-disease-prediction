"""
python manage.py train_model

Trains the ANN on the UCI Heart-Statlog dataset (fetched via sklearn),
then saves:
  - model_artifacts/ann_model.keras
  - model_artifacts/scaler.joblib

Options
-------
--epochs INT        maximum training epochs  (default 200)
--batch  INT        batch size               (default 16)
--test-size FLOAT   fraction held for test   (default 0.20)
"""

import os
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train the ANN heart-disease model and save artefacts to model_artifacts/'

    def add_arguments(self, parser):
        parser.add_argument('--epochs',     type=int,   default=200)
        parser.add_argument('--batch',      type=int,   default=16)
        parser.add_argument('--test-size',  type=float, default=0.20)

    def handle(self, *args, **options):
        self.stdout.write('── Heart Disease ANN – Training ──')

        # ── 1. Imports ────────────────────────────────────────────────────────
        try:
            import tensorflow as tf
            import keras
            from keras.models import Sequential
            from keras.layers import Dense, Dropout, BatchNormalization
            from keras.callbacks import EarlyStopping
            from sklearn.datasets import fetch_openml
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
            import joblib
        except ImportError as e:
            raise CommandError(f'Missing dependency: {e}. Install requirements first.')

        np.random.seed(42)
        tf.random.set_seed(42)

        # ── 2. Load dataset ───────────────────────────────────────────────────
        self.stdout.write('Fetching Heart-Statlog dataset …')
        heart = fetch_openml(name='heart-statlog', version=1, as_frame=True)
        df_raw = heart.frame

        col_map = {
            'age': 'age',
            'sex': 'gender',
            'chest': 'chest_pain',
            'resting_blood_pressure': 'rest_bps',
            'serum_cholestoral': 'cholestrol',
            'fasting_blood_sugar': 'fasting_blood_sugar',
            'resting_electrocardiographic_results': 'rest_ecg',
            'maximum_heart_rate_achieved': 'thalach',
            'exercise_induced_angina': 'exer_angina',
            'oldpeak': 'old_peak',
            'slope': 'slope',
            'number_of_major_vessels': 'ca',
            'thal': 'thalassemia',
            'class': 'target',
        }
        df = df_raw.rename(columns={k: v for k, v in col_map.items() if k in df_raw.columns})

        for col in df.columns:
            if df[col].dtype.name in ['category', 'object', 'bool']:
                df[col] = pd.Categorical(df[col]).codes

        df['target'] = (df['target'] > 0).astype(int)
        self.stdout.write(f'Dataset shape: {df.shape}')

        # ── 3. Split & scale ──────────────────────────────────────────────────
        feature_cols = [c for c in df.columns if c != 'target']
        X = df[feature_cols]
        y = df['target']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=options['test_size'], random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc  = scaler.transform(X_test)

        self.stdout.write(f'Train: {X_train_sc.shape[0]}  Test: {X_test_sc.shape[0]}')

        # ── 4. Build model ────────────────────────────────────────────────────
        n_features = X_train_sc.shape[1]
        model = Sequential([
            Dense(64, activation='relu', input_shape=(n_features,)),
            BatchNormalization(),
            Dropout(0.3),

            Dense(32, activation='relu'),
            BatchNormalization(),
            Dropout(0.2),

            Dense(16, activation='relu'),

            Dense(1, activation='sigmoid'),
        ])

        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy'],
        )
        model.summary(print_fn=lambda x: self.stdout.write(x))

        # ── 5. Train ──────────────────────────────────────────────────────────
        early_stop = EarlyStopping(
            monitor='val_loss', patience=20, restore_best_weights=True
        )

        self.stdout.write(f'Training for up to {options["epochs"]} epochs …')
        history = model.fit(
            X_train_sc, y_train,
            epochs=options['epochs'],
            batch_size=options['batch'],
            validation_split=0.15,
            callbacks=[early_stop],
            verbose=0,
        )

        epochs_run = len(history.history['loss'])
        self.stdout.write(f'Stopped after {epochs_run} epochs.')

        # ── 6. Evaluate ───────────────────────────────────────────────────────
        y_prob = model.predict(X_test_sc, verbose=0).flatten()
        y_pred = (y_prob >= 0.5).astype(int)

        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        self.stdout.write(self.style.SUCCESS(f'Test Accuracy : {acc:.4f}'))
        self.stdout.write(self.style.SUCCESS(f'ROC-AUC Score : {auc:.4f}'))
        self.stdout.write(classification_report(y_test, y_pred,
                                                target_names=['No Disease', 'Disease']))

        # ── 7. Save artefacts ─────────────────────────────────────────────────
        model_dir = settings.MODEL_DIR
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path  = model_dir / 'ann_model.keras'
        scaler_path = model_dir / 'scaler.joblib'

        model.save(str(model_path))
        joblib.dump(scaler, str(scaler_path))

        self.stdout.write(self.style.SUCCESS(f'Model  saved → {model_path}'))
        self.stdout.write(self.style.SUCCESS(f'Scaler saved → {scaler_path}'))
        self.stdout.write(self.style.SUCCESS('Training complete ✓'))
