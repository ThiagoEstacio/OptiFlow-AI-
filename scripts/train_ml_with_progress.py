#!/usr/bin/env python3
"""
Train ML Models with Progress Tracking
Trains both Isolation Forest and LSTM Autoencoder with detailed progress updates
"""

import os
import sys
import time
from datetime import datetime

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("=" * 80)
print("🚀 OPTIFLOW ML TRAINING - ISOLATION FOREST + LSTM AUTOENCODER")
print("=" * 80)
print()

# ========================================
# IMPORTS
# ========================================
print("[1/10] Loading libraries...")
start_time = time.time()

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from influxdb_client import InfluxDBClient

print(f"  ✓ Basic libraries loaded ({time.time() - start_time:.1f}s)")

print("  Loading TensorFlow...")
tf_start = time.time()
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
print(f"  ✓ TensorFlow {tf.__version__} loaded ({time.time() - tf_start:.1f}s)")
print(f"[1/10] Complete ({time.time() - start_time:.1f}s total)")
print()

# ========================================
# CONFIGURATION
# ========================================
print("[2/10] Configuration...")

MODEL_DIR = "/app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

ISOLATION_FOREST_PATH = f"{MODEL_DIR}/isolation_forest_full.joblib"
LSTM_MODEL_PATH = f"{MODEL_DIR}/lstm_autoencoder.h5"
SCALER_PATH = f"{MODEL_DIR}/scaler_full.joblib"
METRICS_PATH = f"{MODEL_DIR}/metrics.json"

# InfluxDB
INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = "my-super-secret-influxdb-token"
INFLUX_ORG = "optiflow"
INFLUX_BUCKET = "timeseries"

# Training
TRAIN_SPLIT = 0.8
CONTAMINATION = 0.015
LSTM_SEQUENCE_LENGTH = 60
LSTM_EPOCHS = 50
LSTM_BATCH_SIZE = 32

TAG_MAPPING = {
    "Motor 01 - Corrente": "MOTOR_01_CURRENT",
    "Motor 01 - Velocidade": "MOTOR_01_SPEED",
    "Motor 01 - Vibração": "MOTOR_01_VIBRATION",
    "Temperatura - Área Produção": "TEMP_SENSOR_01",
    "Temperatura - Caldeira": "TEMP_SENSOR_02",
    "Pressão - Linha Principal": "PRESSURE_01",
    "Pressão - Caldeira": "PRESSURE_02",
    "Nível - Tanque Água": "LEVEL_TANK_01",
    "Consumo Energético Total": "POWER_CONSUMPTION",
    "Taxa de Produção": "PRODUCTION_RATE",
}

TAGS_ORDER = list(TAG_MAPPING.values())

print(f"  Model directory: {MODEL_DIR}")
print(f"  InfluxDB: {INFLUX_URL}")
print(f"  Bucket: {INFLUX_BUCKET}")
print(f"  Features: {len(TAGS_ORDER)} tags")
print(f"  LSTM sequence length: {LSTM_SEQUENCE_LENGTH}")
print(f"  LSTM epochs: {LSTM_EPOCHS}")
print("[2/10] Complete")
print()

# ========================================
# LOAD DATA
# ========================================
print("[3/10] Loading data from InfluxDB...")
data_start = time.time()

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "tag_values")
  |> filter(fn: (r) => r["_field"] == "value")
  |> pivot(rowKey:["_time"], columnKey: ["tag_name"], valueColumn: "_value")
