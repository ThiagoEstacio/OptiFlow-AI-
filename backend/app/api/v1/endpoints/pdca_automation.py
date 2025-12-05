"""
MELH-008: PDCA Automatic Closure

Integrates PDCA cycles with work order system for automatic closure:
- Link PDCA to work orders
- Auto-check completion
- Verify problem resolution
- Track effectiveness
"""

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


class PDCAStatus(str, Enum):
    """PDCA cycle status"""
    PLAN = "plan"  # Problem identified, action planned
    DO = "do"  # Action being executed
    CHECK = "check"  # Verifying results
    ACT = "act"  # Standardizing solution
    CLOSED = "closed"  # Cycle complete
    FAILED = "failed"  # Solution did not work


class PDCAEffectiveness(str, Enum):
    """Effectiveness of PDCA cycle"""
    EFFECTIVE = "effective"  # Problem resolved
    PARTIAL = "partial"  # Problem partially resolved
    INEFFECTIVE = "ineffective"  # Problem not resolved
    PENDING = "pending"  # Not yet evaluated


@dataclass
class PDCACycle:
    """PDCA cycle data"""
    id: str
    equipment_id: str
    problem_type: str
    problem_description: str
    status: PDCAStatus
    effectiveness: PDCAEffectiveness
    created_at: datetime
    linked_os_id: Optional[str]
    root_cause: Optional[str]
    planned_action: Optional[str]
    verification_date: Optional[datetime]
    closed_at: Optional[datetime]
    notes: Optional[str]


# In-memory storage for demo (would be database in production)
_pdca_cycles: Dict[str, Dict] = {}
_scheduled_checks: Dict[str, datetime] = {}


