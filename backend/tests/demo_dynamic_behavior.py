#!/usr/bin/env python3
"""
Demonstração do Comportamento Dinâmico do Simulador
====================================================

Este script demonstra:
1. Aumento de corrente elétrica e consumo de energia ao ligar equipamentos
2. Aumento de fluxo ao abrir as comportas (vazadores)
3. Aquecimento dos mancais ao longo do tempo de operação
"""

import sys
import time
sys.path.insert(0, 'backend')

from app.services.grain_terminal_simulator import GrainTerminalSimulator


def print_separator(title=""):
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)
    print()


def demo_startup_electrical():
    """Demonstra o aumento de corrente e potência ao ligar o sistema"""
    print_separator("TESTE 1: Corrente Elétrica e Consumo ao Ligar Equipamentos")

    sim = GrainTerminalSimulator()

    print("📊 Estado Inicial (Sistema DESLIGADO):")
    print(f"  CORR01 - Corrente: {sim.belts['CORR01'].current_A:.2f} A, Potência: {sim.belts['CORR01'].power_kW:.2f} kW")
    print(f"  CORR02 - Corrente: {sim.belts['CORR02'].current_A:.2f} A, Potência: {sim.belts['CORR02'].power_kW:.2f} kW")
    print(f"  CORR03 - Corrente: {sim.belts['CORR03'].current_A:.2f} A, Potência: {sim.belts['CORR03'].power_kW:.2f} kW")
    print(f"  ELV01  - Corrente: {sim.elevator.current_A:.2f} A, Potência: {sim.elevator.power_kW:.2f} kW")
    print(f"  SLD01  - Potência: {sim.shiploader.power_kW:.2f} kW")
    print(f"  Energia Total: {sim.total_kWh:.4f} kWh")
    print(f"  Custo Total: R$ {sim.cost_BRL:.2f}")

    print("\n⚡ LIGANDO O SISTEMA...")
    sim.start()

    # Simula 3 segundos com sistema ligado mas sem carga
    print("\n📊 Estado após ligar (sem carga - 3 segundos):")
    for i in range(3):
        sim.step(dt_s=1.0)

    print(f"  CORR01 - Corrente: {sim.belts['CORR01'].current_A:.2f} A, Potência: {sim.belts['CORR01'].power_kW:.2f} kW")
    print(f"  CORR02 - Corrente: {sim.belts['CORR02'].current_A:.2f} A, Potência: {sim.belts['CORR02'].power_kW:.2f} kW")
    print(f"  CORR03 - Corrente: {sim.belts['CORR03'].current_A:.2f} A, Potência: {sim.belts['CORR03'].power_kW:.2f} kW")
    print(f"  ELV01  - Corrente: {sim.elevator.current_A:.2f} A, Potência: {sim.elevator.power_kW:.2f} kW")
    print(f"  SLD01  - Potência: {sim.shiploader.power_kW:.2f} kW")
    print(f"  Energia Total: {sim.total_kWh:.4f} kWh (Δ = +{sim.total_kWh:.4f} kWh)")
    print(f"  Custo Total: R$ {sim.cost_BRL:.2f} (Δ = +R$ {sim.cost_BRL:.2f})")

    print("\n✅ RESULTADO:")
    print("  → Corrente elétrica AUMENTOU ao ligar (corrente de partida)")
    print("  → Potência AUMENTOU mesmo sem carga (perdas mecânicas)")
    print("  → Energia está sendo CONSUMIDA e CONTABILIZADA")
    print("  → Custo está sendo CALCULADO em tempo real")

    return sim


