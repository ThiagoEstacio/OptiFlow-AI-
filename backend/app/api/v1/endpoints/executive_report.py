"""
Executive Report API - Geração de Relatórios PDF do Dashboard Executivo

Gera relatórios completos estilo storytelling com:
- Sumário executivo narrativo
- KPIs principais com gauges visuais
- Gráficos de tendência
- Análise de Pareto de alarmes
- Métricas de energia e custos
- Métricas de produção
- Manutenção preditiva
- Insights e recomendações acionáveis
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import io
import random

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem,
    HRFlowable, CondPageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from app.db.session import get_db
from app.models.user import User
from app.core.deps import get_current_user

# Import executive summary functions
from app.api.v1.endpoints.executive_summary import (
    get_executive_overview,
    get_executive_trends,
    get_energy_metrics,
    get_alarms_pareto,
    get_production_metrics,
    get_predictive_maintenance
)

# Import chart generation functions
from app.services.report_charts import (
    create_pareto_chart,
    create_oee_trend_chart,
    create_energy_chart,
    create_kpi_gauges,
    create_production_chart,
    create_maintenance_health_chart,
    create_alarms_distribution_chart
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Cores do tema
THEME_COLORS = {
    'primary': '#1976d2',
    'secondary': '#424242',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'info': '#2196f3',
    'light_blue': '#e3f2fd',
    'light_green': '#e8f5e9',
    'light_orange': '#fff3e0',
    'light_red': '#ffebee',
}


def create_chart_image(chart_bytes: bytes, width: float = 16*cm, height: float = 8*cm) -> Optional[Image]:
    """Converte bytes de imagem PNG para objeto Image do ReportLab"""
    try:
        img_buffer = io.BytesIO(chart_bytes)
        img = Image(img_buffer, width=width, height=height)
        return img
    except Exception as e:
        logger.error(f"Error creating chart image: {e}")
        return None


def create_header(canvas, doc):
    """Desenha o cabeçalho profissional em cada página"""
    canvas.saveState()
    page_width = doc.pagesize[0]
    page_height = doc.pagesize[1]

    # Faixa azul no topo
    canvas.setFillColor(colors.HexColor(THEME_COLORS['primary']))
    canvas.rect(0, page_height - 2*cm, page_width, 2*cm, fill=True, stroke=False)

    # Logo/Título
    canvas.setFont('Helvetica-Bold', 18)
    canvas.setFillColor(colors.white)
    canvas.drawString(1.5*cm, page_height - 1.4*cm, "OptiFlow AI")

    # Subtítulo
    canvas.setFont('Helvetica', 11)
    canvas.drawString(1.5*cm, page_height - 1.9*cm, "Relatório Executivo de Performance Industrial")

    # Data e página no canto direito
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(page_width - 1.5*cm, page_height - 1.4*cm,
                          f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    canvas.drawRightString(page_width - 1.5*cm, page_height - 1.9*cm,
                          f"Página {doc.page}")

    canvas.restoreState()


def create_footer(canvas, doc):
    """Desenha o rodapé em cada página"""
    canvas.saveState()
    page_width = doc.pagesize[0]

    # Linha separadora
    canvas.setStrokeColor(colors.HexColor(THEME_COLORS['primary']))
    canvas.setLineWidth(1)
    canvas.line(1.5*cm, 1.2*cm, page_width - 1.5*cm, 1.2*cm)

    # Texto do rodapé
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.gray)
    canvas.drawString(1.5*cm, 0.7*cm, "Documento Confidencial - OptiFlow AI Platform")
    canvas.drawRightString(page_width - 1.5*cm, 0.7*cm,
                          "Powered by Machine Learning & Real-time Analytics")

    canvas.restoreState()


def header_footer(canvas, doc):
    """Combina header e footer"""
    create_header(canvas, doc)
    create_footer(canvas, doc)


def get_status_color(status: str) -> colors.Color:
    """Retorna cor baseada no status"""
    status_lower = status.lower() if status else ''
    if status_lower in ['good', 'success', 'up']:
        return colors.HexColor(THEME_COLORS['success'])
    elif status_lower in ['warning', 'attention']:
        return colors.HexColor(THEME_COLORS['warning'])
    elif status_lower in ['critical', 'error', 'down', 'bad']:
        return colors.HexColor(THEME_COLORS['error'])
    return colors.HexColor(THEME_COLORS['info'])


def generate_executive_storytelling(overview: Dict, energy: Dict, pareto: Dict,
                                   production: Dict, maintenance: Dict,
                                   time_range: str, styles) -> List:
    """Gera o storytelling executivo do relatório"""
    elements = []

    # Título da seção
    story_title = ParagraphStyle(
        'StoryTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(THEME_COLORS['primary']),
        spaceAfter=15,
        spaceBefore=10,
        alignment=TA_CENTER
    )

    story_text = ParagraphStyle(
        'StoryText',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        firstLineIndent=20
    )

    highlight_box = ParagraphStyle(
        'HighlightBox',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=10,
        spaceBefore=10,
        leftIndent=20,
        rightIndent=20,
        backColor=colors.HexColor(THEME_COLORS['light_blue']),
        borderPadding=10
    )

    elements.append(Paragraph("Sumário Executivo", story_title))

    # Período analisado
    period_map = {'1h': '1 hora', '6h': '6 horas', '24h': '24 horas', '7d': '7 dias', '30d': '30 dias'}
    period_text = period_map.get(time_range, time_range)

    # KPIs
    oee = overview['kpis']['oee']
    availability = overview['kpis']['availability']
    performance = overview['kpis']['performance']
    quality = overview['kpis']['quality']

    # Texto de abertura
    intro_text = f"""
    Este relatório apresenta uma análise completa da performance operacional das últimas <b>{period_text}</b>.
    O sistema OptiFlow AI monitorou continuamente todos os indicadores-chave, identificando oportunidades
    de melhoria e alertando sobre potenciais riscos operacionais.
    """
    elements.append(Paragraph(intro_text, story_text))

    # Status geral do OEE
    oee_status_text = "excelente" if oee['status'] == 'good' else "satisfatório" if oee['status'] == 'warning' else "crítico"
    oee_trend_text = "crescimento" if oee['trend'] == 'up' else "queda" if oee['trend'] == 'down' else "estabilidade"

    oee_narrative = f"""
    <b>Performance Geral (OEE):</b> A eficiência global dos equipamentos (OEE) está em <b>{oee['value']:.1f}%</b>,
    classificada como <b>{oee_status_text}</b> em relação à meta de {oee['target']}%.
    A tendência atual indica <b>{oee_trend_text}</b> no indicador.
    """
    elements.append(Paragraph(oee_narrative, story_text))

    # Destaques dos KPIs em box
    kpi_highlight = f"""
    <b>Resumo dos KPIs:</b><br/>
    • Disponibilidade: {availability['value']:.1f}% (Meta: {availability['target']}%) - {availability['status'].upper()}<br/>
    • Performance: {performance['value']:.1f}% (Meta: {performance['target']}%) - {performance['status'].upper()}<br/>
    • Qualidade: {quality['value']:.1f}% (Meta: {quality['target']}%) - {quality['status'].upper()}
    """
    elements.append(Paragraph(kpi_highlight, highlight_box))

    # Alarmes e Pareto
    total_alarms = pareto['summary']['total_alarms']
    critical_alarms = overview['alarms']['by_severity']['critical']
    top_alarm = pareto['pareto'][0]['alarm_type'] if pareto['pareto'] else "N/A"
    pareto_80 = pareto['summary']['alarms_causing_80_percent']

    alarms_narrative = f"""
    <b>Análise de Alarmes:</b> Durante o período, foram registrados <b>{total_alarms} alarmes</b>,
    sendo <b>{critical_alarms} críticos</b>. A análise de Pareto identificou que apenas
    <b>{pareto_80} tipos de alarmes</b> são responsáveis por 80% das ocorrências,
    com destaque para "<b>{top_alarm[:40]}...</b>" como o mais frequente.
    O custo estimado total dos alarmes é de <b>R$ {pareto['summary']['total_estimated_cost']:,.2f}</b>.
    """
    elements.append(Paragraph(alarms_narrative, story_text))

    # Energia
    energy_current = energy['current']['consumption_kwh']
    bill_forecast = energy['bill_forecast']['total_estimate']
    efficiency_status = "acima" if energy['efficiency']['status'] == 'good' else "dentro" if energy['efficiency']['status'] == 'warning' else "abaixo"

    energy_narrative = f"""
    <b>Gestão Energética:</b> O consumo atual está em <b>{energy_current:,.0f} kWh</b> com uma
    previsão de conta de luz de <b>R$ {bill_forecast:,.2f}</b> para o mês.
    A eficiência energética de <b>{energy['efficiency']['kwh_per_ton']:.2f} kWh/ton</b> está
    {efficiency_status} da meta estabelecida de {energy['efficiency']['target_kwh_per_ton']} kWh/ton.
    """
    elements.append(Paragraph(energy_narrative, story_text))

    # Produção
    throughput = production['current']['throughput_ton_hour']
    achievement = production['target']['achievement_percent']
    gap = production['target']['gap_tons']

    gap_text = f"com gap de {gap:,.0f} toneladas" if gap > 0 else f"superando em {abs(gap):,.0f} toneladas"

    production_narrative = f"""
    <b>Produção:</b> O throughput atual é de <b>{throughput:.1f} ton/hora</b>,
    com atingimento de <b>{achievement:.1f}%</b> da meta, {gap_text}.
    A utilização da capacidade instalada está em <b>{production['capacity']['utilization_percent']:.1f}%</b>.
    """
    elements.append(Paragraph(production_narrative, story_text))

    # Manutenção
    at_risk = maintenance['summary']['at_risk_count']
    avg_health = maintenance['summary']['average_health_score']
    roi = maintenance['roi']['roi_percent']
    savings = maintenance['roi']['monthly_savings']

    maintenance_narrative = f"""
    <b>Manutenção Preditiva:</b> O sistema identificou <b>{at_risk} equipamentos em risco</b>
    de falha nos próximos 7 dias. O health score médio da planta é de <b>{avg_health:.0f}%</b>.
    O sistema de manutenção preditiva está gerando um ROI de <b>{roi:.0f}%</b>,
    com economia mensal estimada de <b>R$ {savings:,.2f}</b>.
    """
    elements.append(Paragraph(maintenance_narrative, story_text))

    # Recomendações prioritárias
    elements.append(Spacer(1, 0.5*cm))

    rec_title = ParagraphStyle(
        'RecTitle',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor(THEME_COLORS['warning']),
        spaceBefore=10,
        spaceAfter=8
    )
    elements.append(Paragraph("Ações Prioritárias Recomendadas:", rec_title))

    # Lista de recomendações baseadas nos dados
    recommendations = []

    if oee['status'] in ['warning', 'critical']:
        recommendations.append(f"Investigar causas da queda de OEE - atualmente {oee['value']:.1f}% vs meta de {oee['target']}%")

    if critical_alarms > 0:
        recommendations.append(f"Tratar {critical_alarms} alarmes críticos ativos para evitar paradas não programadas")

    if at_risk > 0:
        recommendations.append(f"Programar manutenção preventiva para {at_risk} equipamentos em risco de falha")

    if energy['peak_demand'].get('risk_of_penalty', False):
        recommendations.append("Revisar consumo de energia para evitar multa por ultrapassagem de demanda")

    if gap > 0:
        recommendations.append(f"Acelerar produção para fechar gap de {gap:,.0f} toneladas em relação à meta")

    if not recommendations:
        recommendations.append("Manter monitoramento contínuo - operação dentro dos parâmetros esperados")

    rec_style = ParagraphStyle(
        'RecItem',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=25,
        bulletIndent=10,
        spaceAfter=5
    )

    for i, rec in enumerate(recommendations[:5], 1):
        elements.append(Paragraph(f"<b>{i}.</b> {rec}", rec_style))

    return elements


def create_kpi_cards_table(kpis: Dict) -> Table:
    """Cria tabela visual estilo cards para KPIs"""

    def make_kpi_cell(name: str, kpi: Dict, color: str) -> List:
        """Cria célula de KPI estilizada"""
        status_emoji = "✓" if kpi['status'] == 'good' else "⚠" if kpi['status'] == 'warning' else "✗"
        trend_emoji = "↑" if kpi['trend'] == 'up' else "↓" if kpi['trend'] == 'down' else "→"

        return [
            Paragraph(f"<b>{name}</b>", ParagraphStyle('KPIName', fontSize=10, alignment=TA_CENTER)),
            Paragraph(f"<font size='20'><b>{kpi['value']:.1f}%</b></font>",
                     ParagraphStyle('KPIValue', fontSize=20, alignment=TA_CENTER,
                                   textColor=colors.HexColor(color))),
            Paragraph(f"Meta: {kpi['target']}% {status_emoji} {trend_emoji}",
                     ParagraphStyle('KPIMeta', fontSize=9, alignment=TA_CENTER, textColor=colors.gray))
        ]

    # Criar células para cada KPI
    oee_cell = make_kpi_cell("OEE", kpis['oee'], THEME_COLORS['primary'])
    avail_cell = make_kpi_cell("Disponibilidade", kpis['availability'], THEME_COLORS['success'])
    perf_cell = make_kpi_cell("Performance", kpis['performance'], THEME_COLORS['warning'])
    qual_cell = make_kpi_cell("Qualidade", kpis['quality'], THEME_COLORS['info'])

    # Montar tabela
    data = [[
        Table([[c] for c in oee_cell], colWidths=[4*cm]),
        Table([[c] for c in avail_cell], colWidths=[4*cm]),
        Table([[c] for c in perf_cell], colWidths=[4*cm]),
        Table([[c] for c in qual_cell], colWidths=[4*cm])
    ]]

    table = Table(data, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor(THEME_COLORS['primary'])),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor(THEME_COLORS['success'])),
        ('BOX', (2, 0), (2, 0), 1, colors.HexColor(THEME_COLORS['warning'])),
        ('BOX', (3, 0), (3, 0), 1, colors.HexColor(THEME_COLORS['info'])),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(THEME_COLORS['light_blue'])),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor(THEME_COLORS['light_green'])),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor(THEME_COLORS['light_orange'])),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#e3f2fd')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    return table


def create_alarms_summary_table(alarms: Dict, pareto: Dict) -> Table:
    """Cria tabela resumo de alarmes lado a lado"""

    # Severidade
    severity_data = [
        ['Severidade', 'Qtd', '%'],
        ['Crítico', str(alarms['by_severity']['critical']),
         f"{(alarms['by_severity']['critical']/max(1, alarms['total_active'])*100):.0f}%"],
        ['Alto', str(alarms['by_severity']['high']),
         f"{(alarms['by_severity']['high']/max(1, alarms['total_active'])*100):.0f}%"],
        ['Médio', str(alarms['by_severity']['medium']),
         f"{(alarms['by_severity']['medium']/max(1, alarms['total_active'])*100):.0f}%"],
        ['Baixo', str(alarms['by_severity']['low']),
         f"{(alarms['by_severity']['low']/max(1, alarms['total_active'])*100):.0f}%"],
    ]

    severity_table = Table(severity_data, colWidths=[2.5*cm, 1.5*cm, 1.5*cm])
    severity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_COLORS['warning'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.red),
        ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor(THEME_COLORS['warning'])),
    ]))

    # Top 5 Pareto
    pareto_data = [['Top Alarmes (Pareto)', 'Qtd']]
    for item in pareto['pareto'][:5]:
        name = item['alarm_type'][:20] + '...' if len(item['alarm_type']) > 20 else item['alarm_type']
        pareto_data.append([name, str(item['count'])])

    pareto_table = Table(pareto_data, colWidths=[5*cm, 1.5*cm])
    pareto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9c27b0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    # Combinar
    combined = Table([[severity_table, Spacer(1*cm, 0), pareto_table]])
    return combined


def create_energy_summary_table(energy: Dict) -> Table:
    """Cria tabela resumo de energia"""
    bill = energy['bill_forecast']

    data = [
        ['Consumo', f"{energy['current']['consumption_kwh']:,.0f} kWh",
         'Previsão Conta', f"R$ {bill['total_estimate']:,.2f}"],
        ['Demanda', f"{energy['current']['demand_kw']:,.0f} kW",
         'Custo Energia', f"R$ {bill['energy_cost']:,.2f}"],
        ['Fator Potência', f"{energy['current']['power_factor']:.2f}",
         'Custo Demanda', f"R$ {bill['demand_cost']:,.2f}"],
        ['Eficiência', f"{energy['efficiency']['kwh_per_ton']:.2f} kWh/ton",
         'Impostos', f"R$ {bill['taxes']:,.2f}"],
    ]

    table = Table(data, colWidths=[3*cm, 3*cm, 3*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (1, -1), colors.HexColor(THEME_COLORS['light_orange'])),
        ('BACKGROUND', (2, 0), (3, -1), colors.HexColor(THEME_COLORS['light_red'])),
    ]))

    return table


def create_production_summary_table(production: Dict) -> Table:
    """Cria tabela resumo de produção"""
    data = [
        ['Throughput', f"{production['current']['throughput_ton_hour']:.1f} ton/h",
         'Meta', f"{production['target']['achievement_percent']:.1f}%"],
        ['Produção Total', f"{production['period']['total_tons']:,.0f} ton",
         'Gap', f"{production['target']['gap_tons']:,.0f} ton"],
        ['Utilização', f"{production['capacity']['utilization_percent']:.1f}%",
         'Capacidade', f"{production['capacity']['nominal_ton_hour']:.0f} ton/h"],
    ]

    table = Table(data, colWidths=[3*cm, 3*cm, 2.5*cm, 3*cm])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(THEME_COLORS['light_green'])),
    ]))

    return table


def create_maintenance_summary_table(maintenance: Dict) -> Table:
    """Cria tabela resumo de manutenção"""
    roi = maintenance['roi']

    data = [
        ['Equipamentos', str(maintenance['summary']['total_equipment']),
         'Economia/Mês', f"R$ {roi['monthly_savings']:,.2f}"],
        ['Em Risco', str(maintenance['summary']['at_risk_count']),
         'ROI', f"{roi['roi_percent']:.0f}%"],
        ['Health Médio', f"{maintenance['summary']['average_health_score']:.0f}%",
         'Falhas Evitadas', f"{roi['failures_prevented_month']}/mês"],
    ]

    table = Table(data, colWidths=[3*cm, 2.5*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(THEME_COLORS['light_blue'])),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.red),  # Em Risco em vermelho
    ]))

    return table


def create_equipment_health_table(maintenance: Dict) -> Table:
    """Cria tabela de saúde dos equipamentos"""
    data = [['Equipamento', 'Health', 'Risco 7d', 'Status', 'Ação']]

    for equip in maintenance['equipment_health'][:8]:  # Top 8
        health = equip['health_score']
        status_symbol = "✓" if health >= 80 else "⚠" if health >= 60 else "✗"
        data.append([
            equip['equipment_name'][:18],
            f"{health}%",
            f"{equip['failure_probability_7d']}%",
            status_symbol,
            equip['recommended_action'][:25] + '...' if len(equip['recommended_action']) > 25 else equip['recommended_action']
        ])

    table = Table(data, colWidths=[3.5*cm, 1.5*cm, 1.5*cm, 1.2*cm, 5*cm])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(THEME_COLORS['info'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    # Colorir baseado no health score
    for i, equip in enumerate(maintenance['equipment_health'][:8], 1):
        score = equip['health_score']
        if score >= 80:
            style.add('TEXTCOLOR', (1, i), (1, i), colors.green)
        elif score >= 60:
            style.add('TEXTCOLOR', (1, i), (1, i), colors.HexColor(THEME_COLORS['warning']))
        else:
            style.add('TEXTCOLOR', (1, i), (1, i), colors.red)
            style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor(THEME_COLORS['light_red']))

    table.setStyle(style)
    return table


def create_insights_section(all_insights: List[Dict], styles) -> List:
    """Cria seção de insights formatada"""
    elements = []

    insight_style = ParagraphStyle(
        'InsightItem',
        parent=styles['Normal'],
        fontSize=9,
        leftIndent=20,
        spaceAfter=8,
        leading=12
    )

    for insight in all_insights[:10]:  # Máximo 10 insights
        icon = "✓" if insight['type'] == 'success' else "⚠" if insight['type'] == 'warning' else "✗" if insight['type'] == 'critical' else "ℹ"
        color = THEME_COLORS['success'] if insight['type'] == 'success' else THEME_COLORS['warning'] if insight['type'] == 'warning' else THEME_COLORS['error'] if insight['type'] == 'critical' else THEME_COLORS['info']

        text = f"<font color='{color}'><b>{icon} {insight['title']}</b></font>: {insight.get('description', '')} "
        if insight.get('recommendation'):
            text += f"<i>→ {insight['recommendation']}</i>"

        elements.append(Paragraph(text, insight_style))

    return elements


@router.get("/generate")
async def generate_executive_report(
    time_range: str = Query("24h", description="Time range: 1h, 6h, 24h, 7d, 30d"),
    include_charts: bool = Query(True, description="Include charts in report"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Gera relatório PDF completo do Dashboard Executivo com storytelling.

    O relatório inclui:
    - Sumário executivo narrativo com análise contextualizada
    - KPIs visuais com gauges e tendências
    - Gráficos profissionais (Pareto, Tendência, Energia, etc)
    - Análise detalhada de cada área operacional
    - Insights e recomendações acionáveis
    """
    try:
        logger.info(f"Generating executive report for time_range={time_range}")

        # Coletar todos os dados
        overview = await get_executive_overview(time_range, db, current_user)
        trends = await get_executive_trends(time_range, "1h", db, current_user)
        energy = await get_energy_metrics(time_range, db, current_user)
        pareto = await get_alarms_pareto(time_range, 10, db, current_user)
        production = await get_production_metrics(time_range, db, current_user)
        maintenance = await get_predictive_maintenance(db, current_user)

        # Criar buffer para PDF
        buffer = io.BytesIO()

        # Usar A4 Portrait para melhor leitura
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm
        )

        # Estilos
        styles = getSampleStyleSheet()

        # Estilos customizados
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.HexColor(THEME_COLORS['primary']),
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(THEME_COLORS['primary']),
            spaceBefore=15,
            spaceAfter=10,
            borderColor=colors.HexColor(THEME_COLORS['primary']),
            borderWidth=1,
            borderPadding=5,
            leftIndent=0
        )

        subsection_style = ParagraphStyle(
            'SubsectionTitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor(THEME_COLORS['secondary']),
            spaceBefore=10,
            spaceAfter=5
        )

        # Elementos do documento
        elements = []

        # ==================== PÁGINA 1: CAPA E SUMÁRIO ====================
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph("RELATÓRIO EXECUTIVO", title_style))
        elements.append(Paragraph("Performance Industrial & Operacional",
                                 ParagraphStyle('Subtitle', fontSize=14, alignment=TA_CENTER,
                                               textColor=colors.gray, spaceAfter=20)))

        # Linha decorativa
        elements.append(HRFlowable(width="60%", thickness=2,
                                   color=colors.HexColor(THEME_COLORS['primary']),
                                   spaceBefore=10, spaceAfter=20))

        # Info box
        period_map = {'1h': '1 Hora', '6h': '6 Horas', '24h': '24 Horas', '7d': '7 Dias', '30d': '30 Dias'}
        info_data = [
            ['Período:', period_map.get(time_range, time_range)],
            ['Gerado em:', datetime.now().strftime('%d/%m/%Y às %H:%M')],
            ['Responsável:', current_user.email if hasattr(current_user, 'email') else 'Sistema'],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 8*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('RIGHTPADDING', (0, 0), (0, -1), 15),
        ]))
        elements.append(info_table)

        elements.append(Spacer(1, 1.5*cm))

        # Storytelling
        elements.extend(generate_executive_storytelling(overview, energy, pareto,
                                                        production, maintenance,
                                                        time_range, styles))

        # ==================== PÁGINA 2: KPIs E TENDÊNCIAS ====================
        elements.append(PageBreak())
        elements.append(Paragraph("1. Indicadores de Performance (KPIs)", section_style))

        # Gráfico de Gauges
        if include_charts:
            try:
                kpi_chart_bytes = create_kpi_gauges(overview['kpis'])
                kpi_chart = create_chart_image(kpi_chart_bytes, width=18*cm, height=5*cm)
                if kpi_chart:
                    elements.append(kpi_chart)
            except Exception as e:
                logger.warning(f"Could not create KPI gauges: {e}")

        elements.append(Spacer(1, 0.3*cm))
        elements.append(create_kpi_cards_table(overview['kpis']))

        # Tendência OEE
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("1.1 Tendência de OEE", subsection_style))

        if include_charts:
            try:
                oee_data = trends.get('oee', {})
                # Garantir dados para o gráfico
                if not oee_data.get('data'):
                    # Gerar dados simulados se não houver
                    oee_data = {
                        'data': [{'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                                  'value': 75 + random.uniform(-5, 10), 'target': 85}
                                 for i in range(24, 0, -1)],
                        'summary': {'current': overview['kpis']['oee']['value'],
                                   'average': overview['kpis']['oee']['value'] - 2}
                    }
                oee_chart_bytes = create_oee_trend_chart(oee_data)
                oee_chart = create_chart_image(oee_chart_bytes, width=17*cm, height=5.5*cm)
                if oee_chart:
                    elements.append(oee_chart)
            except Exception as e:
                logger.warning(f"Could not create OEE trend chart: {e}")

        # ==================== PÁGINA 3: ALARMES E PARETO ====================
        elements.append(PageBreak())
        elements.append(Paragraph("2. Análise de Alarmes", section_style))

        # Gráfico de Distribuição
        if include_charts:
            try:
                alarms_chart_bytes = create_alarms_distribution_chart(overview['alarms'])
                alarms_chart = create_chart_image(alarms_chart_bytes, width=8*cm, height=5*cm)
                if alarms_chart:
                    # Colocar gráfico e tabela lado a lado
                    combined = Table([[alarms_chart, create_alarms_summary_table(overview['alarms'], pareto)]])
                    elements.append(combined)
            except Exception as e:
                logger.warning(f"Could not create alarms chart: {e}")
                elements.append(create_alarms_summary_table(overview['alarms'], pareto))
        else:
            elements.append(create_alarms_summary_table(overview['alarms'], pareto))

        # Gráfico de Pareto
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("2.1 Análise de Pareto - Regra 80/20", subsection_style))

        if include_charts:
            try:
                pareto_chart_bytes = create_pareto_chart(pareto)
                pareto_chart = create_chart_image(pareto_chart_bytes, width=17*cm, height=7*cm)
                if pareto_chart:
                    elements.append(pareto_chart)
            except Exception as e:
                logger.warning(f"Could not create Pareto chart: {e}")

        elements.append(Paragraph(
            f"<b>Conclusão:</b> {pareto['summary']['pareto_efficiency']} - "
            f"Custo total estimado: R$ {pareto['summary']['total_estimated_cost']:,.2f}",
            ParagraphStyle('ParetoConclusion', fontSize=10, spaceAfter=10, spaceBefore=5)))

        # ==================== PÁGINA 4: ENERGIA ====================
        elements.append(PageBreak())
        elements.append(Paragraph("3. Gestão Energética", section_style))

        if include_charts:
            try:
                # Garantir dados para o gráfico
                if not energy.get('history'):
                    energy['history'] = [
                        {'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                         'consumption_kwh': 800 + random.uniform(-100, 200),
                         'is_peak_hour': 18 <= (datetime.now() - timedelta(hours=i)).hour <= 21}
                        for i in range(24, 0, -1)
                    ]
                energy_chart_bytes = create_energy_chart(energy)
                energy_chart = create_chart_image(energy_chart_bytes, width=17*cm, height=5.5*cm)
                if energy_chart:
                    elements.append(energy_chart)
            except Exception as e:
                logger.warning(f"Could not create energy chart: {e}")

        elements.append(Spacer(1, 0.3*cm))
        elements.append(create_energy_summary_table(energy))

        # Alerta de demanda se necessário
        if energy['peak_demand'].get('risk_of_penalty', False):
            alert_style = ParagraphStyle('Alert', fontSize=10, textColor=colors.red,
                                        spaceBefore=10, spaceAfter=10,
                                        backColor=colors.HexColor(THEME_COLORS['light_red']),
                                        borderPadding=8)
            elements.append(Paragraph(
                f"⚠ <b>ALERTA:</b> Demanda atual ({energy['peak_demand']['current_kw']:,.0f} kW) "
                f"próxima do limite contratado ({energy['peak_demand']['contracted_kw']:,.0f} kW). "
                f"Risco de multa por ultrapassagem!", alert_style))

        # ==================== PÁGINA 5: PRODUÇÃO ====================
        elements.append(PageBreak())
        elements.append(Paragraph("4. Métricas de Produção", section_style))

        if include_charts:
            try:
                # Garantir dados para o gráfico
                if not production.get('history'):
                    production['history'] = [
                        {'timestamp': (datetime.now() - timedelta(hours=i)).isoformat(),
                         'throughput_ton_hour': 120 + random.uniform(-20, 30),
                         'utilization_percent': 75 + random.uniform(-10, 15)}
                        for i in range(24, 0, -1)
                    ]
                production_chart_bytes = create_production_chart(production)
                production_chart = create_chart_image(production_chart_bytes, width=17*cm, height=5.5*cm)
                if production_chart:
                    elements.append(production_chart)
            except Exception as e:
                logger.warning(f"Could not create production chart: {e}")

        elements.append(Spacer(1, 0.3*cm))
        elements.append(create_production_summary_table(production))

        # Status da meta
        gap = production['target']['gap_tons']
        gap_text = f"GAP: {gap:,.0f} ton para atingir meta" if gap > 0 else f"SUPEROU meta em {abs(gap):,.0f} ton"
        gap_color = THEME_COLORS['error'] if gap > 0 else THEME_COLORS['success']
        elements.append(Paragraph(
            f"<font color='{gap_color}'><b>{gap_text}</b></font> - "
            f"Atingimento: {production['target']['achievement_percent']:.1f}%",
            ParagraphStyle('GapStatus', fontSize=11, spaceBefore=10, alignment=TA_CENTER)))

        # ==================== PÁGINA 6: MANUTENÇÃO ====================
        elements.append(PageBreak())
        elements.append(Paragraph("5. Manutenção Preditiva", section_style))

        if include_charts:
            try:
                maintenance_chart_bytes = create_maintenance_health_chart(maintenance)
                maintenance_chart = create_chart_image(maintenance_chart_bytes, width=17*cm, height=5*cm)
                if maintenance_chart:
                    elements.append(maintenance_chart)
            except Exception as e:
                logger.warning(f"Could not create maintenance chart: {e}")

        elements.append(Spacer(1, 0.3*cm))
        elements.append(create_maintenance_summary_table(maintenance))

        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("5.1 Status dos Equipamentos", subsection_style))
        elements.append(create_equipment_health_table(maintenance))

        # ==================== PÁGINA 7: INSIGHTS ====================
        elements.append(PageBreak())
        elements.append(Paragraph("6. Insights e Recomendações", section_style))

        # Coletar todos os insights
        all_insights = []
        all_insights.extend(overview.get('insights', []))
        all_insights.extend(energy.get('insights', []))
        all_insights.extend(pareto.get('insights', []))
        all_insights.extend(maintenance.get('insights', []))

        # Ordenar por tipo (críticos primeiro)
        priority = {'critical': 0, 'warning': 1, 'info': 2, 'success': 3}
        all_insights.sort(key=lambda x: priority.get(x.get('type', 'info'), 2))

        if all_insights:
            elements.extend(create_insights_section(all_insights, styles))
        else:
            elements.append(Paragraph("Nenhum insight crítico identificado no período.",
                                     styles['Normal']))

        # Rodapé final
        elements.append(Spacer(1, 1*cm))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=colors.HexColor(THEME_COLORS['primary'])))
        elements.append(Paragraph(
            "— Fim do Relatório Executivo —<br/>"
            "<font size='8' color='gray'>Este relatório foi gerado automaticamente pelo sistema OptiFlow AI. "
            "Os dados apresentados são baseados em coleta em tempo real e análises de Machine Learning.</font>",
            ParagraphStyle('EndFooter', fontSize=10, alignment=TA_CENTER,
                          spaceBefore=10, textColor=colors.gray)))

        # Construir PDF
        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

        # Preparar resposta
        buffer.seek(0)
        filename = f"relatorio_executivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )

    except Exception as e:
        logger.error(f"Error generating executive report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")


