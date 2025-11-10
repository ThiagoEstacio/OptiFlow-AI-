"""
Framework de testes APRIMORADO para modelos ML/DS

Melhorias:
- LSTM real com TensorFlow (não RandomForest)
- Modelo de eficiência refinado com Random Forest/Gradient Boosting
- Validação cruzada
- Métricas adicionais
- Visualização de importância de features
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json
from pathlib import Path

# ML/DS imports
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import (
    IsolationForest,
    RandomForestRegressor,
    GradientBoostingRegressor
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from scipy import stats
from scipy.stats import weibull_min

# TensorFlow/Keras para LSTM
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
    print("✅ TensorFlow disponível - usando LSTM real")
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow não disponível - usando RandomForest como fallback")


class EnhancedMLModelTester:
    """Framework APRIMORADO de testes para modelos ML"""

    def __init__(self, data_path: str = None):
        self.results = {}
        self.data_path = data_path or "/tmp"

    def generate_synthetic_data(self) -> Dict[str, pd.DataFrame]:
        """Gera dados sintéticos para testes"""
        print("📊 Gerando dados sintéticos para testes...")

        # 1. Dados de manutenção (MTBF/MTTR)
        n_failures = 100
        maintenance_data = pd.DataFrame({
            'equipment_id': [f'motor_{i%5}' for i in range(n_failures)],
            'failure_time': [datetime.now() - timedelta(days=365-i*3) for i in range(n_failures)],
            'mtbf_hours': np.random.gamma(shape=5, scale=100, size=n_failures),
            'mttr_hours': np.random.gamma(shape=2, scale=2, size=n_failures),
            'cost_brl': np.random.uniform(1000, 5000, size=n_failures),
            'maintenance_type': np.random.choice(['corrective', 'preventive', 'predictive'], n_failures, p=[0.6, 0.3, 0.1])
        })

        # 2. Dados de energia (séries temporais) - MAIS REALISTAS
        n_hours = 8760  # 1 ano
        dates = pd.date_range(start='2024-01-01', periods=n_hours, freq='h')

        hour_of_day = dates.hour
        day_of_week = dates.dayofweek
        month = dates.month

        # Padrões mais complexos
        daily_pattern = 300 + 200 * np.sin((hour_of_day - 6) * np.pi / 12)
        weekly_pattern = np.where(day_of_week >= 5, 0.4, 1.0)
        seasonal_pattern = 1 + 0.2 * np.sin((month - 6) * np.pi / 6)

        # Adicionar componente de tendência e ruído autocorrelacionado
        trend = np.linspace(0, 50, n_hours)  # Tendência de aumento
        noise = np.random.normal(0, 15, n_hours)

        # Autocorrelação no ruído (mais realista)
        for i in range(1, len(noise)):
            noise[i] = 0.7 * noise[i-1] + 0.3 * noise[i]

        base_consumption = daily_pattern * weekly_pattern * seasonal_pattern + trend + noise
        base_consumption = np.clip(base_consumption, 50, 800)  # Limitar valores

        # Produção correlacionada com consumo
        production = base_consumption * 0.8 + np.random.normal(0, 10, n_hours)
        production = np.clip(production, 20, 600)

        # Temperatura correlacionada com hora/mês
        temperature = 20 + 10 * np.sin((hour_of_day - 12) * np.pi / 12) + 8 * np.sin((month - 6) * np.pi / 6)
        temperature += np.random.normal(0, 3, n_hours)

        energy_data = pd.DataFrame({
            'timestamp': dates,
            'consumption_kwh': base_consumption,
            'production_tons': production,
            'efficiency_kwh_per_ton': base_consumption / production,
            'temperature_c': temperature,
            'hour': hour_of_day,
            'day_of_week': day_of_week,
            'month': month,
            'is_weekend': (day_of_week >= 5).astype(int)
        })

        # 3. Dados de alarmes para anomalias
        n_alarms = 1000
        alarm_data = pd.DataFrame({
            'timestamp': [datetime.now() - timedelta(hours=n_alarms-i) for i in range(n_alarms)],
            'alarm_type': np.random.choice(['overheating', 'vibration', 'overcurrent', 'bearing'], n_alarms, p=[0.4, 0.3, 0.2, 0.1]),
            'severity': np.random.choice(['low', 'medium', 'critical'], n_alarms, p=[0.5, 0.3, 0.2]),
            'duration_minutes': np.random.gamma(shape=2, scale=30, size=n_alarms),
            'temperature_c': np.random.normal(35, 15, size=n_alarms)
        })

        print(f"✅ Dados sintéticos gerados:")
        print(f"  • Manutenção: {len(maintenance_data)} eventos")
        print(f"  • Energia: {len(energy_data)} registros")
        print(f"  • Alarmes: {len(alarm_data)} eventos")

        return {
            'maintenance': maintenance_data,
            'energy': energy_data,
            'alarms': alarm_data
        }

    def calculate_regression_metrics(self, y_true, y_pred) -> Dict[str, float]:
        """Calcula métricas de regressão"""
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        # MAPE com proteção contra divisão por zero
        mask = y_true != 0
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }

    def test_mtbf_mttr_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 1: Análise de Confiabilidade (MTBF/MTTR)
        Sem mudanças - já está excelente
        """
        print("\n" + "="*80)
        print("📊 TESTE 1: Análise de Confiabilidade (MTBF/MTTR)")
        print("="*80)

        mtbf_values = data['mtbf_hours'].values
        mttr_values = data['mttr_hours'].values

        # Estatísticas MTBF
        mtbf_stats = {
            'mean': float(np.mean(mtbf_values)),
            'median': float(np.median(mtbf_values)),
            'std': float(np.std(mtbf_values)),
            'min': float(np.min(mtbf_values)),
            'max': float(np.max(mtbf_values))
        }

        # Estatísticas MTTR
        mttr_stats = {
            'mean': float(np.mean(mttr_values)),
            'median': float(np.median(mttr_values)),
            'std': float(np.std(mttr_values)),
            'min': float(np.min(mttr_values)),
            'max': float(np.max(mttr_values))
        }

        # Ajustar distribuição de Weibull
        shape, loc, scale = weibull_min.fit(mtbf_values, floc=0)

        # Calcular confiabilidade em diferentes tempos
        times = [100, 200, 500, 1000]
        reliability = {f'{t}h': float(weibull_min.sf(t, shape, loc, scale)) for t in times}

        # Taxa de falha e disponibilidade
        failure_rate = 1 / mtbf_stats['mean']
        availability = mtbf_stats['mean'] / (mtbf_stats['mean'] + mttr_stats['mean'])

        # Análise por equipamento
        equipment_analysis = []
        for eq_id in data['equipment_id'].unique():
            eq_data = data[data['equipment_id'] == eq_id]
            equipment_analysis.append({
                'equipment_id': eq_id,
                'n_failures': len(eq_data),
                'mtbf_mean': float(eq_data['mtbf_hours'].mean()),
                'mttr_mean': float(eq_data['mttr_hours'].mean()),
                'total_cost': float(eq_data['cost_brl'].sum())
            })

        print(f"✅ MTBF médio: {mtbf_stats['mean']:.1f}h ± {mtbf_stats['std']:.1f}h")
        print(f"✅ MTTR médio: {mttr_stats['mean']:.1f}h ± {mttr_stats['std']:.1f}h")
        print(f"✅ Disponibilidade: {availability*100:.2f}%")
        print(f"✅ Weibull shape: {shape:.3f}, scale: {scale:.1f}")

        return {
            'mtbf': mtbf_stats,
            'mttr': mttr_stats,
            'weibull_params': {'shape': float(shape), 'scale': float(scale)},
            'reliability': reliability,
            'failure_rate_per_hour': float(failure_rate),
            'availability': float(availability),
            'equipment_analysis': equipment_analysis
        }

    def create_lstm_model(self, lookback: int, n_features: int) -> Sequential:
        """Cria modelo LSTM com arquitetura otimizada"""
        model = Sequential([
            # Primeira camada LSTM bidirecional
            Bidirectional(LSTM(128, return_sequences=True, input_shape=(lookback, n_features))),
            Dropout(0.2),

            # Segunda camada LSTM
            LSTM(64, return_sequences=False),
            Dropout(0.2),

            # Camadas densas
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(16, activation='relu'),
            Dense(1)  # Saída: previsão de consumo
        ])

        # Compilar com otimizador Adam e learning rate adaptativo
        optimizer = keras.optimizers.Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

        return model

    def prepare_lstm_data(self, data: pd.DataFrame, lookback: int = 168) -> Tuple:
        """Prepara dados para LSTM (lookback de 7 dias)"""
        # Features para LSTM
        feature_cols = ['consumption_kwh', 'production_tons', 'efficiency_kwh_per_ton',
                       'temperature_c', 'hour']

        # Normalizar
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data[feature_cols])

        # Criar sequências
        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i])
            y.append(scaled_data[i, 0])  # Prever consumption_kwh

        X = np.array(X)
        y = np.array(y)

        # Split temporal (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        return X_train, X_test, y_train, y_test, scaler

    def test_lstm_energy_prediction(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 2: LSTM REAL para Previsão de Energia (APRIMORADO)
        """
        print("\n" + "="*80)
        print("🧠 TESTE 2: LSTM para Previsão de Energia")
        print("="*80)

        lookback = 168  # 7 dias
        X_train, X_test, y_train, y_test, scaler = self.prepare_lstm_data(data, lookback)

        print(f"📊 Dados preparados:")
        print(f"  • Train: {len(X_train)} amostras")
        print(f"  • Test: {len(X_test)} amostras")
        print(f"  • Lookback: {lookback} horas")
        print(f"  • Features: {X_train.shape[2]}")

        if TENSORFLOW_AVAILABLE:
            print("🧠 Treinando LSTM real...")

            # Criar modelo
            model = self.create_lstm_model(lookback, X_train.shape[2])

            # Callbacks
            early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.00001)

            # Treinar
            history = model.fit(
                X_train, y_train,
                validation_split=0.2,
                epochs=50,
                batch_size=32,
                callbacks=[early_stop, reduce_lr],
                verbose=0  # Silencioso para não poluir output
            )

            # Prever
            y_pred = model.predict(X_test, verbose=0).flatten()

            # Desnormalizar
            y_test_denorm = scaler.inverse_transform(
                np.column_stack([y_test, np.zeros((len(y_test), 4))])
            )[:, 0]
            y_pred_denorm = scaler.inverse_transform(
                np.column_stack([y_pred, np.zeros((len(y_pred), 4))])
            )[:, 0]

            # Métricas
            metrics = self.calculate_regression_metrics(y_test_denorm, y_pred_denorm)

            # Acurácia direcional
            direction_actual = np.diff(y_test_denorm) > 0
            direction_pred = np.diff(y_pred_denorm) > 0
            directional_accuracy = np.mean(direction_actual == direction_pred)

            print(f"✅ RMSE: {metrics['rmse']:.2f} kWh")
            print(f"✅ R²: {metrics['r2']:.4f}")
            print(f"✅ MAPE: {metrics['mape']:.2f}%")
            print(f"✅ Direcional Accuracy: {directional_accuracy*100:.2f}%")

            return {
                'metrics': metrics,
                'directional_accuracy': float(directional_accuracy),
                'training_history': {
                    'final_loss': float(history.history['loss'][-1]),
                    'final_val_loss': float(history.history['val_loss'][-1]),
                    'epochs_trained': len(history.history['loss'])
                },
                'model_type': 'LSTM_Real',
                'n_train': len(X_train),
                'n_test': len(X_test)
            }

        else:
            # Fallback: RandomForest
            print("🌲 Usando Random Forest (TensorFlow não disponível)...")

            # Flatten das sequências para Random Forest
            X_train_flat = X_train.reshape(X_train.shape[0], -1)
            X_test_flat = X_test.reshape(X_test.shape[0], -1)

            rf = RandomForestRegressor(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1)
            rf.fit(X_train_flat, y_train)
            y_pred = rf.predict(X_test_flat)

            # Desnormalizar
            y_test_denorm = scaler.inverse_transform(
                np.column_stack([y_test, np.zeros((len(y_test), 4))])
            )[:, 0]
            y_pred_denorm = scaler.inverse_transform(
                np.column_stack([y_pred, np.zeros((len(y_pred), 4))])
            )[:, 0]

            metrics = self.calculate_regression_metrics(y_test_denorm, y_pred_denorm)

            direction_actual = np.diff(y_test_denorm) > 0
            direction_pred = np.diff(y_pred_denorm) > 0
            directional_accuracy = np.mean(direction_actual == direction_pred)

            print(f"✅ RMSE: {metrics['rmse']:.2f} kWh")
            print(f"✅ R²: {metrics['r2']:.4f}")
            print(f"✅ MAPE: {metrics['mape']:.2f}%")
            print(f"✅ Direcional Accuracy: {directional_accuracy*100:.2f}%")

            return {
                'metrics': metrics,
                'directional_accuracy': float(directional_accuracy),
                'training_history': None,
                'model_type': 'RandomForest',
                'n_train': len(X_train),
                'n_test': len(X_test)
            }

    def test_efficiency_model_enhanced(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 3: Modelo de Eficiência APRIMORADO (Random Forest + Gradient Boosting)
        """
        print("\n" + "="*80)
        print("📈 TESTE 3: Modelo de Eficiência Energética (APRIMORADO)")
        print("="*80)

        # Features expandidas
        feature_cols = [
            'production_tons', 'temperature_c', 'hour', 'month',
            'day_of_week', 'is_weekend'
        ]
        X = data[feature_cols].values
        y = data['efficiency_kwh_per_ton'].values

        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        print(f"📊 Features: {len(feature_cols)}")
        print(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")

        # 1. Random Forest
        print("\n🌲 Testando Random Forest...")
        rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        y_pred_rf = rf.predict(X_test)
        metrics_rf = self.calculate_regression_metrics(y_test, y_pred_rf)

        # Cross-validation
        cv_scores_rf = cross_val_score(rf, X_train, y_train, cv=5, scoring='r2')

        print(f"  • R²: {metrics_rf['r2']:.4f} (CV: {cv_scores_rf.mean():.4f} ± {cv_scores_rf.std():.4f})")
        print(f"  • MAPE: {metrics_rf['mape']:.2f}%")

        # 2. Gradient Boosting
        print("\n🚀 Testando Gradient Boosting...")
        gb = GradientBoostingRegressor(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            random_state=42
        )
        gb.fit(X_train, y_train)
        y_pred_gb = gb.predict(X_test)
        metrics_gb = self.calculate_regression_metrics(y_test, y_pred_gb)

        cv_scores_gb = cross_val_score(gb, X_train, y_train, cv=5, scoring='r2')

        print(f"  • R²: {metrics_gb['r2']:.4f} (CV: {cv_scores_gb.mean():.4f} ± {cv_scores_gb.std():.4f})")
        print(f"  • MAPE: {metrics_gb['mape']:.2f}%")

        # 3. Escolher melhor modelo
        best_model = 'RandomForest' if metrics_rf['r2'] > metrics_gb['r2'] else 'GradientBoosting'
        best_metrics = metrics_rf if best_model == 'RandomForest' else metrics_gb
        best_clf = rf if best_model == 'RandomForest' else gb

        print(f"\n✅ Melhor modelo: {best_model}")
        print(f"✅ R²: {best_metrics['r2']:.4f}")
        print(f"✅ MAPE: {best_metrics['mape']:.2f}%")
        print(f"✅ RMSE: {best_metrics['rmse']:.4f} kWh/ton")

        # Feature importance
        feature_importance = dict(zip(feature_cols, best_clf.feature_importances_))
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True))

        print(f"\n📊 Feature Importance (Top 5):")
        for feat, imp in list(feature_importance.items())[:5]:
            print(f"  • {feat}: {imp:.4f}")

        return {
            'best_model': best_model,
            'metrics': best_metrics,
            'rf_metrics': metrics_rf,
            'gb_metrics': metrics_gb,
            'rf_cv_scores': {'mean': float(cv_scores_rf.mean()), 'std': float(cv_scores_rf.std())},
            'gb_cv_scores': {'mean': float(cv_scores_gb.mean()), 'std': float(cv_scores_gb.std())},
            'feature_importance': {k: float(v) for k, v in feature_importance.items()},
            'n_features': len(feature_cols),
            'n_train': len(X_train),
            'n_test': len(X_test)
        }

    def test_anomaly_detection(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Teste 4: Detecção de Anomalias (sem mudanças - já está bom)"""
        print("\n" + "="*80)
        print("🚨 TESTE 4: Detecção de Anomalias")
        print("="*80)

        from sklearn.preprocessing import LabelEncoder

        # Preparar features
        le_type = LabelEncoder()
        le_severity = LabelEncoder()

        features = pd.DataFrame({
            'alarm_type': le_type.fit_transform(data['alarm_type']),
            'severity': le_severity.fit_transform(data['severity']),
            'duration_minutes': data['duration_minutes'],
            'temperature_c': data['temperature_c']
        })

        # Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )

        predictions = iso_forest.fit_predict(features)
        scores = iso_forest.score_samples(features)

        # Identificar anomalias
        anomalies_idx = np.where(predictions == -1)[0]
        n_anomalies = len(anomalies_idx)

        print(f"✅ Amostras analisadas: {len(data)}")
        print(f"✅ Anomalias detectadas: {n_anomalies} ({n_anomalies/len(data)*100:.2f}%)")
        print(f"✅ Score médio: {scores.mean():.3f} ± {scores.std():.3f}")

        return {
            'n_samples': len(data),
            'n_anomalies': int(n_anomalies),
            'anomaly_rate': float(n_anomalies / len(data)),
            'score_stats': {
                'mean': float(scores.mean()),
                'std': float(scores.std()),
                'min': float(scores.min()),
                'max': float(scores.max()),
                'q25': float(np.percentile(scores, 25)),
                'q50': float(np.percentile(scores, 50)),
                'q75': float(np.percentile(scores, 75))
            },
            'anomaly_examples': [
                {
                    'index': int(idx),
                    'alarm_type': data.iloc[idx]['alarm_type'],
                    'severity': data.iloc[idx]['severity'],
                    'duration_minutes': float(data.iloc[idx]['duration_minutes']),
                    'temperature_c': float(data.iloc[idx]['temperature_c']),
                    'anomaly_score': float(scores[idx])
                }
                for idx in anomalies_idx[:10]
            ]
        }

    def test_correlation_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Teste 5: Análise de Correlação (sem mudanças)"""
        print("\n" + "="*80)
        print("🔗 TESTE 5: Análise de Correlação")
        print("="*80)

        numeric_cols = ['consumption_kwh', 'production_tons', 'efficiency_kwh_per_ton',
                       'temperature_c', 'hour']

        # Correlação de Pearson
        pearson_corr = data[numeric_cols].corr(method='pearson')

        # Correlação de Spearman
        spearman_corr = data[numeric_cols].corr(method='spearman')

        # P-values
        p_values = {}
        for i, col1 in enumerate(numeric_cols):
            for j, col2 in enumerate(numeric_cols):
                if i < j:
                    r, p = stats.pearsonr(data[col1], data[col2])
                    key = f"{col1}_vs_{col2}"
                    p_values[key] = {
                        'correlation': float(r),
                        'p_value': float(p),
                        'significant': str(p < 0.05)
                    }

        # Identificar correlações fortes
        strong_correlations = [
            {'pair': k, **v}
            for k, v in p_values.items()
            if abs(v['correlation']) > 0.7 and v['significant'] == 'True'
        ]

        print(f"✅ Variáveis analisadas: {len(numeric_cols)}")
        print(f"✅ Correlações fortes encontradas: {len(strong_correlations)}")

        if strong_correlations:
            print(f"\n📊 Top 5 Correlações:")
            for corr in sorted(strong_correlations, key=lambda x: abs(x['correlation']), reverse=True)[:5]:
                print(f"  • {corr['pair']}: r={corr['correlation']:.3f} (p={corr['p_value']:.4f})")

        return {
            'pearson': pearson_corr.to_dict(),
            'spearman': spearman_corr.to_dict(),
            'p_values': p_values,
            'strong_correlations': strong_correlations,
            'n_variables': len(numeric_cols)
        }

    def test_cost_optimization(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Teste 6: Otimização de Custos (sem mudanças)"""
        print("\n" + "="*80)
        print("💰 TESTE 6: Otimização de Custos de Energia")
        print("="*80)

        # Tarifas
        tariffs = {
            'peak': 0.85,         # 18h-21h
            'intermediate': 0.65,  # 17h-18h, 21h-22h
            'off_peak': 0.45      # 22h-17h
        }

        # Classificar por período
        def get_tariff_period(hour):
            if 18 <= hour < 21:
                return 'peak', tariffs['peak']
            elif hour in [17, 21]:
                return 'intermediate', tariffs['intermediate']
            else:
                return 'off_peak', tariffs['off_peak']

        data['period'], data['tariff'] = zip(*data['hour'].map(get_tariff_period))

        # Custo atual
        data['cost_current'] = data['consumption_kwh'] * data['tariff']
        cost_current_yearly = data['cost_current'].sum()
        cost_current_monthly = cost_current_yearly / 12

        # Simulação: deslocar 20% da carga de ponta para fora-ponta
        data['consumption_optimized'] = data['consumption_kwh']
        peak_mask = data['period'] == 'peak'
        peak_consumption = data.loc[peak_mask, 'consumption_kwh'].sum()
        shifted_load = peak_consumption * 0.20

        # Reduzir ponta
        data.loc[peak_mask, 'consumption_optimized'] *= 0.80

        # Aumentar fora-ponta
        off_peak_mask = data['period'] == 'off_peak'
        n_off_peak_hours = off_peak_mask.sum()
        data.loc[off_peak_mask, 'consumption_optimized'] += shifted_load / n_off_peak_hours

        # Custo otimizado
        data['cost_optimized'] = data['consumption_optimized'] * data['tariff']
        cost_optimized_yearly = data['cost_optimized'].sum()
        cost_optimized_monthly = cost_optimized_yearly / 12

        # Economia
        savings_yearly = cost_current_yearly - cost_optimized_yearly
        savings_monthly = savings_yearly / 12
        savings_percentage = (savings_yearly / cost_current_yearly) * 100

        print(f"✅ Custo atual: R$ {cost_current_monthly:,.2f}/mês")
        print(f"✅ Custo otimizado: R$ {cost_optimized_monthly:,.2f}/mês")
        print(f"✅ Economia: R$ {savings_monthly:,.2f}/mês ({savings_percentage:.1f}%)")
        print(f"✅ Economia anual: R$ {savings_yearly:,.2f}")

        # Análise por tarifa
        tariff_analysis = []
        for period, tariff in tariffs.items():
            period_mask = data['period'] == period
            tariff_analysis.append({
                'period': period,
                'tariff_brl': tariff,
                'consumption_current_kwh': float(data.loc[period_mask, 'consumption_kwh'].sum()),
                'consumption_optimized_kwh': float(data.loc[period_mask, 'consumption_optimized'].sum()),
                'cost_current_brl': float(data.loc[period_mask, 'cost_current'].sum()),
                'cost_optimized_brl': float(data.loc[period_mask, 'cost_optimized'].sum())
            })

        return {
            'cost_current': {
                'total_yearly': float(cost_current_yearly),
                'monthly': float(cost_current_monthly)
            },
            'cost_optimized': {
                'total_yearly': float(cost_optimized_yearly),
                'monthly': float(cost_optimized_monthly)
            },
            'savings': {
                'total_yearly': float(savings_yearly),
                'monthly': float(savings_monthly),
                'percentage': float(savings_percentage)
            },
            'tariff_analysis': tariff_analysis,
            'optimization_strategy': 'Deslocar 20% da carga de ponta (18h-21h) para fora ponta (22h-6h)'
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes ML/DS"""
        print("="*80)
        print("🚀 INICIANDO TESTES APRIMORADOS DE MODELOS ML/DS")
        print("="*80)

        # Gerar dados
        data = self.generate_synthetic_data()

        print("\n⏳ Executando 6 testes de modelos ML/DS...\n")

        # Executar testes
        self.results['test_1_mtbf_mttr'] = self.test_mtbf_mttr_analysis(data['maintenance'])
        self.results['test_2_lstm'] = self.test_lstm_energy_prediction(data['energy'])
        self.results['test_3_efficiency'] = self.test_efficiency_model_enhanced(data['energy'])
        self.results['test_4_anomalies'] = self.test_anomaly_detection(data['alarms'])
        self.results['test_5_correlation'] = self.test_correlation_analysis(data['energy'])
        self.results['test_6_optimization'] = self.test_cost_optimization(data['energy'])

        # Gerar relatório
        self.generate_report()

        return self.results

    def generate_report(self):
        """Gera relatório JSON e sumário"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/app/ml_test_results_enhanced_{timestamp}.json"

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DOS TESTES ML/DS (APRIMORADO)")
        print("="*80)
        print("\n✅ TODOS OS 6 MODELOS TESTADOS COM SUCESSO\n")

        print("📈 Resumo das Métricas:\n")

        # Teste 1
        mtbf = self.results['test_1_mtbf_mttr']['mtbf']['mean']
        mttr = self.results['test_1_mtbf_mttr']['mttr']['mean']
        avail = self.results['test_1_mtbf_mttr']['availability']
        print(f"1. MTBF/MTTR Analysis:")
        print(f"   • MTBF: {mtbf:.1f}h")
        print(f"   • MTTR: {mttr:.1f}h")
        print(f"   • Disponibilidade: {avail*100:.2f}%\n")

        # Teste 2
        lstm_r2 = self.results['test_2_lstm']['metrics']['r2']
        lstm_mape = self.results['test_2_lstm']['metrics']['mape']
        lstm_dir = self.results['test_2_lstm']['directional_accuracy']
        lstm_type = self.results['test_2_lstm']['model_type']
        print(f"2. {lstm_type} Energy Prediction:")
        print(f"   • R²: {lstm_r2:.4f}")
        print(f"   • MAPE: {lstm_mape:.2f}%")
        print(f"   • Direcional Accuracy: {lstm_dir*100:.2f}%\n")

        # Teste 3
        eff_model = self.results['test_3_efficiency']['best_model']
        eff_r2 = self.results['test_3_efficiency']['metrics']['r2']
        eff_mape = self.results['test_3_efficiency']['metrics']['mape']
        print(f"3. {eff_model} Efficiency:")
        print(f"   • R²: {eff_r2:.4f}")
        print(f"   • MAPE: {eff_mape:.2f}%\n")

        # Teste 4
        n_anomalies = self.results['test_4_anomalies']['n_anomalies']
        anom_rate = self.results['test_4_anomalies']['anomaly_rate']
        print(f"4. Anomaly Detection:")
        print(f"   • Anomalias detectadas: {n_anomalies} ({anom_rate*100:.2f}%)\n")

        # Teste 5
        n_strong = len(self.results['test_5_correlation']['strong_correlations'])
        print(f"5. Correlation Analysis:")
        print(f"   • Correlações fortes: {n_strong}\n")

        # Teste 6
        savings = self.results['test_6_optimization']['savings']['monthly']
        savings_pct = self.results['test_6_optimization']['savings']['percentage']
        print(f"6. Cost Optimization:")
        print(f"   • Economia potencial: R$ {savings:,.2f}/mês ({savings_pct:.1f}%)\n")

        print(f"✅ Relatório completo salvo em: {report_path}")
        print("\n" + "="*80)
        print("✅ TESTES APRIMORADOS CONCLUÍDOS COM SUCESSO!")
        print("="*80)


async def main():
    """Main"""
    tester = EnhancedMLModelTester()
    results = await tester.run_all_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())
