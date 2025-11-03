"""
Maintenance and Energy Extensions for Grain Terminal Simulator
Adiciona modelos completos de manutenção preditiva e energia conforme JSON spec
"""
from dataclasses import dataclass
from typing import Dict
import math


@dataclass
class MaintenanceState:
    """
    Estado de manutenção por equipamento
    
    Implementa modelo de saúde completo:
    H_next = H - (k_uso*carga_rel) - (k_choque*eventos)
    """
    equipment_id: str
    health_pct: float = 100.0
    hours_running: float = 0.0
    cycle_count: int = 0
    last_maintenance_time: float = 0.0
    
    # Sensores conforme JSON spec
    vibration_mm_s: float = 0.0
    oil_temp_C: float = 50.0
    bearing_temp_C: float = 25.0
    
    # Contadores de eventos
    alarm_count: int = 0
    trip_count: int = 0
    
    # Thresholds
    HEALTH_WARN = 80.0
    HEALTH_PLAN = 60.0
    HEALTH_TRIP = 40.0
    
    # Coeficientes de degradação
    K_USO = 0.002
    K_CHOQUE = 0.02
    
    def update(self, dt_s: float, load_pct: float, events_this_cycle: int, running: bool):
        """
        Atualiza estado de manutenção
        
        Args:
            dt_s: Delta de tempo
            load_pct: Carga relativa (0-100%)
            events_this_cycle: Número de eventos (alarmes/trips) neste ciclo
            running: Se equipamento está rodando
        """
        if running:
            # Horímetro
            self.hours_running += dt_s / 3600.0
            
            # Degradação por uso
            load_rel = load_pct / 100.0
            degradation_uso = self.K_USO * load_rel * dt_s
            self.health_pct -= degradation_uso
            
            # Vibração aumenta com carga e degradação
            health_factor = (100 - self.health_pct) / 100.0
            self.vibration_mm_s = 0.5 + (load_rel * 2.0) + (health_factor * 5.0)
            
            # Temperatura de óleo aumenta com carga
            ambient = 25.0
            self.oil_temp_C = ambient + (load_rel * 30.0) + (health_factor * 15.0)
        
        # Degradação por choques (eventos)
        if events_this_cycle > 0:
            degradation_choque = self.K_CHOQUE * events_this_cycle
            self.health_pct -= degradation_choque
            self.alarm_count += events_this_cycle
        
        # Limita saúde
        self.health_pct = max(0.0, min(100.0, self.health_pct))
    
    def get_alarm_tag(self) -> str:
        """Retorna tag de alarme baseado em threshold"""
        if self.health_pct < self.HEALTH_TRIP:
            return "TRIP_MAN_PROTECAO"
        elif self.health_pct < self.HEALTH_PLAN:
            return "AL_MAN_AGENDAR"
        elif self.health_pct < self.HEALTH_WARN:
            return "AL_MAN_PREVENTIVA"
        return ""
    
    def perform_maintenance(self, current_time: float):
        """Executa manutenção - restaura saúde"""
        self.health_pct = 100.0
        self.last_maintenance_time = current_time
        self.alarm_count = 0
        self.trip_count = 0


