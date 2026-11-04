"""
Alert management routes for threshold breaches and civil defense notifications.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.alert_repository import AlertRepository
from src.repositories.station_repository import StationRepository
from src.api.schemas import AlertItem, AcknowledgeAlertRequest

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertItem])
def get_active_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieves all currently active flood alerts."""
    repo = AlertRepository(db)
    stn_repo = StationRepository(db)
    alerts = repo.get_active_alerts(limit=limit)

    result = []
    for a in alerts:
        stn = stn_repo.get_by_id(a.station_id)
        result.append(
            AlertItem(
                id=a.id,
                station_id=a.station_id,
                station_name=stn.station_name if stn else f"Station {a.station_id}",
                river=stn.river if stn else None,
                severity=a.severity,
                title=a.title,
                message=a.message,
                current_water_level=a.current_water_level,
                threshold_level=a.threshold_level,
                is_active=bool(a.is_active),
                is_acknowledged=bool(a.is_acknowledged),
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                acknowledged_by=a.acknowledged_by,
                created_at=a.created_at.isoformat() if a.created_at else "",
            )
        )
    return result


@router.get("/all", response_model=List[AlertItem])
def get_all_alerts(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieves alert history including acknowledged events."""
    repo = AlertRepository(db)
    stn_repo = StationRepository(db)
    alerts = repo.get_all(limit=limit)

    result = []
    for a in alerts:
        stn = stn_repo.get_by_id(a.station_id)
        result.append(
            AlertItem(
                id=a.id,
                station_id=a.station_id,
                station_name=stn.station_name if stn else f"Station {a.station_id}",
                river=stn.river if stn else None,
                severity=a.severity,
                title=a.title,
                message=a.message,
                current_water_level=a.current_water_level,
                threshold_level=a.threshold_level,
                is_active=bool(a.is_active),
                is_acknowledged=bool(a.is_acknowledged),
                acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                acknowledged_by=a.acknowledged_by,
                created_at=a.created_at.isoformat() if a.created_at else "",
            )
        )
    return result


@router.post("/{alert_id}/acknowledge", response_model=AlertItem)
def acknowledge_alert(
    alert_id: int = Path(..., ge=1, description="Alert identifier"),
    req: AcknowledgeAlertRequest = AcknowledgeAlertRequest(),
    db: Session = Depends(get_db),
):
    """Acknowledges an active flood alert, deactivating immediate siren flags."""
    repo = AlertRepository(db)
    alert = repo.acknowledge_alert(alert_id=alert_id, acknowledged_by=req.acknowledged_by)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert ID {alert_id} not found.")

    stn_repo = StationRepository(db)
    stn = stn_repo.get_by_id(alert.station_id)

    return AlertItem(
        id=alert.id,
        station_id=alert.station_id,
        station_name=stn.station_name if stn else f"Station {alert.station_id}",
        river=stn.river if stn else None,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        current_water_level=alert.current_water_level,
        threshold_level=alert.threshold_level,
        is_active=bool(alert.is_active),
        is_acknowledged=bool(alert.is_acknowledged),
        acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        acknowledged_by=alert.acknowledged_by,
        created_at=alert.created_at.isoformat() if alert.created_at else "",
    )
