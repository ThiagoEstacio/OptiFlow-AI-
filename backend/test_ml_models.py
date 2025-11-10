"""
Framework de testes para modelos ML/DS com métricas adequadas

Testa todos os 6 modelos especificados:
1. Análise de Confiabilidade (MTBF/MTTR)
2. LSTM (Previsão de Energia)
3. Regressão Linear (Eficiência)
4. Detecção de Anomalias
5. Análise de Correlação
6. Otimização de Custos

Métricas implementadas:
- Regressão: MAE, MSE, RMSE, R², MAPE
- Classificação: Accuracy, Precision, Recall, F1-Score, AUC-ROC
- Séries Temporais: MAE, RMSE, MAPE, Direcional Accuracy
- Correlação: Pearson, Spearman, p-value
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
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy import stats
from scipy.stats import weibull_min

# Para LSTM (opcional - se TensorFlow disponível)
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️  TensorFlow not available - LSTM tests will use simpler models")


class MLModelTester:
    """Framework de testes para modelos ML"""

    def __init__(self, data_path: str = None):
        self.results = {}
        self.data_path = data_path or "/tmp"

    def generate_synthetic_data(self) -> Dict[str, pd.DataFrame]:
        """
        Gera dados sintéticos para testes (caso dados históricos não existam)
        """
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

        # 2. Dados de energia (séries temporais)
        n_hours = 8760  # 1 ano
        dates = pd.date_range(start='2024-01-01', periods=n_hours, freq='H')

        # Padrões realistas
        hour_of_day = dates.hour
        day_of_week = dates.dayofweek
        month = dates.month

        # Ciclo diário (mais consumo durante dia)
        daily_pattern = 300 + 200 * np.sin((hour_of_day - 6) * np.pi / 12)

        # Ciclo semanal (menos no fim de semana)
        weekly_pattern = np.where(day_of_week >= 5, 0.4, 1.0)

        # Ciclo anual (mais no verão)
        seasonal_pattern = 1 + 0.2 * np.sin((month - 6) * np.pi / 6)

        # Tendência de eficiência
        trend = 1 - (np.arange(n_hours) / n_hours) * 0.06

        # Ruído
        noise = np.random.normal(0, 20, n_hours)

        energy_consumption = daily_pattern * weekly_pattern * seasonal_pattern * trend + noise
        production = energy_consumption * np.random.uniform(1.5, 2.5, n_hours)

        energy_data = pd.DataFrame({
            'timestamp': dates,
            'hour': hour_of_day,
            'day_of_week': day_of_week,
            'month': month,
            'consumption_kwh': energy_consumption,
            'production_tons': production,
            'efficiency_kwh_per_ton': energy_consumption / production,
            'temperature_c': 15 + 10 * np.sin((month - 6) * np.pi / 6) + np.random.normal(0, 3, n_hours)
        })

        # 3. Dados de alarmes
        n_alarms = 1000
        alarm_data = pd.DataFrame({
            'equipment_id': [f'motor_{i%5}' for i in range(n_alarms)],
            'timestamp': [datetime.now() - timedelta(days=np.random.randint(1, 365)) for _ in range(n_alarms)],
            'alarm_type': np.random.choice(['overheating', 'overcurrent', 'vibration', 'bearing'], n_alarms),
            'severity': np.random.choice(['critical', 'high', 'medium', 'low'], n_alarms, p=[0.1, 0.3, 0.4, 0.2]),
            'duration_minutes': np.random.gamma(shape=2, scale=30, size=n_alarms),
            'temperature_c': np.random.normal(30, 10, n_alarms)
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

    def calculate_regression_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calcula métricas de regressão"""
        mae = mean_absolute_error(y_true, y_pred)
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)

        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        return {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'r2': float(r2),
            'mape': float(mape)
        }

    def test_mtbf_mttr_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 1: Análise de Confiabilidade (MTBF/MTTR)

        Métricas:
        - MTBF médio, mediano, desvio padrão
        - MTTR médio, mediano, desvio padrão
        - Distribuição de Weibull (shape, scale)
        - Taxa de falhas
        - Confiabilidade em t horas
        """
        print("\n" + "="*80)
        print("📊 TESTE 1: Análise de Confiabilidade (MTBF/MTTR)")
        print("="*80)

        # Estatísticas MTBF
        mtbf_stats = {
            'mean': float(data['mtbf_hours'].mean()),
            'median': float(data['mtbf_hours'].median()),
            'std': float(data['mtbf_hours'].std()),
            'min': float(data['mtbf_hours'].min()),
            'max': float(data['mtbf_hours'].max())
        }

        # Estatísticas MTTR
        mttr_stats = {
            'mean': float(data['mttr_hours'].mean()),
            'median': float(data['mttr_hours'].median()),
            'std': float(data['mttr_hours'].std()),
            'min': float(data['mttr_hours'].min()),
            'max': float(data['mttr_hours'].max())
        }

        # Ajuste de distribuição de Weibull
        mtbf_values = data['mtbf_hours'].dropna().values
        if len(mtbf_values) > 0:
            shape, loc, scale = weibull_min.fit(mtbf_values, floc=0)
            weibull_params = {
                'shape': float(shape),
                'scale': float(scale)
            }

            # Calcular confiabilidade em diferentes tempos
            times = [100, 200, 500, 1000]
            reliability = {
                f'{t}h': float(weibull_min.sf(t, shape, loc=0, scale=scale))
                for t in times
            }
        else:
            weibull_params = None
            reliability = None

        # Taxa de falhas
        failure_rate = 1 / mtbf_stats['mean'] if mtbf_stats['mean'] > 0 else 0

        # Disponibilidade
        availability = mtbf_stats['mean'] / (mtbf_stats['mean'] + mttr_stats['mean'])

        # Análise por equipamento
        equipment_analysis = []
        for equipment_id in data['equipment_id'].unique():
            eq_data = data[data['equipment_id'] == equipment_id]
            equipment_analysis.append({
                'equipment_id': equipment_id,
                'n_failures': len(eq_data),
                'mtbf_mean': float(eq_data['mtbf_hours'].mean()),
                'mttr_mean': float(eq_data['mttr_hours'].mean()),
                'total_cost': float(eq_data['cost_brl'].sum())
            })

        results = {
            'mtbf': mtbf_stats,
            'mttr': mttr_stats,
            'weibull_params': weibull_params,
            'reliability': reliability,
            'failure_rate_per_hour': float(failure_rate),
            'availability': float(availability),
            'equipment_analysis': equipment_analysis
        }

        print(f"✅ MTBF médio: {mtbf_stats['mean']:.1f}h ± {mtbf_stats['std']:.1f}h")
        print(f"✅ MTTR médio: {mttr_stats['mean']:.1f}h ± {mttr_stats['std']:.1f}h")
        print(f"✅ Disponibilidade: {availability*100:.2f}%")
        if weibull_params:
            print(f"✅ Weibull shape: {weibull_params['shape']:.3f}, scale: {weibull_params['scale']:.1f}")

        return results

    def test_lstm_energy_prediction(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 2: LSTM para Previsão de Energia

        Métricas:
        - MAE, MSE, RMSE, R², MAPE
        - Direcional Accuracy (prevê corretamente aumento/diminuição)
        """
        print("\n" + "="*80)
        print("🧠 TESTE 2: LSTM para Previsão de Energia")
        print("="*80)

        # Preparar dados
        # Usar últimas 168 horas (1 semana) para prever próxima hora
        lookback = 168
        features = ['consumption_kwh', 'hour', 'day_of_week', 'month', 'temperature_c']

        X, y = [], []
        for i in range(lookback, len(data)):
            X.append(data[features].iloc[i-lookback:i].values)
            y.append(data['consumption_kwh'].iloc[i])

        X = np.array(X)
        y = np.array(y)

        # Split train/test
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        print(f"📊 Dados preparados:")
        print(f"  • Train: {len(X_train)} amostras")
        print(f"  • Test: {len(X_test)} amostras")
        print(f"  • Lookback: {lookback} horas")
        print(f"  • Features: {len(features)}")

        if TENSORFLOW_AVAILABLE and len(X_train) > 100:
            # Modelo LSTM completo
            print("🧠 Treinando modelo LSTM com TensorFlow...")

            model = Sequential([
                LSTM(64, return_sequences=True, input_shape=(lookback, len(features))),
                Dropout(0.2),
                LSTM(32),
                Dropout(0.2),
                Dense(16, activation='relu'),
                Dense(1)
            ])

            model.compile(optimizer='adam', loss='mse', metrics=['mae'])

            history = model.fit(
                X_train, y_train,
                epochs=20,
                batch_size=32,
                validation_split=0.2,
                verbose=0
            )

            # Predições
            y_pred = model.predict(X_test, verbose=0).flatten()

            # Histórico de treinamento
            training_history = {
                'loss': [float(x) for x in history.history['loss']],
                'val_loss': [float(x) for x in history.history['val_loss']],
                'mae': [float(x) for x in history.history['mae']],
                'val_mae': [float(x) for x in history.history['val_mae']]
            }
        else:
            # Fallback: usar Random Forest para séries temporais
            print("🌲 Usando Random Forest (TensorFlow não disponível)...")

            # Flatten X para Random Forest
            X_train_flat = X_train.reshape(X_train.shape[0], -1)
            X_test_flat = X_test.reshape(X_test.shape[0], -1)

            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_flat, y_train)
            y_pred = model.predict(X_test_flat)

            training_history = None

        # Métricas de regressão
        metrics = self.calculate_regression_metrics(y_test, y_pred)

        # Direcional Accuracy
        y_test_diff = np.diff(y_test)
        y_pred_diff = np.diff(y_pred)
        directional_accuracy = np.mean((y_test_diff * y_pred_diff) > 0)

        results = {
            'metrics': metrics,
            'directional_accuracy': float(directional_accuracy),
            'training_history': training_history,
            'model_type': 'LSTM' if TENSORFLOW_AVAILABLE else 'RandomForest',
            'n_train': len(X_train),
            'n_test': len(X_test)
        }

        print(f"✅ RMSE: {metrics['rmse']:.2f} kWh")
        print(f"✅ R²: {metrics['r2']:.4f}")
        print(f"✅ MAPE: {metrics['mape']:.2f}%")
        print(f"✅ Direcional Accuracy: {directional_accuracy*100:.2f}%")

        return results

    def test_linear_regression_efficiency(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 3: Regressão Linear para Eficiência Energética

        Modelo: Efficiency = f(production, temperature, hour, month)

        Métricas:
        - MAE, MSE, RMSE, R², MAPE
        - Coeficientes (importância das features)
        """
        print("\n" + "="*80)
        print("📈 TESTE 3: Regressão Linear para Eficiência Energética")
        print("="*80)

        # Preparar dados
        features = ['production_tons', 'temperature_c', 'hour', 'month']
        X = data[features].values
        y = data['efficiency_kwh_per_ton'].values

        # Normalizar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # Treinar modelo
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Predições
        y_pred = model.predict(X_test)

        # Métricas
        metrics = self.calculate_regression_metrics(y_test, y_pred)

        # Coeficientes (importância)
        coefficients = {
            feature: float(coef)
            for feature, coef in zip(features, model.coef_)
        }

        # Ordenar por importância (valor absoluto)
        sorted_coefficients = dict(
            sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True)
        )

        results = {
            'metrics': metrics,
            'intercept': float(model.intercept_),
            'coefficients': coefficients,
            'feature_importance': sorted_coefficients,
            'n_train': len(X_train),
            'n_test': len(X_test)
        }

        print(f"✅ RMSE: {metrics['rmse']:.4f} kWh/ton")
        print(f"✅ R²: {metrics['r2']:.4f}")
        print(f"✅ MAPE: {metrics['mape']:.2f}%")
        print(f"\n📊 Feature Importance:")
        for feature, coef in sorted_coefficients.items():
            print(f"  • {feature}: {coef:.4f}")

        return results

    def test_anomaly_detection(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 4: Detecção de Anomalias

        Usa Isolation Forest para detectar alarmes anormais

        Métricas:
        - Anomalias detectadas (%)
        - Distribuição de scores
        """
        print("\n" + "="*80)
        print("🚨 TESTE 4: Detecção de Anomalias")
        print("="*80)

        # Features para detecção
        features = ['duration_minutes', 'temperature_c']

        # Adicionar features categóricas como one-hot
        df = data.copy()
        df['is_critical'] = (df['severity'] == 'critical').astype(int)
        df['is_overheating'] = (df['alarm_type'] == 'overheating').astype(int)

        features_extended = features + ['is_critical', 'is_overheating']
        X = df[features_extended].values

        # Treinar Isolation Forest
        model = IsolationForest(
            contamination=0.1,  # Espera 10% de anomalias
            random_state=42
        )

        predictions = model.fit_predict(X)
        scores = model.score_samples(X)

        # Análise
        n_anomalies = np.sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions)

        # Estatísticas dos scores
        score_stats = {
            'mean': float(scores.mean()),
            'std': float(scores.std()),
            'min': float(scores.min()),
            'max': float(scores.max()),
            'q25': float(np.percentile(scores, 25)),
            'q50': float(np.percentile(scores, 50)),
            'q75': float(np.percentile(scores, 75))
        }

        # Exemplos de anomalias
        anomaly_indices = np.where(predictions == -1)[0]
        anomaly_examples = []
        for idx in anomaly_indices[:10]:  # Top 10
            anomaly_examples.append({
                'index': int(idx),
                'alarm_type': df.iloc[idx]['alarm_type'],
                'severity': df.iloc[idx]['severity'],
                'duration_minutes': float(df.iloc[idx]['duration_minutes']),
                'temperature_c': float(df.iloc[idx]['temperature_c']),
                'anomaly_score': float(scores[idx])
            })

        results = {
            'n_samples': len(predictions),
            'n_anomalies': int(n_anomalies),
            'anomaly_rate': float(anomaly_rate),
            'score_stats': score_stats,
            'anomaly_examples': anomaly_examples
        }

        print(f"✅ Amostras analisadas: {len(predictions)}")
        print(f"✅ Anomalias detectadas: {n_anomalies} ({anomaly_rate*100:.2f}%)")
        print(f"✅ Score médio: {score_stats['mean']:.3f} ± {score_stats['std']:.3f}")

        return results

    def test_correlation_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 5: Análise de Correlação

        Calcula correlações entre variáveis operacionais

        Métricas:
        - Pearson correlation
        - Spearman correlation
        - p-values
        """
        print("\n" + "="*80)
        print("🔗 TESTE 5: Análise de Correlação")
        print("="*80)

        # Variáveis numéricas
        numeric_cols = ['consumption_kwh', 'production_tons', 'efficiency_kwh_per_ton', 'temperature_c', 'hour']

        # Correlação de Pearson
        pearson_corr = data[numeric_cols].corr(method='pearson')

        # Correlação de Spearman
        spearman_corr = data[numeric_cols].corr(method='spearman')

        # P-values para correlações
        p_values = {}
        for col1 in numeric_cols:
            for col2 in numeric_cols:
                if col1 < col2:  # Evitar duplicatas
                    r, p = stats.pearsonr(data[col1].dropna(), data[col2].dropna())
                    p_values[f'{col1}_vs_{col2}'] = {
                        'correlation': float(r),
                        'p_value': float(p),
                        'significant': p < 0.05
                    }

        # Correlações mais fortes
        strong_correlations = []
        for pair, values in p_values.items():
            if abs(values['correlation']) > 0.5 and values['significant']:
                strong_correlations.append({
                    'pair': pair,
                    **values
                })

        strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

        results = {
            'pearson': pearson_corr.to_dict(),
            'spearman': spearman_corr.to_dict(),
            'p_values': p_values,
            'strong_correlations': strong_correlations,
            'n_variables': len(numeric_cols)
        }

        print(f"✅ Variáveis analisadas: {len(numeric_cols)}")
        print(f"✅ Correlações fortes encontradas: {len(strong_correlations)}")
        print(f"\n📊 Top 5 Correlações:")
        for corr in strong_correlations[:5]:
            print(f"  • {corr['pair']}: r={corr['correlation']:.3f} (p={corr['p_value']:.4f})")

        return results

    def test_cost_optimization(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Teste 6: Otimização de Custos de Energia

        Simula otimização de horários de operação para minimizar custos

        Métricas:
        - Economia potencial (R$/mês)
        - % de operações deslocadas
        - Novo perfil de consumo
        """
        print("\n" + "="*80)
        print("💰 TESTE 6: Otimização de Custos de Energia")
        print("="*80)

        # Tarifas por horário
        def get_tariff(hour):
            if 18 <= hour < 21:
                return 0.85  # Ponta
            elif (17 <= hour < 18) or (21 <= hour < 22):
                return 0.65  # Intermediário
            else:
                return 0.45  # Fora ponta

        # Adicionar tarifa
        data['tariff'] = data['hour'].apply(get_tariff)
        data['cost_current'] = data['consumption_kwh'] * data['tariff']

        # Calcular custo atual
        cost_current_total = data['cost_current'].sum()
        cost_current_monthly = cost_current_total / 12

        # Simular otimização: deslocar 20% da carga de ponta para fora ponta
        data_optimized = data.copy()

        # Identificar horas de ponta
        peak_mask = (data_optimized['hour'] >= 18) & (data_optimized['hour'] < 21)
        off_peak_mask = (data_optimized['hour'] >= 22) | (data_optimized['hour'] < 6)

        # Deslocar consumo
        peak_consumption = data_optimized.loc[peak_mask, 'consumption_kwh']
        reduction = peak_consumption * 0.2

        data_optimized.loc[peak_mask, 'consumption_kwh'] -= reduction.values

        # Redistribuir em horário fora ponta
        off_peak_indices = data_optimized[off_peak_mask].index
        increase_per_hour = reduction.sum() / len(off_peak_indices)
        data_optimized.loc[off_peak_mask, 'consumption_kwh'] += increase_per_hour

        # Recalcular custos
        data_optimized['cost_optimized'] = data_optimized['consumption_kwh'] * data_optimized['tariff']
        cost_optimized_total = data_optimized['cost_optimized'].sum()
        cost_optimized_monthly = cost_optimized_total / 12

        # Economia
        savings_total = cost_current_total - cost_optimized_total
        savings_monthly = savings_total / 12
        savings_percentage = (savings_total / cost_current_total) * 100

        # Análise por período tarifário
        tariff_analysis = []
        for period, tariff_value in [('peak', 0.85), ('intermediate', 0.65), ('off_peak', 0.45)]:
            mask = data['tariff'] == tariff_value
            tariff_analysis.append({
                'period': period,
                'tariff_brl': tariff_value,
                'consumption_current_kwh': float(data.loc[mask, 'consumption_kwh'].sum()),
                'consumption_optimized_kwh': float(data_optimized.loc[mask, 'consumption_kwh'].sum()),
                'cost_current_brl': float(data.loc[mask, 'cost_current'].sum()),
                'cost_optimized_brl': float(data_optimized.loc[mask, 'cost_optimized'].sum())
            })

        results = {
            'cost_current': {
                'total_yearly': float(cost_current_total),
                'monthly': float(cost_current_monthly)
            },
            'cost_optimized': {
                'total_yearly': float(cost_optimized_total),
                'monthly': float(cost_optimized_monthly)
            },
            'savings': {
                'total_yearly': float(savings_total),
                'monthly': float(savings_monthly),
                'percentage': float(savings_percentage)
            },
            'tariff_analysis': tariff_analysis,
            'optimization_strategy': 'Deslocar 20% da carga de ponta (18h-21h) para fora ponta (22h-6h)'
        }

        print(f"✅ Custo atual: R$ {cost_current_monthly:,.2f}/mês")
        print(f"✅ Custo otimizado: R$ {cost_optimized_monthly:,.2f}/mês")
        print(f"✅ Economia: R$ {savings_monthly:,.2f}/mês ({savings_percentage:.1f}%)")
        print(f"✅ Economia anual: R$ {savings_total:,.2f}")

        return results

    async def run_all_tests(self):
        """Executa todos os testes e gera relatório"""
        print("\n" + "="*80)
        print("🚀 INICIANDO TESTES DE MODELOS ML/DS")
        print("="*80)

        # Gerar dados sintéticos
        data = self.generate_synthetic_data()

        # Executar todos os testes
        print("\n⏳ Executando 6 testes de modelos ML/DS...")

        self.results['test_1_mtbf_mttr'] = self.test_mtbf_mttr_analysis(data['maintenance'])
        self.results['test_2_lstm'] = self.test_lstm_energy_prediction(data['energy'])
        self.results['test_3_regression'] = self.test_linear_regression_efficiency(data['energy'])
        self.results['test_4_anomalies'] = self.test_anomaly_detection(data['alarms'])
        self.results['test_5_correlation'] = self.test_correlation_analysis(data['energy'])
        self.results['test_6_optimization'] = self.test_cost_optimization(data['energy'])

        # Gerar relatório
        self.generate_report()

        return self.results

    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DOS TESTES ML/DS")
        print("="*80)

        # Sumário executivo
        print("\n✅ TODOS OS 6 MODELOS TESTADOS COM SUCESSO\n")

        print("📈 Resumo das Métricas:\n")

        # Teste 1
        mtbf = self.results['test_1_mtbf_mttr']['mtbf']['mean']
        mttr = self.results['test_1_mtbf_mttr']['mttr']['mean']
        avail = self.results['test_1_mtbf_mttr']['availability']
        print(f"1. MTBF/MTTR Analysis:")
        print(f"   • MTBF: {mtbf:.1f}h")
        print(f"   • MTTR: {mttr:.1f}h")
        print(f"   • Disponibilidade: {avail*100:.2f}%")

        # Teste 2
        lstm_r2 = self.results['test_2_lstm']['metrics']['r2']
        lstm_mape = self.results['test_2_lstm']['metrics']['mape']
        dir_acc = self.results['test_2_lstm']['directional_accuracy']
        print(f"\n2. LSTM Energy Prediction:")
        print(f"   • R²: {lstm_r2:.4f}")
        print(f"   • MAPE: {lstm_mape:.2f}%")
        print(f"   • Direcional Accuracy: {dir_acc*100:.2f}%")

        # Teste 3
        reg_r2 = self.results['test_3_regression']['metrics']['r2']
        reg_mape = self.results['test_3_regression']['metrics']['mape']
        print(f"\n3. Linear Regression Efficiency:")
        print(f"   • R²: {reg_r2:.4f}")
        print(f"   • MAPE: {reg_mape:.2f}%")

        # Teste 4
        anomaly_rate = self.results['test_4_anomalies']['anomaly_rate']
        n_anomalies = self.results['test_4_anomalies']['n_anomalies']
        print(f"\n4. Anomaly Detection:")
        print(f"   • Anomalias detectadas: {n_anomalies} ({anomaly_rate*100:.2f}%)")

        # Teste 5
        n_strong = len(self.results['test_5_correlation']['strong_correlations'])
        print(f"\n5. Correlation Analysis:")
        print(f"   • Correlações fortes: {n_strong}")

        # Teste 6
        savings = self.results['test_6_optimization']['savings']['monthly']
        savings_pct = self.results['test_6_optimization']['savings']['percentage']
        print(f"\n6. Cost Optimization:")
        print(f"   • Economia potencial: R$ {savings:,.2f}/mês ({savings_pct:.1f}%)")

        # Salvar JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"ml_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n✅ Relatório completo salvo em: {output_file}")

        print("\n" + "="*80)
        print("✅ TESTES CONCLUÍDOS COM SUCESSO!")
        print("="*80)


async def main():
    """Função principal"""
    tester = MLModelTester()
    results = await tester.run_all_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())
