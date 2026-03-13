from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table

from database import engine
from models import reflect_tables


TABLE_CACHE: dict[str, Table] | None = None


def _load_tables() -> dict[str, Table]:
    global TABLE_CACHE
    if TABLE_CACHE is None:
        TABLE_CACHE = reflect_tables(engine)
    return TABLE_CACHE


def _pick_column(table, candidates: list[str]):
    for name in candidates:
        if name in table.c:
            return table.c[name]
    return None


def _required_column(table, candidates: list[str], table_name: str, purpose: str):
    column = _pick_column(table, candidates)
    if column is None:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Missing column for {purpose} in table '{table_name}'. "
                f"Expected one of: {', '.join(candidates)}"
            ),
        )
    return column


def get_fefo_batches(db: Session, product_id: int) -> list[dict]:
    tables = _load_tables()
    history = tables.get("history_import")
    product = tables.get("product")

    if history is None or product is None:
        raise HTTPException(status_code=500, detail="Required tables 'history_import' or 'product' not found")

    history_id_col = _required_column(history, ["id"], "history_import", "record id")
    history_product_id_col = _required_column(history, ["product_id", "id_product", "medicine_id"], "history_import", "product link")
    history_qty_col = _required_column(history, ["quantity", "qty", "remaining_quantity", "stock"], "history_import", "quantity")
    history_expiry_col = _required_column(history, ["expiry_date", "expired_date", "expiration_date", "date_expired"], "history_import", "expiry date")
    history_batch_col = _pick_column(history, ["batch_code", "batch_no", "batch_number", "lot_code", "lot_no", "lot_number"])

    product_id_col = _required_column(product, ["id", "product_id"], "product", "product id")
    product_name_col = _pick_column(product, ["name", "product_name", "title"])

    stmt = (
        select(
            history_id_col.label("history_id"),
            history_product_id_col.label("product_id"),
            history_qty_col.label("quantity"),
            history_expiry_col.label("expiry_date"),
            history_batch_col.label("batch_code") if history_batch_col is not None else history_id_col.label("batch_code"),
            product_name_col.label("product_name") if product_name_col is not None else product_id_col.label("product_name"),
        )
        .select_from(history.join(product, history_product_id_col == product_id_col))
        .where(and_(history_product_id_col == product_id, history_qty_col > 0))
        .order_by(history_expiry_col.asc())
    )

    rows = db.execute(stmt).mappings().all()

    return [
        {
            "history_id": row["history_id"],
            "product_id": row["product_id"],
            "product_name": str(row["product_name"]),
            "batch_code": str(row["batch_code"]),
            "quantity": int(row["quantity"]),
            "expiry_date": row["expiry_date"],
        }
        for row in rows
    ]


def get_expiry_alerts(db: Session, days: int = 30) -> list[dict]:
    tables = _load_tables()
    history = tables.get("history_import")
    product = tables.get("product")

    if history is None or product is None:
        raise HTTPException(status_code=500, detail="Required tables 'history_import' or 'product' not found")

    today = date.today()
    cutoff = today + timedelta(days=days)

    history_id_col = _required_column(history, ["id"], "history_import", "record id")
    history_product_id_col = _required_column(history, ["product_id", "id_product", "medicine_id"], "history_import", "product link")
    history_qty_col = _required_column(history, ["quantity", "qty", "remaining_quantity", "stock"], "history_import", "quantity")
    history_expiry_col = _required_column(history, ["expiry_date", "expired_date", "expiration_date", "date_expired"], "history_import", "expiry date")
    history_batch_col = _pick_column(history, ["batch_code", "batch_no", "batch_number", "lot_code", "lot_no", "lot_number"])

    product_id_col = _required_column(product, ["id", "product_id"], "product", "product id")
    product_name_col = _pick_column(product, ["name", "product_name", "title"])

    stmt = (
        select(
            history_id_col.label("history_id"),
            history_product_id_col.label("product_id"),
            history_qty_col.label("quantity"),
            history_expiry_col.label("expiry_date"),
            history_batch_col.label("batch_code") if history_batch_col is not None else history_id_col.label("batch_code"),
            product_name_col.label("product_name") if product_name_col is not None else product_id_col.label("product_name"),
        )
        .select_from(history.join(product, history_product_id_col == product_id_col))
        .where(
            and_(
                history_qty_col > 0,
                history_expiry_col >= today,
                history_expiry_col <= cutoff,
            )
        )
        .order_by(history_expiry_col.asc())
    )

    rows = db.execute(stmt).mappings().all()

    return [
        {
            "history_id": row["history_id"],
            "product_id": row["product_id"],
            "product_name": str(row["product_name"]),
            "batch_code": str(row["batch_code"]),
            "quantity": int(row["quantity"]),
            "expiry_date": row["expiry_date"],
            "days_to_expiry": (row["expiry_date"] - today).days,
        }
        for row in rows
    ]
