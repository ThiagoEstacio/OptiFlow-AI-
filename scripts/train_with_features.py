#!/usr/bin/env python3
"""
Train ML model with advanced feature engineering
Expected improvement: F1-Score 0.10 → 0.28 (+180%)
"""

import sys
import os
sys.path.insert(0, '/app')

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
import mlflow
import mlflow.sklearn
import pickle

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.ml_feature_engineering import feature_engineer
from sqlalchemy import text

# Configure MLflow
mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
mlflow.set_experiment("optiflow-ml-optimized")


async def fetch_training_data():
    """Fetch training data from database"""
    print("📊 Fetching training data...")
    
    query = """
        SELECT 
            timestamp,
            value,
            tag_id
        FROM sensor_readings
        WHERE timestamp >= NOW() - INTERVAL '30 days'
        ORDER BY timestamp ASC
        LIMIT 50000
    """
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(query))
        rows = result.fetchall()
    
    if not rows:
        print("❌ No training data found")
        return None
    
    df = pd.DataFrame(rows, columns=['timestamp', 'value', 'tag_id'])
    print(f"✅ Fetched {len(df)} training samples")
    return df


def create_synthetic_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """Add synthetic anomalies for supervised learning"""
    n_anomalies = int(len(df) * contamination)
    anomaly_indices = np.random.choice(df.index, n_anomalies, replace=False)
    
    df['is_anomaly'] = 0
    df.loc[anomaly_indices, 'is_anomaly'] = 1
    
    # Create anomalies by adding noise
    for idx in anomaly_indices:
        noise_type = np.random.choice(['spike', 'drop', 'shift'])
        if noise_type == 'spike':
            df.loc[idx, 'value'] *= np.random.uniform(3, 5)
        elif noise_type == 'drop':
            df.loc[idx, 'value'] *= np.random.uniform(0.1, 0.3)
        else:  # shift
            df.loc[idx, 'value'] += df['value'].std() * np.random.uniform(3, 5)
    
    return df


async def train_model_with_features():
    """Train model with advanced feature engineering"""
    print("\n🤖 Training ML Model with Feature Engineering\n")
    print("=" * 60)
    
    # 1. Fetch data
    df = await fetch_training_data()
    if df is None:
        return
    
    # 2. Add synthetic anomalies for evaluation
    df = create_synthetic_anomalies(df, contamination=0.05)
    print(f"✅ Created {df['is_anomaly'].sum()} synthetic anomalies")
    
    # 3. Engineer features
    print("\n🔧 Engineering features...")
    df_features = feature_engineer.engineer_features(df)
    
    # 4. Prepare data for training
    feature_cols = [col for col in df_features.columns 
                   if col not in ['timestamp', 'value', 'tag_id', 'is_anomaly']]
    
    X = df_features[feature_cols]
    y = df_features['is_anomaly']
    
    print(f"✅ Created {X.shape[1]} features")
    print(f"   Feature groups:")
    groups = feature_engineer.get_feature_importance_groups()
    for group_name, features in groups.items():
        print(f"     - {group_name}: {len(features)} features")
    
    # 5. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 Dataset split:")
    print(f"   Training: {len(X_train)} samples")
    print(f"   Testing:  {len(X_test)} samples")
    print(f"   Anomalies in test: {y_test.sum()}")
    
    # 6. Train model
    print("\n🎓 Training Isolation Forest...")
    
    with mlflow.start_run(run_name="isolation_forest_featured"):
        # Model parameters
        params = {
            "contamination": 0.05,
            "n_estimators": 150,
            "max_samples": "auto",
            "max_features": 0.8,
            "bootstrap": True,
            "random_state": 42,
            "n_jobs": -1
        }
        
        # Log parameters
        mlflow.log_params(params)
        mlflow.log_param("n_features", X.shape[1])
        mlflow.log_param("n_samples", X.shape[0])
        mlflow.log_param("feature_engineering", "enabled")
        
        # Train model
        model = IsolationForest(**params)
        model.fit(X_train)
        
        print("✅ Model trained")
        
        # 7. Evaluate
        print("\n📈 Evaluating model...")
        
        # Predictions (-1 for anomalies, 1 for normal)
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Convert to binary (0 = normal, 1 = anomaly)
        y_pred_train_binary = (y_pred_train == -1).astype(int)
        y_pred_test_binary = (y_pred_test == -1).astype(int)
        
        # Calculate metrics
        train_f1 = f1_score(y_train, y_pred_train_binary)
        test_f1 = f1_score(y_test, y_pred_test_binary)
        test_precision = precision_score(y_test, y_pred_test_binary)
        test_recall = recall_score(y_test, y_pred_test_binary)
        
        # Log metrics
        mlflow.log_metric("train_f1_score", train_f1)
        mlflow.log_metric("test_f1_score", test_f1)
        mlflow.log_metric("test_precision", test_precision)
        mlflow.log_metric("test_recall", test_recall)
        
        print("\n📊 RESULTS:")
        print("=" * 60)
        print(f"Training F1-Score:   {train_f1:.4f}")
        print(f"Test F1-Score:       {test_f1:.4f}")
        print(f"Test Precision:      {test_precision:.4f}")
        print(f"Test Recall:         {test_recall:.4f}")
        print("=" * 60)
        
        # Detailed classification report
        print("\n📋 Classification Report (Test Set):")
        print(classification_report(
            y_test, 
            y_pred_test_binary,
            target_names=['Normal', 'Anomaly'],
            digits=4
        ))
        
        # 8. Save model
        print("\n💾 Saving model...")
        
        # Log model to MLflow
        mlflow.sklearn.log_model(model, "model")
        
        # Save locally
        model_path = "/app/models/isolation_forest_featured.pkl"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': model,
                'feature_names': feature_cols,
                'params': params,
                'metrics': {
                    'f1_score': test_f1,
                    'precision': test_precision,
                    'recall': test_recall
                },
                'trained_at': datetime.now().isoformat()
            }, f)
        
        print(f"✅ Model saved to {model_path}")
        
        # 9. Compare with baseline
        print("\n📊 Comparison with Baseline:")
        print("=" * 60)
        print("BEFORE (1 feature):")
        print("  F1-Score:  0.1032")
        print("  Precision: 0.0543")
        print("  Recall:    0.5000")
        print("")
        print(f"AFTER ({X.shape[1]} features):")
        print(f"  F1-Score:  {test_f1:.4f}  ({(test_f1/0.1032 - 1)*100:+.1f}%)")
        print(f"  Precision: {test_precision:.4f}  ({(test_precision/0.0543 - 1)*100:+.1f}%)")
        print(f"  Recall:    {test_recall:.4f}  ({(test_recall/0.5000 - 1)*100:+.1f}%)")
        print("=" * 60)
        
        if test_f1 > 0.25:
            print("\n✅ SUCCESS! Target achieved (F1 > 0.25)")
        else:
            print(f"\n⚠️  Target not yet achieved (F1 = {test_f1:.4f}, target > 0.25)")
        
        print(f"\n✅ Training complete!")
        print(f"🔗 MLflow UI: {settings.MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    asyncio.run(train_model_with_features())
