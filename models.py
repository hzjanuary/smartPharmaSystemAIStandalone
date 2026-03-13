from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.engine import Engine

REQUIRED_TABLES = (
    "history_import",
    "product",
    "product_category",
    "product_image",
    "supplier",
    "user",
)

metadata = MetaData()


def reflect_tables(engine: Engine) -> dict[str, Table]:
    metadata.clear()
    existing = set(inspect(engine).get_table_names())
    target_tables = [name for name in REQUIRED_TABLES if name in existing]
    metadata.reflect(bind=engine, only=target_tables)
    return {name: metadata.tables[name] for name in metadata.tables}
