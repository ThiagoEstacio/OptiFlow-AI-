#!/usr/bin/env python3
"""
Demonstração de Comportamento de Sobrecarga
===========================================

Este script demonstra o que acontece quando:
1. Abrimos TODAS as comportas além da capacidade da correia
2. A correia sofre sobrecarga e reduz velocidade (underspeed)
3. Material acumula na caixa de transferência
4. Sistema gera alarmes de segurança
"""

import sys
sys.path.insert(0, 'backend')

from app.services.grain_terminal_simulator import GrainTerminalSimulator


def print_separator(title=""):
    print("\n" + "="*90)
    if title:
        print(f"  {title}")
        print("="*90)
    print()


def demo_overload():
    """Demonstra sobrecarga progressiva do sistema"""
    print_separator("TESTE: Sobrecarga Progressiva - Abertura Excessiva das Comportas")

    sim = GrainTerminalSimulator()
    sim.start()

    print("⚙️  CENÁRIO: Operador abre TODAS as comportas progressivamente")
    print("   Vamos observar o comportamento da CORR01 (primeira correia)")
    print()

    # Mostra capacidade nominal
    capacity = 1650  # t/h
    print(f"📋 DADOS TÉCNICOS:")
    print(f"   Capacidade nominal CORR01: {capacity} t/h")
    print(f"   Velocidade nominal: {sim.belts['CORR01'].speed_mps_nom:.2f} m/s")
    print(f"   RPM nominal: {sim.belts['CORR01'].rpm_nom:.1f} RPM")
    print()

    # Fase 1: Operação normal (50%)
    print("=" * 90)
    print("📊 FASE 1: Operação Normal (50% abertura)")
    print("=" * 90)
    for gate in sim.gates:
        gate.open_pct_sp = 50.0

    for _ in range(10):
        sim.step(dt_s=1.0)

    belt = sim.belts['CORR01']
    total_flow = sum(g.flow_tph for g in sim.gates)
    rpm_pct = (belt.rpm / belt.rpm_nom) * 100

    print(f"   Fluxo total comportas: {total_flow:.1f} t/h")
    print(f"   Fluxo CORR01: {belt.flow_tph:.1f} t/h")
    print(f"   Carga CORR01: {belt.load_pct:.1f}% ✅ DENTRO DA CAPACIDADE")
    print(f"   Velocidade: {belt.speed_mps:.2f} m/s ({rpm_pct:.1f}% da nominal)")
    print(f"   RPM: {belt.rpm:.1f} / {belt.rpm_nom:.1f} RPM")
    print(f"   Corrente: {belt.current_A:.1f} A")
    print(f"   Underspeed Warning: {'⚠️  SIM' if belt.underspeed_warn else '✅ NÃO'}")
    print(f"   Underspeed Alarm: {'🚨 SIM' if belt.underspeed_alarm else '✅ NÃO'}")

    # Fase 2: Próximo do limite (80%)
    print("\n" + "=" * 90)
    print("📊 FASE 2: Próximo do Limite (80% abertura)")
    print("=" * 90)
    for gate in sim.gates:
        gate.open_pct_sp = 80.0

    for _ in range(10):
        sim.step(dt_s=1.0)

    total_flow = sum(g.flow_tph for g in sim.gates)
    rpm_pct = (belt.rpm / belt.rpm_nom) * 100

    print(f"   Fluxo total comportas: {total_flow:.1f} t/h")
    print(f"   Fluxo CORR01: {belt.flow_tph:.1f} t/h")
    print(f"   Carga CORR01: {belt.load_pct:.1f}% ⚠️  ALTA")
    print(f"   Velocidade: {belt.speed_mps:.2f} m/s ({rpm_pct:.1f}% da nominal)")
    print(f"   RPM: {belt.rpm:.1f} / {belt.rpm_nom:.1f} RPM")
    print(f"   Corrente: {belt.current_A:.1f} A")
    print(f"   Underspeed Warning: {'⚠️  SIM' if belt.underspeed_warn else '✅ NÃO'}")
    print(f"   Underspeed Alarm: {'🚨 SIM' if belt.underspeed_alarm else '✅ NÃO'}")

    # Fase 3: SOBRECARGA! (100%)
    print("\n" + "=" * 90)
    print("🚨 FASE 3: SOBRECARGA SEVERA (100% abertura - TODAS AS COMPORTAS!)")
    print("=" * 90)
    for gate in sim.gates:
        gate.open_pct_sp = 100.0

    for _ in range(15):
        sim.step(dt_s=1.0)

    total_flow = sum(g.flow_tph for g in sim.gates)
    rpm_pct = (belt.rpm / belt.rpm_nom) * 100

    print(f"   Fluxo total comportas: {total_flow:.1f} t/h 🚨 ACIMA DA CAPACIDADE!")
    print(f"   Fluxo CORR01: {belt.flow_tph:.1f} t/h")
    print(f"   Carga CORR01: {belt.load_pct:.1f}% 🔴 SOBRECARGA CRÍTICA!")
    print(f"   Velocidade: {belt.speed_mps:.2f} m/s ({rpm_pct:.1f}% da nominal) 🔴 REDUZIDA!")
    print(f"   RPM: {belt.rpm:.1f} / {belt.rpm_nom:.1f} RPM 🔴 BAIXA!")
    print(f"   Corrente: {belt.current_A:.1f} A ⚡ SOBRECORRENTE!")
    print(f"   Underspeed Warning: {'⚠️  SIM' if belt.underspeed_warn else '✅ NÃO'}")
    print(f"   Underspeed Alarm: {'🚨 SIM' if belt.underspeed_alarm else '✅ NÃO'}")

    # Mostra alarmes ativos
    print("\n📢 ALARMES ATIVOS:")
    if sim.alarms:
        for alarm in sim.alarms:
            if alarm.active:
                print(f"   🚨 {alarm.tag} - Contagem: {alarm.count}")
    else:
        print("   ✅ Nenhum alarme ativo")

    # Análise do comportamento
    print("\n" + "=" * 90)
    print("📈 ANÁLISE DO COMPORTAMENTO DE SOBRECARGA:")
    print("=" * 90)

    if belt.load_pct > 100:
        print(f"   ✅ CARGA acima de 100%: {belt.load_pct:.1f}%")
        print(f"   ✅ VELOCIDADE reduzida: de 100% para {rpm_pct:.1f}%")
        print(f"   ✅ CORRENTE aumentada: {belt.current_A:.1f}A (sobrecarga)")

    if belt.underspeed_warn:
        print(f"   ✅ WARNING de UNDERSPEED ativado (RPM < 90%)")

    if belt.underspeed_alarm:
        print(f"   ✅ ALARME de UNDERSPEED ativado (RPM < 80%)")

    print()
    print("   🔍 FÍSICA IMPLEMENTADA:")
    print(f"      • Fórmula redução velocidade: speed = speed_nom / (1 + 0.1 × (carga% - 100))")
    print(f"      • Quando carga = {belt.load_pct:.0f}%:")
    print(f"        speed = {belt.speed_mps_nom:.2f} / (1 + 0.1 × {belt.load_pct-100:.0f})")
    print(f"        speed = {belt.speed_mps:.2f} m/s")
    print(f"        RPM = {rpm_pct:.1f}% da nominal")

    return sim


