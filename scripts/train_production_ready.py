"""
🚀 PRODUCTION-READY ML TRAINING
Otimizado para plantas industriais com muitas tags

Melhorias implementadas:
1. ✅ Feature Engineering Avançado (rolling stats, correlações, rate of change)
2. ✅ Ensemble Methods (IF + One-Class SVM com voting)
3. ✅ Hyperparameter Tuning (Grid Search otimizado)
4. ✅ Cache de dados para treinamento rápido
5. ✅ Métricas detalhadas de performance

Performance esperada: F1-Score > 0.25 (2.5x melhoria vs baseline 0.1032)
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import json
from typing import Dict, Tuple

# ML Libraries
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# ========================================
# 📊 CONFIGURATION
# ========================================

MODEL_DIR = "/app/models"
TRAIN_SPLIT = 0.8
RANDOM_STATE = 42

# Feature engineering
ROLLING_WINDOWS = [5, 10, 20]  # Minutes
TAG_NAMES = [
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
# 🔧 FEATURE ENGINEERING
# ========================================

def add_rolling_features(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Add rolling statistics"""
    print("🔧 Adding rolling statistics...")
    for col in columns:
        if col not in df.columns:
            continue
        for window in ROLLING_WINDOWS:
            df[f'{col}_rmean_{window}'] = df[col].rolling(window, min_periods=1).mean()
            df[f'{col}_rstd_{window}'] = df[col].rolling(window, min_periods=1).std()
            df[f'{col}_rmax_{window}'] = df[col].rolling(window, min_periods=1).max()
            df[f'{col}_rmin_{window}'] = df[col].rolling(window, min_periods=1).min()
    return df


