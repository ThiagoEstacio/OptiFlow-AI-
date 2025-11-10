"""
OPC UA Server Extensions - Novos nós para sistemas avançados
Adiciona nós para Interlocks, Alarmes estruturados, Manutenção e Energia detalhada
"""
import logging
from asyncua import ua

logger = logging.getLogger(__name__)


async def create_advanced_nodes(server_instance, teag, idx):
    """
    Cria nós OPC UA para sistemas avançados
    
    Args:
        server_instance: Instância do GrainTerminalOPCUAServer
        teag: Nó raiz TEAG
        idx: Namespace index
    """
    nodes = server_instance.nodes
    
    # ====================================================================
    # INTERLOCKS
    # ====================================================================
    interlocks_folder = await teag.add_object(idx, "INTERLOCKS")
    
    # Contador de interlocks ativos
    nodes['INTERLOCKS_ACTIVE_COUNT'] = await interlocks_folder.add_variable(
        idx, "ACTIVE.COUNT", 0
    )
    
    # Lista simplificada de interlocks ativos (últimos 10)
    for i in range(1, 11):
        nodes[f'INTERLOCK_{i:02d}_ID'] = await interlocks_folder.add_variable(
            idx, f"INTLK{i:02d}.ID", ""
        )
        nodes[f'INTERLOCK_{i:02d}_CAUSE'] = await interlocks_folder.add_variable(
            idx, f"INTLK{i:02d}.CAUSE", ""
        )
        nodes[f'INTERLOCK_{i:02d}_TYPE'] = await interlocks_folder.add_variable(
            idx, f"INTLK{i:02d}.TYPE", ""
        )
    
    # ====================================================================
    # ALARMES ESTRUTURADOS
    # ====================================================================
    alarms_folder = await teag.add_object(idx, "ALARMES")
    
    # Resumo por severidade
    nodes['ALARMS_TOTAL'] = await alarms_folder.add_variable(
        idx, "TOTAL.COUNT", 0
    )
    nodes['ALARMS_CRITICAL'] = await alarms_folder.add_variable(
        idx, "CRITICAL.COUNT", 0
    )
    nodes['ALARMS_HIGH'] = await alarms_folder.add_variable(
        idx, "HIGH.COUNT", 0
    )
    nodes['ALARMS_MEDIUM'] = await alarms_folder.add_variable(
        idx, "MEDIUM.COUNT", 0
    )
    nodes['ALARMS_UNACK'] = await alarms_folder.add_variable(
        idx, "UNACKNOWLEDGED.COUNT", 0
    )
    
    # ====================================================================
    # MANUTENÇÃO
    # ====================================================================
    maintenance_folder = await teag.add_object(idx, "MANUTENCAO")
    
    # KPIs de manutenção
    nodes['MAINT_AVG_HEALTH'] = await maintenance_folder.add_variable(
        idx, "HEALTH_MEDIA.PV", 100.0
    )
    nodes['MAINT_NEEDS_ATTENTION'] = await maintenance_folder.add_variable(
        idx, "ATENCAO.COUNT", 0
    )
    nodes['MAINT_CRITICAL'] = await maintenance_folder.add_variable(
        idx, "CRITICO.COUNT", 0
    )
    
    # Por equipamento (Belt samples)
    for belt_id in ['CORR01', 'CORR02', 'CORR03']:
        belt_maint = await maintenance_folder.add_object(idx, belt_id)
        
        nodes[f'MAINT_{belt_id}_HEALTH'] = await belt_maint.add_variable(
            idx, "HEALTH.PV", 100.0
        )
        nodes[f'MAINT_{belt_id}_HOURS'] = await belt_maint.add_variable(
            idx, "HORIMETRO.TOT", 0.0
        )
        nodes[f'MAINT_{belt_id}_VIBRATION'] = await belt_maint.add_variable(
            idx, "VIBRACAO.PV", 0.0
        )
        nodes[f'MAINT_{belt_id}_OIL_TEMP'] = await belt_maint.add_variable(
            idx, "TEMP_OLEO.PV", 50.0
        )
    
    # Elevador
    elv_maint = await maintenance_folder.add_object(idx, "ELV01")
    nodes['MAINT_ELV01_HEALTH'] = await elv_maint.add_variable(
        idx, "HEALTH.PV", 100.0
    )
    nodes['MAINT_ELV01_HOURS'] = await elv_maint.add_variable(
        idx, "HORIMETRO.TOT", 0.0
    )
    nodes['MAINT_ELV01_VIBRATION'] = await elv_maint.add_variable(
        idx, "VIBRACAO.PV", 0.0
    )
    
    # Balança
    bal_maint = await maintenance_folder.add_object(idx, "BAL01")
    nodes['MAINT_BAL01_HEALTH'] = await bal_maint.add_variable(
        idx, "HEALTH.PV", 100.0
    )
    nodes['MAINT_BAL01_HOURS'] = await bal_maint.add_variable(
        idx, "HORIMETRO.TOT", 0.0
    )
    nodes['MAINT_BAL01_VIBRATION'] = await bal_maint.add_variable(
        idx, "VIBRACAO.PV", 0.0
    )
    nodes['MAINT_BAL01_OIL_TEMP'] = await bal_maint.add_variable(
        idx, "TEMP_OLEO.PV", 50.0
    )
    
    # Shiploader
    sld_maint = await maintenance_folder.add_object(idx, "SLD01")
    nodes['MAINT_SLD01_HEALTH'] = await sld_maint.add_variable(
        idx, "HEALTH.PV", 100.0
    )
    nodes['MAINT_SLD01_HOURS'] = await sld_maint.add_variable(
        idx, "HORIMETRO.TOT", 0.0
    )
    nodes['MAINT_SLD01_VIBRATION'] = await sld_maint.add_variable(
        idx, "VIBRACAO.PV", 0.0
    )
    nodes['MAINT_SLD01_OIL_TEMP'] = await sld_maint.add_variable(
        idx, "TEMP_OLEO.PV", 50.0
    )
    
    # ====================================================================
    # ENERGIA DETALHADA
    # ====================================================================
    energia_folder = await teag.add_object(idx, "ENERGIA")
    
    # KPIs globais
    nodes['ENERGY_TOTAL_POWER'] = await energia_folder.add_variable(
        idx, "POTENCIA_TOTAL.PV", 0.0
    )
    nodes['ENERGY_AVG_PF'] = await energia_folder.add_variable(
        idx, "FP_MEDIO.PV", 0.92
    )
    nodes['ENERGY_TOTAL_KWH'] = await energia_folder.add_variable(
        idx, "ENERGIA_TOTAL.TOT", 0.0
    )
    nodes['ENERGY_KWH_PER_TON'] = await energia_folder.add_variable(
        idx, "KWH_POR_TON.PV", 0.0
    )
    nodes['ENERGY_COST_TOTAL'] = await energia_folder.add_variable(
        idx, "CUSTO_TOTAL.TOT", 0.0
    )
    nodes['ENERGY_COST_PEAK'] = await energia_folder.add_variable(
        idx, "CUSTO_PICO.TOT", 0.0
    )
    nodes['ENERGY_COST_OFFPEAK'] = await energia_folder.add_variable(
        idx, "CUSTO_FORA_PICO.TOT", 0.0
    )
    
    # Por equipamento - Grandezas elétricas completas
    for belt_id in ['CORR01', 'CORR02', 'CORR03']:
        belt_elec = await energia_folder.add_object(idx, belt_id)
        
        nodes[f'ELEC_{belt_id}_VOLTAGE'] = await belt_elec.add_variable(
            idx, "TENSAO_LL.PV", 440.0
        )
        nodes[f'ELEC_{belt_id}_CURRENT'] = await belt_elec.add_variable(
            idx, "CORRENTE.PV", 0.0
        )
        nodes[f'ELEC_{belt_id}_POWER_KW'] = await belt_elec.add_variable(
            idx, "POTENCIA_ATIVA.PV", 0.0
        )
        nodes[f'ELEC_{belt_id}_REACTIVE_KVAR'] = await belt_elec.add_variable(
            idx, "POTENCIA_REATIVA.PV", 0.0
        )
        nodes[f'ELEC_{belt_id}_APPARENT_KVA'] = await belt_elec.add_variable(
            idx, "POTENCIA_APARENTE.PV", 0.0
        )
        nodes[f'ELEC_{belt_id}_PF'] = await belt_elec.add_variable(
            idx, "FATOR_POTENCIA.PV", 0.92
        )
        nodes[f'ELEC_{belt_id}_KWH'] = await belt_elec.add_variable(
            idx, "ENERGIA.TOT", 0.0
        )
    
    # Elevador
    elv_elec = await energia_folder.add_object(idx, "ELV01")
    nodes['ELEC_ELV01_POWER_KW'] = await elv_elec.add_variable(
        idx, "POTENCIA_ATIVA.PV", 0.0
    )
    nodes['ELEC_ELV01_PF'] = await elv_elec.add_variable(
        idx, "FATOR_POTENCIA.PV", 0.92
    )
    nodes['ELEC_ELV01_KWH'] = await elv_elec.add_variable(
        idx, "ENERGIA.TOT", 0.0
    )
    
    # Balança
    bal_elec = await energia_folder.add_object(idx, "BAL01")
    nodes['ELEC_BAL01_VOLTAGE'] = await bal_elec.add_variable(
        idx, "TENSAO_LL.PV", 440.0
    )
    nodes['ELEC_BAL01_CURRENT'] = await bal_elec.add_variable(
        idx, "CORRENTE.PV", 0.0
    )
    nodes['ELEC_BAL01_POWER_KW'] = await bal_elec.add_variable(
        idx, "POTENCIA_ATIVA.PV", 0.0
    )
    nodes['ELEC_BAL01_REACTIVE_KVAR'] = await bal_elec.add_variable(
        idx, "POTENCIA_REATIVA.PV", 0.0
    )
    nodes['ELEC_BAL01_APPARENT_KVA'] = await bal_elec.add_variable(
        idx, "POTENCIA_APARENTE.PV", 0.0
    )
    nodes['ELEC_BAL01_PF'] = await bal_elec.add_variable(
        idx, "FATOR_POTENCIA.PV", 0.92
    )
    nodes['ELEC_BAL01_KWH'] = await bal_elec.add_variable(
        idx, "ENERGIA.TOT", 0.0
    )
    
    # Shiploader
    sld_elec = await energia_folder.add_object(idx, "SLD01")
    nodes['ELEC_SLD01_VOLTAGE'] = await sld_elec.add_variable(
        idx, "TENSAO_LL.PV", 440.0
    )
    nodes['ELEC_SLD01_CURRENT'] = await sld_elec.add_variable(
        idx, "CORRENTE.PV", 0.0
    )
    nodes['ELEC_SLD01_POWER_KW'] = await sld_elec.add_variable(
        idx, "POTENCIA_ATIVA.PV", 0.0
    )
    nodes['ELEC_SLD01_REACTIVE_KVAR'] = await sld_elec.add_variable(
        idx, "POTENCIA_REATIVA.PV", 0.0
    )
    nodes['ELEC_SLD01_APPARENT_KVA'] = await sld_elec.add_variable(
        idx, "POTENCIA_APARENTE.PV", 0.0
    )
    nodes['ELEC_SLD01_PF'] = await sld_elec.add_variable(
        idx, "FATOR_POTENCIA.PV", 0.92
    )
    nodes['ELEC_SLD01_KWH'] = await sld_elec.add_variable(
        idx, "ENERGIA.TOT", 0.0
    )
    
    logger.info(f"✅ Created {len(nodes)} advanced OPC-UA nodes")


