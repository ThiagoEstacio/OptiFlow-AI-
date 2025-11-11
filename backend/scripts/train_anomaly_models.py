#!/usr/bin/env python3
"""
🤖 ML Training - Anomaly Detection Models
==========================================

Treina e compara 2 modelos de detecção de anomalias:
1. Isolation Forest (sklearn) - Rápido, não supervisionado
2. LSTM Autoencoder (TensorFlow) - Deep Learning, captura padrões temporais

Usa os 30 dias de dados históricos do InfluxDB (432k pontos, 6.747 anomalias)
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json

# TensorFlow/Keras para LSTM
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("⚠️  TensorFlow not available. LSTM model will be skipped.")
    TENSORFLOW_AVAILABLE = False

# ========================================
# 📊 CONFIGURATION
# ========================================

INFLUX_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")

# Model paths
MODEL_DIR = "/app/models"
ISOLATION_FOREST_PATH = f"{MODEL_DIR}/isolation_forest.joblib"
LSTM_MODEL_PATH = f"{MODEL_DIR}/lstm_autoencoder.h5"
SCALER_PATH = f"{MODEL_DIR}/scaler.joblib"
METRICS_PATH = f"{MODEL_DIR}/metrics.json"

# Training parameters
TRAIN_SPLIT = 0.8  # 80% treino, 20% validação
CONTAMINATION = 0.015  # ~1.5% de anomalias esperadas (6747/432000)
LSTM_SEQUENCE_LENGTH = 60  # 1 hora de dados (60 minutos)
LSTM_EPOCHS = 50
LSTM_BATCH_SIZE = 32

# Tags to train on
TAGS = [
    "MOTOR_01_CURRENT",
    "MOTOR_01_SPEED",
    "MOTOR_01_VIBRATION",
    "TEMP_SENSOR_01",
    "TEMP_SENSOR_02",
    "PRESSURE_01",
    "PRESSURE_02",
    "LEVEL_TANK_01",
    "POWER_CONSUMPTION",
    "PRODUCTION_RATE",
]


# ========================================
# 📡 DATA LOADING
# ========================================

def load_data_from_influxdb():
    """Carrega 30 dias de dados do InfluxDB"""
    print("📡 Connecting to InfluxDB...")
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    
    # Query last 30 days from tag_values measurement
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "tag_values")
      |> filter(fn: (r) => r["_field"] == "value")
      |> pivot(rowKey:["_time"], columnKey: ["tag_name"], valueColumn: "_value")
    '''
    
    print("⏳ Loading data from InfluxDB (this may take a minute)...")
    result = query_api.query_data_frame(query)
    
    if isinstance(result, list):
        if len(result) == 0:
            raise ValueError("No data found in InfluxDB!")
        df = pd.concat(result, ignore_index=True)
    else:
        df = result
    
    if len(df) == 0:
        raise ValueError("No data found in InfluxDB!")
    
    print(f"✅ Loaded {len(df)} data points")
    print(f"📅 Date range: {df['_time'].min()} to {df['_time'].max()}")
    
    # Map tag names to tag IDs
    tag_name_mapping = {
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
    
    # Rename columns
    df = df.rename(columns=tag_name_mapping)
    
    print(f"🏷️  Tags found: {[col for col in df.columns if col in TAGS]}")
    
    return df


def prepare_features(df):
    """Prepara features para treinamento"""
    print("\n🔧 Preparing features...")
    
    # Select only tag columns
    feature_cols = [col for col in TAGS if col in df.columns]
    
    if not feature_cols:
        raise ValueError("No tag columns found in data!")
    
    # Extract features
    X = df[feature_cols].values
    
    # Check if we have anomaly labels (from historical data generation)
    if 'is_anomaly' in df.columns:
        # Convert "true"/"false" strings or boolean to int
        y_true = df['is_anomaly'].replace({'true': 1, 'false': 0, True: 1, False: 0}).fillna(0).astype(int).values
        print(f"✅ Found {y_true.sum()} labeled anomalies ({y_true.sum()/len(y_true)*100:.2f}%)")
    else:
        print("⚠️  No anomaly labels found. Will use unsupervised evaluation.")
        y_true = None
    
    # Handle NaN values in features
    X = np.nan_to_num(X, nan=0.0)
    
    print(f"📊 Feature matrix shape: {X.shape}")
    print(f"📊 Features: {feature_cols}")
    
    return X, y_true, feature_cols


# ========================================
# 🌲 ISOLATION FOREST
# ========================================

def train_isolation_forest(X_train, X_val, y_val=None):
    """Treina Isolation Forest"""
    print("\n" + "="*60)
    print("🌲 TRAINING ISOLATION FOREST")
    print("="*60)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train model
    print(f"⏳ Training with contamination={CONTAMINATION}...")
    model = IsolationForest(
        contamination=CONTAMINATION,
        random_state=42,
        n_estimators=100,
        max_samples='auto',
        n_jobs=-1,
        verbose=1
    )
    model.fit(X_train_scaled)
    
    # Predictions (-1 = anomaly, 1 = normal)
    y_pred_train = model.predict(X_train_scaled)
    y_pred_val = model.predict(X_val_scaled)
    
    # Convert to binary (1 = anomaly, 0 = normal)
    y_pred_train_binary = (y_pred_train == -1).astype(int)
    y_pred_val_binary = (y_pred_val == -1).astype(int)
    
    print(f"\n📊 Training Results:")
    print(f"   Anomalies detected: {y_pred_train_binary.sum()} / {len(y_pred_train_binary)} ({y_pred_train_binary.sum()/len(y_pred_train_binary)*100:.2f}%)")
    
    print(f"\n📊 Validation Results:")
    print(f"   Anomalies detected: {y_pred_val_binary.sum()} / {len(y_pred_val_binary)} ({y_pred_val_binary.sum()/len(y_pred_val_binary)*100:.2f}%)")
    
    metrics = {}
    
    # If we have true labels, calculate metrics
    if y_val is not None:
        precision = precision_score(y_val, y_pred_val_binary)
        recall = recall_score(y_val, y_pred_val_binary)
        f1 = f1_score(y_val, y_pred_val_binary)
        
        print(f"\n✅ Metrics (with true labels):")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        
        cm = confusion_matrix(y_val, y_pred_val_binary)
        print(f"\n   Confusion Matrix:")
        print(f"   TN={cm[0,0]}, FP={cm[0,1]}")
        print(f"   FN={cm[1,0]}, TP={cm[1,1]}")
        
        metrics = {
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist(),
        }
    
    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, ISOLATION_FOREST_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n💾 Model saved to: {ISOLATION_FOREST_PATH}")
    print(f"💾 Scaler saved to: {SCALER_PATH}")
    
    return model, scaler, metrics


# ========================================
# 🧠 LSTM AUTOENCODER
# ========================================

def create_lstm_autoencoder(sequence_length, n_features):
    """Cria arquitetura LSTM Autoencoder"""
    model = keras.Sequential([
        # Encoder
        layers.LSTM(64, activation='relu', input_shape=(sequence_length, n_features), return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32, activation='relu', return_sequences=False),
        layers.Dropout(0.2),
        layers.RepeatVector(sequence_length),
        
        # Decoder
        layers.LSTM(32, activation='relu', return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(64, activation='relu', return_sequences=True),
        layers.Dropout(0.2),
        layers.TimeDistributed(layers.Dense(n_features))
    ])
    
    model.compile(optimizer='adam', loss='mse')
    return model


def prepare_sequences(X, sequence_length):
    """Prepara sequências para LSTM"""
    sequences = []
    for i in range(len(X) - sequence_length):
        sequences.append(X[i:i+sequence_length])
    return np.array(sequences)


def train_lstm_autoencoder(X_train, X_val, y_val=None):
    """Treina LSTM Autoencoder"""
    print("\n" + "="*60)
    print("🧠 TRAINING LSTM AUTOENCODER")
    print("="*60)
    
    if not TENSORFLOW_AVAILABLE:
        print("⚠️  TensorFlow not available. Skipping LSTM training.")
        return None, {}
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Create sequences
    print(f"⏳ Creating sequences (length={LSTM_SEQUENCE_LENGTH})...")
    X_train_seq = prepare_sequences(X_train_scaled, LSTM_SEQUENCE_LENGTH)
    X_val_seq = prepare_sequences(X_val_scaled, LSTM_SEQUENCE_LENGTH)
    
    print(f"📊 Training sequences shape: {X_train_seq.shape}")
    print(f"📊 Validation sequences shape: {X_val_seq.shape}")
    
    # Create model
    n_features = X_train_seq.shape[2]
    model = create_lstm_autoencoder(LSTM_SEQUENCE_LENGTH, n_features)
    
    print(f"\n🏗️  Model Architecture:")
    model.summary()
    
    # Callbacks
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    )
    
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=0.0001
    )
    
    # Train
    print(f"\n⏳ Training for {LSTM_EPOCHS} epochs...")
    history = model.fit(
        X_train_seq, X_train_seq,
        epochs=LSTM_EPOCHS,
        batch_size=LSTM_BATCH_SIZE,
        validation_data=(X_val_seq, X_val_seq),
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    # Calculate reconstruction error
    X_val_pred = model.predict(X_val_seq, verbose=0)
    mse = np.mean(np.power(X_val_seq - X_val_pred, 2), axis=(1, 2))
    
    # Determine threshold (95th percentile of errors)
    threshold = np.percentile(mse, 95)
    y_pred_val_binary = (mse > threshold).astype(int)
    
    print(f"\n📊 Validation Results:")
    print(f"   Reconstruction error threshold: {threshold:.6f}")
    print(f"   Anomalies detected: {y_pred_val_binary.sum()} / {len(y_pred_val_binary)} ({y_pred_val_binary.sum()/len(y_pred_val_binary)*100:.2f}%)")
    
    metrics = {
        'threshold': float(threshold),
        'final_train_loss': float(history.history['loss'][-1]),
        'final_val_loss': float(history.history['val_loss'][-1]),
    }
    
    # If we have true labels, calculate metrics
    if y_val is not None:
        # Align labels with sequences
        y_val_seq = y_val[LSTM_SEQUENCE_LENGTH:]
        
        precision = precision_score(y_val_seq, y_pred_val_binary)
        recall = recall_score(y_val_seq, y_pred_val_binary)
        f1 = f1_score(y_val_seq, y_pred_val_binary)
        
        print(f"\n✅ Metrics (with true labels):")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        
        cm = confusion_matrix(y_val_seq, y_pred_val_binary)
        print(f"\n   Confusion Matrix:")
        print(f"   TN={cm[0,0]}, FP={cm[0,1]}")
        print(f"   FN={cm[1,0]}, TP={cm[1,1]}")
        
        metrics.update({
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist(),
        })
    
    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save(LSTM_MODEL_PATH)
    print(f"\n💾 Model saved to: {LSTM_MODEL_PATH}")
    
    return model, metrics


# ========================================
# 🚀 MAIN
# ========================================

def main():
    print("\n" + "="*60)
    print("🤖 ML TRAINING - ANOMALY DETECTION")
    print("="*60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load data
        df = load_data_from_influxdb()
        
        # Prepare features
        X, y_true, feature_cols = prepare_features(df)
        
        # Train/validation split
        split_idx = int(len(X) * TRAIN_SPLIT)
        X_train, X_val = X[:split_idx], X[split_idx:]
        
        if y_true is not None:
            y_train, y_val = y_true[:split_idx], y_true[split_idx:]
        else:
            y_train, y_val = None, None
        
        print(f"\n📊 Data Split:")
        print(f"   Training:   {len(X_train)} samples")
        print(f"   Validation: {len(X_val)} samples")
        
        # Train models
        all_metrics = {}
        
        # 1. Isolation Forest
        iso_model, iso_scaler, iso_metrics = train_isolation_forest(X_train, X_val, y_val)
        all_metrics['isolation_forest'] = iso_metrics
        
        # 2. LSTM Autoencoder
        lstm_model, lstm_metrics = train_lstm_autoencoder(X_train, X_val, y_val)
        all_metrics['lstm_autoencoder'] = lstm_metrics
        
        # Save metrics
        all_metrics['metadata'] = {
            'trained_at': datetime.now().isoformat(),
            'n_samples_train': int(len(X_train)),
            'n_samples_val': int(len(X_val)),
            'n_features': int(X.shape[1]),
            'features': feature_cols,
            'contamination': CONTAMINATION,
        }
        
        with open(METRICS_PATH, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        print(f"\n💾 Metrics saved to: {METRICS_PATH}")
        
        # Compare models
        print("\n" + "="*60)
        print("📊 MODEL COMPARISON")
        print("="*60)
        
        if 'f1_score' in iso_metrics and 'f1_score' in lstm_metrics:
            print(f"\nIsolation Forest:")
            print(f"  F1-Score: {iso_metrics['f1_score']:.4f}")
            print(f"  Precision: {iso_metrics['precision']:.4f}")
            print(f"  Recall: {iso_metrics['recall']:.4f}")
            
            print(f"\nLSTM Autoencoder:")
            print(f"  F1-Score: {lstm_metrics['f1_score']:.4f}")
            print(f"  Precision: {lstm_metrics['precision']:.4f}")
            print(f"  Recall: {lstm_metrics['recall']:.4f}")
            
            winner = "Isolation Forest" if iso_metrics['f1_score'] > lstm_metrics['f1_score'] else "LSTM Autoencoder"
            print(f"\n🏆 Best Model: {winner}")
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETE!")
        print("="*60)
        print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
