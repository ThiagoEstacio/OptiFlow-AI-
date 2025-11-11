#!/usr/bin/env python3
"""
Quick Isolation Forest trainer for validation and fast iteration.
Loads up to SAMPLE_MAX rows from the InfluxDB timeseries bucket and trains an IsolationForest.
Saves model and scaler to /app/models.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime
from influxdb_client import InfluxDBClient
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import joblib

INFLUX_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN", "my-super-secret-influxdb-token")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "optiflow")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "timeseries")

MODEL_DIR = "/app/models"
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_fast.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler_fast.joblib")

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

SAMPLE_MAX = 200000  # max rows to sample for quick training
CONTAMINATION = 0.015


def load_sample():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "tag_values")
      |> filter(fn: (r) => r["_field"] == "value")
      |> pivot(rowKey:["_time"], columnKey: ["tag_name"], valueColumn: "_value")
    '''
    print("Querying InfluxDB (may take a bit)...")
    df = query_api.query_data_frame(query)
    if isinstance(df, list):
        df = pd.concat(df, ignore_index=True)
    if df.empty:
        raise SystemExit("No data returned from InfluxDB")
    # Rename columns mapping to internal tag names if present
    mapping = {
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
    df = df.rename(columns=mapping)
    # Keep only tag columns
    cols = [c for c in TAGS if c in df.columns]
    if not cols:
        raise SystemExit("No tag columns found after renaming")
    df_sel = df[cols]
    # downsample if needed
    if len(df_sel) > SAMPLE_MAX:
        frac = SAMPLE_MAX / len(df_sel)
        df_sel = df_sel.sample(frac=frac, random_state=42)
    print(f"Loaded sample: {len(df_sel)} rows, columns: {cols}")
    # handle NaNs
    X = df_sel.fillna(0).values
    # labels if present
    y = None
    if 'is_anomaly' in df.columns:
        ycol = df['is_anomaly']
        y = ycol.replace({'true':1,'false':0,True:1,False:0}).fillna(0).astype(int)
        # align index with df_sel (after sample)
        y = y.loc[df_sel.index].values
    return X, y


def main():
    X, y = load_sample()
    # split
    n = len(X)
    split = int(n * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_val = y[split:] if y is not None else None
    # scale
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    model = IsolationForest(contamination=CONTAMINATION, n_estimators=100, random_state=42, n_jobs=-1)
    print("Training Isolation Forest...")
    model.fit(X_train_s)
    y_pred = (model.predict(X_val_s) == -1).astype(int)
    if y_val is not None:
        precision = precision_score(y_val, y_pred)
        recall = recall_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred)
        print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    else:
        print(f"Anomalies detected (validation): {y_pred.sum()} / {len(y_pred)}")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Saved model to {MODEL_PATH}")

if __name__ == '__main__':
    main()
