"""
FEFO Engine Module

This module implements the core FEFO (First Expired, First Out) business logic
for pharmaceutical inventory management. It provides functions to:
- Calculate batch priorities based on expiry dates
- Get prioritized batch lists for products
- Generate expiry alerts for the entire inventory

FEFO is critical in pharmaceutical industry to ensure products with
shorter shelf life are distributed first, minimizing waste and ensuring
patient safety.
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models import Product, Batch, BatchStatus
from app.schemas.schema import (
    PriorityLevel,
    FEFOBatchResponse,
    FEFOStrategyResponse,
    ExpiryAlertResponse,
    ExpiryAlertsResponse
)


# Priority level thresholds (in days)
CRITICAL_THRESHOLD_DAYS = 15
WARNING_THRESHOLD_DAYS = 45
EXPIRY_ALERT_WINDOW_DAYS = 30


def calculate_days_until_expiry(expiry_date: date) -> int:
    """
    Calculate the number of days from today until the expiry date.
    
    Args:
        expiry_date: The expiration date of the batch.
        
    Returns:
        int: Number of days until expiry. Negative if already expired.
        
    Example:
        >>> from datetime import date, timedelta
        >>> future_date = date.today() + timedelta(days=10)
        >>> calculate_days_until_expiry(future_date)
        10
    """
    today = date.today()
    delta = expiry_date - today
    return delta.days


def determine_priority_level(days_until_expiry: int) -> PriorityLevel:
    """
    Determine the FEFO priority level based on days until expiry.
    
    Priority levels are assigned as follows:
    - CRITICAL: Less than 15 days until expiry (urgent, sell immediately)
    - WARNING: Between 15 and 45 days (prioritize for sale)
    - SAFE: More than 45 days (normal handling)
    
    Args:
        days_until_expiry: Number of days until the batch expires.
        
    Returns:
        PriorityLevel: The calculated priority level.
        
    Example:
        >>> determine_priority_level(10)
        <PriorityLevel.CRITICAL: 'CRITICAL'>
        >>> determine_priority_level(30)
        <PriorityLevel.WARNING: 'WARNING'>
        >>> determine_priority_level(60)
        <PriorityLevel.SAFE: 'SAFE'>
    """
    if days_until_expiry < CRITICAL_THRESHOLD_DAYS:
        return PriorityLevel.CRITICAL
    elif days_until_expiry <= WARNING_THRESHOLD_DAYS:
        return PriorityLevel.WARNING
    else:
        return PriorityLevel.SAFE


def get_valid_batches_query(db: Session, product_id: Optional[int] = None):
    """
    Build a query for valid batches (not expired and quantity > 0).
    
    This is the core filtering logic for FEFO:
    1. Excludes batches with zero quantity (sold out)
    2. Excludes batches that have already expired (expiry_date < today)
    3. Only includes ACTIVE status batches
    
    Args:
        db: SQLAlchemy database session.
        product_id: Optional product ID to filter batches.
        
    Returns:
        Query: SQLAlchemy query object for valid batches.
    """
    today = date.today()
    
    query = db.query(Batch).filter(
        and_(
            Batch.quantity > 0,              # Must have stock
            Batch.expiry_date >= today,      # Must not be expired
            Batch.status == BatchStatus.ACTIVE.value  # Must be active status
        )
    )
    
    if product_id is not None:
        query = query.filter(Batch.product_id == product_id)
    
    return query


def get_fefo_strategy(db: Session, product_id: int) -> Optional[FEFOStrategyResponse]:
    """
    Get FEFO-prioritized batch list for a specific product.
    
    This function implements the complete FEFO strategy:
    1. Retrieves all valid batches for the product
    2. Filters out expired and zero-quantity batches
    3. Sorts by expiry date (ascending - earliest expiry first)
    4. Assigns priority levels based on days until expiry
    
    The returned list is ordered so that batches that should be
    sold first appear at the top.
    
    Args:
        db: SQLAlchemy database session.
        product_id: ID of the product to analyze.
        
    Returns:
        FEFOStrategyResponse: Contains product info and prioritized batch list.
        None: If product is not found.
        
    Example:
        >>> response = get_fefo_strategy(db, product_id=1)
        >>> if response:
        ...     for batch in response.batches:
        ...         print(f"{batch.batch_code}: {batch.priority_level}")
    """
    # First, verify the product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    # Get valid batches sorted by expiry date (FEFO order)
    valid_batches = get_valid_batches_query(db, product_id)\
        .order_by(Batch.expiry_date.asc())\
        .all()
    
    # Transform batches to response format with priority levels
    fefo_batches: List[FEFOBatchResponse] = []
    total_quantity = 0
    
    for batch in valid_batches:
        days_until_expiry = calculate_days_until_expiry(batch.expiry_date)
        priority_level = determine_priority_level(days_until_expiry)
        
        fefo_batch = FEFOBatchResponse(
            id=batch.id,
            product_id=batch.product_id,
            product_name=product.name,
            batch_code=batch.batch_code,
            expiry_date=batch.expiry_date,
            quantity=batch.quantity,
            days_until_expiry=days_until_expiry,
            priority_level=priority_level
        )
        fefo_batches.append(fefo_batch)
        total_quantity += batch.quantity
    
    return FEFOStrategyResponse(
        product_id=product.id,
        product_name=product.name,
        product_sku=product.sku,
        total_available_quantity=total_quantity,
        batches=fefo_batches
    )


def get_expiry_alerts(
    db: Session,
    alert_window_days: int = EXPIRY_ALERT_WINDOW_DAYS
) -> ExpiryAlertsResponse:
    """
    Get all batches that will expire within the specified alert window.
    
    This function scans the entire inventory and returns batches that:
    1. Have quantity > 0 (still in stock)
    2. Will expire within the alert window (default: 30 days)
    3. Are in ACTIVE status
    
    Results are sorted by expiry date (most urgent first).
    
    Args:
        db: SQLAlchemy database session.
        alert_window_days: Number of days to look ahead for expiring items.
                          Default is 30 days.
        
    Returns:
        ExpiryAlertsResponse: Contains summary counts and list of all alerts.
        
    Example:
        >>> alerts = get_expiry_alerts(db, alert_window_days=30)
        >>> print(f"Total alerts: {alerts.total_alerts}")
        >>> print(f"Critical: {alerts.critical_count}")
    """
    today = date.today()
    alert_cutoff_date = today + timedelta(days=alert_window_days)
    
    # Query batches that will expire within the alert window
    # Include batches expiring today or in the future (up to cutoff)
    expiring_batches = db.query(Batch).join(Product).filter(
        and_(
            Batch.quantity > 0,
            Batch.expiry_date >= today,
            Batch.expiry_date <= alert_cutoff_date,
            Batch.status == BatchStatus.ACTIVE.value
        )
    ).order_by(Batch.expiry_date.asc()).all()
    
    # Transform to response format and count priorities
    alerts: List[ExpiryAlertResponse] = []
    critical_count = 0
    warning_count = 0
    
    for batch in expiring_batches:
        # Get product info via relationship
        product = batch.product
        
        days_until_expiry = calculate_days_until_expiry(batch.expiry_date)
        priority_level = determine_priority_level(days_until_expiry)
        
        # Update priority counters
        if priority_level == PriorityLevel.CRITICAL:
            critical_count += 1
        elif priority_level == PriorityLevel.WARNING:
            warning_count += 1
        
        alert = ExpiryAlertResponse(
            id=batch.id,
            product_id=batch.product_id,
            product_name=product.name,
            product_sku=product.sku,
            batch_code=batch.batch_code,
            expiry_date=batch.expiry_date,
            quantity=batch.quantity,
            days_until_expiry=days_until_expiry,
            priority_level=priority_level
        )
        alerts.append(alert)
    
    return ExpiryAlertsResponse(
        total_alerts=len(alerts),
        critical_count=critical_count,
        warning_count=warning_count,
        alerts=alerts
    )


def update_expired_batch_status(db: Session) -> int:
    """
    Batch job to update status of expired batches.
    
    This function can be run periodically (e.g., daily via cron)
    to automatically mark expired batches as EXPIRED.
    
    Args:
        db: SQLAlchemy database session.
        
    Returns:
        int: Number of batches updated to EXPIRED status.
        
    Note:
        This function commits the transaction. Ensure proper
        error handling in the calling code.
    """
    today = date.today()
    
    # Find all active batches that have expired
    expired_batches = db.query(Batch).filter(
        and_(
            Batch.expiry_date < today,
            Batch.status == BatchStatus.ACTIVE.value
        )
    ).all()
    
    count = 0
    for batch in expired_batches:
        batch.status = BatchStatus.EXPIRED.value
        count += 1
    
    if count > 0:
        db.commit()
    
    return count
