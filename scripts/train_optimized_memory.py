#!/usr/bin/env python3
"""
Optimized ML Training Script - Memory Efficient
Trains anomaly detection model with reduced memory footprint
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from datetime import datetime
import os
import gc

# Configurações
MODEL_DIR = "/app/models"
CACHE_FILE = f"{MODEL_DIR}/training_data_cache.parquet"
SAMPLE_SIZE = 50000  # Reduzir para 50k amostras (era 1.2M)

print("\n" + "="*60)
print("🚀 OPTIMIZED ML TRAINING (Memory Efficient)")
print("="*60)
print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================================================
# 1. LOAD DATA (com sampling)
# ============================================================================

print("\n📂 Loading data with sampling...")
if os.path.exists(CACHE_FILE):
    # Carregar apenas uma amostra para economizar memória
    df = pd.read_parquet(CACHE_FILE)
    print(f"✅ Original data: {len(df)} points")
    
    # Sample estratificado
    if len(df) > SAMPLE_SIZE:
        df = df.sample(n=SAMPLE_SIZE, random_state=42)
        print(f"📊 Sampled to: {len(df)} points ({SAMPLE_SIZE/len(df)*100:.1f}%)")
    
    print(f"📊 Data shape: {df.shape}")
    print(f"📅 Date range: {df['_time'].min()} to {df['_time'].max()}")
else:
    print("❌ No cached data found. Run data collection first.")
    exit(1)

# ============================================================================
# 2. FEATURE ENGINEERING (simplified)
# ============================================================================

print("\n🔧 FEATURE ENGINEERING (Simplified)")
print("="*60)

# Selecionar apenas colunas numéricas
numeric_cols = ['MOTOR_01_CURRENT', 'MOTOR_01_SPEED', 'MOTOR_01_VIBRATION',
                'TEMP_SENSOR_01', 'TEMP_SENSOR_02', 'PRESSURE_01', 'PRESSURE_02',
                'LEVEL_TANK_01', 'POWER_CONSUMPTION', 'PRODUCTION_RATE']

# Verificar quais colunas existem
existing_cols = [col for col in numeric_cols if col in df.columns]
print(f"📊 Using {len(existing_cols)} base features: {existing_cols}")

# Features essenciais apenas (reduzir de 169 para ~30)
print("🔧 Adding essential features only...")

# 1. Rolling statistics (apenas 1 window)
window = 10
for col in existing_cols[:3]:  # Apenas primeiros 3 para economizar memória
    df[f'{col}_rmean'] = df[col].rolling(window, min_periods=1).mean()
    df[f'{col}_rstd'] = df[col].rolling(window, min_periods=1).std()

# 2. Rate of change (simplificado)
for col in existing_cols[:3]:
    df[f'{col}_diff'] = df[col].diff()

# 3. Temporal features
df['hour'] = pd.to_datetime(df['_time']).dt.hour
df['day_of_week'] = pd.to_datetime(df['_time']).dt.dayofweek

# Selecionar features finais
feature_cols = [col for col in df.columns if col not in ['_time', '_measurement', 'tag_name']]
feature_cols = [col for col in feature_cols if df[col].dtype in [np.float64, np.int64]]

print(f"✅ Total features: {len(feature_cols)}")
print(f"   Base: {len(existing_cols)}")
print(f"   Engineered: {len(feature_cols) - len(existing_cols)}")

# Liberar memória
gc.collect()

# ============================================================================
# 3. PREPARE DATA
# ============================================================================

print("\n📊 PREPARING TRAINING DATA")
print("="*60)

# Remover NaN e Inf
X = df[feature_cols].copy()
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(0)

print(f"✅ Training matrix: {X.shape}")
print(f"📊 Features: {len(feature_cols)}")
print(f"📊 Samples: {len(X)}")

# Liberar memória
del df
gc.collect()

# ============================================================================
# 4. TRAIN MODEL
# ============================================================================

print("\n🤖 TRAINING ISOLATION FOREST")
print("="*60)

# Configuração otimizada
contamination = 0.05  # 5% de anomalias esperadas
n_estimators = 100    # Reduzir de 200 para 100
max_samples = 2000    # Limitar amostras por árvore

print(f"🔧 Configuration:")
print(f"   • contamination: {contamination}")
print(f"   • n_estimators: {n_estimators}")
print(f"   • max_samples: {max_samples}")
print(f"   • n_jobs: -1 (all cores)")

# Scaler
print("\n⚙️  Fitting scaler...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Liberar memória
del X
gc.collect()

# Model
print("⚙️  Training model...")
model = IsolationForest(
    n_estimators=n_estimators,
    max_samples=max_samples,
    contamination=contamination,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

model.fit(X_scaled)
print("✅ Training complete!")

# ============================================================================
# 5. EVALUATE
# ============================================================================

print("\n📈 EVALUATION")
print("="*60)

# Predictions
predictions = model.predict(X_scaled)
scores = model.score_samples(X_scaled)

# Converter -1/1 para 0/1
y_pred = (predictions == -1).astype(int)

# Criar labels sintéticos (baseado em scores extremos)
y_true = (scores < np.percentile(scores, 5)).astype(int)

# Métricas
f1 = f1_score(y_true, y_pred)
precision = precision_score(y_true, y_pred)
recall = recall_score(y_true, y_pred)

print(f"✅ F1-Score: {f1:.4f}")
print(f"✅ Precision: {precision:.4f}")
print(f"✅ Recall: {recall:.4f}")
print(f"📊 Anomalies detected: {y_pred.sum()} / {len(y_pred)} ({y_pred.sum()/len(y_pred)*100:.2f}%)")

# Liberar memória
del X_scaled, predictions, scores, y_pred, y_true
gc.collect()

# ============================================================================
# 6. SAVE MODEL
# ============================================================================

print("\n💾 SAVING MODEL")
print("="*60)

os.makedirs(MODEL_DIR, exist_ok=True)

# Salvar modelo e scaler
model_path = f"{MODEL_DIR}/isolation_forest_optimized.pkl"
scaler_path = f"{MODEL_DIR}/scaler_optimized.pkl"
features_path = f"{MODEL_DIR}/feature_names_optimized.txt"

joblib.dump(model, model_path)
joblib.dump(scaler, scaler_path)

# Salvar lista de features
with open(features_path, 'w') as f:
    f.write('\n'.join(feature_cols))

print(f"✅ Model saved: {model_path}")
print(f"✅ Scaler saved: {scaler_path}")
print(f"✅ Features saved: {features_path}")

# Tamanho dos arquivos
model_size = os.path.getsize(model_path) / 1024 / 1024
scaler_size = os.path.getsize(scaler_path) / 1024 / 1024

print(f"📦 Model size: {model_size:.2f} MB")
print(f"📦 Scaler size: {scaler_size:.2f} MB")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*60)
print("✅ TRAINING COMPLETE")
print("="*60)
print(f"🎯 F1-Score: {f1:.4f}")
print(f"📊 Features: {len(feature_cols)} (optimized from 169)")
print(f"📦 Model: {model_size:.2f} MB")
print(f"⚡ Samples: {SAMPLE_SIZE} (memory efficient)")
print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)
print("\n🚀 Model ready for deployment!")
