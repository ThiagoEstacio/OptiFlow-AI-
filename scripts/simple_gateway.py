#!/usr/bin/env python3
"""
Gateway Simplificado - Polling do Simulador para InfluxDB
Faz: Simulador → Gateway → Backend API → InfluxDB
"""
import asyncio
import aiohttp
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleGateway:
    def __init__(self):
        self.simulator_url = "http://localhost:8000"
        self.backend_url = "http://localhost:8000"
        self.poll_interval = 1.0
        self.running = False
        self.tag_mapping = {}
        
    async def load_tags(self):
        """Carrega mapeamento de tags do backend"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.backend_url}/api/v1/tags/"
                async with session.get(url) as response:
                    if response.status == 200:
                        tags = await response.json()
                        self.tag_mapping = {tag['name']: tag['id'] for tag in tags}
                        logger.info(f"✅ Carregados {len(self.tag_mapping)} tags")
                    else:
                        logger.error(f"❌ Erro ao carregar tags: {response.status}")
            except Exception as e:
                logger.error(f"❌ Erro ao conectar ao backend: {e}")
    
    async def step_simulator(self):
        """Executa um step no simulador"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.simulator_url}/api/v1/simulator/step"
                async with session.post(url, params={'dt_s': self.poll_interval}) as response:
                    return response.status == 200
            except Exception as e:
                logger.error(f"❌ Erro ao step simulador: {e}")
                return False
    
    async def poll_simulator(self):
        """Faz polling do status do simulador"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.simulator_url}/api/v1/simulator/status"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ Erro ao poll simulador: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"❌ Erro ao conectar ao simulador: {e}")
                return None
    
    def extract_points(self, status):
        """Extrai TODOS os pontos de dados do status do simulador"""
        points = []
        timestamp = datetime.utcnow().isoformat()
        
        # ===== SYSTEM =====
        system = status.get('system', {})
        self._add_point(points, 'ARZ_SISTEMA_LIGADO_PV', 1.0 if system.get('running') else 0.0, timestamp)
        self._add_point(points, 'ARZ_ARMAZ_INVENTARIO_PV', system.get('warehouse_inventory_t'), timestamp)
        self._add_point(points, 'ARZ_ARMAZ_NIVEL_PV', system.get('warehouse_level_pct'), timestamp)
        self._add_point(points, 'ARZ_ENERGIA_TOTAL_KWH', system.get('total_kWh'), timestamp)
        self._add_point(points, 'ARZ_MASSA_TOTAL_T', system.get('total_mass_t'), timestamp)
        self._add_point(points, 'ARZ_CUSTO_BRL', system.get('cost_BRL'), timestamp)
        self._add_point(points, 'ARZ_KWH_POR_TON', system.get('kWh_per_ton'), timestamp)
        
        # ===== GATES (10 gates completos) =====
        for gate in status.get('gates', []):
            gid = gate['id']
            prefix = f'ARZ_GATES_GATE{gid:02d}'
            self._add_point(points, f'{prefix}_POSICAO_PV', gate.get('open_pct'), timestamp)
            self._add_point(points, f'{prefix}_POSICAO_SP', gate.get('open_pct_sp'), timestamp)
            self._add_point(points, f'{prefix}_VAZAO_PV', gate.get('flow_tph'), timestamp)
            self._add_point(points, f'{prefix}_ENTUPIDO_AL', 1.0 if gate.get('plugged') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_FALHA_AL', 1.0 if gate.get('failure') else 0.0, timestamp)
        
        # ===== BELTS (CORR01, CORR02, CORR03 completos) =====
        for belt_id, belt in status.get('belts', {}).items():
            # belt_id já vem como "CORR01", "CORR02", etc
            prefix = f'ARZ_{belt_id}'
            self._add_point(points, f'{prefix}_LIGADO_FB', 1.0 if belt.get('running') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_RPM_PV', belt.get('rpm'), timestamp)
            self._add_point(points, f'{prefix}_VELOCIDADE_PV', belt.get('speed_mps'), timestamp)
            self._add_point(points, f'{prefix}_VAZAO_PV', belt.get('flow_tph'), timestamp)
            self._add_point(points, f'{prefix}_CARGA_PV', belt.get('load_pct'), timestamp)
            self._add_point(points, f'{prefix}_CORRENTE_PV', belt.get('current_A'), timestamp)
            self._add_point(points, f'{prefix}_POTENCIA_PV', belt.get('power_kW'), timestamp)
            self._add_point(points, f'{prefix}_TEMP_MANCAL_PV', belt.get('temp_bearing_C'), timestamp)
            self._add_point(points, f'{prefix}_TEMP_CORREIA_PV', belt.get('temp_belt_C'), timestamp)
            self._add_point(points, f'{prefix}_TEMP_TAMBOR_PV', belt.get('temp_drum_C'), timestamp)
            self._add_point(points, f'{prefix}_CHUTE_NIVEL_PV', belt.get('chute_level_pct'), timestamp)
            self._add_point(points, f'{prefix}_CHUTE_ENTUPIDO_AL', 1.0 if belt.get('chute_plugged') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_SUBVELOCIDADE_WARN', 1.0 if belt.get('underspeed_warn') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_SUBVELOCIDADE_AL', 1.0 if belt.get('underspeed_alarm') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_DESALINHADA_AL', 1.0 if belt.get('misaligned') else 0.0, timestamp)
            self._add_point(points, f'{prefix}_RASGADA_AL', 1.0 if belt.get('torn') else 0.0, timestamp)
        
        # ===== ELEVATOR (ELV01 completo) =====
        elevator = status.get('elevator', {})
        self._add_point(points, 'ELV_ELV01_LIGADO_FB', 1.0 if elevator.get('running') else 0.0, timestamp)
        self._add_point(points, 'ELV_ELV01_VELOCIDADE_PV', elevator.get('speed_mps'), timestamp)
        self._add_point(points, 'ELV_ELV01_VAZAO_PV', elevator.get('flow_tph'), timestamp)
        self._add_point(points, 'ELV_ELV01_CORRENTE_PV', elevator.get('current_A'), timestamp)
        self._add_point(points, 'ELV_ELV01_POTENCIA_PV', elevator.get('power_kW'), timestamp)
        self._add_point(points, 'ELV_ELV01_TEMP_MOTOR_PV', elevator.get('temp_motor_C'), timestamp)
        self._add_point(points, 'ELV_ELV01_TEMP_REDUTOR_PV', elevator.get('temp_gearbox_C'), timestamp)
        self._add_point(points, 'ELV_ELV01_TEMP_MANCAL_SUP_PV', elevator.get('temp_bearing_sup_C'), timestamp)
        self._add_point(points, 'ELV_ELV01_TEMP_MANCAL_INF_PV', elevator.get('temp_bearing_inf_C'), timestamp)
        self._add_point(points, 'ELV_ELV01_CORREIA_FROUXA_AL', 1.0 if elevator.get('belt_loose') else 0.0, timestamp)
        self._add_point(points, 'ELV_ELV01_ESCORREGAMENTO_AL', 1.0 if elevator.get('slip') else 0.0, timestamp)
        self._add_point(points, 'ELV_ELV01_TRAVADA_AL', 1.0 if elevator.get('jammed') else 0.0, timestamp)
        
        # ===== BALANCE (BAL01 completo) =====
        balance = status.get('balance', {})
        self._add_point(points, 'BAL_BAL01_LIGADO_FB', 1.0 if balance.get('running') else 0.0, timestamp)
        self._add_point(points, 'BAL_BAL01_PESO_PV', balance.get('weight_kg'), timestamp)
        self._add_point(points, 'BAL_BAL01_PESO_SP', balance.get('target_kg'), timestamp)
        self._add_point(points, 'BAL_BAL01_CICLOS_TOT', balance.get('cycle_count'), timestamp)
        self._add_point(points, 'BAL_BAL01_TOTAL_TOT', balance.get('total_mass_t'), timestamp)
        self._add_point(points, 'BAL_BAL01_VAZAO_PV', balance.get('avg_flow_tph'), timestamp)
        
        # ===== SHIPLOADER (SLD01 completo) =====
        shiploader = status.get('shiploader', {})
        self._add_point(points, 'SLD_SLD01_LIGADO_FB', 1.0 if shiploader.get('running') else 0.0, timestamp)
        self._add_point(points, 'SLD_SLD01_VAZAO_SP', shiploader.get('flow_sp_tph'), timestamp)
        self._add_point(points, 'SLD_SLD01_VAZAO_PV', shiploader.get('flow_pv_tph'), timestamp)
        self._add_point(points, 'SLD_SLD01_POTENCIA_PV', shiploader.get('power_kW'), timestamp)
        self._add_point(points, 'SLD_SLD01_POEIRA_PV', shiploader.get('dust_level'), timestamp)
        
        # ===== MAINTENANCE =====
        maintenance = status.get('maintenance', {})
        avg_health = maintenance.get('avg_health_pct', 100.0)
        self._add_point(points, 'MANUTENCAO_HEALTH_MEDIO_PV', avg_health, timestamp)
        
        for equip_id, maint in maintenance.get('equipment', {}).items():
            # equip_id já vem como "CORR01", "ELV01", etc
            prefix = f'MANUTENCAO_{equip_id}'
            self._add_point(points, f'{prefix}_HEALTH_PV', maint.get('health_pct'), timestamp)
            self._add_point(points, f'{prefix}_VIBRACAO_PV', maint.get('vibration_mm_s'), timestamp)
            self._add_point(points, f'{prefix}_TEMP_OLEO_PV', maint.get('oil_temp_C'), timestamp)
            self._add_point(points, f'{prefix}_HORIMETRO_TOT', maint.get('hours_running'), timestamp)
        
        # ===== ENERGY =====
        energy = status.get('energy', {})
        self._add_point(points, 'ENERGIA_POTENCIA_TOTAL_PV', energy.get('total_power_kW'), timestamp)
        self._add_point(points, 'ENERGIA_FP_MEDIO_PV', energy.get('avg_power_factor'), timestamp)
        self._add_point(points, 'ENERGIA_ENERGIA_TOTAL_TOT', energy.get('total_kWh'), timestamp)
        self._add_point(points, 'ENERGIA_CUSTO_PICO_TOT', energy.get('cost_peak_BRL'), timestamp)
        self._add_point(points, 'ENERGIA_CUSTO_FORA_PICO_TOT', energy.get('cost_offpeak_BRL'), timestamp)
        self._add_point(points, 'ENERGIA_CUSTO_TOTAL_TOT', energy.get('cost_total_BRL'), timestamp)
        
        for equip_id, elec in energy.get('equipment', {}).items():
            # equip_id já vem como "CORR01", "ELV01", etc
            prefix = f'ENERGIA_{equip_id}'
            self._add_point(points, f'{prefix}_TENSAO_LL_PV', elec.get('voltage_V'), timestamp)
            self._add_point(points, f'{prefix}_CORRENTE_PV', elec.get('current_A'), timestamp)
            self._add_point(points, f'{prefix}_POTENCIA_ATIVA_PV', elec.get('power_kW'), timestamp)
            self._add_point(points, f'{prefix}_POTENCIA_REATIVA_PV', elec.get('power_kVAr'), timestamp)
            self._add_point(points, f'{prefix}_POTENCIA_APARENTE_PV', elec.get('power_kVA'), timestamp)
            self._add_point(points, f'{prefix}_FP_PV', elec.get('power_factor'), timestamp)
            self._add_point(points, f'{prefix}_ENERGIA_TOTAL_TOT', elec.get('kWh_total'), timestamp)
        
        # ===== INTERLOCKS =====
        interlocks = status.get('interlocks', {})
        self._add_point(points, 'ARZ_INTERTRAVAMENTOS_ATIVOS_COUNT', interlocks.get('active_count', 0), timestamp)
        
        # ===== ALARMS =====
        alarms = status.get('alarms', {})
        if alarms:
            self._add_point(points, 'ARZ_ALARMES_ATIVOS_COUNT', alarms.get('active_count', 0), timestamp)
        
        return points
    
    def _add_point(self, points, tag_name, value, timestamp):
        """Adiciona ponto se tag existe no mapeamento"""
        if tag_name in self.tag_mapping and value is not None:
            points.append({
                'tag_id': self.tag_mapping[tag_name],
                'value': float(value),
                'timestamp': timestamp,
                'quality': 'good'
            })
    
    async def send_to_backend(self, points):
        """Envia pontos para o backend (que grava no InfluxDB)"""
        if not points:
            return True
            
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.backend_url}/api/v1/timeseries/batch"
                async with session.post(url, json=points) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Enviados {len(points)} pontos para Backend → InfluxDB")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"❌ Erro ao enviar para backend: {response.status} - {text}")
                        return False
            except Exception as e:
                logger.error(f"❌ Erro ao enviar dados: {e}")
                return False
    
    async def run(self):
        """Loop principal do gateway"""
        self.running = True
        
        logger.info("=" * 60)
        logger.info("🚀 Gateway Simplificado Iniciado")
        logger.info("📡 Simulador → Gateway → Backend → InfluxDB")
        logger.info("=" * 60)
        
        # Carregar tags
        await self.load_tags()
        
        if not self.tag_mapping:
            logger.error("❌ Nenhum tag carregado. Encerrando.")
            return
        
        cycle = 0
        while self.running:
            try:
                cycle += 1
                
                # 1. Step no simulador
                await self.step_simulator()
                
                # 2. Poll status
                status = await self.poll_simulator()
                
                if status:
                    # 3. Extrair pontos
                    points = self.extract_points(status)
                    
                    # 4. Enviar para backend
                    if points:
                        success = await self.send_to_backend(points)
                        if success:
                            logger.info(f"🔄 Ciclo {cycle}: {len(points)} pontos gravados no InfluxDB")
                    else:
                        logger.warning(f"⚠️  Ciclo {cycle}: Nenhum ponto extraído")
                else:
                    logger.warning(f"⚠️  Ciclo {cycle}: Falha ao poll simulador")
                
                # Aguardar intervalo
                await asyncio.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("\n👋 Encerrando gateway...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Erro no ciclo {cycle}: {e}")
                await asyncio.sleep(self.poll_interval)
        
        logger.info("✅ Gateway encerrado")


async def main():
    gateway = SimpleGateway()
    await gateway.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Gateway interrompido pelo usuário")
