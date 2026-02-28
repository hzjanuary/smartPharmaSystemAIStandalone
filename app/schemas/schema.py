"""
Pydantic Schemas Module

This module defines Pydantic models for API request/response validation
and serialization. These schemas ensure type safety and data validation.
"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class BatchStatus(str, Enum):
    """Batch status enumeration for API responses."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"


class PriorityLevel(str, Enum):
    """
    Priority level for FEFO strategy.
    
    Attributes:
        CRITICAL: Expiry within 15 days - must be sold immediately.
        WARNING: Expiry within 15-45 days - prioritize for sale.
        SAFE: Expiry beyond 45 days - normal handling.
    """
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    SAFE = "SAFE"


class ProductBase(BaseModel):
    """Base schema for Product with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit")
    category: Optional[str] = Field(None, max_length=100, description="Product category")


class ProductResponse(ProductBase):
    """Schema for Product API responses."""
    id: int = Field(..., description="Product ID")
    
    model_config = ConfigDict(from_attributes=True)


class BatchBase(BaseModel):
    """Base schema for Batch with common fields."""
    batch_code: str = Field(..., min_length=1, max_length=100, description="Batch/Lot number")
    expiry_date: date = Field(..., description="Batch expiration date")
    quantity: int = Field(..., ge=0, description="Current quantity in stock")
    status: BatchStatus = Field(default=BatchStatus.ACTIVE, description="Batch status")


class BatchResponse(BatchBase):
    """Schema for Batch API responses."""
    id: int = Field(..., description="Batch ID")
    product_id: int = Field(..., description="Reference to parent product")
    
    model_config = ConfigDict(from_attributes=True)


class FEFOBatchResponse(BaseModel):
    """
    Schema for FEFO strategy response.
    
    Extends batch information with priority level and days until expiry.
    """
    id: int = Field(..., description="Batch ID")
    product_id: int = Field(..., description="Reference to parent product")
    product_name: str = Field(..., description="Product name for reference")
    batch_code: str = Field(..., description="Batch/Lot number")
    expiry_date: date = Field(..., description="Batch expiration date")
    quantity: int = Field(..., description="Current quantity in stock")
    days_until_expiry: int = Field(..., description="Number of days until expiration")
    priority_level: PriorityLevel = Field(..., description="FEFO priority classification")
    
    model_config = ConfigDict(from_attributes=True)


class ExpiryAlertResponse(BaseModel):
    """
    Schema for expiry alert response.
    
    Contains batch information with product details for expired/expiring items.
    """
    id: int = Field(..., description="Batch ID")
    product_id: int = Field(..., description="Reference to parent product")
    product_name: str = Field(..., description="Product name for reference")
    product_sku: str = Field(..., description="Product SKU for reference")
    batch_code: str = Field(..., description="Batch/Lot number")
    expiry_date: date = Field(..., description="Batch expiration date")
    quantity: int = Field(..., description="Current quantity in stock")
    days_until_expiry: int = Field(..., description="Number of days until expiration")
    priority_level: PriorityLevel = Field(..., description="Alert priority level")
    
    model_config = ConfigDict(from_attributes=True)


class FEFOStrategyResponse(BaseModel):
    """
    Response schema for FEFO strategy endpoint.
    
    Contains product information and prioritized batch list.
    """
    product_id: int = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    total_available_quantity: int = Field(..., description="Total quantity across all valid batches")
    batches: List[FEFOBatchResponse] = Field(
        default_factory=list,
        description="List of batches sorted by FEFO priority"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ExpiryAlertsResponse(BaseModel):
    """
    Response schema for expiry alerts endpoint.
    
    Contains summary and list of all expiring batches.
    """
    total_alerts: int = Field(..., description="Total number of expiring batches")
    critical_count: int = Field(..., description="Number of CRITICAL priority batches")
    warning_count: int = Field(..., description="Number of WARNING priority batches")
    alerts: List[ExpiryAlertResponse] = Field(
        default_factory=list,
        description="List of expiring batches sorted by urgency"
    )
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