def add_rate_of_change(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Add derivatives"""
    print("🔧 Adding rate of change...")
    for col in columns:
        if col not in df.columns:
            continue
        df[f'{col}_diff'] = df[col].diff()
        df[f'{col}_pct'] = df[col].pct_change()
    return df


def add_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Add cross-tag correlations"""
    print("🔧 Adding correlation features...")
    
    pairs = [
        ('TEMP_SENSOR_01', 'TEMP_SENSOR_02'),
        ('PRESSURE_01', 'PRESSURE_02'),
        ('MOTOR_01_CURRENT', 'MOTOR_01_SPEED'),
        ('MOTOR_01_SPEED', 'MOTOR_01_VIBRATION'),
    ]
    
    for col1, col2 in pairs:
        if col1 in df.columns and col2 in df.columns:
            df[f'{col1}_{col2}_ratio'] = df[col1] / (df[col2] + 1e-6)
            df[f'{col1}_{col2}_diff'] = df[col1] - df[col2]
    
    return df


def engineer_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """Apply all feature engineering"""
    print("\n🔧 FEATURE ENGINEERING")
    print("=" * 60)
    
    # Start with original features
    feature_cols = [col for col in TAG_NAMES if col in df.columns]
    orig_count = len(feature_cols)
    
    # Add engineered features
    df = add_rolling_features(df, TAG_NAMES)
    df = add_rate_of_change(df, TAG_NAMES)
    df = add_correlations(df)
    
    # Get all feature columns
    feature_cols = [col for col in df.columns if col not in ['_time', 'is_anomaly', 'hour', 'day_of_week']]
    
    # Add time features
    if '_time' in df.columns:
        df['hour'] = pd.to_datetime(df['_time']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['_time']).dt.dayofweek
        feature_cols.extend(['hour', 'day_of_week'])
    
    print(f"✅ Total features: {len(feature_cols)}")
    print(f"   Original: {orig_count}")
    print(f"   Engineered: {len(feature_cols) - orig_count}")
    
    return df, feature_cols


# ========================================
# 🤖 MODEL TRAINING
# ========================================

def train_isolation_forest_tuned(X_train, X_val, y_val):
    """Train Isolation Forest with grid search"""
    print("\n🌲 TRAINING ISOLATION FOREST (TUNED)")
    print("=" * 60)
    
    best_f1 = 0
    best_model = None
    best_params = None
    
    param_grid = {
        'n_estimators': [200, 300],
        'max_samples': ['auto', 512],
        'contamination': [0.01, 0.015, 0.02],
        'max_features': [1.0, 0.8],
    }
    
    total_combinations = (len(param_grid['n_estimators']) * 
                          len(param_grid['max_samples']) * 
                          len(param_grid['contamination']) * 
                          len(param_grid['max_features']))
    
    print(f"⏳ Testing {total_combinations} parameter combinations...")
    
    iteration = 0
    for n_est in param_grid['n_estimators']:
        for max_samp in param_grid['max_samples']:
            for cont in param_grid['contamination']:
                for max_feat in param_grid['max_features']:
                    iteration += 1
                    
                    model = IsolationForest(
                        n_estimators=n_est,
                        max_samples=max_samp,
                        contamination=cont,
                        max_features=max_feat,
                        random_state=RANDOM_STATE,
                        n_jobs=-1
                    )
                    
                    model.fit(X_train)
                    y_pred = model.predict(X_val)
                    y_pred_binary = (y_pred == -1).astype(int)
                    
                    f1 = f1_score(y_val, y_pred_binary, zero_division=0)
                    
                    if f1 > best_f1:
                        best_f1 = f1
                        best_model = model
                        best_params = {
                            'n_estimators': n_est,
                            'max_samples': max_samp,
                            'contamination': cont,
                            'max_features': max_feat
                        }
                        print(f"   [{iteration}/{total_combinations}] 🎯 New best F1: {f1:.4f} - {best_params}")
    
    print(f"\n✅ Best parameters: {best_params}")
    print(f"✅ Best F1-Score: {best_f1:.4f}")
    
    # Final evaluation
    y_pred_val = best_model.predict(X_val)
    y_pred_val_binary = (y_pred_val == -1).astype(int)
    
    precision = precision_score(y_val, y_pred_val_binary, zero_division=0)
    recall = recall_score(y_val, y_pred_val_binary, zero_division=0)
    cm = confusion_matrix(y_val, y_pred_val_binary)
    
    print(f"\n📊 Final Metrics:")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   F1-Score:  {best_f1:.4f}")
    print(f"   Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    
    metrics = {
        'model': 'isolation_forest_optimized',
        'parameters': best_params,
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(best_f1),
        'confusion_matrix': cm.tolist(),
    }
    
    return best_model, metrics


def train_ensemble(X_train, X_val, y_val, if_model):
    """Train One-Class SVM and create ensemble"""
    print("\n🎯 TRAINING ENSEMBLE (IF + SVM)")
    print("=" * 60)
    
    # Sample for SVM (faster training)
    sample_size = min(30000, len(X_train))
    indices = np.random.choice(len(X_train), sample_size, replace=False)
    X_train_sample = X_train[indices]
    
    print(f"Training One-Class SVM on {sample_size} samples...")
    svm_model = OneClassSVM(nu=0.015, kernel='rbf', gamma='auto')
    svm_model.fit(X_train_sample)
    
    # Ensemble voting
    print("Creating ensemble predictions...")
    if_pred = if_model.predict(X_val)
    svm_pred = svm_model.predict(X_val)
    
    # Vote: anomaly if both agree
    ensemble_pred = np.where((if_pred == -1) & (svm_pred == -1), -1, 1)
    ensemble_pred_binary = (ensemble_pred == -1).astype(int)
    
    precision = precision_score(y_val, ensemble_pred_binary, zero_division=0)
    recall = recall_score(y_val, ensemble_pred_binary, zero_division=0)
    f1 = f1_score(y_val, ensemble_pred_binary, zero_division=0)
    cm = confusion_matrix(y_val, ensemble_pred_binary)
    
    print(f"\n📊 Ensemble Metrics:")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall:    {recall:.4f}")
    print(f"   F1-Score:  {f1:.4f}")
    print(f"   Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    
    metrics = {
        'model': 'ensemble_if_svm',
        'precision': float(precision),
        'recall': float(recall),
        'f1_score': float(f1),
        'confusion_matrix': cm.tolist(),
    }
    
    return svm_model, metrics


# ========================================
# 💾 MAIN TRAINING PIPELINE
# ========================================

def main():
    print("\n" + "=" * 60)
    print("🚀 PRODUCTION-READY ML TRAINING")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load cached data from previous training
    print("📂 Loading cached data...")
    cache_file = f"{MODEL_DIR}/training_data_cache.parquet"
    
    if os.path.exists(cache_file):
        print(f"✅ Found cached data: {cache_file}")
        df = pd.read_parquet(cache_file)
        print(f"✅ Loaded {len(df)} data points from cache")
    else:
        print("⚠️  No cached data found!")
        print("💡 Run train_anomaly_models.py first to generate cache")
        
        # Try to load from existing model training
        print("\n📂 Attempting to load from InfluxDB...")
        from train_anomaly_models import load_data_from_influxdb
        df = load_data_from_influxdb()
        
        # Cache for future use
        os.makedirs(MODEL_DIR, exist_ok=True)
        df.to_parquet(cache_file)
        print(f"💾 Cached data to: {cache_file}")
    
    print(f"📊 Data shape: {df.shape}")
    print(f"📅 Date range: {df['_time'].min()} to {df['_time'].max()}")
    
    # Feature engineering
    df, feature_cols = engineer_features(df)
    
    # Prepare data
    print("\n📊 PREPARING TRAINING DATA")
    print("=" * 60)
    
    # Handle missing values
    df = df.ffill().bfill().fillna(0)
    
    # Get features and labels
    X = df[feature_cols].values
    y = df['is_anomaly'].replace({'true': 1, 'false': 0, True: 1, False: 0}).fillna(0).astype(int).values
    
    anomaly_count = y.sum()
    anomaly_rate = anomaly_count / len(y) * 100
    
    print(f"✅ Feature matrix: {X.shape}")
    print(f"✅ Anomalies: {anomaly_count:,} ({anomaly_rate:.2f}%)")
    
    # Split data
    split_idx = int(len(X) * TRAIN_SPLIT)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    print(f"\n📊 Train: {len(X_train):,} | Validation: {len(X_val):,}")
    print(f"📊 Train anomalies: {y_train.sum():,} ({y_train.sum()/len(y_train)*100:.2f}%)")
    print(f"📊 Val anomalies: {y_val.sum():,} ({y_val.sum()/len(y_val)*100:.2f}%)")
    
    # Scale features
    print("\n🔧 Scaling with RobustScaler...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # Train Isolation Forest with tuning
    if_model, if_metrics = train_isolation_forest_tuned(X_train_scaled, X_val_scaled, y_val)
    
    # Train Ensemble
    svm_model, ensemble_metrics = train_ensemble(X_train_scaled, X_val_scaled, y_val, if_model)
    
    # Save models
    print("\n💾 SAVING MODELS")
    print("=" * 60)
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    model_path = f"{MODEL_DIR}/isolation_forest_production.joblib"
    svm_path = f"{MODEL_DIR}/svm_production.joblib"
    scaler_path = f"{MODEL_DIR}/scaler_production.joblib"
    metrics_path = f"{MODEL_DIR}/metrics_production.json"
    
    joblib.dump(if_model, model_path)
    joblib.dump(svm_model, svm_path)
    joblib.dump(scaler, scaler_path)
    
    all_metrics = {
        'isolation_forest': if_metrics,
        'ensemble': ensemble_metrics,
        'training_info': {
            'trained_at': datetime.now().isoformat(),
            'n_features': len(feature_cols),
            'n_samples': len(X),
            'anomaly_rate': float(anomaly_rate),
        }
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"💾 IF Model: {model_path}")
    print(f"💾 SVM Model: {svm_path}")
    print(f"💾 Scaler: {scaler_path}")
    print(f"💾 Metrics: {metrics_path}")
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    
    print("\n📊 PERFORMANCE SUMMARY:")
    print(f"\n🌲 Isolation Forest:")
    print(f"   F1-Score: {if_metrics['f1_score']:.4f}")
    print(f"   Precision: {if_metrics['precision']:.4f}")
    print(f"   Recall: {if_metrics['recall']:.4f}")
    
    print(f"\n🎯 Ensemble (IF+SVM):")
    print(f"   F1-Score: {ensemble_metrics['f1_score']:.4f}")
    print(f"   Precision: {ensemble_metrics['precision']:.4f}")
    print(f"   Recall: {ensemble_metrics['recall']:.4f}")
    
    # Compare with baseline
    baseline_f1 = 0.1032
    if_improvement = (if_metrics['f1_score'] / baseline_f1 - 1) * 100
    ensemble_improvement = (ensemble_metrics['f1_score'] / baseline_f1 - 1) * 100
    
    print(f"\n📈 Improvement vs Baseline (F1={baseline_f1:.4f}):")
    print(f"   IF: {if_improvement:+.1f}%")
    print(f"   Ensemble: {ensemble_improvement:+.1f}%")


if __name__ == "__main__":
    main()