async def update_advanced_nodes(server_instance):
    """
    Atualiza valores dos nós avançados a cada ciclo
    
    Args:
        server_instance: Instância do GrainTerminalOPCUAServer
    """
    simulator = server_instance.simulator
    nodes = server_instance.nodes
    
    try:
        # ====================================================================
        # INTERLOCKS
        # ====================================================================
        active_interlocks = simulator.interlock_manager.get_active_interlocks()
        await nodes['INTERLOCKS_ACTIVE_COUNT'].write_value(float(len(active_interlocks)))
        
        # Primeiros 10 interlocks
        for i in range(10):
            if i < len(active_interlocks):
                intlk = active_interlocks[i]
                await nodes[f'INTERLOCK_{i+1:02d}_ID'].write_value(intlk['id'])
                await nodes[f'INTERLOCK_{i+1:02d}_CAUSE'].write_value(intlk['cause'])
                await nodes[f'INTERLOCK_{i+1:02d}_TYPE'].write_value(intlk['type'])
            else:
                await nodes[f'INTERLOCK_{i+1:02d}_ID'].write_value("")
                await nodes[f'INTERLOCK_{i+1:02d}_CAUSE'].write_value("")
                await nodes[f'INTERLOCK_{i+1:02d}_TYPE'].write_value("")
        
        # ====================================================================
        # ALARMES
        # ====================================================================
        alarm_summary = simulator.alarm_manager.get_alarm_summary()
        await nodes['ALARMS_TOTAL'].write_value(float(alarm_summary['total']))
        await nodes['ALARMS_CRITICAL'].write_value(float(alarm_summary['critical']))
        await nodes['ALARMS_HIGH'].write_value(float(alarm_summary['high']))
        await nodes['ALARMS_MEDIUM'].write_value(float(alarm_summary['medium']))
        await nodes['ALARMS_UNACK'].write_value(float(alarm_summary['unacknowledged']))
        
        # ====================================================================
        # MANUTENÇÃO
        # ====================================================================
        maint_summary = simulator.maintenance_manager.get_maintenance_summary()
        await nodes['MAINT_AVG_HEALTH'].write_value(float(maint_summary['avg_health_pct']))
        await nodes['MAINT_NEEDS_ATTENTION'].write_value(float(maint_summary['needs_attention']))
        await nodes['MAINT_CRITICAL'].write_value(float(maint_summary['critical']))
        
        # Por equipamento
        for belt_id in ['CORR01', 'CORR02', 'CORR03']:
            if belt_id in simulator.maintenance_manager.maintenance_states:
                maint = simulator.maintenance_manager.maintenance_states[belt_id]
                await nodes[f'MAINT_{belt_id}_HEALTH'].write_value(maint.health_pct)
                await nodes[f'MAINT_{belt_id}_HOURS'].write_value(maint.hours_running)
                await nodes[f'MAINT_{belt_id}_VIBRATION'].write_value(maint.vibration_mm_s)
                await nodes[f'MAINT_{belt_id}_OIL_TEMP'].write_value(maint.oil_temp_C)
        
        if 'ELV01' in simulator.maintenance_manager.maintenance_states:
            maint = simulator.maintenance_manager.maintenance_states['ELV01']
            await nodes['MAINT_ELV01_HEALTH'].write_value(maint.health_pct)
            await nodes['MAINT_ELV01_HOURS'].write_value(maint.hours_running)
            await nodes['MAINT_ELV01_VIBRATION'].write_value(maint.vibration_mm_s)
        
        if 'BAL01' in simulator.maintenance_manager.maintenance_states:
            maint = simulator.maintenance_manager.maintenance_states['BAL01']
            await nodes['MAINT_BAL01_HEALTH'].write_value(maint.health_pct)
            await nodes['MAINT_BAL01_HOURS'].write_value(maint.hours_running)
            await nodes['MAINT_BAL01_VIBRATION'].write_value(maint.vibration_mm_s)
            await nodes['MAINT_BAL01_OIL_TEMP'].write_value(maint.oil_temp_C)
        
        if 'SLD01' in simulator.maintenance_manager.maintenance_states:
            maint = simulator.maintenance_manager.maintenance_states['SLD01']
            await nodes['MAINT_SLD01_HEALTH'].write_value(maint.health_pct)
            await nodes['MAINT_SLD01_HOURS'].write_value(maint.hours_running)
            await nodes['MAINT_SLD01_VIBRATION'].write_value(maint.vibration_mm_s)
            await nodes['MAINT_SLD01_OIL_TEMP'].write_value(maint.oil_temp_C)
        
        # ====================================================================
        # ENERGIA
        # ====================================================================
        energy_summary = simulator.energy_manager.get_electrical_summary()
        await nodes['ENERGY_TOTAL_POWER'].write_value(energy_summary['total_power_kW'])
        await nodes['ENERGY_AVG_PF'].write_value(energy_summary['average_pf'])
        await nodes['ENERGY_TOTAL_KWH'].write_value(energy_summary['total_kWh'])
        await nodes['ENERGY_KWH_PER_TON'].write_value(energy_summary['kWh_per_ton'])
        await nodes['ENERGY_COST_TOTAL'].write_value(energy_summary['cost_total_BRL'])
        await nodes['ENERGY_COST_PEAK'].write_value(energy_summary['cost_peak_BRL'])
        await nodes['ENERGY_COST_OFFPEAK'].write_value(energy_summary['cost_offpeak_BRL'])
        
        # Por equipamento
        for belt_id in ['CORR01', 'CORR02', 'CORR03']:
            if belt_id in simulator.energy_manager.electrical_states:
                elec = simulator.energy_manager.electrical_states[belt_id]
                await nodes[f'ELEC_{belt_id}_VOLTAGE'].write_value(elec.voltage_ll)
                await nodes[f'ELEC_{belt_id}_CURRENT'].write_value(elec.current_A)
                await nodes[f'ELEC_{belt_id}_POWER_KW'].write_value(elec.power_kW)
                await nodes[f'ELEC_{belt_id}_REACTIVE_KVAR'].write_value(elec.reactive_kvar)
                await nodes[f'ELEC_{belt_id}_APPARENT_KVA'].write_value(elec.apparent_kVA)
                await nodes[f'ELEC_{belt_id}_PF'].write_value(elec.power_factor)
                await nodes[f'ELEC_{belt_id}_KWH'].write_value(elec.kWh_total)
        
        if 'ELV01' in simulator.energy_manager.electrical_states:
            elec = simulator.energy_manager.electrical_states['ELV01']
            await nodes['ELEC_ELV01_POWER_KW'].write_value(elec.power_kW)
            await nodes['ELEC_ELV01_PF'].write_value(elec.power_factor)
            await nodes['ELEC_ELV01_KWH'].write_value(elec.kWh_total)
        
        if 'BAL01' in simulator.energy_manager.electrical_states:
            elec = simulator.energy_manager.electrical_states['BAL01']
            await nodes['ELEC_BAL01_VOLTAGE'].write_value(elec.voltage_ll)
            await nodes['ELEC_BAL01_CURRENT'].write_value(elec.current_A)
            await nodes['ELEC_BAL01_POWER_KW'].write_value(elec.power_kW)
            await nodes['ELEC_BAL01_REACTIVE_KVAR'].write_value(elec.reactive_kvar)
            await nodes['ELEC_BAL01_APPARENT_KVA'].write_value(elec.apparent_kVA)
            await nodes['ELEC_BAL01_PF'].write_value(elec.power_factor)
            await nodes['ELEC_BAL01_KWH'].write_value(elec.kWh_total)
        
        if 'SLD01' in simulator.energy_manager.electrical_states:
            elec = simulator.energy_manager.electrical_states['SLD01']
            await nodes['ELEC_SLD01_VOLTAGE'].write_value(elec.voltage_ll)
            await nodes['ELEC_SLD01_CURRENT'].write_value(elec.current_A)
            await nodes['ELEC_SLD01_POWER_KW'].write_value(elec.power_kW)
            await nodes['ELEC_SLD01_REACTIVE_KVAR'].write_value(elec.reactive_kvar)
            await nodes['ELEC_SLD01_APPARENT_KVA'].write_value(elec.apparent_kVA)
            await nodes['ELEC_SLD01_PF'].write_value(elec.power_factor)
            await nodes['ELEC_SLD01_KWH'].write_value(elec.kWh_total)
    
    except Exception as e:
        logger.error(f"Error updating advanced nodes: {e}")