@dataclass
class ElectricalState:
    """
    Estado elétrico completo por equipamento
    Implementa medições conforme JSON spec: V_ll, I, P_kW, Q_kvar, S_kVA, PF
    """
    equipment_id: str
    motor_kW: float
    
    # Medições
    voltage_ll: float = 440.0          # Tensão linha-linha (V)
    current_A: float = 0.0             # Corrente (A)
    power_kW: float = 0.0              # Potência ativa (kW)
    reactive_kvar: float = 0.0         # Potência reativa (kvar)
    apparent_kVA: float = 0.0          # Potência aparente (kVA)
    power_factor: float = 0.92         # Fator de potência
    
    # Acumuladores
    kWh_total: float = 0.0
    
    # Limites conforme JSON spec
    PF_MIN = 0.85
    OVERCURRENT_WARN_FACTOR = 0.90
    OVERCURRENT_TRIP_FACTOR = 1.15
    
    def update(self, dt_s: float, load_pct: float, running: bool):
        """
        Atualiza estado elétrico
        
        Calcula todas as grandezas elétricas baseado em carga
        """
        if running and load_pct > 0:
            load_factor = load_pct / 100.0
            
            # Potência ativa
            self.power_kW = self.motor_kW * (0.3 + 0.7 * load_factor)
            
            # Fator de potência varia com carga (pior em baixa carga)
            if load_factor < 0.3:
                self.power_factor = 0.70 + (load_factor * 0.6)
            else:
                self.power_factor = 0.92 - (abs(load_factor - 0.75) * 0.1)
            
            self.power_factor = max(0.70, min(0.95, self.power_factor))
            
            # Potência aparente
            self.apparent_kVA = self.power_kW / self.power_factor
            
            # Potência reativa
            self.reactive_kvar = math.sqrt(
                max(0, self.apparent_kVA**2 - self.power_kW**2)
            )
            
            # Corrente
            self.current_A = (self.apparent_kVA * 1000) / (self.voltage_ll * math.sqrt(3))
            
            # Acumular energia
            energy_kWh_step = (self.power_kW * dt_s) / 3600.0
            self.kWh_total += energy_kWh_step
        else:
            # Equipamento desligado
            self.power_kW = 0.0
            self.reactive_kvar = 0.0
            self.apparent_kVA = 0.0
            # Corrente de magnetização residual
            nominal_current = (self.motor_kW * 1000) / (self.voltage_ll * math.sqrt(3) * 0.92)
            self.current_A = nominal_current * 0.2
    
    def get_current_nominal(self) -> float:
        """Retorna corrente nominal do motor"""
        return (self.motor_kW * 1000) / (self.voltage_ll * math.sqrt(3) * 0.92)
    
    def check_overcurrent(self) -> str:
        """Verifica sobrecorrente"""
        nominal = self.get_current_nominal()
        ratio = self.current_A / nominal if nominal > 0 else 0
        
        if ratio >= self.OVERCURRENT_TRIP_FACTOR:
            return "TRIP_SOBRECARGA"
        elif ratio >= self.OVERCURRENT_WARN_FACTOR:
            return "AL_SOBRECORRENTE"
        return ""
    
    def check_power_factor(self) -> str:
        """Verifica fator de potência baixo"""
        if self.power_kW > 0.1 * self.motor_kW and self.power_factor < self.PF_MIN:
            return "AL_FP_BAIXO"
        return ""