'''

print("  Executing query (this may take 30-60 seconds)...")
result = query_api.query_data_frame(query)

if isinstance(result, list):
    if len(result) == 0:
        raise ValueError("No data found!")
    df = pd.concat(result, ignore_index=True)
else:
    df = result

print(f"  ✓ Loaded {len(df):,} data points")
print(f"  Date range: {df['_time'].min()} to {df['_time'].max()}")
print(f"[3/10] Complete ({time.time() - data_start:.1f}s)")
print()

# ========================================
# PREPARE DATA
# ========================================
print("[4/10] Preparing data...")
prep_start = time.time()

# Rename columns
df = df.rename(columns=TAG_MAPPING)

# Check for anomaly labels
has_labels = 'is_anomaly' in df.columns
if has_labels:
    y = df['is_anomaly'].replace({'true': 1, 'false': 0, True: 1, False: 0}).fillna(0).astype(int).values
    print(f"  ✓ Found anomaly labels: {y.sum():,} anomalies ({100*y.mean():.2f}%)")
else:
    y = None
    print("  ⚠ No anomaly labels found")

# Extract features
feature_cols = [col for col in TAGS_ORDER if col in df.columns]
X = df[feature_cols].fillna(0).values

print(f"  Features: {feature_cols}")
print(f"  Shape: {X.shape}")
print(f"  Memory: {X.nbytes / 1024 / 1024:.1f} MB")

# Train/validation split
split_idx = int(len(X) * TRAIN_SPLIT)
X_train, X_val = X[:split_idx], X[split_idx:]
if y is not None:
    y_train, y_val = y[:split_idx], y[split_idx:]
else:
    y_train, y_val = None, None

print(f"  Train: {len(X_train):,} samples")
print(f"  Validation: {len(X_val):,} samples")
print(f"[4/10] Complete ({time.time() - prep_start:.1f}s)")
print()

# ========================================
# SCALE DATA
# ========================================
print("[5/10] Scaling features...")
scale_start = time.time()

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)

print(f"  ✓ StandardScaler fitted")
print(f"  Mean: {scaler.mean_[:3]}...")
print(f"  Std: {scaler.scale_[:3]}...")
print(f"[5/10] Complete ({time.time() - scale_start:.1f}s)")
print()

# ========================================
# TRAIN ISOLATION FOREST
# ========================================
print("[6/10] Training Isolation Forest...")
iso_start = time.time()

iso_model = IsolationForest(
    contamination=CONTAMINATION,
    n_estimators=100,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

print(f"  Contamination: {CONTAMINATION}")
print(f"  Estimators: 100")
print("  Training...")

iso_model.fit(X_train_scaled)

print(f"  ✓ Training complete")

# Evaluate
iso_pred_train = iso_model.predict(X_train_scaled)
iso_pred_val = iso_model.predict(X_val_scaled)

iso_metrics = {
    "model": "isolation_forest",
    "trained_at": datetime.now().isoformat(),
    "train_samples": len(X_train),
    "val_samples": len(X_val),
    "n_features": len(feature_cols),
}

if y_train is not None:
    train_anomalies = (iso_pred_train == -1)
    precision_train = precision_score(y_train, train_anomalies, zero_division=0)
    recall_train = recall_score(y_train, train_anomalies, zero_division=0)
    f1_train = f1_score(y_train, train_anomalies, zero_division=0)
    
    val_anomalies = (iso_pred_val == -1)
    precision_val = precision_score(y_val, val_anomalies, zero_division=0)
    recall_val = recall_score(y_val, val_anomalies, zero_division=0)
    f1_val = f1_score(y_val, val_anomalies, zero_division=0)
    
    iso_metrics.update({
        "train_precision": round(precision_train, 4),
        "train_recall": round(recall_train, 4),
        "train_f1": round(f1_train, 4),
        "val_precision": round(precision_val, 4),
        "val_recall": round(recall_val, 4),
        "val_f1": round(f1_val, 4),
    })
    
    print(f"  Train - Precision: {precision_train:.4f}, Recall: {recall_train:.4f}, F1: {f1_train:.4f}")
    print(f"  Val   - Precision: {precision_val:.4f}, Recall: {recall_val:.4f}, F1: {f1_val:.4f}")

# Save
joblib.dump(iso_model, ISOLATION_FOREST_PATH)
joblib.dump(scaler, SCALER_PATH)
print(f"  ✓ Saved to {ISOLATION_FOREST_PATH}")

print(f"[6/10] Complete ({time.time() - iso_start:.1f}s)")
print()

# ========================================
# PREPARE SEQUENCES FOR LSTM
# ========================================
print("[7/10] Preparing sequences for LSTM...")
seq_start = time.time()

def create_sequences(data, seq_length):
    sequences = []
    for i in range(len(data) - seq_length):
        sequences.append(data[i:i+seq_length])
    return np.array(sequences)

X_train_seq = create_sequences(X_train_scaled, LSTM_SEQUENCE_LENGTH)
X_val_seq = create_sequences(X_val_scaled, LSTM_SEQUENCE_LENGTH)

print(f"  Train sequences: {X_train_seq.shape}")
print(f"  Val sequences: {X_val_seq.shape}")
print(f"  Memory: {(X_train_seq.nbytes + X_val_seq.nbytes) / 1024 / 1024:.1f} MB")
print(f"[7/10] Complete ({time.time() - seq_start:.1f}s)")
print()

# ========================================
# CREATE LSTM MODEL
# ========================================
print("[8/10] Creating LSTM Autoencoder architecture...")
arch_start = time.time()

n_features = X_train_scaled.shape[1]

model = keras.Sequential([
    # Encoder
    layers.LSTM(64, activation='relu', input_shape=(LSTM_SEQUENCE_LENGTH, n_features), return_sequences=True),
    layers.Dropout(0.2),
    layers.LSTM(32, activation='relu', return_sequences=False),
    layers.Dropout(0.2),
    layers.RepeatVector(LSTM_SEQUENCE_LENGTH),
    
    # Decoder
    layers.LSTM(32, activation='relu', return_sequences=True),
    layers.Dropout(0.2),
    layers.LSTM(64, activation='relu', return_sequences=True),
    layers.Dropout(0.2),
    layers.TimeDistributed(layers.Dense(n_features))
])

model.compile(optimizer='adam', loss='mse')

print("  Architecture:")
print("  Encoder: LSTM(64) → Dropout(0.2) → LSTM(32) → RepeatVector")
print("  Decoder: LSTM(32) → Dropout(0.2) → LSTM(64) → Dense")
print(f"  Total parameters: {model.count_params():,}")
print(f"[8/10] Complete ({time.time() - arch_start:.1f}s)")
print()

# ========================================
# TRAIN LSTM
# ========================================
print(f"[9/10] Training LSTM Autoencoder ({LSTM_EPOCHS} epochs)...")
lstm_start = time.time()

print("  This will take 15-30 minutes depending on CPU...")
print()

history = model.fit(
    X_train_seq, X_train_seq,
    epochs=LSTM_EPOCHS,
    batch_size=LSTM_BATCH_SIZE,
    validation_data=(X_val_seq, X_val_seq),
    verbose=1
)

print()
print(f"  ✓ Training complete")
print(f"  Final train loss: {history.history['loss'][-1]:.6f}")
print(f"  Final val loss: {history.history['val_loss'][-1]:.6f}")

# Evaluate anomaly detection
X_val_pred = model.predict(X_val_seq, verbose=0)
mse = np.mean(np.power(X_val_seq - X_val_pred, 2), axis=(1, 2))
threshold = np.percentile(mse, 98.5)  # Top 1.5% as anomalies

lstm_anomalies = (mse > threshold)

lstm_metrics = {
    "model": "lstm_autoencoder",
    "trained_at": datetime.now().isoformat(),
    "train_samples": len(X_train_seq),
    "val_samples": len(X_val_seq),
    "n_features": n_features,
    "sequence_length": LSTM_SEQUENCE_LENGTH,
    "epochs": LSTM_EPOCHS,
    "final_train_loss": float(history.history['loss'][-1]),
    "final_val_loss": float(history.history['val_loss'][-1]),
    "threshold": float(threshold),
}

if y_val is not None:
    y_val_seq = y_val[LSTM_SEQUENCE_LENGTH:]
    precision = precision_score(y_val_seq, lstm_anomalies, zero_division=0)
    recall = recall_score(y_val_seq, lstm_anomalies, zero_division=0)
    f1 = f1_score(y_val_seq, lstm_anomalies, zero_division=0)
    
    lstm_metrics.update({
        "val_precision": round(precision, 4),
        "val_recall": round(recall, 4),
        "val_f1": round(f1, 4),
    })
    
    print(f"  Val - Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")

# Save
model.save(LSTM_MODEL_PATH)
print(f"  ✓ Saved to {LSTM_MODEL_PATH}")

print(f"[9/10] Complete ({time.time() - lstm_start:.1f}s)")
print()

# ========================================
# SAVE METRICS
# ========================================
print("[10/10] Saving metrics...")

import json
metrics = {
    "isolation_forest": iso_metrics,
    "lstm_autoencoder": lstm_metrics,
    "training_completed_at": datetime.now().isoformat(),
    "total_time_seconds": int(time.time() - start_time),
}

with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

print(f"  ✓ Saved to {METRICS_PATH}")
print("[10/10] Complete")
print()

# ========================================
# SUMMARY
# ========================================
print("=" * 80)
print("✅ TRAINING COMPLETE")
print("=" * 80)
print()
print("📊 RESULTS SUMMARY:")
print()
print("Isolation Forest:")
if 'val_f1' in iso_metrics:
    print(f"  F1-Score: {iso_metrics['val_f1']:.4f}")
    print(f"  Precision: {iso_metrics['val_precision']:.4f}")
    print(f"  Recall: {iso_metrics['val_recall']:.4f}")
print(f"  Model: {ISOLATION_FOREST_PATH}")
print()
print("LSTM Autoencoder:")
if 'val_f1' in lstm_metrics:
    print(f"  F1-Score: {lstm_metrics['val_f1']:.4f}")
    print(f"  Precision: {lstm_metrics['val_precision']:.4f}")
    print(f"  Recall: {lstm_metrics['val_recall']:.4f}")
print(f"  Val Loss: {lstm_metrics['final_val_loss']:.6f}")
print(f"  Model: {LSTM_MODEL_PATH}")
print()
print(f"⏱️  Total time: {int(time.time() - start_time)} seconds ({(time.time() - start_time)/60:.1f} minutes)")
print()
print("🎯 Next steps:")
print("  1. Update API to support model selection (isolation_forest / lstm)")
print("  2. Compare models on frontend visualization")
print("  3. Integrate best model with Agent context")
print()
print("=" * 80)
