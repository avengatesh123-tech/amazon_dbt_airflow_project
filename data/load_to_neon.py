"""Load the Amazon CSV files into Neon PostgreSQL."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any


TABLES = (
    "customers",
    "sellers",
    "categories",
    "products",
    "orders",
    "order_items",
    "reviews",
)

INTEGER_COLUMNS = {
    "customer_id",
    "seller_id",
    "category_id",
    "parent_category_id",
    "product_id",
    "order_id",
    "order_item_id",
    "quantity",
    "review_id",
    "rating",
}
DECIMAL_COLUMNS = {"seller_rating", "price", "total_amount", "unit_price", "line_amount"}
PRIMARY_KEYS = {
    "customers": "customer_id",
    "sellers": "seller_id",
    "categories": "category_id",
    "products": "product_id",
    "orders": "order_id",
    "order_items": "order_item_id",
    "reviews": "review_id",
}


def load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding shell variables."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def convert_value(column: str, value: str) -> Any:
    if value == "":
        return None
    if column in INTEGER_COLUMNS:
        return int(value)
    if column in DECIMAL_COLUMNS:
        return Decimal(value)
    return value


def read_rows(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path.name} has no header row")
        return [
            {column: convert_value(column, value) for column, value in row.items()}
            for row in reader
        ]


def load_csv_files(data_dir: Path) -> dict[str, list[dict[str, Any]]]:
    data = {}
    for table in TABLES:
        csv_path = data_dir / f"{table}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing CSV file: {csv_path}")
        data[table] = read_rows(csv_path)
    return data


def upload_tables(data: dict[str, list[dict[str, Any]]], database_url: str) -> None:
    try:
        import psycopg
    except ImportError as error:
        raise RuntimeError(
            "psycopg is missing. Run: python -m pip install \"psycopg[binary]>=3.2\""
        ) from error

    with psycopg.connect(database_url) as connection:
        for table in TABLES:
            rows = data[table]
            if not rows:
                print(f"{table}: 0 rows")
                continue

            columns = list(rows[0])
            column_sql = ", ".join(f'"{column}"' for column in columns)
            placeholders = ", ".join("%s" for _ in columns)
            primary_key = PRIMARY_KEYS[table]
            updates = ", ".join(
                f'"{column}" = EXCLUDED."{column}"'
                for column in columns
                if column != primary_key
            )
            statement = (
                f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders}) '
                f'ON CONFLICT ("{primary_key}") DO UPDATE SET {updates}'
            )

            with connection.cursor() as cursor:
                cursor.executemany(
                    statement,
                    ([row[column] for column in columns] for row in rows),
                )
            connection.commit()
            print(f"{table}: {len(rows)} rows uploaded")


def verify_tables(database_url: str) -> None:
    try:
        import psycopg
    except ImportError as error:
        raise RuntimeError(
            "psycopg is missing. Run: python -m pip install \"psycopg[binary]>=3.2\""
        ) from error

    with psycopg.connect(database_url) as connection:
        for table in TABLES:
            count = connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            print(f"{table}: {count} rows in Neon")


def main() -> int:
    data_dir = Path(__file__).resolve().parent
    load_env_file(data_dir / ".env")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all CSV files without connecting to Neon",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Report row counts in Neon without uploading",
    )
    args = parser.parse_args()

    try:
        data = load_csv_files(data_dir)
        total_rows = sum(len(rows) for rows in data.values())
        for table, rows in data.items():
            print(f"{table}: {len(rows)} rows ready")

        if args.dry_run:
            print(f"Validation complete: {total_rows} rows.")
            return 0

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is missing from data/.env")
        if args.verify:
            verify_tables(database_url)
            return 0
        upload_tables(data, database_url)
        print(f"Upload complete: {total_rows} rows.")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
