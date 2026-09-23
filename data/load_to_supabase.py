import os
import csv
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    raise ValueError("SUPABASE_DB_URL not found in .env")

TABLES = [
    ("customers", "data/customers.csv"),
    ("sellers", "data/sellers.csv"),
    ("categories", "data/categories.csv"),
    ("products", "data/products.csv"),
    ("orders", "data/orders.csv"),
    ("order_items", "data/order_items.csv"),
    ("reviews", "data/reviews.csv"),
]


def load_csv_to_table(cursor, table_name, csv_file):

    print(f"\nLoading {csv_file} → {table_name}")

    with open(csv_file, "r", encoding="utf-8-sig", newline="") as file:

        reader = csv.reader(file)

        # Read CSV header
        columns = next(reader)

        columns_sql = ", ".join(
            f'"{column.strip()}"'
            for column in columns
        )

        sql = f"""
            INSERT INTO "{table_name}" ({columns_sql})
            VALUES ({", ".join(["%s"] * len(columns))})
        """

        rows = []

        for row in reader:

            # Skip completely empty rows
            if not any(value.strip() for value in row):
                continue

            # Convert empty strings to NULL
            row = [
                value.strip() if value.strip() != "" else None
                for value in row
            ]

            rows.append(row)

        execute_batch(cursor, sql, rows)

        rows_loaded = len(rows)

    print(f"✓ {rows_loaded} rows loaded into {table_name}")

    return rows_loaded


def main():

    print("Connecting to Supabase PostgreSQL...")

    connection = psycopg2.connect(DATABASE_URL)

    connection.autocommit = False

    cursor = connection.cursor()

    total_rows = 0

    try:

        for table_name, csv_file in TABLES:

            rows = load_csv_to_table(
                cursor,
                table_name,
                csv_file
            )

            total_rows += rows

        connection.commit()
        print(f"Total rows loaded: {total_rows}")

    except Exception as error:

        connection.rollback()
        print(error)

        raise

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()