"""
Database Models Module

This module defines SQLAlchemy ORM models for the Smart Pharma System.
Models include Product and Batch entities with appropriate relationships.
"""

import enum
from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class BatchStatus(enum.Enum):
    """
    Enumeration for Batch status values.
    
    Attributes:
        ACTIVE: Batch is available for sale/distribution.
        EXPIRED: Batch has expired and cannot be sold.
    """
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    
    def __str__(self):
        return self.value


class Product(Base):
    """
    Product entity representing pharmaceutical products.
    
    Attributes:
        id (int): Primary key, auto-incremented.
        name (str): Product name, required.
        sku (str): Stock Keeping Unit, unique identifier.
        category (str): Product category for classification.
        batches (list[Batch]): Related batch records.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)
    
    # Relationship to batches
    batches = relationship(
        "Batch",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"


class Batch(Base):
    """
    Batch entity representing individual product batches/lots.
    
    Each batch tracks a specific lot of a product with its own
    expiry date and quantity. Used for FEFO (First Expired, First Out)
    inventory management.
    
    Attributes:
        id (int): Primary key, auto-incremented.
        product_id (int): Foreign key to Product.
        batch_code (str): Unique batch/lot number.
        expiry_date (date): Expiration date of the batch.
        quantity (int): Current quantity in stock.
        status (BatchStatus): Current status (ACTIVE/EXPIRED).
        product (Product): Reference to parent product.
    """
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    batch_code = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    status = Column(
        String(20),
        nullable=False,
        default=BatchStatus.ACTIVE.value
    )
    
    # Relationship to product
    product = relationship("Product", back_populates="batches")
    
    # Unique constraint: batch_code should be unique per product
    __table_args__ = (
        UniqueConstraint("product_id", "batch_code", name="uq_product_batch"),
        Index("ix_batches_expiry_status", "expiry_date", "status"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Batch(id={self.id}, batch_code='{self.batch_code}', "
            f"expiry_date={self.expiry_date}, quantity={self.quantity})>"
        )
