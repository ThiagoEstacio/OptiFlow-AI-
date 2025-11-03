#!/usr/bin/env python3
"""
SmartPort - Bulk Terminal Simulator (Grãos e Açúcar)
Simulador de terminal portuário de exportação de grãos e açúcar

Equipamentos simulados:
- Correias transportadoras
- Elevadores de caneca
- Shiploaders (carregadores de navio)
- Silos de armazenamento
- Motores elétricos

Tags para Anomalia Detection (PI Vision / Power BI style):
- Corrente de motores (A)
- Velocidade de motores (RPM)
- Temperatura de rolamentos (°C)
- Vibração (mm/s)
- Fluxo de produto (t/h)
- Níveis de silo (%)
- Qualidade do produto (umidade, temperatura)
"""

import time
import math
import random
import argparse
from datetime import datetime
from typing import Dict, List
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BulkTerminalSimulator:
    """
    Simulador de Terminal de Grãos/Açúcar
    Gera dados realistas para detecção de anomalias
    """

    def __init__(self, host="0.0.0.0", port=5020, update_interval=1.0):
        self.host = host
        self.port = port
        self.update_interval = update_interval
        self.running = False
        self.iteration = 0

        # Estado inicial dos equipamentos
        self.state = {
            # CORREIA TRANSPORTADORA 1 (Recebimento)
            "conv1_motor_current": 120.0,      # Amperes
            "conv1_motor_speed": 1750.0,       # RPM
            "conv1_motor_temp": 65.0,          # °C
            "conv1_bearing_temp": 55.0,        # °C
            "conv1_vibration": 2.8,            # mm/s
            "conv1_flow_rate": 850.0,          # t/h
            "conv1_running": 1,                # Boolean

            # CORREIA TRANSPORTADORA 2 (Transferência)
            "conv2_motor_current": 95.0,
            "conv2_motor_speed": 1750.0,
            "conv2_motor_temp": 62.0,
            "conv2_bearing_temp": 52.0,
            "conv2_vibration": 2.5,
            "conv2_flow_rate": 850.0,
            "conv2_running": 1,

            # ELEVADOR DE CANECA 1
            "elev1_motor_current": 180.0,
            "elev1_motor_speed": 950.0,
            "elev1_motor_temp": 72.0,
            "elev1_bearing_temp": 65.0,
            "elev1_vibration": 3.5,
            "elev1_flow_rate": 850.0,
            "elev1_running": 1,

            # SHIPLOADER (Carregador de Navio)
            "ship_motor_current": 250.0,
            "ship_motor_speed": 1200.0,
            "ship_motor_temp": 75.0,
            "ship_bearing_temp": 68.0,
            "ship_vibration": 4.2,
            "ship_flow_rate": 2000.0,          # t/h (maior capacidade)
            "ship_boom_angle": 45.0,           # graus
            "ship_running": 1,

            # SILO 1
            "silo1_level": 75.0,               # %
            "silo1_temp": 28.0,                # °C (temperatura do produto)
            "silo1_pressure": 1.2,             # bar (pressão pneumática)

            # SILO 2
            "silo2_level": 60.0,
            "silo2_temp": 27.0,
            "silo2_pressure": 1.1,

            # QUALIDADE DO PRODUTO (Grãos/Açúcar)
            "product_moisture": 12.5,          # % (umidade)
            "product_temp": 26.0,              # °C
            "product_density": 750.0,          # kg/m³

            # DESPOEIRADOR (Dust Collector)
            "dust_collector_pressure": 150.0,  # mmH2O (pressão diferencial)
            "dust_collector_running": 1,

            # KPIs OPERACIONAIS
            "loading_rate_accumulated": 0.0,   # toneladas acumuladas
            "vessel_loading_progress": 0.0,    # % de carregamento do navio
            "downtime_minutes": 0.0,           # tempo de parada
            "energy_consumption": 0.0,         # kWh acumulado

            # ALARMES
            "alarm_high_current": 0,
            "alarm_high_vibration": 0,
            "alarm_high_temp": 0,
            "alarm_low_flow": 0,
        }

        # Contadores de anomalia (para simular degradação)
        self.anomaly_counters = {
            "conv1_bearing_degradation": 0,    # Simula rolamento degradando
            "elev1_overload_event": 0,         # Simula sobrecarga
            "ship_vibration_spike": 0,         # Simula desbalanceamento
        }

        # Tag definitions
        self.tag_definitions = self._create_tag_definitions()
        self._init_modbus_store()

    def _create_tag_definitions(self) -> Dict:
        """Definição de tags SmartPort - Terminal de Grãos/Açúcar"""
        return {
            # ==================== CORREIA TRANSPORTADORA 1 ====================
            "CONV1_MOTOR_CURRENT": {
                "address": 40001, "type": "float", "unit": "A", "category": "energy",
                "min": 0, "max": 300, "alarm_high": 250, "scaling": 10,
                "description": "Corrente motor correia 1 (anomalia: sobrecarga)"
            },
            "CONV1_MOTOR_SPEED": {
                "address": 40003, "type": "float", "unit": "RPM", "category": "process",
                "min": 0, "max": 2000, "alarm_low": 1600, "scaling": 1,
                "description": "Velocidade motor correia 1 (anomalia: variação)"
            },
            "CONV1_MOTOR_TEMP": {
                "address": 40005, "type": "float", "unit": "°C", "category": "maintenance",
                "min": 20, "max": 120, "alarm_high": 95, "scaling": 10,
                "description": "Temperatura motor correia 1"
            },
            "CONV1_BEARING_TEMP": {
                "address": 40007, "type": "float", "unit": "°C", "category": "maintenance",
                "min": 20, "max": 120, "alarm_high": 85, "scaling": 10,
                "description": "Temperatura rolamento correia 1 (preditiva)"
            },
            "CONV1_VIBRATION": {
                "address": 40009, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 15, "alarm_high": 7.5, "scaling": 100,
                "description": "Vibração correia 1 (anomalia: desbalanceamento)"
            },
            "CONV1_FLOW_RATE": {
                "address": 40011, "type": "float", "unit": "t/h", "category": "production",
                "min": 0, "max": 1500, "alarm_low": 400, "scaling": 1,
                "description": "Fluxo de produto correia 1"
            },

            # ==================== CORREIA TRANSPORTADORA 2 ====================
            "CONV2_MOTOR_CURRENT": {
                "address": 40013, "type": "float", "unit": "A", "category": "energy",
                "min": 0, "max": 250, "alarm_high": 220, "scaling": 10,
                "description": "Corrente motor correia 2"
            },
            "CONV2_MOTOR_SPEED": {
                "address": 40015, "type": "float", "unit": "RPM", "category": "process",
                "min": 0, "max": 2000, "alarm_low": 1600, "scaling": 1,
                "description": "Velocidade motor correia 2"
            },
            "CONV2_MOTOR_TEMP": {
                "address": 40017, "type": "float", "unit": "°C", "category": "maintenance",
                "min": 20, "max": 120, "alarm_high": 95, "scaling": 10,
                "description": "Temperatura motor correia 2"
            },
            "CONV2_VIBRATION": {
                "address": 40019, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 15, "alarm_high": 7.5, "scaling": 100,
                "description": "Vibração correia 2"
            },

            # ==================== ELEVADOR DE CANECA ====================
            "ELEV1_MOTOR_CURRENT": {
                "address": 40021, "type": "float", "unit": "A", "category": "energy",
                "min": 0, "max": 400, "alarm_high": 350, "scaling": 10,
                "description": "Corrente motor elevador (anomalia: bloqueio)"
            },
            "ELEV1_MOTOR_SPEED": {
                "address": 40023, "type": "float", "unit": "RPM", "category": "process",
                "min": 0, "max": 1200, "alarm_low": 800, "scaling": 1,
                "description": "Velocidade motor elevador"
            },
            "ELEV1_MOTOR_TEMP": {
                "address": 40025, "type": "float", "unit": "°C", "category": "maintenance",
                "min": 20, "max": 130, "alarm_high": 105, "scaling": 10,
                "description": "Temperatura motor elevador"
            },
            "ELEV1_VIBRATION": {
                "address": 40027, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 20, "alarm_high": 10, "scaling": 100,
                "description": "Vibração elevador (anomalia: desalinhamento)"
            },

            # ==================== SHIPLOADER ====================
            "SHIP_MOTOR_CURRENT": {
                "address": 40029, "type": "float", "unit": "A", "category": "energy",
                "min": 0, "max": 500, "alarm_high": 450, "scaling": 10,
                "description": "Corrente motor shiploader"
            },
            "SHIP_MOTOR_SPEED": {
                "address": 40031, "type": "float", "unit": "RPM", "category": "process",
                "min": 0, "max": 1500, "alarm_low": 1000, "scaling": 1,
                "description": "Velocidade motor shiploader"
            },
            "SHIP_FLOW_RATE": {
                "address": 40033, "type": "float", "unit": "t/h", "category": "production",
                "min": 0, "max": 3000, "alarm_low": 1000, "scaling": 1,
                "description": "Fluxo carregamento navio (KPI principal)"
            },
            "SHIP_VIBRATION": {
                "address": 40035, "type": "float", "unit": "mm/s", "category": "maintenance",
                "min": 0, "max": 20, "alarm_high": 12, "scaling": 100,
                "description": "Vibração shiploader"
            },
            "SHIP_BOOM_ANGLE": {
                "address": 40037, "type": "float", "unit": "°", "category": "process",
                "min": -10, "max": 90, "alarm_high": 0, "scaling": 10,
                "description": "Ângulo lança shiploader"
            },

            # ==================== SILOS ====================
            "SILO1_LEVEL": {
                "address": 40039, "type": "float", "unit": "%", "category": "process",
                "min": 0, "max": 100, "alarm_low": 10, "scaling": 10,
                "description": "Nível silo 1"
            },
            "SILO1_TEMP": {
                "address": 40041, "type": "float", "unit": "°C", "category": "quality",
                "min": 10, "max": 60, "alarm_high": 45, "scaling": 10,
                "description": "Temperatura produto silo 1"
            },
            "SILO2_LEVEL": {
                "address": 40043, "type": "float", "unit": "%", "category": "process",
                "min": 0, "max": 100, "alarm_low": 10, "scaling": 10,
                "description": "Nível silo 2"
            },

            # ==================== QUALIDADE ====================
            "PRODUCT_MOISTURE": {
                "address": 40045, "type": "float", "unit": "%", "category": "quality",
                "min": 0, "max": 25, "alarm_high": 14, "scaling": 100,
                "description": "Umidade do produto (grãos/açúcar)"
            },
            "PRODUCT_TEMP": {
                "address": 40047, "type": "float", "unit": "°C", "category": "quality",
                "min": 10, "max": 50, "alarm_high": 40, "scaling": 10,
                "description": "Temperatura do produto"
            },

            # ==================== KPIs ====================
            "LOADING_RATE_TOTAL": {
                "address": 40049, "type": "float", "unit": "t", "category": "production",
                "min": 0, "max": 100000, "alarm_high": 0, "scaling": 1,
                "description": "Toneladas carregadas acumulado"
            },
            "VESSEL_PROGRESS": {
                "address": 40051, "type": "float", "unit": "%", "category": "production",
                "min": 0, "max": 100, "alarm_high": 0, "scaling": 10,
                "description": "Progresso carregamento navio"
            },
            "ENERGY_TOTAL": {
                "address": 40053, "type": "float", "unit": "kWh", "category": "energy",
                "min": 0, "max": 999999, "alarm_high": 0, "scaling": 1,
                "description": "Energia consumida total"
            },

            # ==================== STATUS DIGITAIS ====================
            "CONV1_RUNNING": {
                "address": 1, "type": "boolean", "unit": "", "category": "status",
                "description": "Correia 1 em operação"
            },
            "CONV2_RUNNING": {
                "address": 2, "type": "boolean", "unit": "", "category": "status",
                "description": "Correia 2 em operação"
            },
            "ELEV1_RUNNING": {
                "address": 3, "type": "boolean", "unit": "", "category": "status",
                "description": "Elevador em operação"
            },
            "SHIP_RUNNING": {
                "address": 4, "type": "boolean", "unit": "", "category": "status",
                "description": "Shiploader em operação"
            },

            # ==================== ALARMES ====================
            "ALARM_HIGH_CURRENT": {
                "address": 5, "type": "boolean", "unit": "", "category": "alarm",
                "description": "Alarme sobrecorrente"
            },
            "ALARM_HIGH_VIBRATION": {
                "address": 6, "type": "boolean", "unit": "", "category": "alarm",
                "description": "Alarme vibração alta"
            },
            "ALARM_HIGH_TEMP": {
                "address": 7, "type": "boolean", "unit": "", "category": "alarm",
                "description": "Alarme temperatura alta"
            },
            "ALARM_LOW_FLOW": {
                "address": 8, "type": "boolean", "unit": "", "category": "alarm",
                "description": "Alarme fluxo baixo"
            },
        }

    def _init_modbus_store(self):
        """Inicializar data store Modbus"""
        holding_registers = ModbusSequentialDataBlock(40001, [0] * 100)
        coils = ModbusSequentialDataBlock(1, [False] * 100)

        self.slave_context = ModbusSlaveContext(
            di=None, co=coils, hr=holding_registers, ir=None
        )
        self.context = ModbusServerContext(slaves=self.slave_context, single=True)

    def update_process_values(self):
        """Atualizar valores de processo com padrões realistas e anomalias"""
        t = self.iteration * self.update_interval

        # ==================== SIMULAÇÃO DE ANOMALIAS ====================

        # ANOMALIA 1: Rolamento degradando na correia 1 (vibração + temperatura crescentes)
        if self.iteration > 300:  # Após 5 minutos
            self.anomaly_counters["conv1_bearing_degradation"] += 0.005
            bearing_degradation = min(self.anomaly_counters["conv1_bearing_degradation"], 1.5)
        else:
            bearing_degradation = 0

        # ANOMALIA 2: Sobrecarga periódica no elevador
        if self.iteration % 600 < 60:  # A cada 10 minutos, 1 minuto de sobrecarga
            self.anomaly_counters["elev1_overload_event"] = 1
        else:
            self.anomaly_counters["elev1_overload_event"] = 0

        # ANOMALIA 3: Spike de vibração no shiploader (simulando desbalanceamento)
        if random.random() < 0.002:  # 0.2% chance por iteração
            self.anomaly_counters["ship_vibration_spike"] = 50
        elif self.anomaly_counters["ship_vibration_spike"] > 0:
            self.anomaly_counters["ship_vibration_spike"] -= 1

        # ==================== CORREIA 1 ====================
        # Corrente: base + variação + anomalia sobrecarga
        self.state["conv1_motor_current"] = (120 + 15 * math.sin(t / 50) +
                                             random.gauss(0, 2) +
                                             bearing_degradation * 30)

        # Velocidade: estável com pequeno ruído
        self.state["conv1_motor_speed"] = 1750 + random.gauss(0, 10)

        # Temperatura motor: correlacionado com corrente
        load_factor = self.state["conv1_motor_current"] / 120
        self.state["conv1_motor_temp"] = 45 + load_factor * 30 + random.gauss(0, 1)

        # Temperatura rolamento: ANOMALIA - aumenta gradualmente
        self.state["conv1_bearing_temp"] = (55 + 5 * math.sin(t / 200) +
                                            bearing_degradation * 25 +
                                            random.gauss(0, 1))

        # Vibração: ANOMALIA - aumenta com degradação do rolamento
        self.state["conv1_vibration"] = (2.8 + 0.5 * math.sin(t / 80) +
                                         bearing_degradation * 3 +
                                         random.gauss(0, 0.2))

        # Fluxo: variação normal
        self.state["conv1_flow_rate"] = 850 + 100 * math.sin(t / 150) + random.gauss(0, 10)

        # ==================== CORREIA 2 ====================
        self.state["conv2_motor_current"] = 95 + 10 * math.sin(t / 60) + random.gauss(0, 2)
        self.state["conv2_motor_speed"] = 1750 + random.gauss(0, 8)
        self.state["conv2_motor_temp"] = 62 + 5 * math.sin(t / 180) + random.gauss(0, 1)
        self.state["conv2_vibration"] = 2.5 + 0.3 * math.sin(t / 70) + random.gauss(0, 0.15)
        self.state["conv2_flow_rate"] = self.state["conv1_flow_rate"] * 0.98  # Ligeiramente menor

        # ==================== ELEVADOR ====================
        # ANOMALIA: Sobrecarga periódica
        overload = self.anomaly_counters["elev1_overload_event"] * 80

        self.state["elev1_motor_current"] = 180 + 20 * math.sin(t / 40) + overload + random.gauss(0, 3)
        self.state["elev1_motor_speed"] = 950 + random.gauss(0, 15)
        self.state["elev1_motor_temp"] = 72 + (overload / 80) * 20 + random.gauss(0, 1.5)
        self.state["elev1_vibration"] = 3.5 + 0.8 * math.sin(t / 60) + random.gauss(0, 0.3)
        self.state["elev1_flow_rate"] = self.state["conv2_flow_rate"] * 0.99

        # ==================== SHIPLOADER ====================
        # ANOMALIA: Spike de vibração
        vib_spike = min(self.anomaly_counters["ship_vibration_spike"] * 0.15, 8)

        self.state["ship_motor_current"] = 250 + 30 * math.sin(t / 30) + random.gauss(0, 5)
        self.state["ship_motor_speed"] = 1200 + random.gauss(0, 20)
        self.state["ship_motor_temp"] = 75 + 8 * math.sin(t / 200) + random.gauss(0, 2)
        self.state["ship_vibration"] = 4.2 + 1.2 * math.sin(t / 45) + vib_spike + random.gauss(0, 0.4)

        # Fluxo do shiploader: maior capacidade
        self.state["ship_flow_rate"] = 2000 + 300 * math.sin(t / 120) + random.gauss(0, 30)

        # Ângulo da lança
        self.state["ship_boom_angle"] = 45 + 15 * math.sin(t / 300)

        # ==================== SILOS ====================
        # Nível diminui conforme carregamento
        self.state["silo1_level"] = max(10, 75 - (t / 3600) * 5)  # Desce 5% por hora
        self.state["silo2_level"] = max(10, 60 - (t / 3600) * 3)

        self.state["silo1_temp"] = 28 + 3 * math.sin(t / 500) + random.gauss(0, 0.5)
        self.state["silo1_pressure"] = 1.2 + 0.2 * math.sin(t / 100) + random.gauss(0, 0.05)
        self.state["silo2_pressure"] = 1.1 + 0.15 * math.sin(t / 110) + random.gauss(0, 0.04)

        # ==================== QUALIDADE ====================
        self.state["product_moisture"] = 12.5 + 0.5 * math.sin(t / 600) + random.gauss(0, 0.2)
        self.state["product_temp"] = 26 + 2 * math.sin(t / 400) + random.gauss(0, 0.5)
        self.state["product_density"] = 750 + random.gauss(0, 5)

        # ==================== KPIs ====================
        # Toneladas acumuladas
        self.state["loading_rate_accumulated"] += self.state["ship_flow_rate"] * self.update_interval / 3600

        # Progresso do navio (0-100%)
        vessel_capacity = 60000  # toneladas
        self.state["vessel_loading_progress"] = min(100, (self.state["loading_rate_accumulated"] / vessel_capacity) * 100)

        # Energia total (kWh)
        total_power_kw = (self.state["conv1_motor_current"] * 380 * math.sqrt(3) * 0.85 / 1000 +
                         self.state["conv2_motor_current"] * 380 * math.sqrt(3) * 0.85 / 1000 +
                         self.state["elev1_motor_current"] * 380 * math.sqrt(3) * 0.85 / 1000 +
                         self.state["ship_motor_current"] * 380 * math.sqrt(3) * 0.85 / 1000)
        self.state["energy_consumption"] += total_power_kw * self.update_interval / 3600

        # ==================== ALARMES ====================
        self.state["alarm_high_current"] = 1 if (self.state["conv1_motor_current"] > 250 or
                                                  self.state["elev1_motor_current"] > 350) else 0
        self.state["alarm_high_vibration"] = 1 if (self.state["conv1_vibration"] > 7.5 or
                                                    self.state["ship_vibration"] > 12) else 0
        self.state["alarm_high_temp"] = 1 if (self.state["conv1_bearing_temp"] > 85 or
                                               self.state["elev1_motor_temp"] > 105) else 0
        self.state["alarm_low_flow"] = 1 if self.state["ship_flow_rate"] < 1000 else 0

        # ==================== STATUS ====================
        # Simulação de paradas ocasionais
        if random.random() < 0.0005:  # 0.05% chance de parada
            self.state["conv1_running"] = 0
            self.state["conv2_running"] = 0
            self.state["elev1_running"] = 0
            self.state["ship_running"] = 0
            self.state["downtime_minutes"] += self.update_interval / 60
        elif self.iteration % 50 == 0:  # Religar
            self.state["conv1_running"] = 1
            self.state["conv2_running"] = 1
            self.state["elev1_running"] = 1
            self.state["ship_running"] = 1

    def write_to_modbus(self):
        """Escrever estado atual nos registros Modbus"""
        # Valores analógicos (holding registers)
        registers = {
            40001: int(self.state["conv1_motor_current"] * 10),
            40003: int(self.state["conv1_motor_speed"]),
            40005: int(self.state["conv1_motor_temp"] * 10),
            40007: int(self.state["conv1_bearing_temp"] * 10),
            40009: int(self.state["conv1_vibration"] * 100),
            40011: int(self.state["conv1_flow_rate"]),

            40013: int(self.state["conv2_motor_current"] * 10),
            40015: int(self.state["conv2_motor_speed"]),
            40017: int(self.state["conv2_motor_temp"] * 10),
            40019: int(self.state["conv2_vibration"] * 100),

            40021: int(self.state["elev1_motor_current"] * 10),
            40023: int(self.state["elev1_motor_speed"]),
            40025: int(self.state["elev1_motor_temp"] * 10),
            40027: int(self.state["elev1_vibration"] * 100),

            40029: int(self.state["ship_motor_current"] * 10),
            40031: int(self.state["ship_motor_speed"]),
            40033: int(self.state["ship_flow_rate"]),
            40035: int(self.state["ship_vibration"] * 100),
            40037: int(self.state["ship_boom_angle"] * 10),

            40039: int(self.state["silo1_level"] * 10),
            40041: int(self.state["silo1_temp"] * 10),
            40043: int(self.state["silo2_level"] * 10),

            40045: int(self.state["product_moisture"] * 100),
            40047: int(self.state["product_temp"] * 10),

            40049: int(self.state["loading_rate_accumulated"]),
            40051: int(self.state["vessel_loading_progress"] * 10),
            40053: int(self.state["energy_consumption"]),
        }

        for addr, value in registers.items():
            self.context[0].setValues(3, addr, [value])

        # Valores digitais (coils)
        self.context[0].setValues(1, 1, [bool(self.state["conv1_running"])])
        self.context[0].setValues(1, 2, [bool(self.state["conv2_running"])])
        self.context[0].setValues(1, 3, [bool(self.state["elev1_running"])])
        self.context[0].setValues(1, 4, [bool(self.state["ship_running"])])
        self.context[0].setValues(1, 5, [bool(self.state["alarm_high_current"])])
        self.context[0].setValues(1, 6, [bool(self.state["alarm_high_vibration"])])
        self.context[0].setValues(1, 7, [bool(self.state["alarm_high_temp"])])
        self.context[0].setValues(1, 8, [bool(self.state["alarm_low_flow"])])

    def update_loop(self):
        """Loop principal de atualização"""
        logger.info("🔄 Iniciando loop de atualização...")

        while self.running:
            self.update_process_values()
            self.write_to_modbus()

            # Log a cada 10 iterações
            if self.iteration % 10 == 0:
                logger.info(f"📊 Iteração {self.iteration} | Tempo: {self.iteration * self.update_interval:.0f}s")
                logger.info(f"   CORREIA 1: {self.state['conv1_motor_current']:.1f}A | "
                          f"{self.state['conv1_motor_speed']:.0f}RPM | "
                          f"Vib: {self.state['conv1_vibration']:.2f}mm/s | "
                          f"Temp Rolam: {self.state['conv1_bearing_temp']:.1f}°C")
                logger.info(f"   ELEVADOR:  {self.state['elev1_motor_current']:.1f}A | "
                          f"Temp: {self.state['elev1_motor_temp']:.1f}°C")
                logger.info(f"   SHIPLOADER: {self.state['ship_flow_rate']:.0f} t/h | "
                          f"Vib: {self.state['ship_vibration']:.2f}mm/s | "
                          f"Progresso: {self.state['vessel_loading_progress']:.1f}%")

                # Alertas de anomalia
                if self.state["alarm_high_vibration"]:
                    logger.warning("   ⚠️  ANOMALIA: Vibração alta detectada!")
                if self.state["alarm_high_current"]:
                    logger.warning("   ⚠️  ANOMALIA: Sobrecorrente detectada!")
                if self.state["alarm_high_temp"]:
                    logger.warning("   ⚠️  ANOMALIA: Temperatura alta detectada!")

            self.iteration += 1
            time.sleep(self.update_interval)

    def start(self):
        """Iniciar simulador"""
        self.running = True

        # Thread de atualização
        update_thread = threading.Thread(target=self.update_loop, daemon=True)
        update_thread.start()

        # Identidade Modbus
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'SmartPort'
        identity.ProductCode = 'BULK-TERMINAL'
        identity.VendorUrl = 'https://smartport.com'
        identity.ProductName = 'Bulk Terminal Simulator'
        identity.ModelName = 'GRAIN-SUGAR-SIM'
        identity.MajorMinorRevision = '1.0.0'

        logger.info("=" * 90)
        logger.info("🚢 SmartPort - Simulador de Terminal de Grãos/Açúcar")
        logger.info("=" * 90)
        logger.info(f"📡 Modbus TCP: {self.host}:{self.port}")
        logger.info(f"⏱️  Intervalo: {self.update_interval}s")
        logger.info(f"🏷️  Tags: {len(self.tag_definitions)}")
        logger.info("")
        logger.info("📦 EQUIPAMENTOS SIMULADOS:")
        logger.info("   • Correia Transportadora 1 (Recebimento)")
        logger.info("   • Correia Transportadora 2 (Transferência)")
        logger.info("   • Elevador de Caneca")
        logger.info("   • Shiploader (Carregador de Navio)")
        logger.info("   • 2 Silos de Armazenamento")
        logger.info("")
        logger.info("🔍 ANOMALIAS SIMULADAS:")
        logger.info("   • Rolamento degradando (Correia 1) - após 5min")
        logger.info("   • Sobrecarga periódica (Elevador) - a cada 10min")
        logger.info("   • Spikes de vibração (Shiploader) - aleatórios")
        logger.info("")
        logger.info("📊 COMPATÍVEL COM: PI Vision, Power BI, Grafana, SmartPort Analytics")
        logger.info("=" * 90)

        try:
            StartTcpServer(self.context, identity=identity, address=(self.host, self.port))
        except KeyboardInterrupt:
            self.running = False
            logger.info("\n🛑 Simulador parado pelo usuário")
        except Exception as e:
            self.running = False
            logger.error(f"❌ Erro no servidor: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='SmartPort - Simulador de Terminal de Grãos/Açúcar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python smartport_bulk_terminal_simulator.py
  python smartport_bulk_terminal_simulator.py --port 5030
  python smartport_bulk_terminal_simulator.py --interval 0.5
        """
    )

    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host (padrão: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5020, help='Porta Modbus TCP (padrão: 5020)')
    parser.add_argument('--interval', type=float, default=1.0, help='Intervalo em segundos (padrão: 1.0)')

    args = parser.parse_args()

    simulator = BulkTerminalSimulator(
        host=args.host,
        port=args.port,
        update_interval=args.interval
    )

    simulator.start()


if __name__ == '__main__':
    main()
