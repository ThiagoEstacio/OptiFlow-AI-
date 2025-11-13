"""
Advanced Report Generator

Comprehensive report generation with multiple templates:
- Operational reports
- Quality analysis reports
- ML performance reports
- Alarm history reports
- Executive summaries
- Energy consumption reports

Supports: PDF, Excel, CSV formats
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
import os
import csv
import io

logger = logging.getLogger(__name__)

# Check available libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available")

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not available")


class AdvancedReportGenerator:
    """
    Advanced report generator with multiple templates and formats
    """

    def __init__(self, db: Optional[AsyncSession]):
        self.db = db
        self.reports_dir = "generated_reports/"
        os.makedirs(self.reports_dir, exist_ok=True)

    # ========================================================================
    # OPERATIONAL REPORTS
    # ========================================================================

    async def generate_operational_report_pdf(
        self,
        site_id: str,
        report_date: date
    ) -> str:
        """Generate operational report in PDF format"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required for PDF generation")

        try:
            filename = f"operational_{report_date.strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title = Paragraph(f"<b>Relatório Operacional</b><br/>{report_date.strftime('%d/%m/%Y')}",
                            styles['Title'])
            story.append(title)
            story.append(Spacer(1, 20))

            # Summary section with sample data
            summary_data = [
                ['Métrica', 'Valor', 'Meta', 'Status'],
                ['Eficiência Operacional', '95.2%', '90%', '✓'],
                ['Disponibilidade', '98.5%', '95%', '✓'],
                ['Produção (ton)', '12,450', '12,000', '✓'],
                ['Consumo Energia (kWh)', '1,523', '1,600', '✓'],
                ['Alarmes Críticos', '2', '< 5', '✓'],
            ]

            t = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            story.append(t)
            story.append(Spacer(1, 30))

            # Footer
            footer = Paragraph(
                f"<i>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - OptiFlow AI</i>",
                styles['Normal']
            )
            story.append(footer)

            doc.build(story)
            logger.info(f"PDF generated: {filepath}")
            return filename

        except Exception as e:
            logger.error(f"Error generating operational PDF: {e}")
            raise

    async def generate_operational_report_excel(
        self,
        site_id: str,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate operational report in Excel format"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl required for Excel generation")

        try:
            filename = f"operational_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            filepath = os.path.join(self.reports_dir, filename)

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Resumo"

            # Title
            ws['A1'] = "Relatório Operacional"
            ws['A1'].font = Font(size=16, bold=True)
            ws['A2'] = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

            # Headers
            headers = ['Data', 'Eficiência %', 'Produção (ton)', 'Energia (kWh)', 'Alarmes']
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=4, column=col)
                cell.value = header
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color='1a365d', end_color='1a365d', fill_type='solid')
                cell.font = Font(color='FFFFFF', bold=True)

            # Sample data
            current_date = start_date
            row = 5
            while current_date <= end_date:
                ws.cell(row=row, column=1).value = current_date.strftime('%d/%m/%Y')
                ws.cell(row=row, column=2).value = 95.0 + (row % 5)
                ws.cell(row=row, column=3).value = 12000 + (row * 100)
                ws.cell(row=row, column=4).value = 1500 + (row * 10)
                ws.cell(row=row, column=5).value = row % 3
                current_date += timedelta(days=1)
                row += 1

            # Auto-size columns
            for column in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column_letter].width = adjusted_width

            wb.save(filepath)
            logger.info(f"Excel generated: {filepath}")
            return filename

        except Exception as e:
            logger.error(f"Error generating operational Excel: {e}")
            raise

    async def generate_operational_report_csv(
        self,
        site_id: str,
        start_date: date,
        end_date: date
    ) -> str:
        """Generate operational report in CSV format"""
        try:
            filename = f"operational_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.reports_dir, filename)

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Header
                writer.writerow(['Data', 'Eficiência (%)', 'Produção (ton)', 'Energia (kWh)', 'Alarmes'])

                # Sample data
                current_date = start_date
                row_num = 0
                while current_date <= end_date:
                    writer.writerow([
                        current_date.strftime('%d/%m/%Y'),
                        f"{95.0 + (row_num % 5):.1f}",
                        12000 + (row_num * 100),
                        1500 + (row_num * 10),
                        row_num % 3
                    ])
                    current_date += timedelta(days=1)
                    row_num += 1

            logger.info(f"CSV generated: {filepath}")
            return filename

        except Exception as e:
            logger.error(f"Error generating operational CSV: {e}")
            raise

    # ========================================================================
    # QUALITY REPORTS
    # ========================================================================

    async def generate_quality_report(
        self,
        site_id: str,
        start_date: date,
        end_date: date,
        format: str = "pdf"
    ) -> str:
        """Generate quality analysis report"""

        if format == "pdf":
            return await self._generate_quality_pdf(site_id, start_date, end_date)
        elif format == "excel":
            return await self._generate_quality_excel(site_id, start_date, end_date)
        else:
            raise ValueError(f"Format '{format}' not supported for quality reports")

    async def _generate_quality_pdf(self, site_id: str, start_date: date, end_date: date) -> str:
        """Generate quality report in PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required")

        filename = f"quality_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        story.append(Paragraph(f"<b>Análise de Qualidade</b>", styles['Title']))
        story.append(Paragraph(f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
                              styles['Heading2']))
        story.append(Spacer(1, 20))

        # Quality metrics
        metrics_data = [
            ['Métrica', 'Valor', 'Tendência'],
            ['Taxa de Conformidade', '99.7%', '↑ +0.3%'],
            ['Taxa de Defeitos', '0.3%', '↓ -0.1%'],
            ['Produtos Inspecionados', '42,450', '↑ +2.1%'],
            ['Tempo Médio Detecção', '2.3 min', '↓ -0.5 min'],
        ]

        t = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ]))

        story.append(t)
        story.append(Spacer(1, 20))

        doc.build(story)
        return filename

    async def _generate_quality_excel(self, site_id: str, start_date: date, end_date: date) -> str:
        """Generate quality report in Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl required")

        filename = f"quality_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Quality Metrics"

        ws['A1'] = "Análise de Qualidade"
        ws['A1'].font = Font(size=16, bold=True)

        headers = ['Métrica', 'Valor', 'Meta', 'Status']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = Font(bold=True)

        ws.cell(row=4, column=1).value = "Taxa de Conformidade"
        ws.cell(row=4, column=2).value = "99.7%"
        ws.cell(row=4, column=3).value = "> 99%"
        ws.cell(row=4, column=4).value = "OK"

        wb.save(filepath)
        return filename

    # ========================================================================
    # ML PERFORMANCE REPORTS
    # ========================================================================

    async def generate_ml_report(self, format: str = "pdf") -> str:
        """Generate ML models performance report"""

        if format == "pdf":
            return await self._generate_ml_pdf()
        elif format == "excel":
            return await self._generate_ml_excel()
        else:
            raise ValueError(f"Format '{format}' not supported")

    async def _generate_ml_pdf(self) -> str:
        """Generate ML report in PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required")

        filename = f"ml_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("<b>Performance de Modelos ML</b>", styles['Title']))
        story.append(Spacer(1, 20))

        ml_data = [
            ['Modelo', 'Acurácia', 'Previsões/dia', 'Status'],
            ['Isolation Forest', '99.7%', '15,420', 'Ativo'],
            ['Gradient Boosting', '94.2%', '8,340', 'Ativo'],
            ['LSTM Energy', '96.8%', '12,120', 'Ativo'],
        ]

        t = Table(ml_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(t)
        doc.build(story)
        return filename

    async def _generate_ml_excel(self) -> str:
        """Generate ML report in Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl required")

        filename = f"ml_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ML Performance"

        ws['A1'] = "Performance de Modelos ML"
        ws['A1'].font = Font(size=16, bold=True)

        headers = ['Modelo', 'Acurácia', 'R² Score', 'Previsões/dia']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col)
            cell.value = header
            cell.font = Font(bold=True)

        models = [
            ['Isolation Forest', '99.7%', '0.997', 15420],
            ['Gradient Boosting', '94.2%', '0.942', 8340],
            ['LSTM Energy', '96.8%', '0.968', 12120],
        ]

        for row, model_data in enumerate(models, start=4):
            for col, value in enumerate(model_data, start=1):
                ws.cell(row=row, column=col).value = value

        wb.save(filepath)
        return filename

    # ========================================================================
    # ALARM REPORTS
    # ========================================================================

    async def generate_alarm_report(
        self,
        start_date: date,
        end_date: date,
        format: str = "pdf",
        severity: Optional[str] = None
    ) -> str:
        """Generate alarm history report"""

        if format == "pdf":
            return await self._generate_alarm_pdf(start_date, end_date, severity)
        elif format == "excel":
            return await self._generate_alarm_excel(start_date, end_date, severity)
        elif format == "csv":
            return await self._generate_alarm_csv(start_date, end_date, severity)
        else:
            raise ValueError(f"Format '{format}' not supported")

    async def _generate_alarm_pdf(self, start_date: date, end_date: date, severity: Optional[str]) -> str:
        """Generate alarm report in PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required")

        filename = f"alarms_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("<b>Histórico de Alarmes</b>", styles['Title']))
        story.append(Spacer(1, 20))

        alarm_data = [
            ['Timestamp', 'Alarme', 'Severidade', 'Duração'],
            ['12/11 14:23', 'Alta Temperatura', 'HIGH', '15 min'],
            ['12/11 16:45', 'Overcurrent', 'MEDIUM', '8 min'],
            ['13/11 09:12', 'Sistema Parado', 'CRITICAL', '2 min'],
        ]

        t = Table(alarm_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        story.append(t)
        doc.build(story)
        return filename

    async def _generate_alarm_excel(self, start_date: date, end_date: date, severity: Optional[str]) -> str:
        """Generate alarm report in Excel"""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl required")

        filename = f"alarms_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Alarm History"

        headers = ['Timestamp', 'Alarme', 'Severidade', 'Duração (min)', 'Status']
        for col, header in enumerate(headers, start=1):
            ws.cell(row=1, column=col).value = header
            ws.cell(row=1, column=col).font = Font(bold=True)

        wb.save(filepath)
        return filename

    async def _generate_alarm_csv(self, start_date: date, end_date: date, severity: Optional[str]) -> str:
        """Generate alarm report in CSV"""
        filename = f"alarms_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        filepath = os.path.join(self.reports_dir, filename)

        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Alarme', 'Severidade', 'Duração'])
            writer.writerow(['12/11/2025 14:23', 'Alta Temperatura', 'HIGH', '15 min'])

        return filename

    # ========================================================================
    # EXECUTIVE REPORTS
    # ========================================================================

    async def generate_executive_report(self, period: str = "monthly", format: str = "pdf") -> str:
        """Generate executive summary report"""

        if format != "pdf":
            raise ValueError("Executive reports only available in PDF format")

        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required")

        filename = f"executive_{period}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(self.reports_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("<b>Sumário Executivo</b>", styles['Title']))
        story.append(Paragraph(f"<i>Período: {period}</i>", styles['Heading2']))
        story.append(Spacer(1, 30))

        # Key metrics
        kpi_data = [
            ['KPI', 'Atual', 'Meta', 'Variação'],
            ['Eficiência Operacional', '95.2%', '90%', '+5.2%'],
            ['Disponibilidade', '98.5%', '95%', '+3.5%'],
            ['Custo por Tonelada', 'R$ 12.50', 'R$ 15.00', '-16.7%'],
            ['ROI Anual', 'R$ 2.4M', 'R$ 2.0M', '+20%'],
        ]

        t = Table(kpi_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ]))

        story.append(t)
        doc.build(story)
        return filename

    # ========================================================================
    # DASHBOARD EXPORT
    # ========================================================================

    async def generate_dashboard_report_pdf(
        self,
        dashboard_id: str,
        dashboard_name: str,
        widgets_data: List[Dict[str, Any]],
        user_name: str = "Admin"
    ) -> str:
        """
        Generate a PDF report from dashboard data

        Args:
            dashboard_id: Dashboard unique identifier
            dashboard_name: Name of the dashboard
            widgets_data: List of widget data containing:
                - title: Widget title
                - type: Widget type (chart, metric, table, etc)
                - data: Widget data
                - value: For metric widgets
                - trend: For metric widgets
            user_name: Name of user generating report
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab required for PDF generation")

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dashboard_{dashboard_id}_{timestamp}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=30,
                alignment=1  # Center
            )

            story.append(Paragraph(f"<b>{dashboard_name}</b>", title_style))

            # Metadata
            metadata_style = styles['Normal']
            metadata_style.fontSize = 10
            metadata_style.textColor = colors.grey

            story.append(Paragraph(
                f"Exportado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}<br/>"
                f"Por: {user_name}<br/>"
                f"Dashboard ID: {dashboard_id}",
                metadata_style
            ))
            story.append(Spacer(1, 0.3*inch))

            # Summary box
            summary_data = [
                ['Total de Widgets', str(len(widgets_data))],
                ['Período', 'Tempo Real'],
                ['Status', 'Ativo']
            ]

            t = Table(summary_data, colWidths=[3*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            story.append(t)
            story.append(Spacer(1, 0.5*inch))

            # Process each widget
            for idx, widget in enumerate(widgets_data, 1):
                widget_title = widget.get('title', f'Widget {idx}')
                widget_type = widget.get('type', 'unknown')

                # Widget header
                header_style = ParagraphStyle(
                    'WidgetHeader',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#2d3748'),
                    spaceAfter=10,
                    spaceBefore=20
                )

                story.append(Paragraph(f"<b>{idx}. {widget_title}</b>", header_style))

                # Widget content based on type
                if widget_type == 'metric':
                    self._add_metric_widget(story, widget, styles)
                elif widget_type == 'chart':
                    self._add_chart_widget(story, widget, styles)
                elif widget_type == 'table':
                    self._add_table_widget(story, widget, styles)
                elif widget_type == 'status':
                    self._add_status_widget(story, widget, styles)
                else:
                    # Generic widget
                    story.append(Paragraph(f"Tipo: {widget_type}", styles['Normal']))
                    if 'description' in widget:
                        story.append(Paragraph(widget['description'], styles['Normal']))

                story.append(Spacer(1, 0.2*inch))

            # Footer
            story.append(Spacer(1, 0.5*inch))
            footer_style = styles['Normal']
            footer_style.fontSize = 8
            footer_style.textColor = colors.grey
            footer_style.alignment = 1  # Center

            story.append(Paragraph(
                "Relatório gerado automaticamente pelo OptiFlow AI Platform",
                footer_style
            ))

            doc.build(story)
            logger.info(f"Dashboard report generated: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating dashboard PDF: {e}", exc_info=True)
            raise

    def _add_metric_widget(self, story: List, widget: Dict, styles):
        """Add metric widget to PDF"""
        value = widget.get('value', 'N/A')
        trend = widget.get('trend', '')
        unit = widget.get('unit', '')

        metric_data = [
            ['Valor Atual', f"{value} {unit}"],
        ]

        if trend:
            metric_data.append(['Tendência', trend])

        if 'target' in widget:
            metric_data.append(['Meta', f"{widget['target']} {unit}"])

        t = Table(metric_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 16),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2b6cb0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(t)

    def _add_chart_widget(self, story: List, widget: Dict, styles):
        """Add chart widget to PDF"""
        chart_type = widget.get('chart_type', 'bar')
        data = widget.get('data', [])

        # Add description
        if 'description' in widget:
            story.append(Paragraph(widget['description'], styles['Normal']))

        # Create simple data table representation
        if data:
            # Extract data for table
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Convert dict data to table
                    headers = list(data[0].keys())
                    table_data = [headers]

                    for row in data[:10]:  # Limit to 10 rows
                        table_data.append([str(row.get(h, '')) for h in headers])

                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ]))

                    story.append(t)
        else:
            story.append(Paragraph(f"Gráfico: {chart_type}", styles['Normal']))

    def _add_table_widget(self, story: List, widget: Dict, styles):
        """Add table widget to PDF"""
        data = widget.get('data', [])
        headers = widget.get('headers', [])

        if not data:
            story.append(Paragraph("Sem dados disponíveis", styles['Normal']))
            return

        # Build table
        table_data = []

        if headers:
            table_data.append(headers)

        for row in data[:20]:  # Limit to 20 rows
            if isinstance(row, dict):
                table_data.append([str(row.get(h, '')) for h in headers])
            elif isinstance(row, list):
                table_data.append([str(cell) for cell in row])

        if table_data:
            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4299e1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))

            story.append(t)

    def _add_status_widget(self, story: List, widget: Dict, styles):
        """Add status widget to PDF"""
        status = widget.get('status', 'unknown')
        message = widget.get('message', '')

        status_data = [
            ['Status', status.upper()],
        ]

        if message:
            status_data.append(['Mensagem', message])

        # Color based on status
        bg_color = colors.green if status == 'ok' else colors.orange if status == 'warning' else colors.red

        t = Table(status_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (1, 0), (1, 0), bg_color),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.whitesmoke),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        story.append(t)

    async def generate_dashboard_report_excel(
        self,
        dashboard_id: str,
        dashboard_name: str,
        widgets_data: List[Dict[str, Any]],
        user_name: str = "Admin"
    ) -> str:
        """
        Generate an Excel report from dashboard data
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl required for Excel generation")

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dashboard_{dashboard_id}_{timestamp}.xlsx"
            filepath = os.path.join(self.reports_dir, filename)

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Dashboard"

            # Header
            ws['A1'] = dashboard_name
            ws['A1'].font = Font(size=18, bold=True, color="1a365d")
            ws.merge_cells('A1:E1')

            # Metadata
            ws['A2'] = f"Exportado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            ws['A3'] = f"Por: {user_name}"
            ws['A4'] = f"Dashboard ID: {dashboard_id}"

            row = 6

            # Process each widget
            for idx, widget in enumerate(widgets_data, 1):
                widget_title = widget.get('title', f'Widget {idx}')
                widget_type = widget.get('type', 'unknown')

                # Widget header
                ws[f'A{row}'] = f"{idx}. {widget_title}"
                ws[f'A{row}'].font = Font(size=14, bold=True)
                row += 1

                ws[f'A{row}'] = f"Tipo: {widget_type}"
                row += 1

                # Widget data
                if widget_type == 'metric':
                    ws[f'A{row}'] = "Valor"
                    ws[f'B{row}'] = widget.get('value', 'N/A')
                    row += 1

                    if 'trend' in widget:
                        ws[f'A{row}'] = "Tendência"
                        ws[f'B{row}'] = widget['trend']
                        row += 1

                elif widget_type == 'table':
                    data = widget.get('data', [])
                    headers = widget.get('headers', [])

                    if headers:
                        for col_idx, header in enumerate(headers):
                            cell = ws.cell(row=row, column=col_idx + 1)
                            cell.value = header
                            cell.font = Font(bold=True)
                        row += 1

                    for data_row in data[:50]:  # Limit to 50 rows
                        if isinstance(data_row, dict):
                            for col_idx, header in enumerate(headers):
                                ws.cell(row=row, column=col_idx + 1).value = data_row.get(header, '')
                        elif isinstance(data_row, list):
                            for col_idx, value in enumerate(data_row):
                                ws.cell(row=row, column=col_idx + 1).value = value
                        row += 1

                row += 2  # Space between widgets

            wb.save(filepath)
            logger.info(f"Dashboard Excel report generated: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating dashboard Excel: {e}", exc_info=True)
            raise

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_report_path(self, filename: str) -> str:
        """Get full path to report file"""
        return os.path.join(self.reports_dir, filename)
