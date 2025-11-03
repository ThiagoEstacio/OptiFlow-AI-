"""
Sistema de Eventos Operacionais Realísticos para Demonstração Comercial
========================================================================

Este módulo simula eventos operacionais dinâmicos que tornam o simulador
ultra-realístico para apresentações de venda do Smartport:

- Chegada de navios e agendamento de embarques
- Troca de produtos (soja → milho → trigo)
- Paradas programadas e emergenciais
- Condições climáticas (chuva, vento) afetando operação
- Variações de demanda e urgência operacional
- Eventos de manutenção preventiva/corretiva
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class EventType(Enum):
    """Tipos de eventos operacionais"""
    SHIP_ARRIVAL = "ship_arrival"
    SHIP_DEPARTURE = "ship_departure"
    PRODUCT_CHANGE = "product_change"
    WEATHER_CHANGE = "weather_change"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    EMERGENCY_STOP = "emergency_stop"
    SHIFT_CHANGE = "shift_change"
    POWER_FLUCTUATION = "power_fluctuation"


class WeatherCondition(Enum):
    """Condições climáticas"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"
    STRONG_WIND = "strong_wind"


class ProductType(Enum):
    """Tipos de produtos"""
    SOJA = "soja"
    MILHO = "milho"
    TRIGO = "trigo"
    FARELO = "farelo"


@dataclass
class Ship:
    """Representa um navio aguardando ou sendo carregado"""
    name: str
    dwt: int  # Deadweight tonnage (toneladas)
    product: ProductType
    arrival_time: datetime
    target_load_t: float
    loaded_t: float = 0.0
    berth_assigned: Optional[str] = None
    status: str = "waiting"  # waiting, loading, loaded, departed
    priority: int = 1  # 1=normal, 2=high, 3=urgent
    
    @property
    def loading_progress(self) -> float:
        """Retorna progresso de carregamento (0-100%)"""
        return (self.loaded_t / self.target_load_t) * 100 if self.target_load_t > 0 else 0


