"""
Report Generator

Generates professional PDF and Excel reports for port operations.

Reports:
- Daily operations summary
- Ship loading reports
- Truck entry reports
- Equipment performance
- Custom date range reports
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import os

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Image as RLImage
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available. PDF generation disabled.")

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.chart import BarChart, PieChart, Reference
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl not available. Excel generation disabled.")

from app.models.operational_data import TruckEntry, ShipLoading, DailyOperations

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Professional report generation for port operations.

    Formats:
    - PDF (using reportlab)
    - Excel (using openpyxl)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.reports_dir = "generated_reports/"

        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)

    async def generate_daily_operations_pdf(
        self,
        site_id: int,
        operation_date: date
    ) -> str:
        """
        Generate PDF report for daily operations.

        Args:
            site_id: Site ID
            operation_date: Date to generate report for

        Returns:
            Filename of generated PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation")

        try:
            logger.info(f"Generating daily operations PDF for {operation_date}")

            # Get daily operations data
            result = await self.db.execute(
                select(DailyOperations).where(
                    and_(
                        DailyOperations.site_id == site_id,
                        DailyOperations.operation_date == operation_date
                    )
                )
            )
            daily_ops = result.scalar_one_or_none()

            # Get truck entries
            truck_result = await self.db.execute(
                select(TruckEntry).where(
                    and_(
                        TruckEntry.site_id == site_id,
                        func.date(TruckEntry.entry_time) == operation_date
                    )
                )
            )
            trucks = truck_result.scalars().all()

            # Get ship loadings
            ship_result = await self.db.execute(
                select(ShipLoading).where(
                    and_(
                        ShipLoading.site_id == site_id,
                        func.date(ShipLoading.arrival_time) == operation_date
                    )
                )
            )
            ships = ship_result.scalars().all()

            # Create PDF
            filename = f"daily_operations_{operation_date.strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a365d'),
                spaceAfter=30,
                alignment=1  # Center
            )

            story.append(Paragraph(
                f"Relatório de Operações Diárias",
                title_style
            ))
            story.append(Paragraph(
                f"Data: {operation_date.strftime('%d/%m/%Y')}",
                styles['Heading2']
            ))
            story.append(Spacer(1, 20))

            # Summary section
            if daily_ops:
                story.append(Paragraph("Resumo das Operações", styles['Heading2']))

                summary_data = [
                    ['Métrica', 'Valor'],
                    ['Caminhões Recebidos', str(daily_ops.trucks_received)],
                    ['Tonelagem Total (Caminhões)', f"{daily_ops.trucks_total_tonnage:.2f} t"],
                    ['Navios no Porto', str(daily_ops.ships_in_port)],
                    ['Navios em Carregamento', str(daily_ops.ships_loading)],
                    ['Tonelagem Carregada', f"{daily_ops.total_tonnage_loaded:.2f} t"],
                    ['Horas Operacionais', f"{daily_ops.operating_hours:.1f} h"],
                    ['Eficiência Operacional', f"{daily_ops.operational_efficiency or 0:.1f}%"],
                ]

                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(summary_table)
                story.append(Spacer(1, 20))

            # Truck entries section
            if trucks:
                story.append(Paragraph("Entradas de Caminhões", styles['Heading2']))

                truck_data = [['Placa', 'Produto', 'Peso Líquido (kg)', 'Horário']]
                for truck in trucks[:20]:  # Limit to 20 for PDF
                    truck_data.append([
                        truck.truck_id,
                        truck.product_type,
                        f"{truck.net_weight:.2f}",
                        truck.entry_time.strftime('%H:%M') if truck.entry_time else '-'
                    ])

                truck_table = Table(truck_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                truck_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(truck_table)
                story.append(Spacer(1, 20))

            # Ship loadings section
            if ships:
                story.append(Paragraph("Carregamentos de Navios", styles['Heading2']))

                ship_data = [['Navio', 'Berço', 'Produto', 'Tonelagem', 'Status']]
                for ship in ships:
                    ship_data.append([
                        ship.ship_name,
                        str(ship.berth_number),
                        ship.product_type,
                        f"{ship.loaded_tonnage:.2f}",
                        ship.status
                    ])

                ship_table = Table(ship_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
                ship_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                story.append(ship_table)

            # Footer
            story.append(Spacer(1, 30))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                alignment=1
            )
            story.append(Paragraph(
                f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - OptiFlow AI",
                footer_style
            ))

            # Build PDF
            doc.build(story)

            logger.info(f"PDF generated: {filepath}")

            return filename

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

    async def generate_daily_operations_excel(
        self,
        site_id: int,
        start_date: date,
        end_date: date
    ) -> str:
        """
        Generate Excel report for date range.

        Args:
            site_id: Site ID
            start_date: Start date
            end_date: End date

        Returns:
            Filename of generated Excel file
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel generation")

        try:
            logger.info(f"Generating Excel report for {start_date} to {end_date}")

            # Create workbook
            wb = openpyxl.Workbook()

            # Remove default sheet
            wb.remove(wb.active)

            # Summary sheet
            ws_summary = wb.create_sheet("Resumo")
            await self._create_summary_sheet(ws_summary, site_id, start_date, end_date)

            # Trucks sheet
            ws_trucks = wb.create_sheet("Caminhões")
            await self._create_trucks_sheet(ws_trucks, site_id, start_date, end_date)

            # Ships sheet
            ws_ships = wb.create_sheet("Navios")
            await self._create_ships_sheet(ws_ships, site_id, start_date, end_date)

            # Save workbook
            filename = f"operations_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            filepath = os.path.join(self.reports_dir, filename)
            wb.save(filepath)

            logger.info(f"Excel generated: {filepath}")

            return filename

        except Exception as e:
            logger.error(f"Error generating Excel: {e}")
            raise

    async def _create_summary_sheet(
        self,
        ws,
        site_id: int,
        start_date: date,
        end_date: date
    ):
        """Create summary sheet in Excel."""
        # Title
        ws['A1'] = "Resumo de Operações"
        ws['A1'].font = Font(size=16, bold=True)
        ws['A2'] = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

        # Get daily operations
        result = await self.db.execute(
            select(DailyOperations).where(
                and_(
                    DailyOperations.site_id == site_id,
                    DailyOperations.operation_date >= start_date,
                    DailyOperations.operation_date <= end_date
                )
            ).order_by(DailyOperations.operation_date)
        )
        daily_ops = result.scalars().all()

        # Headers
        headers = ['Data', 'Caminhões', 'Tonelagem Caminhões', 'Navios', 'Tonelagem Carregada', 'Eficiência %']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='1a365d', end_color='1a365d', fill_type='solid')
            cell.font = Font(color='FFFFFF', bold=True)

        # Data
        for row, ops in enumerate(daily_ops, start=5):
            ws.cell(row=row, column=1).value = ops.operation_date.strftime('%d/%m/%Y')
            ws.cell(row=row, column=2).value = ops.trucks_received
            ws.cell(row=row, column=3).value = ops.trucks_total_tonnage
            ws.cell(row=row, column=4).value = ops.ships_departed
            ws.cell(row=row, column=5).value = ops.total_tonnage_loaded
            ws.cell(row=row, column=6).value = ops.operational_efficiency

        # Auto-size columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width

    async def _create_trucks_sheet(
        self,
        ws,
        site_id: int,
        start_date: date,
        end_date: date
    ):
        """Create trucks sheet in Excel."""
        # Headers
        headers = ['Data/Hora', 'Placa', 'Motorista', 'Empresa', 'Produto', 'Peso Bruto', 'Tara', 'Peso Líquido']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)

        # Get truck entries
        result = await self.db.execute(
            select(TruckEntry).where(
                and_(
                    TruckEntry.site_id == site_id,
                    func.date(TruckEntry.entry_time) >= start_date,
                    func.date(TruckEntry.entry_time) <= end_date
                )
            ).order_by(TruckEntry.entry_time)
        )
        trucks = result.scalars().all()

        # Data
        for row, truck in enumerate(trucks, start=2):
            ws.cell(row=row, column=1).value = truck.entry_time.strftime('%d/%m/%Y %H:%M') if truck.entry_time else ''
            ws.cell(row=row, column=2).value = truck.truck_id
            ws.cell(row=row, column=3).value = truck.driver_name
            ws.cell(row=row, column=4).value = truck.company
            ws.cell(row=row, column=5).value = truck.product_type
            ws.cell(row=row, column=6).value = truck.gross_weight
            ws.cell(row=row, column=7).value = truck.tare_weight
            ws.cell(row=row, column=8).value = truck.net_weight

    async def _create_ships_sheet(
        self,
        ws,
        site_id: int,
        start_date: date,
        end_date: date
    ):
        """Create ships sheet in Excel."""
        # Headers
        headers = ['Navio', 'Berço', 'Produto', 'Tonelagem Alvo', 'Tonelagem Carregada', 'Status', 'Chegada', 'Partida']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)

        # Get ship loadings
        result = await self.db.execute(
            select(ShipLoading).where(
                and_(
                    ShipLoading.site_id == site_id,
                    func.date(ShipLoading.arrival_time) >= start_date,
                    func.date(ShipLoading.arrival_time) <= end_date
                )
            ).order_by(ShipLoading.arrival_time)
        )
        ships = result.scalars().all()

        # Data
        for row, ship in enumerate(ships, start=2):
            ws.cell(row=row, column=1).value = ship.ship_name
            ws.cell(row=row, column=2).value = ship.berth_number
            ws.cell(row=row, column=3).value = ship.product_type
            ws.cell(row=row, column=4).value = ship.target_tonnage
            ws.cell(row=row, column=5).value = ship.loaded_tonnage
            ws.cell(row=row, column=6).value = ship.status
            ws.cell(row=row, column=7).value = ship.arrival_time.strftime('%d/%m/%Y %H:%M') if ship.arrival_time else ''
            ws.cell(row=row, column=8).value = ship.departure_time.strftime('%d/%m/%Y %H:%M') if ship.departure_time else ''

    def get_report_path(self, filename: str) -> str:
        """Get full path to generated report."""
        return os.path.join(self.reports_dir, filename)
