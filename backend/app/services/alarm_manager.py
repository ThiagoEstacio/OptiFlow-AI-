"""
Alarm Manager - Sistema Estruturado de Alarmes
Implementa alarmes com severidade, delays, actions e debouncing
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlarmSeverity(str, Enum):
    """Severidade de alarmes conforme JSON spec"""
    CRITICAL = "E"  # Emergency/Critical
    HIGH = "A"      # Alta
    MEDIUM = "B"    # Média/Warning
    LOW = "C"       # Baixa/Info


class AlarmType(str, Enum):
    """Tipos de alarme"""
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PROCESS = "process"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"


@dataclass
class AlarmDefinition:
    """
    Definição de alarme conforme JSON spec
    
    Exemplo:
        tag: "AL_CORRxx_DESALINHAMENTO"
        severity: "A"
        latch: true
        delay_on_s: 1.0
        action: "reduzir_fluxo"
    """
    tag: str
    description: str
    severity: AlarmSeverity
    alarm_type: AlarmType
    latch: bool = True
    delay_on_s: float = 0.0
    delay_off_s: float = 0.0
    action: Optional[str] = None
    
    # Estado interno
    active: bool = field(default=False, init=False)
    acknowledged: bool = field(default=False, init=False)
    triggered_at: Optional[float] = field(default=None, init=False)
    count: int = field(default=0, init=False)
    _timer: float = field(default=0.0, init=False)


class AlarmManager:
    """
    Gerenciador de Alarmes Estruturado
    
    - Severidade (E/A/B/C)
    - Delays de ativação/desativação
    - Debouncing
    - Latch/Unlatch
    - Ações automáticas
    """
    
    def __init__(self):
        self.definitions: Dict[str, AlarmDefinition] = {}
        self.action_handlers: Dict[str, Callable] = {}
        
        # Carregar catálogo de alarmes
        self._load_alarm_catalog()
    
    def _load_alarm_catalog(self):
        """Carrega catálogo completo de alarmes do JSON spec"""
        
        catalog = [
            # ============================================================
            # ALARMES MECÂNICOS - Correias
            # ============================================================
            AlarmDefinition(
                tag="AL_CORR01_DESALINHAMENTO",
                description="Correia CORR01 desalinhada",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=1.0,
                action="reduzir_fluxo"
            ),
            AlarmDefinition(
                tag="AL_CORR02_DESALINHAMENTO",
                description="Correia CORR02 desalinhada",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=1.0,
                action="reduzir_fluxo"
            ),
            AlarmDefinition(
                tag="AL_CORR03_DESALINHAMENTO",
                description="Correia CORR03 desalinhada",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=1.0,
                action="reduzir_fluxo"
            ),
            
            AlarmDefinition(
                tag="AL_CORR01_SUBVELOCIDADE",
                description="Subvelocidade em CORR01",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=0.5,
                action="fechar_um_vazador"
            ),
            AlarmDefinition(
                tag="AL_CORR02_SUBVELOCIDADE",
                description="Subvelocidade em CORR02",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=0.5,
                action="fechar_um_vazador"
            ),
            AlarmDefinition(
                tag="AL_CORR03_SUBVELOCIDADE",
                description="Subvelocidade em CORR03",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=0.5,
                action="fechar_um_vazador"
            ),
            
            # ============================================================
            # TRIPS CRÍTICOS - Rasgo
            # ============================================================
            AlarmDefinition(
                tag="TRIP_CORR01_RASGO",
                description="Rasgo detectado em CORR01",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parar_correia"
            ),
            AlarmDefinition(
                tag="TRIP_CORR02_RASGO",
                description="Rasgo detectado em CORR02",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parar_correia"
            ),
            AlarmDefinition(
                tag="TRIP_CORR03_RASGO",
                description="Rasgo detectado em CORR03",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parar_correia"
            ),
            
            # ============================================================
            # ALARMES TÉRMICOS
            # ============================================================
            AlarmDefinition(
                tag="AL_CORR01_BEARING_TEMP_ALTA",
                description="Temperatura alta em mancal CORR01",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.THERMAL,
                latch=False,
                delay_on_s=2.0,
                delay_off_s=5.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="AL_CORR02_BEARING_TEMP_ALTA",
                description="Temperatura alta em mancal CORR02",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.THERMAL,
                latch=False,
                delay_on_s=2.0,
                delay_off_s=5.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="AL_CORR03_BEARING_TEMP_ALTA",
                description="Temperatura alta em mancal CORR03",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.THERMAL,
                latch=False,
                delay_on_s=2.0,
                delay_off_s=5.0,
                action="alerta"
            ),
            
            AlarmDefinition(
                tag="TRIP_CORR01_BEARING_SOBRETEMP",
                description="Sobretemperatura crítica mancal CORR01",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.THERMAL,
                latch=True,
                delay_on_s=0.0,
                action="parada_imediata"
            ),
            AlarmDefinition(
                tag="TRIP_CORR02_BEARING_SOBRETEMP",
                description="Sobretemperatura crítica mancal CORR02",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.THERMAL,
                latch=True,
                delay_on_s=0.0,
                action="parada_imediata"
            ),
            AlarmDefinition(
                tag="TRIP_CORR03_BEARING_SOBRETEMP",
                description="Sobretemperatura crítica mancal CORR03",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.THERMAL,
                latch=True,
                delay_on_s=0.0,
                action="parada_imediata"
            ),
            
            AlarmDefinition(
                tag="AL_ELV01_MOTOR_TEMP_ALTA",
                description="Temperatura alta motor elevador",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.THERMAL,
                latch=False,
                delay_on_s=2.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="TRIP_ELV01_MOTOR_SOBRETEMP",
                description="Sobretemperatura crítica motor elevador",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.THERMAL,
                latch=True,
                delay_on_s=0.0,
                action="parada_imediata"
            ),
            
            # ============================================================
            # ALARMES DE CHUTE - Acúmulo/Entupimento
            # ============================================================
            AlarmDefinition(
                tag="AL_CHT01_ACUMULO",
                description="Acúmulo de material em chute CORR01",
                severity=AlarmSeverity.MEDIUM,
                alarm_type=AlarmType.PROCESS,
                latch=False,
                delay_on_s=3.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="AL_CHT02_ACUMULO",
                description="Acúmulo de material em chute CORR02",
                severity=AlarmSeverity.MEDIUM,
                alarm_type=AlarmType.PROCESS,
                latch=False,
                delay_on_s=3.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="AL_CHT03_ACUMULO",
                description="Acúmulo de material em chute CORR03",
                severity=AlarmSeverity.MEDIUM,
                alarm_type=AlarmType.PROCESS,
                latch=False,
                delay_on_s=3.0,
                action="alerta"
            ),
            
            AlarmDefinition(
                tag="TRIP_CHT01_ENTALO",
                description="Entupimento crítico chute CORR01",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parada_upstream"
            ),
            AlarmDefinition(
                tag="TRIP_CHT02_ENTALO",
                description="Entupimento crítico chute CORR02",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parada_upstream"
            ),
            AlarmDefinition(
                tag="TRIP_CHT03_ENTALO",
                description="Entupimento crítico chute CORR03",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.SAFETY,
                latch=True,
                delay_on_s=0.0,
                action="parada_upstream"
            ),
            
            # ============================================================
            # ALARMES ELÉTRICOS
            # ============================================================
            AlarmDefinition(
                tag="AL_FP_BAIXO",
                description="Fator de potência abaixo do mínimo",
                severity=AlarmSeverity.MEDIUM,
                alarm_type=AlarmType.ELECTRICAL,
                latch=False,
                delay_on_s=5.0,
                action="alerta_energia"
            ),
            AlarmDefinition(
                tag="AL_SOBRECORRENTE",
                description="Sobrecorrente detectada",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.ELECTRICAL,
                latch=True,
                delay_on_s=1.0,
                action="alerta"
            ),
            AlarmDefinition(
                tag="TRIP_SOBRECARGA",
                description="Sobrecarga persistente - proteção",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.ELECTRICAL,
                latch=True,
                delay_on_s=0.0,
                action="parada_equipamento"
            ),
            
            # ============================================================
            # ALARMES DE MANUTENÇÃO
            # ============================================================
            AlarmDefinition(
                tag="AL_MAN_PREVENTIVA",
                description="Limite de saúde atingido - MP recomendada",
                severity=AlarmSeverity.MEDIUM,
                alarm_type=AlarmType.MAINTENANCE,
                latch=False,
                delay_on_s=0.0,
                action="agendar_mp"
            ),
            AlarmDefinition(
                tag="AL_MAN_AGENDAR",
                description="Saúde baixa - programar manutenção",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MAINTENANCE,
                latch=True,
                delay_on_s=0.0,
                action="programar_parada"
            ),
            AlarmDefinition(
                tag="TRIP_MAN_PROTECAO",
                description="Saúde crítica - proteção de manutenção",
                severity=AlarmSeverity.CRITICAL,
                alarm_type=AlarmType.MAINTENANCE,
                latch=True,
                delay_on_s=0.0,
                action="parada_equipamento"
            ),
            
            # ============================================================
            # ALARMES DO ELEVADOR
            # ============================================================
            AlarmDefinition(
                tag="AL_ELV01_ESCORREGAMENTO",
                description="Escorregamento detectado no elevador",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=0.5,
                action="alerta"
            ),
            AlarmDefinition(
                tag="AL_ELV01_CORREIA_FROUXA",
                description="Correia frouxa no elevador",
                severity=AlarmSeverity.HIGH,
                alarm_type=AlarmType.MECHANICAL,
                latch=True,
                delay_on_s=1.0,
                action="alerta"
            ),
        ]
        
        for alarm in catalog:
            self.definitions[alarm.tag] = alarm
        
        logger.info(f"✅ Loaded {len(self.definitions)} alarm definitions")
    
    def register_action_handler(self, action_name: str, handler: Callable):
        """Registra handler para ação de alarme"""
        self.action_handlers[action_name] = handler
    
    def evaluate(self, tag: str, condition: bool, current_time: float, dt_s: float):
        """
        Avalia condição de alarme com debouncing
        
        Args:
            tag: Tag do alarme
            condition: Condição atual (True = alarme deve estar ativo)
            current_time: Tempo atual da simulação
            dt_s: Delta de tempo
        """
        if tag not in self.definitions:
            return
        
        alarm = self.definitions[tag]
        
        if condition:
            # Condição de alarme presente
            if not alarm.active:
                # Incrementa timer
                alarm._timer += dt_s
                
                # Verifica delay_on
                if alarm._timer >= alarm.delay_on_s:
                    # Ativa alarme
                    alarm.active = True
                    alarm.triggered_at = current_time
                    alarm.count += 1
                    alarm._timer = 0.0
                    
                    logger.warning(f"🚨 ALARM ACTIVE: {alarm.tag} ({alarm.severity.value}) - {alarm.description}")
                    
                    # Executa ação
                    if alarm.action and alarm.action in self.action_handlers:
                        self.action_handlers[alarm.action](alarm)
        else:
            # Condição normalizada
            if alarm.active and not alarm.latch:
                # Alarme não-latch, pode desativar automaticamente
                alarm._timer += dt_s
                
                if alarm._timer >= alarm.delay_off_s:
                    alarm.active = False
                    alarm._timer = 0.0
                    logger.info(f"✅ Alarm cleared: {alarm.tag}")
            elif not alarm.active:
                # Reset timer se não estava ativo
                alarm._timer = 0.0
    
    def acknowledge(self, tag: str) -> bool:
        """Reconhece alarme (ACK)"""
        if tag in self.definitions:
            alarm = self.definitions[tag]
            if alarm.active:
                alarm.acknowledged = True
                logger.info(f"✅ Alarm acknowledged: {tag}")
                return True
        return False
    
    def reset(self, tag: str) -> bool:
        """Reset manual de alarme latch"""
        if tag in self.definitions:
            alarm = self.definitions[tag]
            if alarm.latch and alarm.active:
                alarm.active = False
                alarm.acknowledged = False
                alarm._timer = 0.0
                logger.info(f"✅ Alarm reset: {tag}")
                return True
        return False
    
    def reset_all(self):
        """Reset de todos os alarmes"""
        for alarm in self.definitions.values():
            alarm.active = False
            alarm.acknowledged = False
            alarm._timer = 0.0
        logger.info("✅ All alarms reset")
    
    def get_active_alarms(self, severity: Optional[AlarmSeverity] = None) -> List[Dict]:
        """Retorna alarmes ativos, opcionalmente filtrados por severidade"""
        alarms = [
            {
                'tag': alarm.tag,
                'description': alarm.description,
                'severity': alarm.severity.value,
                'type': alarm.alarm_type.value,
                'triggered_at': alarm.triggered_at,
                'acknowledged': alarm.acknowledged,
                'count': alarm.count
            }
            for alarm in self.definitions.values()
            if alarm.active and (severity is None or alarm.severity == severity)
        ]
        return sorted(alarms, key=lambda x: ['E', 'A', 'B', 'C'].index(x['severity']))
    
    def get_alarm_summary(self) -> Dict:
        """Retorna resumo de alarmes por severidade"""
        active = self.get_active_alarms()
        return {
            'total': len(active),
            'critical': len([a for a in active if a['severity'] == 'E']),
            'high': len([a for a in active if a['severity'] == 'A']),
            'medium': len([a for a in active if a['severity'] == 'B']),
            'low': len([a for a in active if a['severity'] == 'C']),
            'unacknowledged': len([a for a in active if not a['acknowledged']])
        }
