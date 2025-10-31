"""
Interlock Manager - Sistema de Intertravamentos
Implementa matriz de causa-efeito com delays, tipos de trip e reset automático/manual
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InterlockType(str, Enum):
    """Tipos de intertravamento"""
    HARD_TRIP = "hard_trip"           # Trip imediato, para equipamento
    ALARM_ACTION = "alarm_action"     # Ação corretiva em alarme
    EMERGENCY = "emergency"           # Emergência, para toda planta
    PERMISSIVE = "permissive"         # Permissivo, impede start


class ResetType(str, Enum):
    """Tipos de reset"""
    MANUAL = "manual"                     # Operador deve resetar
    AUTO_WHEN_NORMAL = "auto_when_normal" # Reset automático quando condição normaliza
    AUTO_TIMER = "auto_timer"             # Reset após tempo


@dataclass
class InterlockRule:
    """
    Regra de intertravamento
    
    Exemplo:
        cause: "TRIP_CORR03_RASGO"
        effects: ["CMD_CORR03_DESLIGAR", "CMD_BAL01_PARAR", "GATES_CLOSE_ALL"]
        type: HARD_TRIP
        delay_s: 0.0
        reset: MANUAL
    """
    id: str
    cause: str                           # Tag/condição que dispara
    effects: List[str]                    # Lista de ações a executar
    type: InterlockType
    delay_s: float = 0.0                  # Delay antes de aplicar
    reset: ResetType = ResetType.MANUAL
    description: str = ""
    
    # Estado interno
    active: bool = field(default=False, init=False)
    triggered_at: Optional[float] = field(default=None, init=False)
    latched: bool = field(default=False, init=False)


class InterlockManager:
    """
    Gerenciador de Intertravamentos
    
    Avalia matriz de causa-efeito a cada ciclo e aplica ações
    quando condições são verdadeiras, respeitando delays e regras de reset
    """
    
    def __init__(self):
        self.rules: List[InterlockRule] = []
        self.active_interlocks: Dict[str, float] = {}  # rule_id -> activation_time
        self.action_handlers: Dict[str, Callable] = {}
        
        # Carregar matriz padrão
        self._load_default_matrix()
    
    def _load_default_matrix(self):
        """Carrega matriz de intertravamentos do JSON spec"""
        
        # ================================================================
        # TRIPS CRÍTICOS - Rasgo de Correia
        # ================================================================
        self.rules.append(InterlockRule(
            id="INTLK_001",
            cause="TRIP_CORR03_RASGO",
            effects=["CMD_CORR03_DESLIGAR", "CMD_BAL01_PARAR", "CMD_CORR02_PARAR", 
                    "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Rasgo na correia final - Para toda linha em cascata"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_002",
            cause="TRIP_CORR02_RASGO",
            effects=["CMD_CORR02_DESLIGAR", "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", 
                    "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Rasgo CORR02 - Para upstream"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_003",
            cause="TRIP_CORR01_RASGO",
            effects=["CMD_CORR01_DESLIGAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Rasgo CORR01 - Para correia e fecha gates"
        ))
        
        # ================================================================
        # SOBRETEMPERATURA
        # ================================================================
        self.rules.append(InterlockRule(
            id="INTLK_010",
            cause="TRIP_ELV01_SOBRETEMP",
            effects=["CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Superaquecimento elevador - Para elevador e upstream"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_011",
            cause="TRIP_CORR01_BEARING_SOBRETEMP",
            effects=["CMD_CORR01_DESLIGAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Mancal CORR01 em sobretemperatura"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_012",
            cause="TRIP_CORR02_BEARING_SOBRETEMP",
            effects=["CMD_CORR02_DESLIGAR", "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Mancal CORR02 em sobretemperatura"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_013",
            cause="TRIP_CORR03_BEARING_SOBRETEMP",
            effects=["CMD_CORR03_DESLIGAR", "CMD_BAL01_PARAR", "CMD_CORR02_PARAR", 
                    "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Mancal CORR03 em sobretemperatura"
        ))
        
        # ================================================================
        # ENTUPIMENTO DE CHUTES
        # ================================================================
        self.rules.append(InterlockRule(
            id="INTLK_020",
            cause="TRIP_CHT01_ENTALO",
            effects=["CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Entupimento chute CORR01 - Para upstream"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_021",
            cause="TRIP_CHT02_ENTALO",
            effects=["CMD_CORR02_PARAR", "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Entupimento chute CORR02"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_022",
            cause="TRIP_CHT03_ENTALO",
            effects=["CMD_CORR03_PARAR", "CMD_BAL01_PARAR", "CMD_CORR02_PARAR", 
                    "CMD_ELV01_PARAR", "CMD_CORR01_PARAR", "GATES_CLOSE_ALL"],
            type=InterlockType.HARD_TRIP,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Entupimento chute CORR03"
        ))
        
        # ================================================================
        # ALARMES COM AÇÕES CORRETIVAS
        # ================================================================
        self.rules.append(InterlockRule(
            id="INTLK_030",
            cause="AL_NIVEL_HH_CHT01",
            effects=["GATE_CLOSE_ONE", "LIMIT_VELOCIDADES_80PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.0,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Nível muito alto chute 1 - Fecha 1 gate e limita velocidade"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_031",
            cause="AL_NIVEL_HH_CHT02",
            effects=["GATE_CLOSE_ONE", "LIMIT_VELOCIDADES_80PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.0,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Nível muito alto chute 2"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_032",
            cause="AL_NIVEL_HH_CHT03",
            effects=["GATE_CLOSE_ONE", "LIMIT_VELOCIDADES_80PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.0,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Nível muito alto chute 3"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_040",
            cause="AL_CORR01_SUBVELOCIDADE",
            effects=["REDUZIR_A_TOT_20PCT", "MANTER_BUFFER_60PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.5,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Subvelocidade CORR01 - Reduz abertura gates"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_041",
            cause="AL_CORR02_SUBVELOCIDADE",
            effects=["REDUZIR_A_TOT_20PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.5,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Subvelocidade CORR02"
        ))
        
        self.rules.append(InterlockRule(
            id="INTLK_042",
            cause="AL_CORR03_SUBVELOCIDADE",
            effects=["REDUZIR_A_TOT_20PCT"],
            type=InterlockType.ALARM_ACTION,
            delay_s=0.5,
            reset=ResetType.AUTO_WHEN_NORMAL,
            description="Subvelocidade CORR03"
        ))
        
        # ================================================================
        # EMERGÊNCIA GERAL
        # ================================================================
        self.rules.append(InterlockRule(
            id="INTLK_099",
            cause="SEG_EMERG_GERAL",
            effects=["CMD_ALL_STOP", "GATES_CLOSE_ALL"],
            type=InterlockType.EMERGENCY,
            delay_s=0.0,
            reset=ResetType.MANUAL,
            description="Emergência geral - Para toda planta"
        ))
        
        logger.info(f"✅ Loaded {len(self.rules)} interlock rules")
    
    def register_action_handler(self, action_name: str, handler: Callable):
        """Registra handler para ação específica"""
        self.action_handlers[action_name] = handler
        logger.debug(f"Registered handler for action: {action_name}")
    
    def evaluate(self, simulator, current_time: float) -> List[str]:
        """
        Avalia todas as regras e retorna lista de ações executadas
        
        Args:
            simulator: Referência ao GrainTerminalSimulator
            current_time: Tempo atual da simulação
        
        Returns:
            Lista de ações executadas neste ciclo
        """
        executed_actions = []
        
        for rule in self.rules:
            # Verifica condição de disparo
            cause_active = self._check_cause(rule.cause, simulator)
            
            if cause_active:
                # Marca tempo de ativação
                if rule.id not in self.active_interlocks:
                    self.active_interlocks[rule.id] = current_time
                    rule.triggered_at = current_time
                    logger.warning(f"🚨 Interlock triggered: {rule.id} - {rule.description}")
                
                # Verifica delay
                elapsed = current_time - self.active_interlocks[rule.id]
                
                if elapsed >= rule.delay_s and not rule.latched:
                    # Aplica efeitos
                    for effect in rule.effects:
                        self._apply_effect(effect, simulator)
                        executed_actions.append(f"{rule.id}:{effect}")
                    
                    rule.active = True
                    rule.latched = True
                    
                    logger.error(f"🔴 Interlock ACTIVE: {rule.id} - Effects applied: {rule.effects}")
            
            else:
                # Condição normalizada
                if rule.id in self.active_interlocks:
                    # Auto-reset se aplicável
                    if rule.reset == ResetType.AUTO_WHEN_NORMAL:
                        self._reset_rule(rule)
                        logger.info(f"✅ Interlock auto-reset: {rule.id}")
        
        return executed_actions
    
    def _check_cause(self, cause: str, simulator) -> bool:
        """Verifica se condição de causa está ativa"""
        
        # TRIPS - Rasgo de correia
        if cause == "TRIP_CORR01_RASGO":
            return simulator.belts.get('CORR01', None) and simulator.belts['CORR01'].torn
        elif cause == "TRIP_CORR02_RASGO":
            return simulator.belts.get('CORR02', None) and simulator.belts['CORR02'].torn
        elif cause == "TRIP_CORR03_RASGO":
            return simulator.belts.get('CORR03', None) and simulator.belts['CORR03'].torn
        
        # TRIPS - Sobretemperatura
        elif cause == "TRIP_ELV01_SOBRETEMP":
            return simulator.elevator.temp_motor_C >= 105
        elif cause == "TRIP_CORR01_BEARING_SOBRETEMP":
            return simulator.belts.get('CORR01', None) and simulator.belts['CORR01'].temp_bearing_C >= 80
        elif cause == "TRIP_CORR02_BEARING_SOBRETEMP":
            return simulator.belts.get('CORR02', None) and simulator.belts['CORR02'].temp_bearing_C >= 80
        elif cause == "TRIP_CORR03_BEARING_SOBRETEMP":
            return simulator.belts.get('CORR03', None) and simulator.belts['CORR03'].temp_bearing_C >= 80
        
        # TRIPS - Entupimento
        elif cause == "TRIP_CHT01_ENTALO":
            return simulator.belts.get('CORR01', None) and simulator.belts['CORR01'].chute_plugged
        elif cause == "TRIP_CHT02_ENTALO":
            return simulator.belts.get('CORR02', None) and simulator.belts['CORR02'].chute_plugged
        elif cause == "TRIP_CHT03_ENTALO":
            return simulator.belts.get('CORR03', None) and simulator.belts['CORR03'].chute_plugged
        
        # ALARMES - Nível alto chute
        elif cause == "AL_NIVEL_HH_CHT01":
            return simulator.belts.get('CORR01', None) and simulator.belts['CORR01'].chute_level_pct >= 95
        elif cause == "AL_NIVEL_HH_CHT02":
            return simulator.belts.get('CORR02', None) and simulator.belts['CORR02'].chute_level_pct >= 95
        elif cause == "AL_NIVEL_HH_CHT03":
            return simulator.belts.get('CORR03', None) and simulator.belts['CORR03'].chute_level_pct >= 95
        
        # ALARMES - Subvelocidade
        elif cause == "AL_CORR01_SUBVELOCIDADE":
            return simulator.belts.get('CORR01', None) and simulator.belts['CORR01'].underspeed_alarm
        elif cause == "AL_CORR02_SUBVELOCIDADE":
            return simulator.belts.get('CORR02', None) and simulator.belts['CORR02'].underspeed_alarm
        elif cause == "AL_CORR03_SUBVELOCIDADE":
            return simulator.belts.get('CORR03', None) and simulator.belts['CORR03'].underspeed_alarm
        
        # EMERGÊNCIA
        elif cause == "SEG_EMERG_GERAL":
            return simulator.emergency_stop
        
        return False
    
    def _apply_effect(self, effect: str, simulator):
        """Aplica efeito/ação no simulador"""
        
        # Comandos de parada
        if effect == "CMD_CORR01_DESLIGAR":
            simulator.belts['CORR01'].running = False
        elif effect == "CMD_CORR02_DESLIGAR":
            simulator.belts['CORR02'].running = False
        elif effect == "CMD_CORR03_DESLIGAR":
            simulator.belts['CORR03'].running = False
        elif effect == "CMD_ELV01_PARAR":
            simulator.elevator.running = False
        elif effect == "CMD_BAL01_PARAR":
            simulator.balance.running = False
        elif effect == "CMD_ALL_STOP":
            for belt in simulator.belts.values():
                belt.running = False
            simulator.elevator.running = False
            simulator.balance.running = False
            simulator.shiploader.running = False
        
        # Comandos de gates
        elif effect == "GATES_CLOSE_ALL":
            for gate in simulator.gates:
                gate.open_pct_sp = 0.0
        elif effect == "GATE_CLOSE_ONE":
            # Fecha o gate com maior abertura
            open_gates = [g for g in simulator.gates if g.open_pct > 5]
            if open_gates:
                gate_to_close = max(open_gates, key=lambda g: g.open_pct)
                gate_to_close.open_pct_sp = 0.0
        
        # Ajustes de controle
        elif effect == "REDUZIR_A_TOT_20PCT":
            simulator.pi_controller.A_tot *= 0.8
        elif effect == "MANTER_BUFFER_60PCT":
            # Ajusta setpoint para manter buffer de nível
            pass  # Implementação futura
        elif effect == "LIMIT_VELOCIDADES_80PCT":
            for belt in simulator.belts.values():
                if belt.running:
                    belt.speed_mps = min(belt.speed_mps, belt.speed_mps_nom * 0.8)
        
        # Handler customizado
        elif effect in self.action_handlers:
            self.action_handlers[effect](simulator)
    
    def _reset_rule(self, rule: InterlockRule):
        """Reseta regra de intertravamento"""
        rule.active = False
        rule.latched = False
        rule.triggered_at = None
        self.active_interlocks.pop(rule.id, None)
    
    def manual_reset(self, rule_id: str) -> bool:
        """Reset manual de um intertravamento"""
        rule = next((r for r in self.rules if r.id == rule_id), None)
        if rule and rule.reset == ResetType.MANUAL:
            self._reset_rule(rule)
            logger.info(f"✅ Manual reset: {rule_id}")
            return True
        return False
    
    def reset_all(self):
        """Reset de todos os intertravamentos (usado em reset geral)"""
        for rule in self.rules:
            self._reset_rule(rule)
        logger.info("✅ All interlocks reset")
    
    def get_active_interlocks(self) -> List[Dict]:
        """Retorna lista de intertravamentos ativos"""
        return [
            {
                'id': rule.id,
                'cause': rule.cause,
                'type': rule.type.value,
                'description': rule.description,
                'triggered_at': rule.triggered_at,
                'effects': rule.effects
            }
            for rule in self.rules if rule.active
        ]
