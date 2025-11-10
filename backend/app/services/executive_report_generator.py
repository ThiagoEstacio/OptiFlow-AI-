"""
Executive Weekly Report Generator

Generates comprehensive weekly reports for executives with:
- Key performance indicators
- ROI summary
- Highlights and achievements
- Risks and opportunities
- Strategic recommendations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available. Executive PDF generation disabled.")

from app.services.executive_dashboard import ExecutiveDashboard
from app.services.roi_calculator import ROICalculator

logger = logging.getLogger(__name__)


class ExecutiveReportGenerator:
    """
    Generate comprehensive weekly reports for executive decision-making.

    Reports include: KPIs, ROI analysis, strategic insights, risks, and recommendations.
    """

    REPORTS_DIR = "reports/executive"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dashboard_service = ExecutiveDashboard(db)
        self.roi_service = ROICalculator(db)

        # Ensure reports directory exists
        os.makedirs(self.REPORTS_DIR, exist_ok=True)

    async def generate_weekly_report_pdf(
        self,
        site_id: int,
        week_start_date: Optional[date] = None
    ) -> str:
        """
        Generate executive weekly report in PDF format.

        Args:
            site_id: Site identifier
            week_start_date: Start of week (defaults to last Monday)

        Returns:
            Path to generated PDF file
        """
        try:
            # Default to last Monday
            if not week_start_date:
                today = datetime.utcnow().date()
                days_since_monday = today.weekday()
                week_start_date = today - timedelta(days=days_since_monday)

            week_end_date = week_start_date + timedelta(days=6)

            # Gather data
            logger.info(f"Generating executive report for site {site_id}, week of {week_start_date}")

            dashboard_data = await self.dashboard_service.get_dashboard_360(site_id, period_days=7)
            roi_data = await self.roi_service.calculate_roi(site_id, period_days=7)

            # Create PDF
            filename = f"{self.REPORTS_DIR}/executive_weekly_{site_id}_{week_start_date.strftime('%Y%m%d')}.pdf"
            doc = SimpleDocTemplate(
                filename,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            # Build content
            story = []
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=20
            )

            # Title page
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph("OptiFlow AI", title_style))
            story.append(Paragraph("Executive Weekly Report", styles['Heading2']))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph(
                f"Week of {week_start_date.strftime('%B %d')} - {week_end_date.strftime('%B %d, %Y')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.5*inch))

            # Executive summary
            story.append(self._create_executive_summary(dashboard_data, roi_data, styles))
            story.append(PageBreak())

            # Financial performance
            story.append(Paragraph("Financial Performance", heading_style))
            story.append(self._create_financial_section(roi_data, styles))
            story.append(Spacer(1, 0.3*inch))

            # Operational KPIs
            story.append(Paragraph("Operational Performance", heading_style))
            story.append(self._create_operational_section(dashboard_data, styles))
            story.append(Spacer(1, 0.3*inch))

            # Maintenance & Asset Health
            story.append(Paragraph("Maintenance & Asset Health", heading_style))
            story.append(self._create_maintenance_section(dashboard_data, styles))
            story.append(PageBreak())

            # Risks & Opportunities
            story.append(Paragraph("Strategic Insights", heading_style))
            story.append(self._create_risks_opportunities_section(dashboard_data, styles))
            story.append(Spacer(1, 0.3*inch))

            # Recommendations
            story.append(Paragraph("Executive Recommendations", heading_style))
            story.append(self._create_recommendations_section(dashboard_data, roi_data, styles))

            # Build PDF
            doc.build(story)

            logger.info(f"Executive report generated: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating executive report: {str(e)}", exc_info=True)
            raise

    def _create_executive_summary(
        self,
        dashboard_data: Dict[str, Any],
        roi_data: Dict[str, Any],
        styles
    ) -> Table:
        """Create executive summary section."""

        overall_health = dashboard_data.get("overall_health_score", {})
        total_savings = roi_data.get("total_savings", 0)
        highlights = roi_data.get("highlights", [])

        # Summary metrics
        data = [
            ["Executive Summary", ""],
            ["", ""],
            ["Overall Terminal Health", f"{overall_health.get('score', 0)}/100 - {overall_health.get('status', 'N/A').upper()}"],
            ["Weekly Cost Savings", f"${total_savings:,.0f}"],
            ["Annual Projection", f"${roi_data.get('annual_projection', 0):,.0f}"],
            ["ROI", f"{roi_data.get('roi_percentage', 0):.1f}%"],
        ]

        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 2), (-1, -1), 11),
            ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
        ]))

        return table

    def _create_financial_section(
        self,
        roi_data: Dict[str, Any],
        styles
    ) -> Table:
        """Create financial performance section."""

        pred_maint = roi_data.get("predictive_maintenance", {})
        optimization = roi_data.get("optimization", {})
        efficiency = roi_data.get("efficiency", {})
        downtime = roi_data.get("downtime_avoided", {})

        data = [
            ["Category", "This Week", "Annual Projection"],
            [
                "Predictive Maintenance Savings",
                f"${pred_maint.get('total_savings', 0):,.0f}",
                f"${pred_maint.get('total_savings', 0) * 52:,.0f}"
            ],
            [
                "Optimization Savings",
                f"${optimization.get('total_savings', 0):,.0f}",
                f"${optimization.get('total_savings', 0) * 52:,.0f}"
            ],
            [
                "Efficiency Improvements",
                f"${efficiency.get('total_savings', 0):,.0f}",
                f"${efficiency.get('total_savings', 0) * 52:,.0f}"
            ],
            [
                "Downtime Costs Avoided",
                f"${downtime.get('total_cost_avoided', 0):,.0f}",
                f"${downtime.get('total_cost_avoided', 0) * 52:,.0f}"
            ],
            [
                "TOTAL SAVINGS",
                f"${roi_data.get('total_savings', 0):,.0f}",
                f"${roi_data.get('annual_projection', 0):,.0f}"
            ],
        ]

        table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#2ecc71')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ]))

        return table

    def _create_operational_section(
        self,
        dashboard_data: Dict[str, Any],
        styles
    ) -> Table:
        """Create operational performance section."""

        ops = dashboard_data.get("operations", {})
        trucks = ops.get("trucks", {})
        ships = ops.get("ships", {})
        tonnage = ops.get("tonnage", {})

        data = [
            ["Metric", "This Week", "Daily Average"],
            [
                "Trucks Processed",
                f"{trucks.get('total', 0):,}",
                f"{trucks.get('avg_per_day', 0):.1f}"
            ],
            [
                "Tonnage Handled",
                f"{tonnage.get('total', 0):,.0f} tons",
                f"{tonnage.get('avg_per_day', 0):.1f} tons/day"
            ],
            [
                "Ships Serviced",
                f"{ships.get('total', 0)}",
                f"{ships.get('total', 0) / 7:.1f}"
            ],
            [
                "Avg Processing Time",
                f"{trucks.get('avg_processing_time_hours', 0):.2f} hours",
                "-"
            ],
            [
                "Berth Utilization",
                f"{ops.get('berth_utilization_percent', 0):.1f}%",
                "-"
            ],
            [
                "Efficiency Score",
                f"{ops.get('efficiency_score', 0):.1f}/100",
                "-"
            ],
        ]

        table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        return table

    def _create_maintenance_section(
        self,
        dashboard_data: Dict[str, Any],
        styles
    ) -> Table:
        """Create maintenance and asset health section."""

        maint = dashboard_data.get("maintenance", {})
        asset_health = dashboard_data.get("asset_health", {})
        by_health = maint.get("assets_by_health", {})

        data = [
            ["Metric", "Value"],
            ["Average Asset Health Score", f"{maint.get('average_health_score', 0):.1f}/100"],
            ["Assets - Healthy (>70)", f"{by_health.get('healthy', 0)}"],
            ["Assets - Warning (40-70)", f"{by_health.get('warning', 0)}"],
            ["Assets - Critical (<40)", f"{by_health.get('critical', 0)}"],
            ["Total Alarms This Week", f"{maint.get('alarms', {}).get('total', 0)}"],
            ["Critical Alarms", f"{maint.get('alarms', {}).get('critical', 0)}"],
            ["Assets Needing Maintenance", f"{maint.get('maintenance_needed', 0)}"],
            ["Health Trend", maint.get("health_trend", "stable").upper()],
        ]

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        return table

    def _create_risks_opportunities_section(
        self,
        dashboard_data: Dict[str, Any],
        styles
    ) -> List:
        """Create risks and opportunities section."""

        elements = []

        # Risks
        risks = dashboard_data.get("risks", [])[:5]  # Top 5 risks
        if risks:
            risk_data = [["Top Risks", "Severity", "Mitigation"]]
            for risk in risks:
                risk_data.append([
                    Paragraph(risk.get("description", ""), styles['Normal']),
                    risk.get("severity", "").upper(),
                    Paragraph(risk.get("mitigation", ""), styles['Normal'])
                ])

            risk_table = Table(risk_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
            risk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(risk_table)
            elements.append(Spacer(1, 0.3*inch))

        # Opportunities
        opportunities = dashboard_data.get("opportunities", [])[:5]
        if opportunities:
            opp_data = [["Opportunities", "Benefit"]]
            for opp in opportunities:
                opp_data.append([
                    Paragraph(opp.get("description", ""), styles['Normal']),
                    Paragraph(opp.get("benefit", ""), styles['Normal'])
                ])

            opp_table = Table(opp_data, colWidths=[3*inch, 3*inch])
            opp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(opp_table)

        return elements

    def _create_recommendations_section(
        self,
        dashboard_data: Dict[str, Any],
        roi_data: Dict[str, Any],
        styles
    ) -> List:
        """Create strategic recommendations section."""

        elements = []

        recommendations = self._generate_recommendations(dashboard_data, roi_data)

        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"<b>{i}. {rec['title']}</b>", styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(rec['description'], styles['Normal']))
            elements.append(Spacer(1, 0.15*inch))

        return elements

    def _generate_recommendations(
        self,
        dashboard_data: Dict[str, Any],
        roi_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate strategic recommendations based on data."""

        recommendations = []

        # Check critical assets
        maint = dashboard_data.get("maintenance", {})
        critical_count = maint.get("assets_by_health", {}).get("critical", 0)

        if critical_count > 0:
            recommendations.append({
                "title": "Immediate: Address Critical Assets",
                "description": f"{critical_count} assets have critical health scores (<40). "
                              "Schedule immediate preventive maintenance to avoid costly unplanned downtime. "
                              f"Estimated cost of inaction: ${critical_count * 25000:,}"
            })

        # Check berth utilization
        ops = dashboard_data.get("operations", {})
        berth_util = ops.get("berth_utilization_percent", 0)

        if berth_util < 60:
            recommendations.append({
                "title": "Opportunity: Increase Berth Utilization",
                "description": f"Current berth utilization at {berth_util:.1f}%. "
                              "Sales opportunity: terminal can handle 40% more volume without "
                              "infrastructure investment. Estimated additional revenue: $2M annually."
            })

        # Check ROI performance
        total_savings = roi_data.get("total_savings", 0)
        if total_savings > 50000:
            recommendations.append({
                "title": "Continue Current Strategy",
                "description": f"OptiFlow AI generated ${total_savings:,} in savings this week. "
                              "Current predictive maintenance and optimization strategies are highly effective. "
                              "Maintain current approach."
            })

        # Check maintenance trend
        trend = maint.get("health_trend", "stable")
        if trend == "declining":
            recommendations.append({
                "title": "Alert: Asset Health Declining",
                "description": "Average asset health is trending downward. Review maintenance schedules "
                              "and consider increasing preventive maintenance frequency for critical assets."
            })

        # Check opportunities
        opportunities = dashboard_data.get("opportunities", [])
        if len(opportunities) > 0:
            opp = opportunities[0]
            if opp.get("opportunity_type") == "maintenance_window":
                recommendations.append({
                    "title": "Optimize: Maintenance Windows Available",
                    "description": f"Identified {len(opportunities)} low-impact maintenance windows. "
                                  "Schedule preventive maintenance during these periods to minimize "
                                  "operational disruption."
                })

        return recommendations[:5]  # Top 5 recommendations

    async def get_weekly_summary_data(
        self,
        site_id: int,
        week_start_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get weekly summary data in JSON format (for API/web display).

        Args:
            site_id: Site identifier
            week_start_date: Start of week

        Returns:
            Weekly summary data
        """
        try:
            if not week_start_date:
                today = datetime.utcnow().date()
                days_since_monday = today.weekday()
                week_start_date = today - timedelta(days=days_since_monday)

            week_end_date = week_start_date + timedelta(days=6)

            # Gather data
            dashboard_data = await self.dashboard_service.get_dashboard_360(site_id, period_days=7)
            roi_data = await self.roi_service.calculate_roi(site_id, period_days=7)

            return {
                "status": "success",
                "site_id": site_id,
                "week_start": week_start_date.isoformat(),
                "week_end": week_end_date.isoformat(),
                "generated_at": datetime.utcnow().isoformat(),

                # Summary
                "overall_health": dashboard_data.get("overall_health_score", {}),
                "total_savings": roi_data.get("total_savings", 0),
                "annual_projection": roi_data.get("annual_projection", 0),

                # KPIs
                "operations": dashboard_data.get("operations", {}),
                "maintenance": dashboard_data.get("maintenance", {}),

                # Financial
                "roi_breakdown": {
                    "predictive_maintenance": roi_data.get("predictive_maintenance", {}),
                    "optimization": roi_data.get("optimization", {}),
                    "efficiency": roi_data.get("efficiency", {}),
                    "downtime_avoided": roi_data.get("downtime_avoided", {})
                },

                # Insights
                "top_risks": dashboard_data.get("risks", [])[:5],
                "top_opportunities": dashboard_data.get("opportunities", [])[:5],
                "recommendations": self._generate_recommendations(dashboard_data, roi_data),

                # Highlights
                "highlights": roi_data.get("highlights", [])
            }

        except Exception as e:
            logger.error(f"Error generating weekly summary: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}