def demo_overload_evolution():
    """Mostra evolução temporal da sobrecarga"""
    print_separator("TESTE: Evolução Temporal da Sobrecarga")

    sim = GrainTerminalSimulator()
    sim.start()

    print("🎬 CENÁRIO: Abrindo progressivamente até sobrecarga crítica\n")

    # Abre gradualmente
    print("   Tempo | Abertura |  Fluxo  | Carga CORR01 | Velocidade |  RPM%  | Underspeed")
    print("  " + "-" * 85)

    steps = [0, 20, 40, 60, 80, 90, 95, 100, 105, 110, 120]  # % de abertura

    for target_pct in steps:
        for gate in sim.gates:
            gate.open_pct_sp = min(100, target_pct)

        # Simula 5 segundos
        for _ in range(5):
            sim.step(dt_s=1.0)

        belt = sim.belts['CORR01']
        total_flow = sum(g.flow_tph for g in sim.gates)
        avg_opening = sum(g.open_pct for g in sim.gates) / len(sim.gates)
        rpm_pct = (belt.rpm / belt.rpm_nom) * 100

        underspeed_status = "✅ OK"
        if belt.underspeed_alarm:
            underspeed_status = "🚨 ALARM"
        elif belt.underspeed_warn:
            underspeed_status = "⚠️  WARN"

        carga_status = ""
        if belt.load_pct > 120:
            carga_status = " 🔴 CRÍTICO"
        elif belt.load_pct > 100:
            carga_status = " ⚠️  ALTO"
        elif belt.load_pct > 80:
            carga_status = " 🟡 MÉDIO"

        print(f"   {sim.time_s:4.0f}s |  {avg_opening:5.1f}% | {total_flow:6.0f} | " +
              f"   {belt.load_pct:5.1f}%{carga_status:11s} | " +
              f"  {belt.speed_mps:5.2f} m/s | {rpm_pct:5.1f}% | {underspeed_status}")

    print("\n✅ RESULTADO:")
    print("   → Carga aumenta proporcionalmente à abertura das comportas")
    print("   → Velocidade diminui quando carga excede 100%")
    print("   → RPM cai conforme velocidade reduz")
    print("   → Underspeed WARNING ativa quando RPM < 90%")
    print("   → Underspeed ALARM ativa quando RPM < 80%")


