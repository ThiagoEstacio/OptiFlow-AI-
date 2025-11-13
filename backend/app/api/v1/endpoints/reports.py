"""
Reports API Endpoints

Provides comprehensive report generation and export functionality:
- Operational reports (daily, weekly, monthly)
- Quality reports
- ML/Analytics reports
- Executive summaries
- Custom reports

Export formats: PDF, Excel, CSV
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
import logging
import os

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.report_generator import ReportGenerator
from app.services.advanced_report_generator import AdvancedReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ReportRequest(BaseModel):
    """Request model for report generation"""
    report_type: str = Field(..., description="Type of report: operational, quality, ml, executive, custom")
    start_date: Optional[date] = Field(None, description="Start date for report period")
    end_date: Optional[date] = Field(None, description="End date for report period")
    format: str = Field("pdf", description="Export format: pdf, excel, csv")
    filters: Optional[dict] = Field(None, description="Additional filters")


class ReportResponse(BaseModel):
    """Response model for report generation"""
    success: bool
    message: str
    report_id: Optional[str] = None
    filename: Optional[str] = None
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None


class ReportListItem(BaseModel):
    """List item model for available reports"""
    report_id: str
    report_type: str
    created_at: datetime
    filename: str
    format: str
    file_size_bytes: int


# ============================================================================
# REPORT TEMPLATES
# ============================================================================

@router.get("/templates", response_model=List[dict])
async def list_report_templates(
    current_user: User = Depends(get_current_user)
):
    """
    List all available report templates

    Returns pre-configured report types that can be generated
    """
    templates = [
        {
            "id": "operational_daily",
            "name": "Relatório Operacional Diário",
            "description": "Resumo completo das operações do dia",
            "formats": ["pdf", "excel", "csv"],
            "parameters": ["date"],
            "estimated_time": "30s"
        },
        {
            "id": "operational_weekly",
            "name": "Relatório Operacional Semanal",
            "description": "Análise consolidada da semana",
            "formats": ["pdf", "excel"],
            "parameters": ["week_start_date"],
            "estimated_time": "1min"
        },
        {
            "id": "quality_analysis",
            "name": "Análise de Qualidade",
            "description": "Métricas de qualidade, defeitos e tendências",
            "formats": ["pdf", "excel"],
            "parameters": ["start_date", "end_date"],
            "estimated_time": "45s"
        },
        {
            "id": "ml_performance",
            "name": "Performance de Modelos ML",
            "description": "Acurácia, previsões e insights dos modelos",
            "formats": ["pdf", "excel"],
            "parameters": ["model_ids"],
            "estimated_time": "30s"
        },
        {
            "id": "executive_summary",
            "name": "Sumário Executivo",
            "description": "Visão geral para tomada de decisão",
            "formats": ["pdf"],
            "parameters": ["period"],
            "estimated_time": "1min"
        },
        {
            "id": "alarm_history",
            "name": "Histórico de Alarmes",
            "description": "Alarmes acionados, duração e resolução",
            "formats": ["pdf", "excel", "csv"],
            "parameters": ["start_date", "end_date", "severity"],
            "estimated_time": "30s"
        },
        {
            "id": "equipment_performance",
            "name": "Performance de Equipamentos",
            "description": "Eficiência, disponibilidade e manutenções",
            "formats": ["pdf", "excel"],
            "parameters": ["equipment_ids", "date_range"],
            "estimated_time": "45s"
        },
        {
            "id": "energy_consumption",
            "name": "Consumo de Energia",
            "description": "Análise detalhada de consumo e eficiência energética",
            "formats": ["pdf", "excel"],
            "parameters": ["start_date", "end_date"],
            "estimated_time": "40s"
        }
    ]

    return templates


# ============================================================================
# REPORT GENERATION
# ============================================================================

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a report based on specified type and parameters

    Reports are generated asynchronously and can be downloaded when ready
    """
    try:
        logger.info(f"Generating {request.report_type} report in {request.format} format")

        # Validate dates
        if request.start_date and request.end_date:
            if request.end_date < request.start_date:
                raise HTTPException(status_code=400, detail="end_date must be after start_date")

        # Use advanced report generator
        generator = AdvancedReportGenerator(db)

        # Generate report synchronously for now (can be backgrounded)
        if request.report_type == "operational_daily":
            report_date = request.start_date or date.today()

            if request.format == "pdf":
                filename = await generator.generate_operational_report_pdf(
                    site_id=str(current_user.organization_id),
                    report_date=report_date
                )
            elif request.format == "excel":
                filename = await generator.generate_operational_report_excel(
                    site_id=str(current_user.organization_id),
                    start_date=report_date,
                    end_date=report_date
                )
            elif request.format == "csv":
                filename = await generator.generate_operational_report_csv(
                    site_id=str(current_user.organization_id),
                    start_date=report_date,
                    end_date=report_date
                )
            else:
                raise HTTPException(status_code=400, detail=f"Format '{request.format}' not supported")

        elif request.report_type == "quality_analysis":
            start_date = request.start_date or date.today() - timedelta(days=30)
            end_date = request.end_date or date.today()

            filename = await generator.generate_quality_report(
                site_id=str(current_user.organization_id),
                start_date=start_date,
                end_date=end_date,
                format=request.format
            )

        elif request.report_type == "ml_performance":
            filename = await generator.generate_ml_report(
                format=request.format
            )

        elif request.report_type == "alarm_history":
            start_date = request.start_date or date.today() - timedelta(days=7)
            end_date = request.end_date or date.today()

            filename = await generator.generate_alarm_report(
                start_date=start_date,
                end_date=end_date,
                format=request.format,
                severity=request.filters.get("severity") if request.filters else None
            )

        elif request.report_type == "executive_summary":
            period = request.filters.get("period", "monthly") if request.filters else "monthly"

            filename = await generator.generate_executive_report(
                period=period,
                format=request.format
            )

        else:
            raise HTTPException(status_code=400, detail=f"Report type '{request.report_type}' not supported")

        # Get file info
        filepath = generator.get_report_path(filename)
        file_size = os.path.getsize(filepath)

        return ReportResponse(
            success=True,
            message="Relatório gerado com sucesso",
            report_id=filename.split('.')[0],
            filename=filename,
            download_url=f"/api/v1/reports/download/{filename}",
            file_size_bytes=file_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")


# ============================================================================
# REPORT DOWNLOAD
# ============================================================================

@router.get("/download/{filename}")
async def download_report(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download a generated report file

    Returns the file for download with appropriate content-type
    """
    try:
        generator = AdvancedReportGenerator(None)
        filepath = generator.get_report_path(filename)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        # Determine media type
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.xlsx'):
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            media_type = 'text/csv'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            filepath,
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")


# ============================================================================
# REPORT HISTORY
# ============================================================================

@router.get("/history", response_model=List[ReportListItem])
async def list_report_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    List recently generated reports

    Returns metadata about generated reports available for download
    """
    try:
        generator = AdvancedReportGenerator(None)
        reports_dir = generator.reports_dir

        if not os.path.exists(reports_dir):
            return []

        # List files
        files = []
        for filename in os.listdir(reports_dir):
            filepath = os.path.join(reports_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "size": stat.st_size
                })

        # Sort by creation time (newest first)
        files.sort(key=lambda x: x['created_at'], reverse=True)

        # Build response
        reports = []
        for file in files[:limit]:
            # Extract report type from filename
            report_type = "unknown"
            if "operational" in file["filename"]:
                report_type = "operational"
            elif "quality" in file["filename"]:
                report_type = "quality"
            elif "ml" in file["filename"]:
                report_type = "ml"
            elif "alarm" in file["filename"]:
                report_type = "alarm"
            elif "executive" in file["filename"]:
                report_type = "executive"

            # Extract format from extension
            format = file["filename"].split('.')[-1]

            reports.append(ReportListItem(
                report_id=file["filename"].split('.')[0],
                report_type=report_type,
                created_at=file["created_at"],
                filename=file["filename"],
                format=format,
                file_size_bytes=file["size"]
            ))

        return reports

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar relatórios: {str(e)}")


# ============================================================================
# DELETE REPORT
# ============================================================================

@router.delete("/{filename}")
async def delete_report(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a generated report file
    """
    try:
        generator = AdvancedReportGenerator(None)
        filepath = generator.get_report_path(filename)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")

        os.remove(filepath)

        return {"success": True, "message": "Relatório deletado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar relatório: {str(e)}")


# ============================================================================
# DASHBOARD EXPORT
# ============================================================================

class DashboardExportRequest(BaseModel):
    """Request model for dashboard export"""
    dashboard_id: str = Field(..., description="Dashboard unique identifier")
    dashboard_name: str = Field(..., description="Dashboard name/title")
    format: str = Field("pdf", description="Export format: pdf, excel")
    widgets: List[dict] = Field(..., description="List of widget data to include in report")


@router.post("/export-dashboard", response_model=ReportResponse)
async def export_dashboard(
    request: DashboardExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a dashboard as a report

    Takes dashboard configuration and widget data and generates a PDF or Excel report
    containing all widgets and their current data.

    Widget data format:
    ```json
    {
        "title": "Widget Title",
        "type": "metric|chart|table|status",
        "value": "123",  // For metric widgets
        "trend": "+5.2%",  // For metric widgets
        "unit": "kWh",  // For metric widgets
        "data": [...],  // For chart/table widgets
        "headers": [...],  // For table widgets
        "status": "ok|warning|error",  // For status widgets
        "message": "Status message"  // For status widgets
    }
    ```
    """
    try:
        logger.info(f"Exporting dashboard '{request.dashboard_name}' in {request.format} format")

        # Validate format
        if request.format not in ['pdf', 'excel']:
            raise HTTPException(status_code=400, detail=f"Format '{request.format}' not supported for dashboard export")

        # Use advanced report generator
        generator = AdvancedReportGenerator(db)

        # Get user name for report metadata
        user_name = f"{current_user.email}"

        # Generate report based on format
        if request.format == 'pdf':
            filename = await generator.generate_dashboard_report_pdf(
                dashboard_id=request.dashboard_id,
                dashboard_name=request.dashboard_name,
                widgets_data=request.widgets,
                user_name=user_name
            )
        elif request.format == 'excel':
            filename = await generator.generate_dashboard_report_excel(
                dashboard_id=request.dashboard_id,
                dashboard_name=request.dashboard_name,
                widgets_data=request.widgets,
                user_name=user_name
            )
        else:
            raise HTTPException(status_code=400, detail=f"Format '{request.format}' not supported")

        # Get file info
        filepath = generator.get_report_path(filename)
        file_size = os.path.getsize(filepath)

        return ReportResponse(
            success=True,
            message=f"Dashboard exportado com sucesso como {request.format.upper()}",
            report_id=f"dashboard_{request.dashboard_id}",
            filename=filename,
            download_url=f"/api/v1/reports/download/{filename}",
            file_size_bytes=file_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao exportar dashboard: {str(e)}")
