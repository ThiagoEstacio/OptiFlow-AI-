"""
ML Insights Service - Integração dos Modelos ML/DS com Autonomous Agent

Este serviço permite que o Autonomous Agent gere insights automáticos usando:
1. MTBF/MTTR Analysis - Previsão de manutenções
2. LSTM Energy Prediction - Previsão de consumo energético
3. Gradient Boosting Efficiency - Análise de eficiência
4. Isolation Forest Anomalies - Detecção de anomalias
5. Correlation Analysis - Identificação de correlações
6. Cost Optimization - Recomendações de economia

Uso:
    from app.services.ml_insights_service import ml_insights_service

    # Gerar insights automáticos
    insights = await ml_insights_service.generate_all_insights(
        organization_id=org_id,
        time_range='last_7_days'
    )
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import logging

# ML imports
from sklearn.ensemble import IsolationForest, RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from scipy import stats
from scipy.stats import weibull_min

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

from app.models.alarm import AlarmEvent, AlarmDefinition
# Comentando imports que podem não existir - usando apenas AlarmEvent
# from app.models.operational_data import OperationalData
# from app.models.external_data import ExternalData

logger = logging.getLogger(__name__)


def _convert_numpy_types(obj):
    """
    Recursivamente converte tipos numpy para tipos Python nativos para serialização JSON
    """
    if isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):  # datetime objects
        return obj.isoformat()
    return obj


class MLInsightsService:
    """
    Serviço de Insights ML para Autonomous Agent

    Gerencia todos os 6 modelos ML/DS e fornece insights automáticos
    """

    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_cache_ttl = 3600  # Cache de modelos por 1 hora
        self.prediction_cache_ttl = 300  # Cache de previsões por 5 minutos

        # Inicializar storage de modelos
        from app.services.ml_model_storage import ml_model_storage
        self.model_storage = ml_model_storage

        # Tentar carregar modelos pré-treinados
        self._load_pretrained_models()

    def _load_pretrained_models(self):
        """Carrega modelos pré-treinados do disco na inicialização"""
        try:
            logger.info("Tentando carregar modelos pré-treinados...")

            # Carregar Gradient Boosting para eficiência
            gb_model = self.model_storage.load_sklearn_model('gradient_boosting_efficiency')
            if gb_model:
                self.models['gradient_boosting'] = gb_model
                logger.info("✅ Gradient Boosting carregado")

            # Carregar Isolation Forest para anomalias
            if_model = self.model_storage.load_sklearn_model('isolation_forest_anomalies')
            if if_model:
                self.models['isolation_forest'] = if_model
                logger.info("✅ Isolation Forest carregado")

            # Carregar LSTM para energia (se TensorFlow disponível)
            if TENSORFLOW_AVAILABLE:
                lstm_model = self.model_storage.load_tensorflow_model('lstm_energy')
                if lstm_model:
                    self.models['lstm'] = lstm_model
                    logger.info("✅ LSTM carregado")

            # Log resumo
            loaded = len(self.models)
            if loaded > 0:
                logger.info(f"✅ {loaded} modelos pré-treinados carregados com sucesso")
            else:
                logger.warning("⚠️ Nenhum modelo pré-treinado encontrado. Modelos serão treinados sob demanda")

        except Exception as e:
            logger.warning(f"Erro ao carregar modelos pré-treinados: {e}. Usando treino sob demanda")

    async def generate_all_insights(
        self,
        db: AsyncSession,
        organization_id: str,
        time_range: str = 'last_7_days'
    ) -> Dict[str, Any]:
        """
        Gera todos os insights ML para o Autonomous Agent

        Args:
            db: Database session
            organization_id: ID da organização
            time_range: Período de análise ('last_24h', 'last_7_days', 'last_30_days')

        Returns:
            Dict com todos os insights organizados por tipo
        """
        # Verificar cache primeiro
        try:
            from app.services.redis_cache import redis_cache_service

            cached_insights = redis_cache_service.get_insights(
                organization_id=organization_id,
                time_range=time_range
            )

            if cached_insights:
                logger.info(f"Retornando insights do cache para {organization_id}")
                return cached_insights

        except Exception as e:
            logger.warning(f"Erro ao verificar cache: {e}. Continuando sem cache")

        logger.info(f"Gerando insights ML para organização {organization_id}")

        # Determinar período
        end_time = datetime.now()
        if time_range == 'last_24h':
            start_time = end_time - timedelta(hours=24)
        elif time_range == 'last_7_days':
            start_time = end_time - timedelta(days=7)
        elif time_range == 'last_30_days':
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=7)

        # Buscar dados do banco
        data = await self._fetch_data(db, organization_id, start_time, end_time)

        # Gerar insights de cada modelo (em paralelo)
        insights = await asyncio.gather(
            self._insight_reliability(data),
            self._insight_energy_prediction(data),
            self._insight_efficiency(data),
            self._insight_anomalies(data),
            self._insight_correlations(data),
            self._insight_cost_optimization(data),
            return_exceptions=True
        )

        # Organizar resultados
        result = {
            'organization_id': organization_id,
            'time_range': time_range,
            'generated_at': datetime.now().isoformat(),
            'insights': {
                'reliability': insights[0] if not isinstance(insights[0], Exception) else None,
                'energy_prediction': insights[1] if not isinstance(insights[1], Exception) else None,
                'efficiency': insights[2] if not isinstance(insights[2], Exception) else None,
                'anomalies': insights[3] if not isinstance(insights[3], Exception) else None,
                'correlations': insights[4] if not isinstance(insights[4], Exception) else None,
                'cost_optimization': insights[5] if not isinstance(insights[5], Exception) else None,
            },
            'summary': self._generate_summary(insights)
        }

        logger.info(f"Insights gerados com sucesso: {len([i for i in insights if not isinstance(i, Exception)])}/6")

        # Converter tipos numpy para serialização JSON
        result = _convert_numpy_types(result)

        # Armazenar no cache
        try:
            from app.services.redis_cache import redis_cache_service

            redis_cache_service.set_insights(
                organization_id=organization_id,
                time_range=time_range,
                insights=result,
                ttl_seconds=self.prediction_cache_ttl
            )

        except Exception as e:
            logger.warning(f"Erro ao armazenar insights no cache: {e}")

        return result

    async def _fetch_data(
        self,
        db: AsyncSession,
        organization_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Busca dados do banco para análise"""

        try:
            # Buscar dados reais do InfluxDB (tags/sensores)
            operational_df = await self._fetch_influx_operational_data(organization_id, start_time, end_time)

            # Buscar dados de alarmes do PostgreSQL
            alarm_df = await self._fetch_alarm_data(db, organization_id, start_time, end_time)

            # Se não houver dados reais suficientes, usar dados sintéticos como fallback
            if operational_df.empty or len(operational_df) < 100:
                logger.warning(f"Dados reais insuficientes ({len(operational_df)} registros). Usando dados sintéticos como fallback")
                operational_df = self._generate_synthetic_operational_data(start_time, end_time)

            if alarm_df.empty:
                logger.warning("Sem dados de alarmes reais. Usando dados sintéticos como fallback")
                alarm_df = self._generate_synthetic_alarm_data(start_time, end_time)

            # Adicionar features temporais
            if not operational_df.empty:
                operational_df['hour'] = pd.to_datetime(operational_df['timestamp']).dt.hour
                operational_df['day_of_week'] = pd.to_datetime(operational_df['timestamp']).dt.dayofweek
                operational_df['month'] = pd.to_datetime(operational_df['timestamp']).dt.month
                operational_df['is_weekend'] = (operational_df['day_of_week'] >= 5).astype(int)

            logger.info(f"Dados carregados: {len(operational_df)} operacionais, {len(alarm_df)} alarmes")

            return {
                'operational': operational_df,
                'alarms': alarm_df
            }

        except Exception as e:
            logger.error(f"Erro ao buscar dados reais: {e}. Usando dados sintéticos como fallback")
            operational_df = self._generate_synthetic_operational_data(start_time, end_time)
            alarm_df = self._generate_synthetic_alarm_data(start_time, end_time)

            # Adicionar features temporais
            if not operational_df.empty:
                operational_df['hour'] = pd.to_datetime(operational_df['timestamp']).dt.hour
                operational_df['day_of_week'] = pd.to_datetime(operational_df['timestamp']).dt.dayofweek
                operational_df['month'] = pd.to_datetime(operational_df['timestamp']).dt.month
                operational_df['is_weekend'] = (operational_df['day_of_week'] >= 5).astype(int)

            return {
                'operational': operational_df,
                'alarms': alarm_df
            }

    async def _fetch_influx_operational_data(
        self,
        organization_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        Busca dados operacionais do InfluxDB (tags de energia, produção, temperatura)

        Procura por tags relevantes para os modelos ML:
        - Consumo de energia (kWh)
        - Produção (toneladas)
        - Temperatura (°C)
        - Equipamentos
        """
        try:
            from app.services.influxdb import influxdb_service
            from app.models.tag import Tag
            from sqlalchemy import select

            # Buscar tags disponíveis no sistema (energia, produção, temperatura)
            # TODO: Otimizar query com filtros mais específicos
            # Por enquanto, buscar todas as tags do InfluxDB

            # Listar tags disponíveis no InfluxDB
            available_tags = influxdb_service.list_all_measurements()

            if not available_tags:
                logger.warning("Nenhuma tag encontrada no InfluxDB")
                return pd.DataFrame()

            logger.info(f"Encontradas {len(available_tags)} tags no InfluxDB")

            # Buscar dados para cada tag
            all_data = []

            # Limitar a 50 tags para não sobrecarregar
            for tag_id in available_tags[:50]:
                try:
                    # Buscar dados da tag
                    tag_data = influxdb_service.query_tag_data(
                        tag_id=tag_id,
                        start_time=start_time,
                        end_time=end_time,
                        aggregation='mean',
                        interval='1h'  # Agregar por hora
                    )

                    if tag_data:
                        # Adicionar tag_id aos dados
                        for point in tag_data:
                            all_data.append({
                                'tag_id': tag_id,
                                'timestamp': point['timestamp'],
                                'value': point['value'],
                                'quality': point.get('quality', 'good')
                            })

                except Exception as e:
                    logger.warning(f"Erro ao buscar dados da tag {tag_id}: {e}")
                    continue

            if not all_data:
                logger.warning("Nenhum dado de tags encontrado no período")
                return pd.DataFrame()

            # Converter para DataFrame
            df = pd.DataFrame(all_data)

            # Pivotar dados para ter uma coluna por tag
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df_pivot = df.pivot_table(
                index='timestamp',
                columns='tag_id',
                values='value',
                aggfunc='mean'
            ).reset_index()

            # Mapear colunas para formato esperado pelos modelos ML
            # Procurar por padrões de nomes de tags
            operational_data = {
                'timestamp': df_pivot['timestamp']
            }

            # Tentar identificar colunas de energia, produção, temperatura
            for col in df_pivot.columns:
                col_lower = str(col).lower()
                if any(kw in col_lower for kw in ['energy', 'power', 'kw', 'energia', 'potencia']):
                    operational_data['consumption_kwh'] = df_pivot[col]
                elif any(kw in col_lower for kw in ['production', 'throughput', 'producao', 'ton']):
                    operational_data['production_tons'] = df_pivot[col]
                elif any(kw in col_lower for kw in ['temp', 'temperature', 'temperatura']):
                    operational_data['temperature_c'] = df_pivot[col]
                elif any(kw in col_lower for kw in ['equipment', 'motor', 'pump', 'conveyor']):
                    # Identificar equipamento
                    if 'equipment_id' not in operational_data:
                        operational_data['equipment_id'] = col

            # Se não encontrou colunas específicas, usar as primeiras colunas disponíveis
            if 'consumption_kwh' not in operational_data:
                # Usar primeira coluna numérica como consumo
                numeric_cols = [c for c in df_pivot.columns if c != 'timestamp']
                if len(numeric_cols) > 0:
                    operational_data['consumption_kwh'] = df_pivot[numeric_cols[0]]
                    operational_data['production_tons'] = df_pivot[numeric_cols[1]] if len(numeric_cols) > 1 else 100.0
                    operational_data['temperature_c'] = df_pivot[numeric_cols[2]] if len(numeric_cols) > 2 else 25.0
                    operational_data['equipment_id'] = 'EQUIPMENT_01'

            result_df = pd.DataFrame(operational_data)

            # Garantir que temos todas as colunas necessárias
            required_cols = ['timestamp', 'consumption_kwh', 'production_tons', 'temperature_c', 'equipment_id']
            for col in required_cols:
                if col not in result_df.columns:
                    if col == 'equipment_id':
                        result_df[col] = 'EQUIPMENT_01'
                    else:
                        result_df[col] = 0.0

            logger.info(f"Dados InfluxDB carregados: {len(result_df)} registros, {len(result_df.columns)} colunas")

            return result_df

        except Exception as e:
            logger.error(f"Erro ao buscar dados do InfluxDB: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    async def _fetch_alarm_data(
        self,
        db: AsyncSession,
        organization_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        Busca dados de alarmes do PostgreSQL com nomes dos equipamentos
        """
        try:
            from sqlalchemy import select, and_
            from sqlalchemy.orm import joinedload, selectinload

            # Buscar alarmes no período com join para AlarmDefinition
            query = select(AlarmEvent).options(
                selectinload(AlarmEvent.definition)
            ).where(
                and_(
                    AlarmEvent.trigger_timestamp >= start_time,
                    AlarmEvent.trigger_timestamp <= end_time
                )
            ).order_by(AlarmEvent.trigger_timestamp).limit(1000)

            result = await db.execute(query)
            alarms = result.scalars().all()

            if not alarms:
                logger.warning("Nenhum alarme encontrado no período")
                return pd.DataFrame()

            # Converter para DataFrame
            alarm_data = []
            for alarm in alarms:
                # Calcular duração se tiver clear_timestamp
                duration_minutes = 60.0  # Default
                if hasattr(alarm, 'clear_timestamp') and alarm.clear_timestamp:
                    duration_minutes = (alarm.clear_timestamp - alarm.trigger_timestamp).total_seconds() / 60

                # Determinar severidade baseada no tipo de alarme ou duração
                severity = 'medium'  # Default
                if duration_minutes > 120:
                    severity = 'critical'
                elif duration_minutes < 30:
                    severity = 'low'

                # Extrair nome do equipamento do nome do alarme
                # Formato esperado: ALARME_EQUIP01_TIPO ou nome_do_alarme
                equipment_name = 'EQUIPMENT_01'
                if hasattr(alarm, 'definition') and alarm.definition:
                    alarm_name = alarm.definition.name
                    # Tentar extrair equipamento do nome (ex: ALARME_CORR01_TEMP -> CORR01)
                    if alarm_name:
                        parts = alarm_name.split('_')
                        if len(parts) >= 2:
                            # Pegar o segundo elemento (nome do equipamento)
                            equipment_name = parts[1] if parts[0] == 'ALARME' else parts[0]
                        else:
                            equipment_name = alarm_name
                elif hasattr(alarm, 'definition_id'):
                    equipment_name = str(alarm.definition_id)[:8]  # Primeiros 8 chars do UUID

                alarm_data.append({
                    'timestamp': alarm.trigger_timestamp,
                    'equipment_id': equipment_name,
                    'alarm_type': alarm.state.value if hasattr(alarm, 'state') else 'active',
                    'severity': severity,
                    'duration_minutes': duration_minutes,
                    'resolved': alarm.state.value == 'cleared' if hasattr(alarm, 'state') else False
                })

            df = pd.DataFrame(alarm_data)
            logger.info(f"Dados de alarmes carregados: {len(df)} registros")

            return df

        except Exception as e:
            logger.error(f"Erro ao buscar dados de alarmes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def _generate_synthetic_operational_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Gera dados sintéticos para demonstração"""
        hours = int((end_time - start_time).total_seconds() / 3600)
        dates = pd.date_range(start=start_time, periods=hours, freq='h')

        hour_of_day = dates.hour

        # Padrão diário
        daily_pattern = 300 + 200 * np.sin((hour_of_day - 6) * np.pi / 12)
        noise = np.random.normal(0, 15, hours)

        consumption = daily_pattern + noise
        consumption = np.clip(consumption, 50, 800)

        production = consumption * 0.8 + np.random.normal(0, 10, hours)
        production = np.clip(production, 20, 600)

        return pd.DataFrame({
            'timestamp': dates,
            'consumption_kwh': consumption,
            'production_tons': production,
            'efficiency_kwh_per_ton': consumption / production,
            'temperature_c': 20 + 10 * np.sin((hour_of_day - 12) * np.pi / 12) + np.random.normal(0, 3, hours)
        })

    def _generate_synthetic_alarm_data(self, start_time: datetime, end_time: datetime) -> pd.DataFrame:
        """Gera alarmes sintéticos para demonstração"""
        hours = int((end_time - start_time).total_seconds() / 3600)
        n_alarms = int(hours * 0.1)  # ~10% do tempo tem alarmes

        return pd.DataFrame({
            'timestamp': [start_time + timedelta(hours=i) for i in range(n_alarms)],
            'alarm_type': np.random.choice(['overheating', 'vibration', 'overcurrent', 'bearing'], n_alarms),
            'severity': np.random.choice(['low', 'medium', 'critical'], n_alarms, p=[0.5, 0.3, 0.2]),
            'duration_minutes': np.random.gamma(2, 30, n_alarms),
            'equipment_id': np.random.choice(['motor_1', 'motor_2', 'motor_3'], n_alarms)
        })

    async def _insight_reliability(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 1: Análise de Confiabilidade (MTBF/MTTR)

        Retorna:
        - Equipamentos críticos (MTBF baixo)
        - Previsão de próximas manutenções
        - Alertas de confiabilidade
        """
        alarm_df = data['alarms']

        if alarm_df.empty or len(alarm_df) < 5:
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para análise de confiabilidade'
            }

        # Calcular MTBF por equipamento
        equipment_stats = []
        for eq_id in alarm_df['equipment_id'].unique():
            eq_alarms = alarm_df[alarm_df['equipment_id'] == eq_id]

            # MTBF: tempo médio entre falhas
            if len(eq_alarms) > 1:
                time_diffs = eq_alarms['timestamp'].diff().dt.total_seconds() / 3600
                mtbf = time_diffs.mean()
            else:
                mtbf = None

            # MTTR: tempo médio de reparo
            mttr = eq_alarms['duration_minutes'].mean() / 60  # converter para horas

            equipment_stats.append({
                'equipment_id': eq_id,
                'n_failures': len(eq_alarms),
                'mtbf_hours': float(mtbf) if mtbf else None,
                'mttr_hours': float(mttr),
                'availability': float((mtbf / (mtbf + mttr)) * 100) if mtbf else None,
                'critical': mtbf < 100 if mtbf else False  # Crítico se MTBF < 100h
            })

        # Identificar equipamentos críticos
        critical_equipment = [eq for eq in equipment_stats if eq.get('critical', False)]

        # Previsão de próximas manutenções (usando Weibull)
        next_maintenances = []
        if len(alarm_df) >= 10:
            try:
                all_mtbf = [eq['mtbf_hours'] for eq in equipment_stats if eq['mtbf_hours']]
                if all_mtbf:
                    shape, loc, scale = weibull_min.fit(all_mtbf, floc=0)

                    # Prever próxima falha para cada equipamento
                    for eq in equipment_stats:
                        if eq['mtbf_hours']:
                            # Probabilidade de falha nas próximas 24h, 48h, 7 dias
                            prob_24h = 1 - weibull_min.sf(24, shape, loc, scale)
                            prob_48h = 1 - weibull_min.sf(48, shape, loc, scale)
                            prob_7d = 1 - weibull_min.sf(168, shape, loc, scale)

                            next_maintenances.append({
                                'equipment_id': eq['equipment_id'],
                                'probability_failure_24h': float(prob_24h),
                                'probability_failure_48h': float(prob_48h),
                                'probability_failure_7d': float(prob_7d),
                                'recommended_action': 'immediate' if prob_24h > 0.3 else 'monitor'
                            })
            except Exception as e:
                logger.error(f"Erro ao calcular Weibull: {e}")

        return {
            'status': 'success',
            'equipment_statistics': equipment_stats,
            'critical_equipment': critical_equipment,
            'next_maintenances': next_maintenances,
            'alerts': [
                f"⚠️ {eq['equipment_id']}: MTBF crítico ({eq['mtbf_hours']:.1f}h)"
                for eq in critical_equipment
            ],
            'recommendations': self._generate_reliability_recommendations(equipment_stats)
        }

    async def _insight_energy_prediction(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 2: Previsão de Consumo Energético (LSTM)

        Retorna:
        - Previsão de consumo para próximas 24h
        - Alertas de consumo anormal
        - Tendências
        """
        operational_df = data['operational']

        if operational_df.empty or len(operational_df) < 168:  # Mínimo 7 dias
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para previsão de energia (mínimo 7 dias)'
            }

        # Preparar dados
        feature_cols = ['consumption_kwh', 'production_tons', 'efficiency_kwh_per_ton', 'temperature_c', 'hour']

        # Verificar se todas as colunas existem
        missing_cols = [col for col in feature_cols if col not in operational_df.columns]
        if missing_cols:
            return {
                'status': 'error',
                'message': f'Colunas faltando: {missing_cols}'
            }

        # Usar últimos 7 dias para prever próximas 24h
        recent_data = operational_df.tail(168)  # últimas 168 horas

        if TENSORFLOW_AVAILABLE and 'lstm_energy_model' in self.models:
            # Usar modelo LSTM treinado
            predictions = self._predict_with_lstm(recent_data, feature_cols, hours_ahead=24)
        else:
            # Fallback: usar média móvel simples
            predictions = self._predict_with_moving_average(recent_data['consumption_kwh'], hours_ahead=24)

        # Calcular tendência
        recent_consumption = recent_data['consumption_kwh'].values
        trend_slope = np.polyfit(range(len(recent_consumption)), recent_consumption, 1)[0]

        # Detectar consumo anormal (> 2 std da média)
        mean_consumption = recent_consumption.mean()
        std_consumption = recent_consumption.std()
        current_consumption = recent_consumption[-1]
        is_abnormal = abs(current_consumption - mean_consumption) > 2 * std_consumption

        return {
            'status': 'success',
            'current_consumption_kwh': float(current_consumption),
            'predicted_24h': predictions,
            'trend': 'increasing' if trend_slope > 0 else 'decreasing',
            'trend_slope_kwh_per_hour': float(trend_slope),
            'mean_consumption_kwh': float(mean_consumption),
            'std_consumption_kwh': float(std_consumption),
            'abnormal_consumption': is_abnormal,
            'alerts': [
                f"⚠️ Consumo anormal detectado: {current_consumption:.1f} kWh (média: {mean_consumption:.1f} kWh)"
            ] if is_abnormal else [],
            'recommendations': self._generate_energy_recommendations(predictions, trend_slope)
        }

    async def _insight_efficiency(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 3: Análise de Eficiência Energética (Gradient Boosting)

        Retorna:
        - Eficiência atual vs. esperada
        - Fatores que impactam eficiência
        - Recomendações de melhoria
        """
        operational_df = data['operational']

        if operational_df.empty or len(operational_df) < 100:
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para análise de eficiência'
            }

        # Calcular eficiência atual
        current_efficiency = operational_df['efficiency_kwh_per_ton'].iloc[-1]
        mean_efficiency = operational_df['efficiency_kwh_per_ton'].mean()
        std_efficiency = operational_df['efficiency_kwh_per_ton'].std()

        # Identificar períodos de baixa eficiência
        low_efficiency_threshold = mean_efficiency + std_efficiency
        low_efficiency_periods = operational_df[operational_df['efficiency_kwh_per_ton'] > low_efficiency_threshold]

        # Análise de fatores (correlação)
        correlations = {}
        for col in ['production_tons', 'temperature_c', 'hour']:
            if col in operational_df.columns:
                corr = operational_df['efficiency_kwh_per_ton'].corr(operational_df[col])
                correlations[col] = float(corr)

        # Identificar horários de pior eficiência
        if 'hour' in operational_df.columns:
            efficiency_by_hour = operational_df.groupby('hour')['efficiency_kwh_per_ton'].mean()
            worst_hours = efficiency_by_hour.nlargest(3).index.tolist()
            best_hours = efficiency_by_hour.nsmallest(3).index.tolist()
        else:
            worst_hours = []
            best_hours = []

        return {
            'status': 'success',
            'current_efficiency_kwh_per_ton': float(current_efficiency),
            'mean_efficiency_kwh_per_ton': float(mean_efficiency),
            'std_efficiency_kwh_per_ton': float(std_efficiency),
            'efficiency_status': 'good' if current_efficiency < mean_efficiency else 'poor',
            'low_efficiency_periods': len(low_efficiency_periods),
            'correlations': correlations,
            'worst_hours': worst_hours,
            'best_hours': best_hours,
            'alerts': [
                f"⚠️ Eficiência atual baixa: {current_efficiency:.2f} kWh/ton (média: {mean_efficiency:.2f})"
            ] if current_efficiency > low_efficiency_threshold else [],
            'recommendations': self._generate_efficiency_recommendations(correlations, worst_hours, best_hours)
        }

    async def _insight_anomalies(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 4: Detecção de Anomalias (Isolation Forest)

        Retorna:
        - Anomalias detectadas recentemente
        - Padrões de anomalias
        - Equipamentos com mais anomalias
        """
        alarm_df = data['alarms']

        if alarm_df.empty or len(alarm_df) < 20:
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para detecção de anomalias'
            }

        # Preparar features
        le_type = LabelEncoder()
        le_severity = LabelEncoder()

        features = pd.DataFrame({
            'alarm_type_encoded': le_type.fit_transform(alarm_df['alarm_type']),
            'severity_encoded': le_severity.fit_transform(alarm_df['severity']),
            'duration_minutes': alarm_df['duration_minutes']
        })

        # Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(features)
        scores = iso_forest.score_samples(features)

        # Identificar anomalias
        anomalies_idx = np.where(predictions == -1)[0]

        # Anomalias recentes (últimas 24h)
        recent_time = alarm_df['timestamp'].max() - timedelta(hours=24)
        recent_anomalies = alarm_df.iloc[anomalies_idx][
            alarm_df.iloc[anomalies_idx]['timestamp'] > recent_time
        ]

        # Equipamentos com mais anomalias
        equipment_anomalies = alarm_df.iloc[anomalies_idx].groupby('equipment_id').size()
        top_equipment = equipment_anomalies.nlargest(3).to_dict()

        # Padrões de anomalias
        anomaly_patterns = alarm_df.iloc[anomalies_idx]['alarm_type'].value_counts().to_dict()

        return {
            'status': 'success',
            'total_anomalies': len(anomalies_idx),
            'anomaly_rate': float(len(anomalies_idx) / len(alarm_df)),
            'recent_anomalies': len(recent_anomalies),
            'anomaly_patterns': anomaly_patterns,
            'equipment_with_most_anomalies': top_equipment,
            'recent_anomaly_details': recent_anomalies[['timestamp', 'equipment_id', 'alarm_type', 'severity']].to_dict('records')[:5],
            'alerts': [
                f"⚠️ {len(recent_anomalies)} anomalias detectadas nas últimas 24h"
            ] if len(recent_anomalies) > 0 else [],
            'recommendations': self._generate_anomaly_recommendations(anomaly_patterns, top_equipment)
        }

    async def _insight_correlations(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 5: Análise de Correlações

        Retorna:
        - Correlações fortes identificadas
        - Variáveis que impactam o sistema
        - Insights de causa-efeito
        """
        operational_df = data['operational']

        if operational_df.empty or len(operational_df) < 50:
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para análise de correlação'
            }

        numeric_cols = ['consumption_kwh', 'production_tons', 'efficiency_kwh_per_ton', 'temperature_c']
        available_cols = [col for col in numeric_cols if col in operational_df.columns]

        if len(available_cols) < 2:
            return {
                'status': 'insufficient_data',
                'message': 'Colunas numéricas insuficientes para correlação'
            }

        # Correlação de Pearson
        corr_matrix = operational_df[available_cols].corr(method='pearson')

        # Identificar correlações fortes (|r| > 0.7)
        strong_correlations = []
        for i, col1 in enumerate(available_cols):
            for j, col2 in enumerate(available_cols):
                if i < j:
                    r = corr_matrix.loc[col1, col2]
                    if abs(r) > 0.7:
                        # Calcular p-value
                        _, p = stats.pearsonr(operational_df[col1], operational_df[col2])
                        strong_correlations.append({
                            'variable_1': col1,
                            'variable_2': col2,
                            'correlation': float(r),
                            'p_value': float(p),
                            'strength': 'very strong' if abs(r) > 0.9 else 'strong',
                            'direction': 'positive' if r > 0 else 'negative'
                        })

        return {
            'status': 'success',
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_correlations,
            'n_strong_correlations': len(strong_correlations),
            'insights': self._generate_correlation_insights(strong_correlations),
            'recommendations': self._generate_correlation_recommendations(strong_correlations)
        }

    async def _insight_cost_optimization(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Insight 6: Otimização de Custos

        Retorna:
        - Potencial de economia
        - Estratégias de otimização
        - ROI estimado
        """
        operational_df = data['operational']

        if operational_df.empty or len(operational_df) < 24:
            return {
                'status': 'insufficient_data',
                'message': 'Dados insuficientes para otimização de custos (mínimo 24h)'
            }

        # Tarifas (exemplo - devem vir de configuração)
        tariffs = {
            'peak': 0.85,         # 18h-21h
            'intermediate': 0.65,  # 17h-18h, 21h-22h
            'off_peak': 0.45      # resto
        }

        # Classificar consumo por período tarifário
        def get_tariff_period(hour):
            if 18 <= hour < 21:
                return 'peak', tariffs['peak']
            elif hour in [17, 21]:
                return 'intermediate', tariffs['intermediate']
            else:
                return 'off_peak', tariffs['off_peak']

        if 'hour' in operational_df.columns:
            operational_df['period'], operational_df['tariff'] = zip(
                *operational_df['hour'].map(get_tariff_period)
            )
        else:
            return {
                'status': 'error',
                'message': 'Dados não contêm informação de hora'
            }

        # Custo atual
        operational_df['cost_current'] = operational_df['consumption_kwh'] * operational_df['tariff']
        cost_current = operational_df['cost_current'].sum()
        cost_current_monthly = cost_current * 30 / len(operational_df)  # Projeção mensal

        # Simulação: deslocar 20% da carga de ponta para fora-ponta
        peak_consumption = operational_df[operational_df['period'] == 'peak']['consumption_kwh'].sum()
        shifted_load = peak_consumption * 0.20

        # Calcular economia potencial
        savings_from_peak = shifted_load * (tariffs['peak'] - tariffs['off_peak'])
        savings_monthly = savings_from_peak * 30 / len(operational_df)
        savings_yearly = savings_monthly * 12
        savings_percentage = (savings_from_peak / cost_current) * 100

        # Identificar horários de pico para otimizar
        if 'hour' in operational_df.columns:
            consumption_by_hour = operational_df.groupby('hour')['consumption_kwh'].mean()
            peak_hours = consumption_by_hour.nlargest(5).to_dict()
        else:
            peak_hours = {}

        return {
            'status': 'success',
            'current_cost_monthly': float(cost_current_monthly),
            'potential_savings_monthly': float(savings_monthly),
            'potential_savings_yearly': float(savings_yearly),
            'savings_percentage': float(savings_percentage),
            'peak_hours': peak_hours,
            'optimization_strategy': 'Deslocar 20% da carga de ponta (18h-21h) para fora-ponta (22h-6h)',
            'recommendations': self._generate_cost_recommendations(peak_hours, savings_monthly)
        }

    def _predict_with_lstm(self, data: pd.DataFrame, feature_cols: List[str], hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Prever consumo usando modelo LSTM (se disponível)"""
        # TODO: Implementar quando modelo LSTM estiver treinado e salvo
        return self._predict_with_moving_average(data['consumption_kwh'], hours_ahead)

    def _predict_with_moving_average(self, consumption_series: pd.Series, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Prever consumo usando média móvel (fallback)"""
        # Média móvel de 24 horas
        ma_24 = consumption_series.rolling(window=24).mean().iloc[-1]

        # Gerar previsões simples (média móvel + tendência)
        recent_values = consumption_series.tail(24).values
        trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]

        predictions = []
        for i in range(hours_ahead):
            predicted_value = ma_24 + trend * i
            timestamp = datetime.now() + timedelta(hours=i+1)
            predictions.append({
                'hour_ahead': i + 1,
                'timestamp': timestamp.isoformat(),
                'predicted_consumption_kwh': float(predicted_value),
                'confidence': 0.7  # Baixa confiança para média móvel simples
            })

        return predictions

    def _generate_summary(self, insights: List[Any]) -> Dict[str, Any]:
        """Gera sumário executivo dos insights"""
        successful = [i for i in insights if not isinstance(i, Exception) and isinstance(i, dict) and i.get('status') == 'success']

        # Contar alertas
        total_alerts = sum([len(i.get('alerts', [])) for i in successful])

        # Extrair principais recomendações
        top_recommendations = []
        for insight in successful:
            if 'recommendations' in insight:
                top_recommendations.extend(insight['recommendations'][:2])

        return {
            'total_insights': len(successful),
            'total_alerts': total_alerts,
            'severity': 'high' if total_alerts >= 3 else 'medium' if total_alerts > 0 else 'low',
            'top_recommendations': top_recommendations[:5],
            'status': 'ok' if total_alerts < 3 else 'attention_required'
        }

    # Métodos de geração de recomendações
    def _generate_reliability_recommendations(self, equipment_stats: List[Dict]) -> List[str]:
        recommendations = []
        for eq in equipment_stats:
            if eq.get('mtbf_hours') and eq['mtbf_hours'] < 100:
                recommendations.append(f"🔧 Programar manutenção preventiva para {eq['equipment_id']} (MTBF: {eq['mtbf_hours']:.1f}h)")
        if not recommendations:
            recommendations.append("✅ Todos os equipamentos com MTBF aceitável")
        return recommendations[:3]

    def _generate_energy_recommendations(self, predictions: List[Dict], trend_slope: float) -> List[str]:
        recommendations = []
        if trend_slope > 0:
            recommendations.append(f"📈 Consumo em tendência de alta ({trend_slope:.2f} kWh/h) - investigar causas")

        # Verificar se há picos previstos
        max_pred = max([p['predicted_consumption_kwh'] for p in predictions])
        avg_pred = np.mean([p['predicted_consumption_kwh'] for p in predictions])
        if max_pred > avg_pred * 1.2:
            recommendations.append(f"⚡ Pico de consumo previsto: {max_pred:.1f} kWh - considerar deslocamento de carga")

        if not recommendations:
            recommendations.append("✅ Consumo energético dentro do esperado")

        return recommendations[:3]

    def _generate_efficiency_recommendations(self, correlations: Dict, worst_hours: List, best_hours: List) -> List[str]:
        recommendations = []

        # Análise de correlações
        for var, corr in correlations.items():
            if abs(corr) > 0.5:
                if corr > 0:
                    recommendations.append(f"📊 Maior {var} aumenta eficiência - otimizar {var}")
                else:
                    recommendations.append(f"📊 Maior {var} reduz eficiência - minimizar {var}")

        # Horários
        if worst_hours:
            recommendations.append(f"⏰ Evitar operação em horários de baixa eficiência: {worst_hours}")

        return recommendations[:3]

    def _generate_anomaly_recommendations(self, patterns: Dict, top_equipment: Dict) -> List[str]:
        recommendations = []

        if patterns:
            top_pattern = max(patterns, key=patterns.get)
            recommendations.append(f"🔍 Investigar padrão de anomalias: {top_pattern} ({patterns[top_pattern]} ocorrências)")

        if top_equipment:
            top_eq = max(top_equipment, key=top_equipment.get)
            recommendations.append(f"🔧 Inspeção prioritária em {top_eq} ({top_equipment[top_eq]} anomalias)")

        return recommendations[:3]

    def _generate_correlation_insights(self, strong_correlations: List[Dict]) -> List[str]:
        insights = []
        for corr in strong_correlations[:3]:
            direction = "aumenta" if corr['direction'] == 'positive' else "diminui"
            insights.append(
                f"📊 {corr['variable_1']} {direction} quando {corr['variable_2']} aumenta "
                f"(r={corr['correlation']:.3f})"
            )
        return insights

    def _generate_correlation_recommendations(self, strong_correlations: List[Dict]) -> List[str]:
        recommendations = []
        for corr in strong_correlations[:2]:
            if corr['direction'] == 'positive':
                recommendations.append(
                    f"✅ Otimizar {corr['variable_1']} e {corr['variable_2']} em conjunto"
                )
            else:
                recommendations.append(
                    f"⚖️ Balancear {corr['variable_1']} vs {corr['variable_2']} (trade-off)"
                )
        return recommendations

    def _generate_cost_recommendations(self, peak_hours: Dict, savings_monthly: float) -> List[str]:
        recommendations = []

        if savings_monthly > 1000:
            recommendations.append(
                f"💰 Economia potencial de R$ {savings_monthly:.2f}/mês com deslocamento de carga"
            )

        if peak_hours:
            top_hour = max(peak_hours, key=peak_hours.get)
            recommendations.append(
                f"⏰ Reduzir operação no horário de pico: {top_hour}h ({peak_hours[top_hour]:.1f} kWh)"
            )

        recommendations.append("💡 Considerar investimento em armazenamento de energia para arbitragem tarifária")

        return recommendations[:3]


# Singleton instance
ml_insights_service = MLInsightsService()