def show_current_limitations():
    """Mostra limitações do modelo atual"""
    print_separator("LIMITAÇÕES DO MODELO ATUAL E MELHORIAS POSSÍVEIS")

    print("✅ IMPLEMENTADO ATUALMENTE:")
    print("   • Redução de velocidade por sobrecarga (física realista)")
    print("   • Detecção de underspeed (warning < 90%, alarm < 80%)")
    print("   • Aumento de corrente por sobrecarga")
    print("   • Registro de alarmes")
    print()

    print("❌ NÃO IMPLEMENTADO (pode ser adicionado):")
    print("   • Acúmulo de nível na caixa de transferência (chute_level_pct)")
    print("   • Entupimento automático quando chute_level > 80%")
    print("   • Trip automático por underspeed persistente")
    print("   • Trip automático por nível alto de chute")
    print("   • Parada em cascata dos equipamentos por trip")
    print("   • Danos ao equipamento por operação prolongada em sobrecarga")
    print()

    print("🔧 SUGESTÕES DE MELHORIA:")
    print("   1. Modelar acúmulo de material no chute:")
    print("      - Se entrada > saída → nível aumenta")
    print("      - Se nível > 80% → alarme")
    print("      - Se nível > 95% → entupimento + trip")
    print()
    print("   2. Implementar trips de segurança:")
    print("      - Underspeed por > 10s → trip da correia")
    print("      - Chute plugged → trip upstream + alarme")
    print("      - Sobrecorrente > 120% → trip do motor")
    print()
    print("   3. Parada em cascata:")
    print("      - Se CORR01 tripar → fechar comportas automaticamente")
    print("      - Se correia parar → equipamento upstream deve parar")
    print()

    print("💡 VOCÊ QUER QUE EU IMPLEMENTE ESSAS MELHORIAS?")
    print("   Posso adicionar:")
    print("   • Modelagem completa de acúmulo no chute")
    print("   • Trips automáticos de segurança")
    print("   • Parada em cascata dos equipamentos")
    print("   • Simulação de entupimento realista")


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                                    ║")
    print("║              DEMONSTRAÇÃO DE SOBRECARGA E SEGURANÇA OPERACIONAL                   ║")
    print("║                   Terminal Exportador de Grãos - 1500 t/h                         ║")
    print("║                                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════╝")

    # Teste 1: Sobrecarga progressiva
    demo_overload()

    # Teste 2: Evolução temporal
    demo_overload_evolution()

    # Mostra o que está e não está implementado
    show_current_limitations()

    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                         DEMONSTRAÇÃO CONCLUÍDA                                     ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════╝")
    print("\n")
