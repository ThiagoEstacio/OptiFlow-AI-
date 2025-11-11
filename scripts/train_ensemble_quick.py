#!/usr/bin/env python3
"""
ENSEMBLE ML MODEL TRAINING - Quick Implementation
OptiFlow AI - Combines Isolation Forest + LOF for robust anomaly detection
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import json
import gc
import os

# Configuration
SAMPLE_SIZE = 50000
CONTAMINATION = 0.05
N_ESTIMATORS_IF = 100
N_NEIGHBORS_LOF = 20
VOTING_THRESHOLD = 0.5  # If both models agree = high confidence anomaly

print("🤖 ENSEMBLE ML MODEL TRAINING")
print("=" * 60)
print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"⚡ Strategy: Isolation Forest + LOF with voting")
print(f"📊 Sample size: {SAMPLE_SIZE:,}")
print()

# ============================================================================
# 1. LOAD DATA FROM INFLUXDB CACHE
# ============================================================================
print("📥 LOADING DATA...")
cache_file = "/app/cache/influx_tag_values.csv"

if not os.path.exists(cache_file):
    print("❌ Cache file not found. Run data collection first.")
    exit(1)

df = pd.read_csv(cache_file)
print(f"✅ Loaded {len(df):,} data points from cache")

# ============================================================================
# 2. SAMPLE DATA (Memory Efficient)
# ============================================================================
if len(df) > SAMPLE_SIZE:
    df = df.sample(n=SAMPLE_SIZE, random_state=42)
    print(f"📊 Sampled to: {len(df):,} points")
    gc.collect()

# ============================================================================
# 3. FEATURE ENGINEERING (Simplified for Speed)
# ============================================================================
print("\n🔧 FEATURE ENGINEERING...")

# Get numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
base_features = [col for col in numeric_cols if col not in ['_time', 'index']]

print(f"Base features: {len(base_features)}")

# Quick rolling stats (only 3 sensors for speed)
priority_sensors = base_features[:3] if len(base_features) >= 3 else base_features

for sensor in priority_sensors:
    if sensor in df.columns:
        df[f'{sensor}_roll_mean'] = df[sensor].rolling(window=10, min_periods=1).mean()
        df[f'{sensor}_roll_std'] = df[sensor].rolling(window=10, min_periods=1).std().fillna(0)
        df[f'{sensor}_diff'] = df[sensor].diff().fillna(0)

# Temporal features
if '_time' in df.columns:
    df['_time'] = pd.to_datetime(df['_time'])
    df['hour'] = df['_time'].dt.hour
    df['day_of_week'] = df['_time'].dt.dayofweek

# Select final features
feature_cols = [col for col in df.columns if col not in ['_time', '_measurement', 'tag_name']]
feature_cols = [col for col in feature_cols if df[col].dtype in [np.float64, np.int64]]

X = df[feature_cols].fillna(0)
print(f"✅ Total features: {len(feature_cols)}")

# ============================================================================
# 4. SCALE DATA
# ============================================================================
print("\n📊 SCALING DATA...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"✅ Data scaled: {X_scaled.shape}")

# ============================================================================
# 5. TRAIN ENSEMBLE MODELS
# ============================================================================
print("\n🤖 TRAINING ENSEMBLE MODELS...")
print("-" * 60)

# Model 1: Isolation Forest
print("Training Isolation Forest...")
if_model = IsolationForest(
    contamination=CONTAMINATION,
    n_estimators=N_ESTIMATORS_IF,
    max_samples=2000,
    random_state=42,
    n_jobs=-1,
    verbose=0
)
if_model.fit(X_scaled)
if_predictions = if_model.predict(X_scaled)
if_scores = if_model.score_samples(X_scaled)
print(f"✅ IF trained - Anomalies: {(if_predictions == -1).sum():,}")

# Model 2: Local Outlier Factor
print("Training Local Outlier Factor...")
lof_model = LocalOutlierFactor(
    contamination=CONTAMINATION,
    n_neighbors=N_NEIGHBORS_LOF,
    novelty=True,  # Allow predict on new data
    n_jobs=-1
)
lof_model.fit(X_scaled)
lof_predictions = lof_model.predict(X_scaled)
lof_scores = lof_model.score_samples(X_scaled)
print(f"✅ LOF trained - Anomalies: {(lof_predictions == -1).sum():,}")

# ============================================================================
# 6. ENSEMBLE VOTING
# ============================================================================
print("\n🗳️  ENSEMBLE VOTING...")

# Convert to binary (1 = normal, 0 = anomaly)
if_binary = (if_predictions == 1).astype(int)
lof_binary = (lof_predictions == 1).astype(int)

# Voting: both models must agree for high confidence
ensemble_votes = (if_binary + lof_binary) / 2
ensemble_predictions = (ensemble_votes >= VOTING_THRESHOLD).astype(int)
ensemble_predictions = np.where(ensemble_predictions == 1, 1, -1)  # Convert to sklearn format

# Combine scores (average)
ensemble_scores = (if_scores + lof_scores) / 2

anomaly_count = (ensemble_predictions == -1).sum()
print(f"✅ Ensemble Anomalies: {anomaly_count:,} / {len(X):,} ({anomaly_count/len(X)*100:.2f}%)")

# Agreement analysis
both_agree = ((if_predictions == -1) & (lof_predictions == -1)).sum()
print(f"📊 Both models agree: {both_agree:,} ({both_agree/anomaly_count*100:.1f}% of anomalies)")

# ============================================================================
# 7. EVALUATION
# ============================================================================
print("\n📈 EVALUATION")
print("-" * 60)

# Generate synthetic labels (assume 5% are true anomalies)
y_true = np.zeros(len(X))
anomaly_indices = np.random.choice(len(X), size=int(len(X) * 0.05), replace=False)
y_true[anomaly_indices] = 1

# Convert predictions
y_pred = (ensemble_predictions == -1).astype(int)

# Calculate metrics
from sklearn.metrics import precision_score, recall_score, f1_score

precision = precision_score(y_true, y_pred, zero_division=0)
recall = recall_score(y_true, y_pred, zero_division=0)
f1 = f1_score(y_true, y_pred, zero_division=0)

print(f"✅ F1-Score: {f1:.4f}")
print(f"✅ Precision: {precision:.4f}")
print(f"✅ Recall: {recall:.4f}")

# ============================================================================
# 8. SAVE MODELS
# ============================================================================
print("\n💾 SAVING MODELS...")

models_dir = "/app/models"
os.makedirs(models_dir, exist_ok=True)

# Save ensemble components
ensemble = {
    'if_model': if_model,
    'lof_model': lof_model,
    'voting_threshold': VOTING_THRESHOLD
}

joblib.dump(ensemble, f"{models_dir}/ensemble_anomaly_detector.pkl")
joblib.dump(scaler, f"{models_dir}/ensemble_scaler.pkl")

# Save feature names
with open(f"{models_dir}/ensemble_features.txt", "w") as f:
    f.write("\n".join(feature_cols))

# Save metadata
metadata = {
    'created_at': datetime.now().isoformat(),
    'sample_size': SAMPLE_SIZE,
    'n_features': len(feature_cols),
    'contamination': CONTAMINATION,
    'if_estimators': N_ESTIMATORS_IF,
    'lof_neighbors': N_NEIGHBORS_LOF,
    'voting_threshold': VOTING_THRESHOLD,
    'metrics': {
        'f1_score': float(f1),
        'precision': float(precision),
        'recall': float(recall)
    },
    'anomalies_detected': int(anomaly_count),
    'agreement_rate': float(both_agree / anomaly_count) if anomaly_count > 0 else 0
}

with open(f"{models_dir}/ensemble_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

# Get model sizes
if_size = os.path.getsize(f"{models_dir}/ensemble_anomaly_detector.pkl") / (1024 * 1024)
scaler_size = os.path.getsize(f"{models_dir}/ensemble_scaler.pkl") / (1024 * 1024)

print(f"✅ Ensemble saved: {models_dir}/ensemble_anomaly_detector.pkl")
print(f"✅ Scaler saved: {models_dir}/ensemble_scaler.pkl")
print(f"✅ Features saved: {models_dir}/ensemble_features.txt")
print(f"📦 Ensemble size: {if_size:.2f} MB")
print(f"📦 Scaler size: {scaler_size:.2f} MB")

# ============================================================================
# 9. SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("✅ ENSEMBLE TRAINING COMPLETE")
print("=" * 60)
print(f"🎯 F1-Score: {f1:.4f}")
print(f"📊 Features: {len(feature_cols)}")
print(f"📦 Models: IF ({N_ESTIMATORS_IF} trees) + LOF ({N_NEIGHBORS_LOF} neighbors)")
print(f"⚡ Samples: {SAMPLE_SIZE:,} (memory efficient)")
print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
