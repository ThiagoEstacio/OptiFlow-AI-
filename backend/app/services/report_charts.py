"""
Report Charts Service - Geração de gráficos profissionais para relatórios PDF

Gera gráficos estilo dashboard usando matplotlib:
- Gráfico de Pareto (barras + linha acumulada)
- Gráfico de tendência OEE
- Gráfico de consumo energético
- Gauges para KPIs
- Gráficos de pizza para distribuição
"""
import io
import matplotlib
matplotlib.use('Agg')  # Backend sem interface gráfica
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Wedge
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Cores do tema OptiFlow (Material Design)
COLORS = {
    'primary': '#1976d2',
    'secondary': '#dc004e',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'info': '#2196f3',
    'grey': '#9e9e9e',
    'dark': '#212121',
    'light': '#fafafa',
    'purple': '#9c27b0',
    'cyan': '#00bcd4',
    'orange': '#ff5722',
}

# Paleta de cores para gráficos
CHART_PALETTE = [
    '#1976d2', '#4caf50', '#ff9800', '#f44336', '#9c27b0',
    '#00bcd4', '#ff5722', '#795548', '#607d8b', '#e91e63'
]


def set_chart_style():
    """Configura estilo profissional para os gráficos"""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 14,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.axisbelow': True,
    })


def create_pareto_chart(pareto_data: Dict) -> bytes:
    """
    Cria gráfico de Pareto profissional (barras + linha acumulada)
    Similar ao dashboard frontend
    """
    set_chart_style()

    fig, ax1 = plt.subplots(figsize=(10, 5), dpi=150)

    # Dados
    items = pareto_data.get('pareto', [])[:10]  # Top 10
    if not items:
        # Gráfico vazio
        ax1.text(0.5, 0.5, 'Sem dados de alarmes', ha='center', va='center',
                transform=ax1.transAxes, fontsize=14, color='gray')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()

    labels = [item['alarm_type'][:20] + '...' if len(item['alarm_type']) > 20
              else item['alarm_type'] for item in items]
    counts = [item['count'] for item in items]
    cumulative = [item['cumulative_percent'] for item in items]
    is_80 = [item.get('is_80_percent', False) for item in items]

    # Cores das barras (destacar os que causam 80%)
    bar_colors = [COLORS['primary'] if is80 else COLORS['info'] for is80 in is_80]

    # Gráfico de barras
    x = np.arange(len(labels))
    bars = ax1.bar(x, counts, color=bar_colors, alpha=0.8, edgecolor='white', linewidth=1)

    # Configurar eixo Y esquerdo
    ax1.set_xlabel('Tipo de Alarme', fontweight='bold')
    ax1.set_ylabel('Quantidade de Ocorrências', color=COLORS['primary'], fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=COLORS['primary'])
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)

    # Eixo Y direito para % acumulado
    ax2 = ax1.twinx()
    ax2.plot(x, cumulative, color=COLORS['error'], marker='o', linewidth=2.5,
             markersize=6, markerfacecolor='white', markeredgewidth=2)
    ax2.set_ylabel('% Acumulado', color=COLORS['error'], fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=COLORS['error'])
    ax2.set_ylim(0, 105)

    # Linha de 80%
    ax2.axhline(y=80, color=COLORS['warning'], linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.text(len(x)-1, 82, '80%', color=COLORS['warning'], fontsize=9, fontweight='bold')

    # Valores nas barras
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax1.annotate(f'{count:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Título
    total = pareto_data.get('summary', {}).get('total_alarms', sum(counts))
    ax1.set_title(f'Análise de Pareto - Top 10 Alarmes (Total: {total:,})',
                  fontsize=14, fontweight='bold', color=COLORS['dark'], pad=15)

    # Legenda
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['primary'], label='Causam 80% dos problemas'),
        mpatches.Patch(facecolor=COLORS['info'], label='Outros alarmes'),
        plt.Line2D([0], [0], color=COLORS['error'], marker='o', label='% Acumulado',
                   markerfacecolor='white', markersize=6),
    ]
    ax1.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.25),
               ncol=3, frameon=True, fancybox=True, shadow=True)

    plt.tight_layout()

    # Salvar em buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white', edgecolor='none')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_oee_trend_chart(trend_data: Dict) -> bytes:
    """
    Cria gráfico de tendência OEE com área preenchida
    Similar ao dashboard frontend
    """
    set_chart_style()

    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

    data_points = trend_data.get('data', [])
    if not data_points:
        ax.text(0.5, 0.5, 'Sem dados de tendência', ha='center', va='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()

    # Preparar dados
    timestamps = [datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00'))
                  if isinstance(d['timestamp'], str) else d['timestamp']
                  for d in data_points]
    values = [d['value'] for d in data_points]
    targets = [d.get('target', 85) for d in data_points]

    # Plotar área
    ax.fill_between(timestamps, values, alpha=0.3, color=COLORS['primary'])
    ax.plot(timestamps, values, color=COLORS['primary'], linewidth=2.5,
            marker='o', markersize=4, label='OEE Real')

    # Linha de meta
    ax.plot(timestamps, targets, color=COLORS['success'], linewidth=2,
            linestyle='--', label='Meta')

    # Configurações
    ax.set_xlabel('Data/Hora', fontweight='bold')
    ax.set_ylabel('OEE (%)', fontweight='bold')
    ax.set_ylim(0, 100)

    # Formatar eixo X
    fig.autofmt_xdate()

    # Título e resumo
    summary = trend_data.get('summary', {})
    current = summary.get('current', values[-1] if values else 0)
    avg = summary.get('average', np.mean(values) if values else 0)

    ax.set_title(f'Tendência de OEE - Atual: {current:.1f}% | Média: {avg:.1f}%',
                 fontsize=14, fontweight='bold', color=COLORS['dark'], pad=15)

    # Legenda
    ax.legend(loc='upper left', frameon=True, fancybox=True)

    # Grid
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_energy_chart(energy_data: Dict) -> bytes:
    """
    Cria gráfico de consumo energético com barras agrupadas
    """
    set_chart_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), dpi=150)

    history = energy_data.get('history', [])

    # Gráfico 1: Consumo por hora
    if history:
        hours = [datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')).strftime('%H:%M')
                 for h in history[-24:]]  # Últimas 24h
        consumption = [h['consumption_kwh'] for h in history[-24:]]
        is_peak = [h.get('is_peak_hour', False) for h in history[-24:]]

        colors_bars = [COLORS['error'] if peak else COLORS['primary'] for peak in is_peak]

        bars = ax1.bar(range(len(hours)), consumption, color=colors_bars, alpha=0.8)
        ax1.set_xticks(range(0, len(hours), 3))
        ax1.set_xticklabels([hours[i] for i in range(0, len(hours), 3)], rotation=45, ha='right')
        ax1.set_xlabel('Hora', fontweight='bold')
        ax1.set_ylabel('Consumo (kWh)', fontweight='bold')
        ax1.set_title('Consumo por Hora (24h)', fontweight='bold', color=COLORS['dark'])

        # Legenda
        legend_elements = [
            mpatches.Patch(facecolor=COLORS['error'], label='Horário de Ponta'),
            mpatches.Patch(facecolor=COLORS['primary'], label='Fora de Ponta'),
        ]
        ax1.legend(handles=legend_elements, loc='upper right', fontsize=8)
    else:
        ax1.text(0.5, 0.5, 'Sem histórico', ha='center', va='center',
                transform=ax1.transAxes, fontsize=12, color='gray')

    # Gráfico 2: Composição da conta
    bill = energy_data.get('bill_forecast', {})
    if bill:
        labels = ['Energia', 'Demanda', 'Impostos']
        values = [
            bill.get('energy_cost', 0),
            bill.get('demand_cost', 0),
            bill.get('taxes', 0)
        ]
        colors_pie = [COLORS['primary'], COLORS['warning'], COLORS['error']]

        wedges, texts, autotexts = ax2.pie(values, labels=labels, colors=colors_pie,
                                            autopct='%1.1f%%', startangle=90,
                                            explode=(0.02, 0.02, 0.02))
        ax2.set_title(f'Composição da Conta\nTotal: R$ {bill.get("total_estimate", 0):,.2f}',
                     fontweight='bold', color=COLORS['dark'])

        # Estilizar textos
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
    else:
        ax2.text(0.5, 0.5, 'Sem previsão', ha='center', va='center',
                transform=ax2.transAxes, fontsize=12, color='gray')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_kpi_gauges(kpis: Dict) -> bytes:
    """
    Cria gauges visuais para os 4 KPIs principais (OEE, Disponibilidade, Performance, Qualidade)
    """
    set_chart_style()

    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), dpi=150)

    kpi_list = [
        ('OEE', kpis.get('oee', {}), COLORS['primary']),
        ('Disponibilidade', kpis.get('availability', {}), COLORS['success']),
        ('Performance', kpis.get('performance', {}), COLORS['warning']),
        ('Qualidade', kpis.get('quality', {}), COLORS['info']),
    ]

    for ax, (name, kpi, color) in zip(axes, kpi_list):
        value = kpi.get('value', 0)
        target = kpi.get('target', 85)
        status = kpi.get('status', 'good')

        # Determinar cor baseada no status
        if status == 'good':
            gauge_color = COLORS['success']
        elif status == 'warning':
            gauge_color = COLORS['warning']
        else:
            gauge_color = COLORS['error']

        # Criar gauge semicircular
        theta1, theta2 = 180, 180 - (180 * min(value, 100) / 100)

        # Fundo do gauge
        wedge_bg = Wedge((0.5, 0), 0.4, 0, 180, width=0.15,
                         facecolor='#e0e0e0', edgecolor='white', linewidth=2,
                         transform=ax.transAxes)
        ax.add_patch(wedge_bg)

        # Valor do gauge
        wedge_value = Wedge((0.5, 0), 0.4, theta2, 180, width=0.15,
                            facecolor=gauge_color, edgecolor='white', linewidth=2,
                            transform=ax.transAxes)
        ax.add_patch(wedge_value)

        # Linha de meta
        meta_angle = 180 - (180 * min(target, 100) / 100)
        meta_rad = np.radians(meta_angle)
        x_meta = 0.5 + 0.32 * np.cos(meta_rad)
        y_meta = 0.32 * np.sin(meta_rad)
        ax.plot([0.5, x_meta], [0, y_meta], color=COLORS['dark'],
                linewidth=2, linestyle='--', transform=ax.transAxes)

        # Texto do valor
        ax.text(0.5, 0.15, f'{value:.1f}%', ha='center', va='center',
                fontsize=20, fontweight='bold', color=gauge_color,
                transform=ax.transAxes)

        # Nome do KPI
        ax.text(0.5, -0.1, name, ha='center', va='center',
                fontsize=11, fontweight='bold', color=COLORS['dark'],
                transform=ax.transAxes)

        # Meta
        ax.text(0.5, -0.25, f'Meta: {target}%', ha='center', va='center',
                fontsize=9, color=COLORS['grey'], transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.3, 0.5)
        ax.set_aspect('equal')
        ax.axis('off')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_production_chart(production_data: Dict) -> bytes:
    """
    Cria gráfico de produção com throughput e utilização
    """
    set_chart_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), dpi=150)

    history = production_data.get('history', [])

    # Gráfico 1: Throughput por hora
    if history:
        hours = [datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')).strftime('%H:%M')
                 for h in history[-24:]]
        throughput = [h['throughput_ton_hour'] for h in history[-24:]]
        utilization = [h['utilization_percent'] for h in history[-24:]]

        ax1.plot(range(len(hours)), throughput, color=COLORS['primary'],
                linewidth=2.5, marker='o', markersize=4, label='Throughput')
        ax1.fill_between(range(len(hours)), throughput, alpha=0.2, color=COLORS['primary'])

        # Linha de capacidade nominal
        nominal = production_data.get('capacity', {}).get('nominal_ton_hour', 150)
        ax1.axhline(y=nominal, color=COLORS['success'], linestyle='--',
                   linewidth=1.5, label=f'Capacidade: {nominal} ton/h')

        ax1.set_xticks(range(0, len(hours), 3))
        ax1.set_xticklabels([hours[i] for i in range(0, len(hours), 3)], rotation=45, ha='right')
        ax1.set_xlabel('Hora', fontweight='bold')
        ax1.set_ylabel('Throughput (ton/h)', fontweight='bold')
        ax1.set_title('Throughput por Hora', fontweight='bold', color=COLORS['dark'])
        ax1.legend(loc='upper right', fontsize=8)
    else:
        ax1.text(0.5, 0.5, 'Sem histórico', ha='center', va='center',
                transform=ax1.transAxes, fontsize=12, color='gray')

    # Gráfico 2: Atingimento de meta
    target_data = production_data.get('target', {})
    if target_data:
        achievement = target_data.get('achievement_percent', 0)
        gap = target_data.get('gap_tons', 0)

        # Gráfico de barras horizontal
        categories = ['Produzido', 'Meta']
        produced = target_data.get('production_target_tons', 0) - gap if gap > 0 else target_data.get('production_target_tons', 0) + abs(gap)
        target_val = target_data.get('production_target_tons', 0)

        values = [produced, target_val]
        colors_bar = [COLORS['primary'], COLORS['grey']]

        bars = ax2.barh(categories, values, color=colors_bar, height=0.5, edgecolor='white')

        # Adicionar valores
        for bar, val in zip(bars, values):
            ax2.text(val + 50, bar.get_y() + bar.get_height()/2,
                    f'{val:,.0f} ton', va='center', fontsize=10, fontweight='bold')

        ax2.set_xlabel('Toneladas', fontweight='bold')
        ax2.set_title(f'Atingimento de Meta: {achievement:.1f}%',
                     fontweight='bold', color=COLORS['dark'])

        # Cor do título baseada no status
        status = target_data.get('status', 'warning')
        if status == 'good':
            title_color = COLORS['success']
        elif status == 'warning':
            title_color = COLORS['warning']
        else:
            title_color = COLORS['error']
        ax2.title.set_color(title_color)
    else:
        ax2.text(0.5, 0.5, 'Sem dados de meta', ha='center', va='center',
                transform=ax2.transAxes, fontsize=12, color='gray')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_maintenance_health_chart(maintenance_data: Dict) -> bytes:
    """
    Cria gráfico de saúde dos equipamentos (barras horizontais com cores)
    """
    set_chart_style()

    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

    equipment = maintenance_data.get('equipment_health', [])

    if not equipment:
        ax.text(0.5, 0.5, 'Sem dados de equipamentos', ha='center', va='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()

    # Ordenar por health score
    equipment = sorted(equipment, key=lambda x: x['health_score'])

    names = [eq['equipment_name'] for eq in equipment]
    scores = [eq['health_score'] for eq in equipment]

    # Cores baseadas no score
    colors_bar = []
    for score in scores:
        if score >= 80:
            colors_bar.append(COLORS['success'])
        elif score >= 60:
            colors_bar.append(COLORS['warning'])
        else:
            colors_bar.append(COLORS['error'])

    # Barras horizontais
    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, scores, color=colors_bar, height=0.6, edgecolor='white')

    # Configurar eixos
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel('Health Score (%)', fontweight='bold')
    ax.set_xlim(0, 105)

    # Adicionar valores
    for bar, score in zip(bars, scores):
        ax.text(score + 2, bar.get_y() + bar.get_height()/2,
                f'{score}%', va='center', fontsize=9, fontweight='bold')

    # Linhas de referência
    ax.axvline(x=80, color=COLORS['success'], linestyle='--', linewidth=1, alpha=0.7)
    ax.axvline(x=60, color=COLORS['warning'], linestyle='--', linewidth=1, alpha=0.7)

    # Título
    avg_health = maintenance_data.get('summary', {}).get('average_health_score', np.mean(scores))
    at_risk = maintenance_data.get('summary', {}).get('at_risk_count', 0)
    ax.set_title(f'Saúde dos Equipamentos - Média: {avg_health:.0f}% | Em Risco: {at_risk}',
                fontweight='bold', color=COLORS['dark'], pad=15)

    # Legenda
    legend_elements = [
        mpatches.Patch(facecolor=COLORS['success'], label='Bom (≥80%)'),
        mpatches.Patch(facecolor=COLORS['warning'], label='Atenção (60-79%)'),
        mpatches.Patch(facecolor=COLORS['error'], label='Crítico (<60%)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=8)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()


def create_alarms_distribution_chart(alarms_data: Dict) -> bytes:
    """
    Cria gráfico de distribuição de alarmes por severidade
    """
    set_chart_style()

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

    by_severity = alarms_data.get('by_severity', {})

    if not by_severity:
        ax.text(0.5, 0.5, 'Sem dados de alarmes', ha='center', va='center',
                transform=ax.transAxes, fontsize=14, color='gray')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()

    labels = ['Crítico', 'Alto', 'Médio', 'Baixo']
    values = [
        by_severity.get('critical', 0),
        by_severity.get('high', 0),
        by_severity.get('medium', 0),
        by_severity.get('low', 0)
    ]
    colors_pie = [COLORS['error'], COLORS['warning'], COLORS['info'], COLORS['success']]

    # Filtrar zeros
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors_pie) if v > 0]
    if not filtered:
        ax.text(0.5, 0.5, 'Nenhum alarme ativo', ha='center', va='center',
                transform=ax.transAxes, fontsize=14, color='gray')
    else:
        labels, values, colors_pie = zip(*filtered)

        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors_pie,
                                           autopct='%1.0f%%', startangle=90,
                                           explode=[0.02]*len(values),
                                           shadow=True)

        for autotext in autotexts:
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
            autotext.set_color('white')

    total = alarms_data.get('total_active', sum(values))
    ax.set_title(f'Distribuição de Alarmes por Severidade\nTotal: {total}',
                fontweight='bold', color=COLORS['dark'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf.getvalue()