class EnergyManager:
    """
    Gerenciador de energia do sistema
    Calcula KPIs e custos conforme JSON spec
    """
    
    def __init__(self):
        self.electrical_states: Dict[str, ElectricalState] = {}
        
        # KPIs globais
        self.total_kWh = 0.0
        self.total_mass_t = 0.0
        self.kWh_per_ton = 0.0
        
        # Tarifas (R$/kWh)
        self.tariff_peak = 1.50
        self.tariff_offpeak = 0.65
        
        # Custos
        self.cost_peak_BRL = 0.0
        self.cost_offpeak_BRL = 0.0
        self.cost_total_BRL = 0.0
    
    def register_equipment(self, equipment_id: str, motor_kW: float):
        """Registra equipamento no gerenciador de energia"""
        self.electrical_states[equipment_id] = ElectricalState(
            equipment_id=equipment_id,
            motor_kW=motor_kW
        )
    
    def update(self, dt_s: float, hour_of_day: int = 12):
        """
        Atualiza KPIs de energia
        
        Args:
            dt_s: Delta de tempo
            hour_of_day: Hora do dia (0-23) para tarifa horária
        """
        # Soma potência de todos equipamentos
        total_power_kW = sum(
            state.power_kW for state in self.electrical_states.values()
        )
        
        # Energia neste step
        energy_kWh_step = (total_power_kW * dt_s) / 3600.0
        self.total_kWh += energy_kWh_step
        
        # Custo baseado em hora pico/fora pico
        # Pico: 18h-21h e 6h-9h (horários típicos)
        is_peak = (6 <= hour_of_day < 9) or (18 <= hour_of_day < 21)
        
        if is_peak:
            cost_step = energy_kWh_step * self.tariff_peak
            self.cost_peak_BRL += cost_step
        else:
            cost_step = energy_kWh_step * self.tariff_offpeak
            self.cost_offpeak_BRL += cost_step
        
        self.cost_total_BRL = self.cost_peak_BRL + self.cost_offpeak_BRL
    
    def update_production(self, mass_t_step: float):
        """Atualiza produção e calcula kWh/ton"""
        self.total_mass_t += mass_t_step
        
        if self.total_mass_t > 0.1:
            self.kWh_per_ton = self.total_kWh / self.total_mass_t
    
    def get_average_power_factor(self) -> float:
        """Calcula fator de potência médio ponderado"""
        total_kVA = sum(state.apparent_kVA for state in self.electrical_states.values())
        total_kW = sum(state.power_kW for state in self.electrical_states.values())
        
        if total_kVA > 0.1:
            return total_kW / total_kVA
        return 0.92
    
    def get_electrical_summary(self) -> Dict:
        """Retorna resumo elétrico do sistema"""
        return {
            'total_power_kW': sum(s.power_kW for s in self.electrical_states.values()),
            'total_current_A': sum(s.current_A for s in self.electrical_states.values()),
            'total_reactive_kvar': sum(s.reactive_kvar for s in self.electrical_states.values()),
            'average_pf': self.get_average_power_factor(),
            'total_kWh': self.total_kWh,
            'kWh_per_ton': self.kWh_per_ton,
            'cost_total_BRL': self.cost_total_BRL,
            'cost_peak_BRL': self.cost_peak_BRL,
            'cost_offpeak_BRL': self.cost_offpeak_BRL
        }


class MaintenanceManager:
    """
    Gerenciador de manutenção do sistema
    Rastreia saúde e sensores de todos equipamentos
    """
    
    def __init__(self):
        self.maintenance_states: Dict[str, MaintenanceState] = {}
    
    def register_equipment(self, equipment_id: str):
        """Registra equipamento no gerenciador de manutenção"""
        self.maintenance_states[equipment_id] = MaintenanceState(
            equipment_id=equipment_id
        )
    
    def update_equipment(self, equipment_id: str, dt_s: float, load_pct: float, 
                        events: int, running: bool):
        """Atualiza estado de manutenção de um equipamento"""
        if equipment_id in self.maintenance_states:
            self.maintenance_states[equipment_id].update(dt_s, load_pct, events, running)
    
    def perform_maintenance(self, equipment_id: str, current_time: float) -> bool:
        """Executa manutenção em equipamento"""
        if equipment_id in self.maintenance_states:
            self.maintenance_states[equipment_id].perform_maintenance(current_time)
            return True
        return False
    
    def get_equipment_needing_maintenance(self) -> list:
        """Retorna lista de equipamentos que precisam manutenção"""
        return [
            {
                'equipment_id': eq_id,
                'health_pct': state.health_pct,
                'alarm_tag': state.get_alarm_tag(),
                'hours_running': state.hours_running,
                'vibration_mm_s': state.vibration_mm_s,
                'oil_temp_C': state.oil_temp_C
            }
            for eq_id, state in self.maintenance_states.items()
            if state.health_pct < 80.0
        ]
    
    def get_maintenance_summary(self) -> Dict:
        """Retorna resumo de manutenção"""
        states = list(self.maintenance_states.values())
        
        return {
            'avg_health_pct': sum(s.health_pct for s in states) / len(states) if states else 100.0,
            'total_hours': sum(s.hours_running for s in states),
            'equipment_count': len(states),
            'needs_attention': len([s for s in states if s.health_pct < 80]),
            'critical': len([s for s in states if s.health_pct < 40]),
            'total_alarms': sum(s.alarm_count for s in states),
            'total_trips': sum(s.trip_count for s in states)
        }
