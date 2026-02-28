"""
API Endpoints Module

This module defines the REST API routes for the Smart Pharma AI Service.
All endpoints are prefixed with /ai to distinguish AI-powered features
from standard CRUD operations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schema import (
    FEFOStrategyResponse,
    ExpiryAlertsResponse,
    ErrorResponse
)
from app.services.fefo_engine import (
    get_fefo_strategy,
    get_expiry_alerts,
    update_expired_batch_status,
    EXPIRY_ALERT_WINDOW_DAYS
)


# Create API router with prefix and tags
router = APIRouter(
    prefix="/ai",
    tags=["AI Services"],
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)


@router.get(
    "/fefo-strategy/{product_id}",
    response_model=FEFOStrategyResponse,
    summary="Get FEFO Strategy for Product",
    description="""
    Retrieve the FEFO (First Expired, First Out) prioritized batch list 
    for a specific product.
    
    The response includes:
    - Product information
    - Total available quantity across all valid batches
    - List of batches sorted by expiry date (earliest first)
    - Priority level for each batch (CRITICAL, WARNING, SAFE)
    
    **Priority Levels:**
    - CRITICAL: Expires in < 15 days
    - WARNING: Expires in 15-45 days  
    - SAFE: Expires in > 45 days
    
    **Filtering:**
    - Excludes batches with zero quantity
    - Excludes already expired batches
    - Only includes ACTIVE status batches
    """
)
async def get_product_fefo_strategy(
    product_id: int,
    db: Session = Depends(get_db)
) -> FEFOStrategyResponse:
    """
    Get FEFO-prioritized batch list for a specific product.
    
    Args:
        product_id: The ID of the product to analyze.
        db: Database session (injected).
        
    Returns:
        FEFOStrategyResponse: Product info with prioritized batch list.
        
    Raises:
        HTTPException 404: If product is not found.
    """
    result = get_fefo_strategy(db, product_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return result


@router.get(
    "/expiry-alerts",
    response_model=ExpiryAlertsResponse,
    summary="Get Expiry Alerts",
    description="""
    Retrieve all batches that will expire within the specified time window.
    
    The response includes:
    - Total number of alerts
    - Count of CRITICAL priority items
    - Count of WARNING priority items
    - List of all expiring batches with product details
    
    Results are sorted by expiry date (most urgent first).
    
    **Default alert window:** 30 days
    **Use cases:**
    - Daily review of expiring inventory
    - Planning promotional sales for near-expiry items
    - Compliance reporting
    """
)
async def get_all_expiry_alerts(
    alert_window_days: Optional[int] = Query(
        default=EXPIRY_ALERT_WINDOW_DAYS,
        ge=1,
        le=365,
        description="Number of days to look ahead for expiring items"
    ),
    db: Session = Depends(get_db)
) -> ExpiryAlertsResponse:
    """
    Get all batches expiring within the specified window.
    
    Args:
        alert_window_days: Days to look ahead (1-365). Default: 30.
        db: Database session (injected).
        
    Returns:
        ExpiryAlertsResponse: Summary and list of expiring batches.
    """
    return get_expiry_alerts(db, alert_window_days)


@router.post(
    "/maintenance/update-expired-status",
    summary="Update Expired Batch Status",
    description="""
    Maintenance endpoint to update status of expired batches.
    
    This endpoint scans all ACTIVE batches and marks those with
    past expiry dates as EXPIRED.
    
    **Note:** This is a maintenance operation. Consider running it
    via a scheduled job (cron) rather than manual API calls.
    """,
    responses={
        200: {
            "description": "Successfully updated expired batches",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Successfully updated 5 batches to EXPIRED status",
                        "updated_count": 5
                    }
                }
            }
        }
    }
)
async def update_expired_batches(
    db: Session = Depends(get_db)
) -> dict:
    """
    Update status of expired batches to EXPIRED.
    
    Args:
        db: Database session (injected).
        
    Returns:
        dict: Message and count of updated batches.
    """
    updated_count = update_expired_batch_status(db)
    
    return {
        "message": f"Successfully updated {updated_count} batches to EXPIRED status",
        "updated_count": updated_count
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Simple health check endpoint to verify service is running."
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        dict: Service status information.
    """
    return {
        "status": "healthy",
        "service": "Smart Pharma AI Service",
        "version": "1.0.0"
    }