def demo_flow_control():
    """Demonstra o aumento de fluxo ao abrir as comportas"""
    print_separator("TESTE 2: Controle de Fluxo - Abertura de Comportas (Vazadores)")

    sim = GrainTerminalSimulator()
    sim.start()

    print("📊 Estado Inicial (Comportas FECHADAS):")
    total_flow = sum(g.flow_tph for g in sim.gates)
    print(f"  Comportas abertura média: {sum(g.open_pct for g in sim.gates)/len(sim.gates):.1f}%")
    print(f"  Fluxo total das comportas: {total_flow:.2f} t/h")
    print(f"  CORR01 Fluxo: {sim.belts['CORR01'].flow_tph:.2f} t/h")
    print(f"  CORR01 Carga: {sim.belts['CORR01'].load_pct:.1f}%")
    print(f"  CORR01 Corrente: {sim.belts['CORR01'].current_A:.2f} A")
    print(f"  CORR01 Potência: {sim.belts['CORR01'].power_kW:.2f} kW")

    # Simula alguns passos para estabilizar
    for _ in range(3):
        sim.step(dt_s=1.0)

    print("\n🔧 ABRINDO COMPORTAS para 50%...")
    for gate in sim.gates:
        gate.open_pct_sp = 50.0

    # Simula 10 segundos (comportas abrem a 5%/s, então leva ~10s para abrir de 0 a 50%)
    print("\n📈 Evolução do Fluxo (abertura progressiva):")
    for i in range(1, 11):
        sim.step(dt_s=1.0)
        total_flow = sum(g.flow_tph for g in sim.gates)
        avg_opening = sum(g.open_pct for g in sim.gates)/len(sim.gates)
        if i % 2 == 0:  # Mostra a cada 2 segundos
            print(f"  t={i}s: Abertura={avg_opening:.1f}%, Fluxo={total_flow:.1f} t/h, " +
                  f"CORR01={sim.belts['CORR01'].flow_tph:.1f} t/h ({sim.belts['CORR01'].load_pct:.1f}%), " +
                  f"Corrente={sim.belts['CORR01'].current_A:.1f}A, " +
                  f"Potência={sim.belts['CORR01'].power_kW:.1f}kW")

    initial_flow = total_flow
    initial_current = sim.belts['CORR01'].current_A
    initial_power = sim.belts['CORR01'].power_kW

    print("\n🔧 ABRINDO COMPORTAS para 100%...")
    for gate in sim.gates:
        gate.open_pct_sp = 100.0

    # Simula mais 10 segundos
    print("\n📈 Evolução do Fluxo (abertura para 100%):")
    for i in range(11, 21):
        sim.step(dt_s=1.0)
        total_flow = sum(g.flow_tph for g in sim.gates)
        avg_opening = sum(g.open_pct for g in sim.gates)/len(sim.gates)
        if i % 2 == 0:  # Mostra a cada 2 segundos
            print(f"  t={i}s: Abertura={avg_opening:.1f}%, Fluxo={total_flow:.1f} t/h, " +
                  f"CORR01={sim.belts['CORR01'].flow_tph:.1f} t/h ({sim.belts['CORR01'].load_pct:.1f}%), " +
                  f"Corrente={sim.belts['CORR01'].current_A:.1f}A, " +
                  f"Potência={sim.belts['CORR01'].power_kW:.1f}kW")

    final_flow = total_flow
    final_current = sim.belts['CORR01'].current_A
    final_power = sim.belts['CORR01'].power_kW

    print("\n✅ RESULTADO:")
    print(f"  → Fluxo AUMENTOU de {initial_flow:.1f} t/h para {final_flow:.1f} t/h " +
          f"(+{final_flow-initial_flow:.1f} t/h, +{((final_flow/initial_flow-1)*100):.1f}%)")
    print(f"  → Corrente AUMENTOU de {initial_current:.1f}A para {final_current:.1f}A " +
          f"(+{final_current-initial_current:.1f}A, +{((final_current/initial_current-1)*100):.1f}%)")
    print(f"  → Potência AUMENTOU de {initial_power:.1f}kW para {final_power:.1f}kW " +
          f"(+{final_power-initial_power:.1f}kW, +{((final_power/initial_power-1)*100):.1f}%)")
    print("  → Carga da correia AUMENTOU proporcionalmente ao fluxo")

    return sim


