#!/usr/bin/env python3
"""
Train ML model with advanced feature engineering (simplified without MLflow)
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
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
import pickle
import json

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.ml_feature_engineering import feature_engineer
from sqlalchemy import text


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
    """Create synthetic anomalies for supervised evaluation"""
    print(f"\n🔧 Creating synthetic anomalies ({contamination*100}% contamination)...")
    
    df_clean = df.copy()
    df_clean['is_anomaly'] = 0
    
    # Number of anomalies to create
    n_anomalies = int(len(df) * contamination)
    anomaly_indices = np.random.choice(df.index, size=n_anomalies, replace=False)
    
    # Create different types of anomalies
    for idx in anomaly_indices:
        anomaly_type = np.random.choice(['spike', 'drop', 'shift'])
        
        if anomaly_type == 'spike':
            # Value spike (3-5x mean)
            df_clean.loc[idx, 'value'] *= np.random.uniform(3, 5)
        
        elif anomaly_type == 'drop':
            # Value drop (10-30% of mean)
            df_clean.loc[idx, 'value'] *= np.random.uniform(0.1, 0.3)
        
        elif anomaly_type == 'shift':
            # Sudden shift (±50-100% of std)
            shift = np.random.uniform(0.5, 1.0) * df['value'].std()
            df_clean.loc[idx, 'value'] += shift * np.random.choice([-1, 1])
        
        df_clean.loc[idx, 'is_anomaly'] = 1
    
    print(f"✅ Created {n_anomalies} synthetic anomalies")
    return df_clean


def train_model(X_train, y_train, X_test, y_test):
    """Train Isolation Forest with optimized parameters"""
    print("\n🤖 Training Isolation Forest...")
    
    model = IsolationForest(
        n_estimators=150,
        max_samples='auto',
        contamination=0.05,
        max_features=0.8,
        bootstrap=True,
        n_jobs=-1,
        random_state=42,
        verbose=1
    )
    
    print(f"Training on {len(X_train)} samples with {X_train.shape[1]} features...")
    model.fit(X_train)
    
    # Predict on test set
    print("\n📊 Evaluating model...")
    y_pred_test = model.predict(X_test)
    y_pred_test = np.where(y_pred_test == -1, 1, 0)  # Convert -1/1 to 1/0
    
    # Calculate metrics
    f1 = f1_score(y_test, y_pred_test)
    precision = precision_score(y_test, y_pred_test, zero_division=0)
    recall = recall_score(y_test, y_pred_test, zero_division=0)
    
    print("\n" + "="*60)
    print("📈 MODEL PERFORMANCE")
    print("="*60)
    print(f"F1-Score:  {f1:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print("="*60)
    
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred_test, 
                                target_names=['Normal', 'Anomaly']))
    
    print("\n📊 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred_test)
    print(f"True Negatives:  {cm[0][0]}")
    print(f"False Positives: {cm[0][1]}")
    print(f"False Negatives: {cm[1][0]}")
    print(f"True Positives:  {cm[1][1]}")
    
    return model, {
        'f1_score': float(f1),
        'precision': float(precision),
        'recall': float(recall),
        'confusion_matrix': cm.tolist()
    }


async def main():
    """Main training pipeline"""
    print("\n" + "="*60)
    print("🚀 OPTIFLOW ML - FEATURE ENGINEERING TRAINING")
    print("="*60)
    print(f"Start time: {datetime.now()}")
    
    # 1. Fetch training data
    df = await fetch_training_data()
    if df is None:
        return
    
    # 2. Create synthetic anomalies
    df = create_synthetic_anomalies(df, contamination=0.05)
    
    # 3. Engineer features
    print("\n🔧 Engineering features...")
    print(f"Input shape: {df.shape}")
    
    X_engineered = feature_engineer.engineer_features(df)
    print(f"Output shape: {X_engineered.shape}")
    print(f"✅ Generated {X_engineered.shape[1]} features from raw data")
    
    # Print feature groups
    print("\n📊 Feature Groups:")
    feature_counts = feature_engineer.get_feature_counts()
    for group, count in feature_counts.items():
        print(f"  - {group}: {count} features")
    
    # 4. Prepare train/test split
    print("\n📊 Splitting data (80/20)...")
    y = df['is_anomaly'].values
    X_train, X_test, y_train, y_test = train_test_split(
        X_engineered, y, 
        test_size=0.2, 
        random_state=42,
        stratify=y
    )
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Anomaly ratio: {y.mean()*100:.2f}%")
    
    # 5. Train model
    model, metrics = train_model(X_train, y_train, X_test, y_test)
    
    # 6. Save model
    print("\n💾 Saving model...")
    model_dir = '/app/models'
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = f'{model_dir}/isolation_forest_features.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"✅ Model saved to {model_path}")
    
    # Save metrics
    metrics_path = f'{model_dir}/metrics_features.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Metrics saved to {metrics_path}")
    
    # 7. Compare with baseline
    print("\n" + "="*60)
    print("📊 COMPARISON WITH BASELINE")
    print("="*60)
    print(f"Baseline F1-Score: 0.1032")
    print(f"New F1-Score:      {metrics['f1_score']:.4f}")
    improvement = ((metrics['f1_score'] - 0.1032) / 0.1032) * 100
    print(f"Improvement:       {improvement:+.1f}%")
    print("="*60)
    
    print(f"\n✅ Training completed at {datetime.now()}")
    
    return metrics


if __name__ == '__main__':
    metrics = asyncio.run(main())
    
    # Exit with appropriate code
    if metrics and metrics['f1_score'] >= 0.25:
        print("\n🎉 SUCCESS! F1-Score target achieved (≥0.25)")
        sys.exit(0)
    elif metrics:
        print(f"\n⚠️  WARNING: F1-Score below target ({metrics['f1_score']:.4f} < 0.25)")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Training did not complete")
        sys.exit(1)