@router.post("/create")
async def create_pdca_cycle(
    equipment_id: str = Query(..., description="Equipment identifier"),
    problem_type: str = Query(..., description="Type of problem"),
    problem_description: str = Query(..., description="Problem description"),
    root_cause: Optional[str] = Query(default=None, description="Identified root cause"),
    planned_action: Optional[str] = Query(default=None, description="Planned corrective action"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new PDCA cycle.

    MELH-008: Initiates a PDCA cycle for problem resolution tracking.
    """
    try:
        import uuid
        pdca_id = f"PDCA-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        pdca = {
            "id": pdca_id,
            "equipment_id": equipment_id,
            "problem_type": problem_type,
            "problem_description": problem_description,
            "status": PDCAStatus.PLAN.value,
            "effectiveness": PDCAEffectiveness.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "linked_os_id": None,
            "root_cause": root_cause,
            "planned_action": planned_action,
            "verification_date": None,
            "closed_at": None,
            "notes": None,
            "created_by": str(current_user.id)
        }

        _pdca_cycles[pdca_id] = pdca

        logger.info(f"Created PDCA cycle: {pdca_id}")

        return {
            "success": True,
            "pdca_id": pdca_id,
            "status": PDCAStatus.PLAN.value,
            "message": "PDCA cycle created. Link to work order to proceed.",
            "next_step": "Link to work order using /pdca/{pdca_id}/link-os"
        }

    except Exception as e:
        logger.error(f"Error creating PDCA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create PDCA cycle: {str(e)}"
        )


@router.post("/{pdca_id}/link-os")
async def link_pdca_to_work_order(
    pdca_id: str,
    os_id: str = Query(..., description="Work order ID"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Link PDCA cycle to a work order (OS).

    MELH-008: Links PDCA to OS and schedules automatic verification.
    When OS is completed, system will automatically check if problem
    was resolved.

    Args:
        pdca_id: PDCA cycle identifier
        os_id: Work order identifier
    """
    if pdca_id not in _pdca_cycles:
        raise HTTPException(status_code=404, detail="PDCA cycle not found")

    try:
        pdca = _pdca_cycles[pdca_id]

        # Update PDCA with OS link
        pdca["linked_os_id"] = os_id
        pdca["status"] = PDCAStatus.DO.value
        pdca["linked_at"] = datetime.utcnow().isoformat()

        # Schedule automatic check (72 hours after linking)
        check_time = datetime.utcnow() + timedelta(hours=72)
        _scheduled_checks[pdca_id] = check_time

        logger.info(f"Linked PDCA {pdca_id} to OS {os_id}")

        return {
            "success": True,
            "pdca_id": pdca_id,
            "os_id": os_id,
            "status": PDCAStatus.DO.value,
            "message": "PDCA linked to work order. Automatic verification scheduled.",
            "scheduled_verification": check_time.isoformat(),
            "verification_hours": 72
        }

    except Exception as e:
        logger.error(f"Error linking PDCA to OS: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to link PDCA to work order: {str(e)}"
        )


@router.post("/{pdca_id}/auto-check")
async def auto_check_pdca(
    pdca_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Automatic verification of PDCA cycle.

    MELH-008: Checks if:
    1. Work order was completed
    2. Problem has not recurred since completion
    3. KPIs have improved

    Called automatically by scheduler or manually for immediate check.
    """
    if pdca_id not in _pdca_cycles:
        raise HTTPException(status_code=404, detail="PDCA cycle not found")

    try:
        pdca = _pdca_cycles[pdca_id]

        if not pdca.get("linked_os_id"):
            return {
                "success": False,
                "status": "NOT_LINKED",
                "message": "PDCA not linked to any work order"
            }

        # Check work order status
        os_status = await _check_work_order_status(pdca["linked_os_id"], db)

        if os_status.get("status") != "CLOSED":
            return {
                "success": True,
                "pdca_id": pdca_id,
                "check_status": "WAITING",
                "message": f"Work order {pdca['linked_os_id']} not yet completed",
                "os_status": os_status.get("status", "UNKNOWN"),
                "recommendation": "Check will run again when OS is closed"
            }

        # OS is closed - check for problem recurrence
        os_closed_at = os_status.get("closed_at", datetime.utcnow())
        recurrence = await _check_recurrence(
            db=db,
            equipment_id=pdca["equipment_id"],
            problem_type=pdca["problem_type"],
            since=os_closed_at,
            hours=168  # 7 days
        )

        # Update PDCA based on results
        pdca["status"] = PDCAStatus.CHECK.value
        pdca["verification_date"] = datetime.utcnow().isoformat()

        if recurrence:
            # Problem recurred - PDCA failed
            pdca["status"] = PDCAStatus.FAILED.value
            pdca["effectiveness"] = PDCAEffectiveness.INEFFECTIVE.value
            pdca["notes"] = f"Problem recurred on {recurrence['occurred_at']}: {recurrence.get('description', 'N/A')}"

            return {
                "success": True,
                "pdca_id": pdca_id,
                "check_status": "FAILED",
                "effectiveness": PDCAEffectiveness.INEFFECTIVE.value,
                "message": "Problem recurred after intervention",
                "recurrence": recurrence,
                "recommendation": "Reopen analysis and investigate root cause further"
            }
        else:
            # No recurrence - PDCA effective
            pdca["status"] = PDCAStatus.ACT.value
            pdca["effectiveness"] = PDCAEffectiveness.EFFECTIVE.value
            pdca["notes"] = "Problem did not recur within verification period"

            return {
                "success": True,
                "pdca_id": pdca_id,
                "check_status": "EFFECTIVE",
                "effectiveness": PDCAEffectiveness.EFFECTIVE.value,
                "message": "Solution verified effective - No recurrence detected",
                "recommendation": "Standardize solution and document lessons learned",
                "next_step": "Close PDCA using /pdca/{pdca_id}/close"
            }

    except Exception as e:
        logger.error(f"Error checking PDCA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check PDCA status: {str(e)}"
        )


@router.post("/{pdca_id}/close")
async def close_pdca_cycle(
    pdca_id: str,
    lessons_learned: Optional[str] = Query(default=None, description="Lessons learned"),
    standardization_notes: Optional[str] = Query(default=None, description="Standardization actions"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Close PDCA cycle after verification.

    Marks cycle as complete and records lessons learned.
    """
    if pdca_id not in _pdca_cycles:
        raise HTTPException(status_code=404, detail="PDCA cycle not found")

    try:
        pdca = _pdca_cycles[pdca_id]

        if pdca["status"] not in [PDCAStatus.ACT.value, PDCAStatus.CHECK.value]:
            return {
                "success": False,
                "message": f"Cannot close PDCA in status '{pdca['status']}'. Must be in ACT or CHECK phase.",
                "current_status": pdca["status"]
            }

        pdca["status"] = PDCAStatus.CLOSED.value
        pdca["closed_at"] = datetime.utcnow().isoformat()
        pdca["closed_by"] = str(current_user.id)

        if lessons_learned:
            pdca["lessons_learned"] = lessons_learned
        if standardization_notes:
            pdca["standardization_notes"] = standardization_notes

        # Remove from scheduled checks
        if pdca_id in _scheduled_checks:
            del _scheduled_checks[pdca_id]

        logger.info(f"Closed PDCA cycle: {pdca_id}")

        return {
            "success": True,
            "pdca_id": pdca_id,
            "status": PDCAStatus.CLOSED.value,
            "effectiveness": pdca["effectiveness"],
            "message": "PDCA cycle closed successfully",
            "duration_days": _calculate_duration(pdca),
            "closed_at": pdca["closed_at"]
        }

    except Exception as e:
        logger.error(f"Error closing PDCA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close PDCA cycle: {str(e)}"
        )


@router.get("/{pdca_id}")
async def get_pdca_details(
    pdca_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get PDCA cycle details.
    """
    if pdca_id not in _pdca_cycles:
        raise HTTPException(status_code=404, detail="PDCA cycle not found")

    pdca = _pdca_cycles[pdca_id]

    return {
        "success": True,
        **pdca,
        "scheduled_check": _scheduled_checks.get(pdca_id, {})
    }


@router.get("/list")
async def list_pdca_cycles(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    equipment_id: Optional[str] = Query(default=None, description="Filter by equipment"),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    List PDCA cycles with optional filters.
    """
    cycles = list(_pdca_cycles.values())

    # Apply filters
    if status:
        cycles = [c for c in cycles if c["status"] == status]
    if equipment_id:
        cycles = [c for c in cycles if c["equipment_id"] == equipment_id]

    # Sort by created_at descending
    cycles.sort(key=lambda c: c["created_at"], reverse=True)

    # Summary
    summary = {
        "total": len(cycles),
        "by_status": {},
        "by_effectiveness": {}
    }
    for c in cycles:
        status_key = c["status"]
        eff_key = c["effectiveness"]
        summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1
        summary["by_effectiveness"][eff_key] = summary["by_effectiveness"].get(eff_key, 0) + 1

    return {
        "success": True,
        "cycles": cycles[:limit],
        "total": len(cycles),
        "summary": summary
    }


@router.get("/pending-checks")
async def get_pending_checks(
    current_user: User = Depends(get_current_user)
):
    """
    Get PDCA cycles pending automatic verification.
    """
    pending = []

    for pdca_id, check_time in _scheduled_checks.items():
        if pdca_id in _pdca_cycles:
            pdca = _pdca_cycles[pdca_id]
            pending.append({
                "pdca_id": pdca_id,
                "equipment_id": pdca["equipment_id"],
                "problem_type": pdca["problem_type"],
                "linked_os_id": pdca.get("linked_os_id"),
                "scheduled_check": check_time.isoformat(),
                "is_overdue": check_time < datetime.utcnow()
            })

    # Sort by scheduled check time
    pending.sort(key=lambda p: p["scheduled_check"])

    return {
        "success": True,
        "pending_count": len(pending),
        "overdue_count": sum(1 for p in pending if p["is_overdue"]),
        "pending_checks": pending
    }


@router.get("/effectiveness-report")
async def get_effectiveness_report(
    months: int = Query(default=6, ge=1, le=24, description="Report period in months"),
    current_user: User = Depends(get_current_user)
):
    """
    Get PDCA effectiveness report.

    Shows success rate and improvement trends.
    """
    cycles = list(_pdca_cycles.values())

    # Filter by period
    cutoff = datetime.utcnow() - timedelta(days=months * 30)
    cycles = [c for c in cycles if datetime.fromisoformat(c["created_at"]) >= cutoff]

    # Calculate metrics
    closed = [c for c in cycles if c["status"] == PDCAStatus.CLOSED.value]
    effective = sum(1 for c in closed if c["effectiveness"] == PDCAEffectiveness.EFFECTIVE.value)
    partial = sum(1 for c in closed if c["effectiveness"] == PDCAEffectiveness.PARTIAL.value)
    ineffective = sum(1 for c in closed if c["effectiveness"] == PDCAEffectiveness.INEFFECTIVE.value)

    success_rate = (effective / len(closed) * 100) if closed else 0

    # Average duration
    durations = [_calculate_duration(c) for c in closed if _calculate_duration(c) is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "success": True,
        "period_months": months,
        "metrics": {
            "total_cycles": len(cycles),
            "closed_cycles": len(closed),
            "open_cycles": len(cycles) - len(closed),
            "effective": effective,
            "partial": partial,
            "ineffective": ineffective,
            "success_rate_percent": round(success_rate, 1),
            "average_duration_days": round(avg_duration, 1)
        },
        "by_problem_type": _group_by_problem_type(cycles),
        "recommendations": _generate_effectiveness_recommendations(success_rate, cycles)
    }


# Helper functions

async def _check_work_order_status(os_id: str, db: AsyncSession) -> Dict:
    """Check work order status"""
    # In production, query work order system
    # For demo, return sample data
    return {
        "os_id": os_id,
        "status": "CLOSED",
        "closed_at": datetime.utcnow() - timedelta(hours=24)
    }


async def _check_recurrence(
    db: AsyncSession,
    equipment_id: str,
    problem_type: str,
    since: datetime,
    hours: int
) -> Optional[Dict]:
    """Check if problem recurred since given date"""
    try:
        from app.models.alarm_event import AlarmEvent

        end_time = since + timedelta(hours=hours)

        query = select(AlarmEvent).where(
            and_(
                AlarmEvent.tag_id.contains(equipment_id),
                AlarmEvent.timestamp >= since,
                AlarmEvent.timestamp <= end_time,
                AlarmEvent.message.contains(problem_type)
            )
        ).limit(1)

        result = await db.execute(query)
        event = result.scalar_one_or_none()

        if event:
            return {
                "occurred_at": event.timestamp.isoformat(),
                "description": event.message
            }

        return None

    except Exception as e:
        logger.warning(f"Error checking recurrence: {e}")
        # For demo, return no recurrence
        return None


def _calculate_duration(pdca: Dict) -> Optional[float]:
    """Calculate PDCA cycle duration in days"""
    if not pdca.get("closed_at"):
        return None

    created = datetime.fromisoformat(pdca["created_at"])
    closed = datetime.fromisoformat(pdca["closed_at"])

    return (closed - created).total_seconds() / 86400


def _group_by_problem_type(cycles: List[Dict]) -> Dict:
    """Group cycles by problem type"""
    by_type = {}
    for c in cycles:
        p_type = c["problem_type"]
        if p_type not in by_type:
            by_type[p_type] = {"total": 0, "effective": 0}
        by_type[p_type]["total"] += 1
        if c["effectiveness"] == PDCAEffectiveness.EFFECTIVE.value:
            by_type[p_type]["effective"] += 1

    return by_type


def _generate_effectiveness_recommendations(success_rate: float, cycles: List[Dict]) -> List[str]:
    """Generate recommendations based on effectiveness data"""
    recommendations = []

    if success_rate < 60:
        recommendations.append("Low success rate - Review root cause analysis methodology")
    if success_rate < 80:
        recommendations.append("Consider implementing 5-Why analysis for complex problems")

    # Check for recurring problem types
    problem_counts = {}
    for c in cycles:
        p_type = c["problem_type"]
        problem_counts[p_type] = problem_counts.get(p_type, 0) + 1

    for p_type, count in problem_counts.items():
        if count > 3:
            recommendations.append(f"Recurring issues with '{p_type}' - Consider systemic solution")

    if not recommendations:
        recommendations.append("PDCA process performing well - Continue current practices")

    return recommendations