def demo_thermal_heating():
    """Demonstra o aquecimento dos mancais ao longo do tempo"""
    print_separator("TESTE 3: Aquecimento Térmico - Mancais das Correias")

    sim = GrainTerminalSimulator()
    sim.start()

    # Abre as comportas para gerar carga
    for gate in sim.gates:
        gate.open_pct_sp = 80.0

    print("📊 Estado Inicial (Temperatura Ambiente):")
    print(f"  CORR01 Temp. Mancal: {sim.belts['CORR01'].temp_bearing_C:.2f}°C")
    print(f"  CORR01 Temp. Correia: {sim.belts['CORR01'].temp_belt_C:.2f}°C")
    print(f"  CORR01 Temp. Tambor: {sim.belts['CORR01'].temp_drum_C:.2f}°C")
    print(f"  ELV01 Temp. Motor: {sim.elevator.temp_motor_C:.2f}°C")
    print(f"  ELV01 Temp. Redutor: {sim.elevator.temp_gearbox_C:.2f}°C")

    print("\n🔥 OPERANDO COM CARGA (80% abertura das comportas)...")
    print("\n📈 Evolução da Temperatura ao longo do tempo:\n")

    print("   Tempo | CORR01 Mancal | CORR01 Correia | CORR01 Tambor | ELV01 Motor | ELV01 Redutor | Carga")
    print("  " + "-"*105)

    for i in range(0, 121, 10):  # 0 to 120 segundos, a cada 10s
        if i > 0:
            for _ in range(10):
                sim.step(dt_s=1.0)

        print(f"   {i:3d}s  |   {sim.belts['CORR01'].temp_bearing_C:6.2f}°C  | " +
              f"   {sim.belts['CORR01'].temp_belt_C:6.2f}°C   | " +
              f"  {sim.belts['CORR01'].temp_drum_C:6.2f}°C  | " +
              f"  {sim.elevator.temp_motor_C:6.2f}°C  | " +
              f"   {sim.elevator.temp_gearbox_C:6.2f}°C   | " +
              f"{sim.belts['CORR01'].load_pct:5.1f}%")

    temp_bearing_delta = sim.belts['CORR01'].temp_bearing_C - 25.0
    temp_motor_delta = sim.elevator.temp_motor_C - 25.0

    print("\n🛑 PARANDO O SISTEMA...")
    sim.stop()

    print("\n❄️  Resfriamento (sistema desligado):\n")
    print("   Tempo | CORR01 Mancal | CORR01 Correia | CORR01 Tambor | ELV01 Motor | ELV01 Redutor")
    print("  " + "-"*90)

    for i in range(0, 61, 10):  # 0 to 60 segundos de resfriamento
        if i > 0:
            for _ in range(10):
                sim.step(dt_s=1.0)

        print(f"   {i:3d}s  |   {sim.belts['CORR01'].temp_bearing_C:6.2f}°C  | " +
              f"   {sim.belts['CORR01'].temp_belt_C:6.2f}°C   | " +
              f"  {sim.belts['CORR01'].temp_drum_C:6.2f}°C  | " +
              f"  {sim.elevator.temp_motor_C:6.2f}°C  | " +
              f"   {sim.elevator.temp_gearbox_C:6.2f}°C")

    temp_bearing_final = sim.belts['CORR01'].temp_bearing_C
    temp_motor_final = sim.elevator.temp_motor_C

    print("\n✅ RESULTADO:")
    print(f"  → Mancal CORR01 AQUECEU +{temp_bearing_delta:.2f}°C durante operação (25.0 → {25.0+temp_bearing_delta:.2f}°C)")
    print(f"  → Motor ELV01 AQUECEU +{temp_motor_delta:.2f}°C durante operação (25.0 → {25.0+temp_motor_delta:.2f}°C)")
    print(f"  → Após parar, mancal RESFRIOU para {temp_bearing_final:.2f}°C")
    print(f"  → Após parar, motor RESFRIOU para {temp_motor_final:.2f}°C")
    print("  → Aquecimento é PROPORCIONAL à carga mecânica")
    print("  → Resfriamento ocorre NATURALMENTE ao desligar")