@dataclass
class OperationalEvent:
    """Evento operacional"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    description: str
    impact: Dict[str, Any] = field(default_factory=dict)
    duration_s: Optional[float] = None
    resolved: bool = False


class OperationalEventsManager:
    """Gerenciador de eventos operacionais realísticos"""
    
    def __init__(self):
        self.current_weather = WeatherCondition.CLEAR
        self.current_product = ProductType.SOJA
        self.ships_queue: List[Ship] = []
        self.active_events: List[OperationalEvent] = []
        self.event_history: List[OperationalEvent] = []
        
        # Estatísticas operacionais
        self.total_ships_served = 0
        self.total_loaded_t = 0.0
        self.weather_downtime_s = 0.0
        self.maintenance_downtime_s = 0.0
        
        # Gerador de nomes de navios realísticos
        self.ship_prefixes = ["MV", "MS", "SS", "NS"]
        self.ship_names = [
            "Atlantic Pride", "Pacific Glory", "Baltic Star", "Nordic Wave",
            "Southern Cross", "Eastern Dawn", "Western Sun", "Ocean Spirit",
            "Grain Master", "Cargo Queen", "Trade Wind", "Sea Harvest",
            "Golden Horizon", "Silver Stream", "Crystal Bay", "Pearl River"
        ]
        
        # Tempo para próximo evento
        self.next_ship_arrival_s = random.uniform(1800, 3600)  # 30-60 min
        self.next_weather_change_s = random.uniform(3600, 7200)  # 1-2 h
        self.next_product_change_s = random.uniform(14400, 28800)  # 4-8 h
        
        # Sensor noise models (para realismo)
        self.sensor_noise_std = {
            'temperature': 0.5,  # ±0.5°C
            'flow_rate': 2.0,    # ±2 t/h
            'weight': 0.1,       # ±0.1 t
            'speed': 0.02,       # ±0.02 m/s
            'current': 0.5,      # ±0.5 A
            'voltage': 2.0,      # ±2 V
        }
        
        # Inicializa com alguns navios na fila
        self._generate_initial_ships()
    
    def _generate_initial_ships(self):
        """Gera navios iniciais na fila"""
        for i in range(random.randint(2, 4)):
            self._create_random_ship(offset_minutes=i * 30)
    
    def _create_random_ship(self, offset_minutes: int = 0) -> Ship:
        """Cria um navio com dados realísticos"""
        prefix = random.choice(self.ship_prefixes)
        name = f"{prefix} {random.choice(self.ship_names)}"
        
        # DWT típico de graneleiros (Panamax/Supramax)
        dwt = random.choice([
            random.randint(50000, 80000),   # Panamax
            random.randint(30000, 50000),   # Supramax
            random.randint(10000, 30000),   # Handysize
        ])
        
        # Carga típica é 80-95% do DWT
        target_load = dwt * random.uniform(0.80, 0.95)
        
        ship = Ship(
            name=name,
            dwt=dwt,
            product=random.choice(list(ProductType)),
            arrival_time=datetime.now() - timedelta(minutes=offset_minutes),
            target_load_t=target_load,
            priority=random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        )
        
        self.ships_queue.append(ship)
        
        # Cria evento de chegada
        event = OperationalEvent(
            event_id=f"EVT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            event_type=EventType.SHIP_ARRIVAL,
            timestamp=ship.arrival_time,
            description=f"Navio {ship.name} chegou (DWT: {ship.dwt:,}t, Produto: {ship.product.value})",
            impact={
                'ship_name': ship.name,
                'dwt': ship.dwt,
                'product': ship.product.value,
                'target_load_t': target_load,
                'priority': ship.priority
            }
        )
        self.active_events.append(event)
        
        return ship
    
    def step(self, dt_s: float) -> Dict[str, Any]:
        """
        Atualiza sistema de eventos (chamado a cada step do simulador)
        
        Returns:
            Dict com eventos ocorridos e modificadores operacionais
        """
        modifiers = {
            'weather_flow_factor': 1.0,
            'weather_speed_factor': 1.0,
            'maintenance_active': False,
            'emergency_stop': False,
            'power_stable': True,
            'current_weather': self.current_weather.value,
            'current_product': self.current_product.value,
            'ships_waiting': len([s for s in self.ships_queue if s.status == "waiting"]),
            'ships_loading': len([s for s in self.ships_queue if s.status == "loading"]),
            'new_events': []
        }
        
        # ===== CHEGADA DE NAVIOS =====
        self.next_ship_arrival_s -= dt_s
        if self.next_ship_arrival_s <= 0:
            ship = self._create_random_ship()
            modifiers['new_events'].append({
                'type': 'ship_arrival',
                'ship': ship.name,
                'dwt': ship.dwt,
                'product': ship.product.value
            })
            self.next_ship_arrival_s = random.uniform(1800, 7200)  # 30min-2h
        
        # ===== MUDANÇA DE CLIMA =====
        self.next_weather_change_s -= dt_s
        if self.next_weather_change_s <= 0:
            old_weather = self.current_weather
            self.current_weather = self._transition_weather(old_weather)
            
            if self.current_weather != old_weather:
                event = OperationalEvent(
                    event_id=f"EVT_WEATHER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type=EventType.WEATHER_CHANGE,
                    timestamp=datetime.now(),
                    description=f"Condição climática alterada: {old_weather.value} → {self.current_weather.value}",
                    impact={'from': old_weather.value, 'to': self.current_weather.value}
                )
                self.active_events.append(event)
                modifiers['new_events'].append({
                    'type': 'weather_change',
                    'from': old_weather.value,
                    'to': self.current_weather.value
                })
            
            self.next_weather_change_s = random.uniform(3600, 10800)  # 1-3h
        
        # Aplicar efeitos climáticos
        if self.current_weather == WeatherCondition.LIGHT_RAIN:
            modifiers['weather_flow_factor'] = 0.90  # 10% redução
            modifiers['weather_speed_factor'] = 0.95
        elif self.current_weather == WeatherCondition.HEAVY_RAIN:
            modifiers['weather_flow_factor'] = 0.70  # 30% redução
            modifiers['weather_speed_factor'] = 0.80
            self.weather_downtime_s += dt_s * 0.3
        elif self.current_weather == WeatherCondition.STRONG_WIND:
            modifiers['weather_flow_factor'] = 0.85  # 15% redução
            modifiers['weather_speed_factor'] = 0.90
        
        # ===== MUDANÇA DE PRODUTO =====
        self.next_product_change_s -= dt_s
        if self.next_product_change_s <= 0 and random.random() < 0.3:  # 30% chance
            old_product = self.current_product
            products = [p for p in ProductType if p != old_product]
            self.current_product = random.choice(products)
            
            event = OperationalEvent(
                event_id=f"EVT_PRODUCT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                event_type=EventType.PRODUCT_CHANGE,
                timestamp=datetime.now(),
                description=f"Troca de produto: {old_product.value} → {self.current_product.value}",
                impact={'from': old_product.value, 'to': self.current_product.value},
                duration_s=600  # 10 min de parada para limpeza
            )
            self.active_events.append(event)
            modifiers['new_events'].append({
                'type': 'product_change',
                'from': old_product.value,
                'to': self.current_product.value,
                'downtime_s': 600
            })
            
            self.next_product_change_s = random.uniform(14400, 43200)  # 4-12h
        
        # ===== EVENTOS ALEATÓRIOS =====
        # Flutuação de energia (raro)
        if random.random() < 0.0001 * dt_s:  # ~0.01% por segundo
            event = OperationalEvent(
                event_id=f"EVT_POWER_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                event_type=EventType.POWER_FLUCTUATION,
                timestamp=datetime.now(),
                description="Flutuação de energia detectada",
                impact={'voltage_drop': random.uniform(5, 15)},
                duration_s=random.uniform(2, 10)
            )
            self.active_events.append(event)
            modifiers['power_stable'] = False
            modifiers['new_events'].append({
                'type': 'power_fluctuation',
                'duration_s': event.duration_s
            })
        
        # Resolve eventos com duração
        for event in self.active_events[:]:
            if event.duration_s:
                event.duration_s -= dt_s
                if event.duration_s <= 0:
                    event.resolved = True
                    self.event_history.append(event)
                    self.active_events.remove(event)
        
        return modifiers
    
    def _transition_weather(self, current: WeatherCondition) -> WeatherCondition:
        """Transição realística de clima (Markov chain)"""
        transitions = {
            WeatherCondition.CLEAR: {
                WeatherCondition.CLEAR: 0.7,
                WeatherCondition.CLOUDY: 0.25,
                WeatherCondition.LIGHT_RAIN: 0.05,
            },
            WeatherCondition.CLOUDY: {
                WeatherCondition.CLEAR: 0.3,
                WeatherCondition.CLOUDY: 0.4,
                WeatherCondition.LIGHT_RAIN: 0.2,
                WeatherCondition.STRONG_WIND: 0.1,
            },
            WeatherCondition.LIGHT_RAIN: {
                WeatherCondition.CLOUDY: 0.4,
                WeatherCondition.LIGHT_RAIN: 0.3,
                WeatherCondition.HEAVY_RAIN: 0.2,
                WeatherCondition.CLEAR: 0.1,
            },
            WeatherCondition.HEAVY_RAIN: {
                WeatherCondition.HEAVY_RAIN: 0.4,
                WeatherCondition.LIGHT_RAIN: 0.4,
                WeatherCondition.CLOUDY: 0.2,
            },
            WeatherCondition.STRONG_WIND: {
                WeatherCondition.CLOUDY: 0.5,
                WeatherCondition.STRONG_WIND: 0.3,
                WeatherCondition.CLEAR: 0.2,
            },
        }
        
        options = transitions.get(current, {WeatherCondition.CLEAR: 1.0})
        states = list(options.keys())
        probs = list(options.values())
        return random.choices(states, weights=probs)[0]
    
    def add_sensor_noise(self, value: float, sensor_type: str) -> float:
        """
        Adiciona ruído realístico ao valor do sensor
        
        Args:
            value: Valor nominal do sensor
            sensor_type: Tipo de sensor (para buscar std apropriado)
        
        Returns:
            Valor com ruído gaussiano aplicado
        """
        std = self.sensor_noise_std.get(sensor_type, 0.1)
        noise = np.random.normal(0, std)
        return max(0, value + noise)  # Evita valores negativos
    
    def add_sensor_drift(self, value: float, time_s: float, drift_rate: float = 0.0001) -> float:
        """
        Adiciona drift temporal ao sensor (degradação/calibração)
        
        Args:
            value: Valor nominal
            time_s: Tempo desde inicialização (segundos)
            drift_rate: Taxa de drift por segundo
        
        Returns:
            Valor com drift aplicado
        """
        drift = value * drift_rate * time_s
        return value + drift
    
    def get_loading_ship(self) -> Optional[Ship]:
        """Retorna navio atualmente sendo carregado"""
        for ship in self.ships_queue:
            if ship.status == "loading":
                return ship
        return None
    
    def start_loading_ship(self, ship: Ship, berth: str = "SLD01"):
        """Inicia carregamento de um navio"""
        ship.status = "loading"
        ship.berth_assigned = berth
        
        event = OperationalEvent(
            event_id=f"EVT_LOAD_START_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            event_type=EventType.SHIP_ARRIVAL,
            timestamp=datetime.now(),
            description=f"Iniciando carregamento do {ship.name}",
            impact={'ship': ship.name, 'target_t': ship.target_load_t}
        )
        self.active_events.append(event)
    
    def update_ship_loading(self, loaded_t: float):
        """Atualiza quantidade carregada no navio atual"""
        ship = self.get_loading_ship()
        if ship:
            ship.loaded_t += loaded_t
            
            # Navio completo?
            if ship.loaded_t >= ship.target_load_t:
                ship.status = "loaded"
                self.total_ships_served += 1
                self.total_loaded_t += ship.loaded_t
                
                event = OperationalEvent(
                    event_id=f"EVT_LOAD_COMPLETE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    event_type=EventType.SHIP_DEPARTURE,
                    timestamp=datetime.now(),
                    description=f"{ship.name} carregado com {ship.loaded_t:.0f}t - Partindo",
                    impact={'ship': ship.name, 'total_loaded_t': ship.loaded_t}
                )
                self.active_events.append(event)
                
                # Remove da fila após alguns segundos
                self.ships_queue.remove(ship)
                
                # Inicia próximo navio automaticamente
                waiting_ships = [s for s in self.ships_queue if s.status == "waiting"]
                if waiting_ships:
                    next_ship = sorted(waiting_ships, key=lambda s: s.priority, reverse=True)[0]
                    self.start_loading_ship(next_ship)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados para dashboard executivo"""
        return {
            'weather': {
                'current': self.current_weather.value,
                'flow_impact': self._get_weather_flow_factor(),
            },
            'ships': {
                'waiting': len([s for s in self.ships_queue if s.status == "waiting"]),
                'loading': len([s for s in self.ships_queue if s.status == "loading"]),
                'total_served': self.total_ships_served,
                'total_loaded_t': self.total_loaded_t,
                'queue': [
                    {
                        'name': s.name,
                        'dwt': s.dwt,
                        'product': s.product.value,
                        'target_t': s.target_load_t,
                        'loaded_t': s.loaded_t,
                        'progress': s.loading_progress,
                        'status': s.status,
                        'priority': s.priority
                    }
                    for s in self.ships_queue[:5]  # Top 5
                ]
            },
            'product': {
                'current': self.current_product.value,
            },
            'downtime': {
                'weather_s': self.weather_downtime_s,
                'maintenance_s': self.maintenance_downtime_s,
            },
            'recent_events': [
                {
                    'type': e.event_type.value,
                    'description': e.description,
                    'timestamp': e.timestamp.isoformat(),
                }
                for e in self.active_events[-10:]  # Últimos 10
            ]
        }
    
    def _get_weather_flow_factor(self) -> float:
        """Retorna fator de redução de flow baseado no clima"""
        factors = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.CLOUDY: 1.0,
            WeatherCondition.LIGHT_RAIN: 0.90,
            WeatherCondition.HEAVY_RAIN: 0.70,
            WeatherCondition.STRONG_WIND: 0.85,
        }
        return factors.get(self.current_weather, 1.0)
