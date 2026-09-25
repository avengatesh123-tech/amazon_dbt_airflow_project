"""Load the Amazon CSV data into Neon through its PostgREST API."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_API_URL = (
	"https://ep-tiny-hall-b5yi3mds.apirest.c-7.us-east-2.aws.neon.tech/amazon/rest/v1"
)
BATCH_SIZE = 500

# Parent tables must be loaded before tables containing their foreign keys.
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


def convert_value(column: str, value: str) -> Any:
	"""Convert CSV values to JSON values suitable for PostgreSQL."""
	if value == "":
		return None
	if column in INTEGER_COLUMNS:
		return int(value)
	if column in DECIMAL_COLUMNS:
		return float(value)
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


def upload_batch(api_url: str, api_key: str, table: str, rows: list[dict[str, Any]]) -> None:
	request = Request(
		f"{api_url.rstrip('/')}/{table}",
		data=json.dumps(rows).encode("utf-8"),
		method="POST",
		headers={
			"Accept": "application/json",
			"Content-Type": "application/json",
			"Authorization": f"Bearer {api_key}",
			"apikey": api_key,
			"Prefer": "resolution=merge-duplicates,return=minimal",
		},
	)
	try:
		with urlopen(request, timeout=60) as response:
			if response.status not in (200, 201, 204):
				raise RuntimeError(f"Neon returned unexpected HTTP status {response.status}")
	except HTTPError as error:
		details = error.read().decode("utf-8", errors="replace")
		raise RuntimeError(f"Upload to {table} failed ({error.code}): {details}") from error
	except URLError as error:
		raise RuntimeError(f"Could not connect to Neon while uploading {table}: {error.reason}") from error


def load_data(data_dir: Path, api_url: str, api_key: str, dry_run: bool = False) -> None:
	total_rows = 0
	for table in TABLES:
		csv_path = data_dir / f"{table}.csv"
		if not csv_path.exists():
			raise FileNotFoundError(f"Missing CSV file: {csv_path}")

		rows = read_rows(csv_path)
		print(f"{table}: {len(rows)} rows")
		if not dry_run:
			for start in range(0, len(rows), BATCH_SIZE):
				upload_batch(api_url, api_key, table, rows[start : start + BATCH_SIZE])
		total_rows += len(rows)
	print(f"Completed {'validation' if dry_run else 'upload'} of {total_rows} rows.")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--dry-run", action="store_true", help="Validate CSV files without uploading")
	parser.add_argument(
		"--api-url",
		default=os.getenv("NEON_API_URL", DEFAULT_API_URL),
		help="Neon REST base URL (defaults to NEON_API_URL or the configured endpoint)",
	)
	args = parser.parse_args()

	api_key = os.getenv("NEON_API_KEY", "")
	if not api_key and not args.dry_run:
		print("Set NEON_API_KEY before uploading; use --dry-run to validate locally.", file=sys.stderr)
		return 2

	try:
		load_data(Path(__file__).resolve().parent, args.api_url, api_key, args.dry_run)
	except (FileNotFoundError, ValueError, TypeError, ValueError, RuntimeError) as error:
		print(f"Error: {error}", file=sys.stderr)
		return 1
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