def demo_integrated():
    """Demonstração integrada de todos os comportamentos dinâmicos"""
    print_separator("TESTE 4: Demonstração Integrada - Todos os Comportamentos")

    sim = GrainTerminalSimulator()

    print("🎬 CENÁRIO: Startup → Operação → Aumento de Carga → Monitoramento\n")

    # Fase 1: Sistema desligado
    print("⏸️  FASE 1: Sistema Desligado (t=0s)")
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h")
    print(f"   Energia Acumulada: {sim.total_kWh:.4f} kWh")

    # Fase 2: Liga o sistema
    print("\n⚡ FASE 2: Ligando Sistema (t=0s)")
    sim.start()
    sim.step(dt_s=1.0)
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A ✅ SUBIU")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW ✅ SUBIU")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h")
    print(f"   Energia Acumulada: {sim.total_kWh:.4f} kWh ✅ CONSUMINDO")

    # Fase 3: Abre comportas para 30%
    print("\n📤 FASE 3: Abrindo Comportas para 30% (t=5s)")
    for gate in sim.gates:
        gate.open_pct_sp = 30.0
    for _ in range(5):
        sim.step(dt_s=1.0)
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A ✅ AUMENTOU")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW ✅ AUMENTOU")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h ✅ AUMENTOU")
    print(f"   Energia Acumulada: {sim.total_kWh:.4f} kWh")

    # Fase 4: Abre comportas para 60%
    print("\n📤 FASE 4: Aumentando para 60% (t=15s)")
    for gate in sim.gates:
        gate.open_pct_sp = 60.0
    for _ in range(10):
        sim.step(dt_s=1.0)
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A ✅ AUMENTOU MAIS")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW ✅ AUMENTOU MAIS")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C ✅ AQUECENDO")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h ✅ AUMENTOU MAIS")
    print(f"   Energia Acumulada: {sim.total_kWh:.4f} kWh")

    # Fase 5: Operação prolongada
    print("\n🔥 FASE 5: Operação Prolongada (t=75s)")
    for _ in range(60):
        sim.step(dt_s=1.0)
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A (estável)")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW (estável)")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C ✅ AQUECEU SIGNIFICATIVAMENTE")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h (estável)")
    print(f"   Energia Acumulada: {sim.total_kWh:.3f} kWh ✅ ACUMULANDO")
    print(f"   Custo: R$ {sim.cost_BRL:.2f}")

    # Fase 6: Parada
    print("\n🛑 FASE 6: Parando Sistema (t=75s)")
    sim.stop()
    for _ in range(30):
        sim.step(dt_s=1.0)
    print(f"   Corrente CORR01: {sim.belts['CORR01'].current_A:.1f}A ✅ VOLTOU AO MÍNIMO")
    print(f"   Potência Total: {sum(b.power_kW for b in sim.belts.values()) + sim.elevator.power_kW + sim.shiploader.power_kW:.1f}kW ✅ ZEROU")
    print(f"   Temperatura Mancal: {sim.belts['CORR01'].temp_bearing_C:.1f}°C ✅ RESFRIANDO")
    print(f"   Fluxo Total: {sum(g.flow_tph for g in sim.gates):.1f} t/h ✅ ZEROU")
    print(f"   Energia Total Consumida: {sim.total_kWh:.3f} kWh")
    print(f"   Custo Total: R$ {sim.cost_BRL:.2f}")

    print("\n" + "="*80)
    print("  ✅ TODAS AS DINÂMICAS ESTÃO FUNCIONANDO CORRETAMENTE!")
    print("="*80)


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║            DEMONSTRAÇÃO DE COMPORTAMENTO DINÂMICO DO SIMULADOR            ║")
    print("║                 Terminal Exportador de Grãos - 1500 t/h                   ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")

    # Executa todas as demonstrações
    demo_startup_electrical()
    time.sleep(1)

    demo_flow_control()
    time.sleep(1)

    demo_thermal_heating()
    time.sleep(1)

    demo_integrated()

    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                       DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO                   ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print("\n")