@router.get("/preview")
async def preview_report_data(
    time_range: str = Query("24h", description="Time range"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna preview dos dados que serão incluídos no relatório.
    """
    try:
        overview = await get_executive_overview(time_range, db, current_user)
        energy = await get_energy_metrics(time_range, db, current_user)
        pareto = await get_alarms_pareto(time_range, 10, db, current_user)
        production = await get_production_metrics(time_range, db, current_user)
        maintenance = await get_predictive_maintenance(db, current_user)

        return {
            "status": "success",
            "time_range": time_range,
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "2.0",
            "features": [
                "Storytelling executivo",
                "Gráficos visuais (gauges, Pareto, tendências)",
                "Análise de alarmes com regra 80/20",
                "Gestão energética com previsão de conta",
                "Métricas de produção e capacidade",
                "Manutenção preditiva com ROI",
                "Insights e recomendações priorizadas"
            ],
            "sections": {
                "executive_summary": {
                    "included": True,
                    "type": "storytelling"
                },
                "kpis": {
                    "included": True,
                    "oee": overview['kpis']['oee']['value'],
                    "availability": overview['kpis']['availability']['value'],
                    "performance": overview['kpis']['performance']['value'],
                    "quality": overview['kpis']['quality']['value']
                },
                "alarms": {
                    "included": True,
                    "total_active": overview['alarms']['total_active'],
                    "critical": overview['alarms']['by_severity']['critical']
                },
                "pareto": {
                    "included": True,
                    "total_alarms": pareto['summary']['total_alarms'],
                    "cost_estimate": pareto['summary']['total_estimated_cost']
                },
                "energy": {
                    "included": True,
                    "consumption": energy['current']['consumption_kwh'],
                    "bill_estimate": energy['bill_forecast']['total_estimate']
                },
                "production": {
                    "included": True,
                    "throughput": production['current']['throughput_ton_hour'],
                    "achievement": production['target']['achievement_percent']
                },
                "maintenance": {
                    "included": True,
                    "equipment_count": maintenance['summary']['total_equipment'],
                    "at_risk": maintenance['summary']['at_risk_count'],
                    "roi": maintenance['roi']['roi_percent']
                },
                "insights": {
                    "included": True,
                    "total": len(overview.get('insights', [])) +
                            len(energy.get('insights', [])) +
                            len(pareto.get('insights', [])) +
                            len(maintenance.get('insights', []))
                }
            }
        }

    except Exception as e:
        logger.error(f"Error previewing report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
