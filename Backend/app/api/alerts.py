"""
Alerts API Endpoints
Manages agricultural alerts, notifications, and warning systems.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.schemas.alert_schema import AlertCreate, AlertResponse, AlertUpdate
from app.models.alert import Alert
from app.services.sms_service import SMSService
from app.services.websocket_service import WebSocketService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new alert for weather, pest, or market conditions.
    """
    try:
        # Create alert record
        db_alert = Alert(
            user_id=alert.user_id,
            type=alert.type,
            condition=alert.condition,
            threshold=alert.threshold,
            location=alert.location,
            crop_type=alert.crop_type,
            is_active=True,
            notification_methods=alert.notification_methods
        )
        
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        # Send confirmation notification
        if "sms" in alert.notification_methods:
            background_tasks.add_task(
                send_alert_confirmation_sms,
                db_alert.id,
                alert.user_id
            )
        
        logger.info(f"Alert created for user {alert.user_id}: {alert.type}")
        
        return AlertResponse.from_orm(db_alert)
        
    except Exception as e:
        logger.error(f"Failed to create alert: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create alert"
        )


@router.get("/alerts/{user_id}", response_model=List[AlertResponse])
async def get_user_alerts(
    user_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all alerts for a specific user.
    """
    try:
        query = db.query(Alert).filter(Alert.user_id == user_id)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        alerts = query.all()
        
        return [AlertResponse.from_orm(alert) for alert in alerts]
        
    except Exception as e:
        logger.error(f"Failed to get alerts for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve alerts"
        )


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing alert.
    """
    try:
        db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update fields
        for field, value in alert_update.dict(exclude_unset=True).items():
            setattr(db_alert, field, value)
        
        db.commit()
        db.refresh(db_alert)
        
        logger.info(f"Alert {alert_id} updated")
        
        return AlertResponse.from_orm(db_alert)
        
    except Exception as e:
        logger.error(f"Failed to update alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update alert"
        )


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an alert.
    """
    try:
        db_alert = db.query(Alert).filter(Alert.id == alert_id).first()
        
        if not db_alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        db.delete(db_alert)
        db.commit()
        
        logger.info(f"Alert {alert_id} deleted")
        
        return {"message": "Alert deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete alert"
        )


@router.post("/alerts/check")
async def check_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Check all active alerts and trigger notifications if conditions are met.
    This endpoint is typically called by a scheduler.
    """
    try:
        active_alerts = db.query(Alert).filter(Alert.is_active == True).all()
        
        triggered_alerts = []
        
        for alert in active_alerts:
            is_triggered = await evaluate_alert_condition(alert)
            
            if is_triggered:
                triggered_alerts.append(alert.id)
                
                # Send notifications
                background_tasks.add_task(
                    send_alert_notifications,
                    alert.id,
                    alert.user_id,
                    alert.notification_methods
                )
        
        logger.info(f"Checked {len(active_alerts)} alerts, triggered {len(triggered_alerts)}")
        
        return {
            "checked_alerts": len(active_alerts),
            "triggered_alerts": len(triggered_alerts),
            "triggered_alert_ids": triggered_alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to check alerts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check alerts"
        )


@router.get("/alerts/history/{user_id}")
async def get_alert_history(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get alert trigger history for a user.
    """
    try:
        # This would typically query an alert_history table
        # For now, we'll return triggered alerts
        alerts = db.query(Alert).filter(
            Alert.user_id == user_id,
            Alert.last_triggered.isnot(None)
        ).order_by(Alert.last_triggered.desc()).offset(offset).limit(limit).all()
        
        return {
            "history": [
                {
                    "alert_id": alert.id,
                    "type": alert.type,
                    "condition": alert.condition,
                    "triggered_at": alert.last_triggered,
                    "location": alert.location,
                    "crop_type": alert.crop_type
                }
                for alert in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get alert history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve alert history"
        )


async def evaluate_alert_condition(alert: Alert) -> bool:
    """
    Evaluate if an alert condition is met.
    """
    try:
        # This would implement the actual condition checking logic
        # based on the alert type and current data
        
        if alert.type == "weather":
            # Check weather conditions
            return await check_weather_alert(alert)
        elif alert.type == "pest":
            # Check pest/disease conditions
            return await check_pest_alert(alert)
        elif alert.type == "market":
            # Check market conditions
            return await check_market_alert(alert)
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to evaluate alert condition: {str(e)}")
        return False


async def check_weather_alert(alert: Alert) -> bool:
    """Check weather-based alert conditions."""
    # Implementation would check current weather against thresholds
    return False


async def check_pest_alert(alert: Alert) -> bool:
    """Check pest/disease alert conditions."""
    # Implementation would check pest risk levels
    return False


async def check_market_alert(alert: Alert) -> bool:
    """Check market-based alert conditions."""
    # Implementation would check price movements
    return False


async def send_alert_confirmation_sms(alert_id: int, user_id: int):
    """Send SMS confirmation for alert creation."""
    try:
        sms_service = SMSService()
        await sms_service.send_alert_confirmation(alert_id, user_id)
    except Exception as e:
        logger.error(f"Failed to send alert confirmation SMS: {str(e)}")


async def send_alert_notifications(alert_id: int, user_id: int, methods: List[str]):
    """Send alert notifications via configured methods."""
    try:
        if "sms" in methods:
            sms_service = SMSService()
            await sms_service.send_alert_notification(alert_id, user_id)
        
        if "websocket" in methods:
            ws_service = WebSocketService()
            await ws_service.send_alert_notification(alert_id, user_id)
            
    except Exception as e:
        logger.error(f"Failed to send alert notifications: {str(e)}")