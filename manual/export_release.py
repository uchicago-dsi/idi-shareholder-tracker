"""Exports the combined Shareholder Tracker release from the production database.

The website serves the `investment` table, which holds the SEC rows and the
pension/NBIM rows side by side. Exporting that table is the only way to
produce a complete Downloads-page release: `main.py --sec-only` has no pension
rows, and a full `main.py` run needs pension input files that no longer exist.

Requires the Cloud SQL proxy on 127.0.0.1:5432 and the `PG*` environment
variables described in REFRESH.md (psql performs the export; DuckDB builds the
Parquet and SQLite files). Output mirrors the CDN layout, one dated folder per
release:

    data/output/<YYYY-MM-DD>/shareholder_tracker_release_<YYYYMMDD>.csv
    data/output/<YYYY-MM-DD>/shareholder_tracker_release_<YYYYMMDD>.zip
    data/output/<YYYY-MM-DD>/shareholder_tracker_release_<YYYYMMDD>.parquet
    data/output/<YYYY-MM-DD>/shareholder_tracker_release_<YYYYMMDD>.sqlite
    data/output/<YYYY-MM-DD>/shareholder_tracker_release_<YYYYMMDD>.sqlite.gz
"""

# Standard library imports
import argparse
import gzip
import logging
import os
import shutil
import subprocess
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import duckdb

# Release columns: the `investment` table minus its generated `id`/`document`
COLUMNS = [
    "source",
    "document_report_date",
    "document_filing_date",
    "investor_type",
    "investor_cik",
    "investor_name",
    "investor_abbreviation",
    "investor_country_name",
    "investor_country_code",
    "investor_region_name",
    "investor_region_code",
    "issuer_name",
    "issuer_country_name",
    "issuer_country_code",
    "issuer_sector",
    "security_type",
    "security_vintage_year",
    "security_principal_amount_currency_code",
    "security_principal_amount",
    "security_market_value_currency_code",
    "security_market_value_amount",
    "security_market_value_multiplier",
    "security_market_value_conversion_rate",
    "security_market_value_amount_usd",
    "security_isin",
    "security_cusip",
    "security_figi",
    "stock_ticker",
    "stock_number_of_shares",
    "stock_percent_ownership",
    "stock_percent_voting_power",
    "stock_voting_auth_sole",
    "stock_voting_auth_shared",
    "stock_voting_auth_none",
    "url",
    "text",
    "last_accessed_date",
]

# Numeric columns, typed to match the December 2025 release; all others are text
DOUBLE_COLUMNS = {
    "security_principal_amount",
    "security_market_value_amount",
    "security_market_value_conversion_rate",
    "stock_percent_ownership",
    "stock_percent_voting_power",
}
BIGINT_COLUMNS = {
    "security_market_value_amount_usd",
    "stock_number_of_shares",
    "stock_voting_auth_sole",
    "stock_voting_auth_shared",
    "stock_voting_auth_none",
}


@contextmanager
def _atomic_write(fpath: Path) -> Iterator[Path]:
    """Yields a temporary path that replaces `fpath` only on success.

    A partially written file is removed instead, so an interrupted run never
    leaves a truncated artifact under its final name.

    Args:
        fpath: The final path of the artifact.

    Yields:
        The temporary path to write to.
    """
    tmp_fpath = fpath.with_name(fpath.name + ".tmp")
    tmp_fpath.unlink(missing_ok=True)
    try:
        yield tmp_fpath
        os.replace(tmp_fpath, fpath)
    except BaseException:
        tmp_fpath.unlink(missing_ok=True)
        raise


def _export_csv(csv_fpath: Path) -> None:
    """Dumps the `investment` table to a pipe-delimited CSV via psql.

    Uses the same CSV dialect as `main.py` (`|` delimiter, `NULL` for nulls).

    Args:
        csv_fpath: The destination path for the CSV file.

    Returns:
        `None`
    """
    query = f"SELECT {', '.join(COLUMNS)} FROM investment ORDER BY id"
    with _atomic_write(csv_fpath) as tmp_fpath:
        copy_cmd = (
            f"\\copy ({query}) TO '{tmp_fpath.as_posix()}' "
            "WITH (FORMAT csv, HEADER true, DELIMITER '|', NULL 'NULL')"
        )
        subprocess.run(
            ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", copy_cmd],
            check=True,
        )


def _build_parquet_and_sqlite(
    csv_fpath: Path, parquet_fpath: Path, sqlite_fpath: Path
) -> duckdb.DuckDBPyConnection:
    """Reads the CSV export and writes the Parquet and SQLite release files.

    Args:
        csv_fpath: The path to the CSV export.

        parquet_fpath: The destination path for the Parquet file.

        sqlite_fpath: The destination path for the SQLite database.

    Returns:
        The DuckDB connection, holding the release in a `release` table.
    """
    # Reject a CSV whose columns are not the release columns in order:
    # `columns=` below assigns names positionally, so a reordered export
    # would be silently mislabeled rather than rejected
    with open(csv_fpath, encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split("|")
    if header != COLUMNS:
        raise ValueError(
            f"CSV header does not match the release columns.\n"
            f"  expected: {COLUMNS}\n"
            f"  found:    {header}"
        )

    # Read numeric columns as doubles so integer-valued decimals such as
    # "1234.0" parse, then cast the integer columns on the way out
    read_types = {
        col: (
            "DOUBLE" if col in DOUBLE_COLUMNS | BIGINT_COLUMNS else "VARCHAR"
        )
        for col in COLUMNS
    }
    select = ", ".join(
        f"CAST({col} AS BIGINT) AS {col}" if col in BIGINT_COLUMNS else col
        for col in COLUMNS
    )
    # Set the quote character explicitly: DuckDB's sniffer can miss it, and
    # issuer names such as "CASTIK CAPITAL | EPIC III" contain the delimiter
    con = duckdb.connect()
    con.execute(
        f"CREATE TABLE release AS SELECT {select} FROM read_csv("
        f"'{csv_fpath.as_posix()}', delim='|', quote='\"', escape='\"', "
        f"header=true, nullstr='NULL', columns={read_types})"
    )

    # Write Parquet
    with _atomic_write(parquet_fpath) as tmp_fpath:
        con.execute(f"COPY release TO '{tmp_fpath.as_posix()}' (FORMAT parquet)")

    # Write SQLite, using the same table name as main.py
    con.execute("INSTALL sqlite; LOAD sqlite;")
    with _atomic_write(sqlite_fpath) as tmp_fpath:
        con.execute(f"ATTACH '{tmp_fpath.as_posix()}' AS sqlite_db (TYPE sqlite)")
        con.execute("CREATE TABLE sqlite_db.investments AS SELECT * FROM release")
        con.execute("DETACH sqlite_db")

    return con


def _compress(csv_fpath: Path, sqlite_fpath: Path) -> tuple[Path, Path]:
    """Zips the CSV and gzips the SQLite database, as published on the CDN.

    Args:
        csv_fpath: The path to the CSV file.

        sqlite_fpath: The path to the SQLite database.

    Returns:
        The paths to the zip and gzip files.
    """
    zip_fpath = csv_fpath.with_suffix(".zip")
    with _atomic_write(zip_fpath) as tmp_fpath:
        with zipfile.ZipFile(tmp_fpath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_fpath, arcname=csv_fpath.name)
        # Guard against a short read: the archived CSV must be the whole file
        archived_size = zipfile.ZipFile(tmp_fpath).getinfo(csv_fpath.name).file_size
        if archived_size != csv_fpath.stat().st_size:
            raise RuntimeError(
                f"Zip holds {archived_size:,} of {csv_fpath.stat().st_size:,} "
                f"CSV bytes."
            )

    gz_fpath = sqlite_fpath.with_suffix(".sqlite.gz")
    with _atomic_write(gz_fpath) as tmp_fpath:
        with open(sqlite_fpath, "rb") as src, gzip.open(tmp_fpath, "wb") as dst:
            shutil.copyfileobj(src, dst)

    return zip_fpath, gz_fpath


def main() -> None:
    """Exports, converts, and compresses the combined release.

    Args:
        `None`

    Returns:
        `None`
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=(
            "Exports the combined release (SEC + pension rows) from the "
            "production `investment` table and packages it for the CDN."
        )
    )
    parser.add_argument(
        "--release-date",
        default=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        help="Release date as YYYY-MM-DD. Defaults to today (UTC).",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help=(
            "Reuse an existing CSV export instead of querying the "
            "production database."
        ),
    )
    args = parser.parse_args()

    # Instantiate logger
    logger = logging.getLogger("RELEASE EXPORT")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Define output file paths, one dated folder per release
    release_date = datetime.strptime(args.release_date, "%Y-%m-%d")
    output_dir = (
        Path(__file__).parents[1] / "data" / "output" / args.release_date
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"shareholder_tracker_release_{release_date:%Y%m%d}"
    csv_fpath = output_dir / f"{base}.csv"
    parquet_fpath = output_dir / f"{base}.parquet"
    sqlite_fpath = output_dir / f"{base}.sqlite"

    # Export from production, or copy in a previous export
    if args.csv:
        logger.info(f"Reusing CSV export {args.csv}.")
        if args.csv.resolve() != csv_fpath.resolve():
            with _atomic_write(csv_fpath) as tmp_fpath:
                shutil.copyfile(args.csv, tmp_fpath)
    else:
        logger.info("Exporting the investment table from production.")
        _export_csv(csv_fpath)

    # Build Parquet and SQLite files
    logger.info("Writing Parquet and SQLite files.")
    con = _build_parquet_and_sqlite(csv_fpath, parquet_fpath, sqlite_fpath)

    # Compress
    logger.info("Zipping CSV and gzipping SQLite database.")
    zip_fpath, gz_fpath = _compress(csv_fpath, sqlite_fpath)

    # Summarize for verification against the production row counts
    logger.info("Release summary:")
    total, sources, sec, pension = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT source), "
        "COUNT(*) FILTER (WHERE source LIKE 'U.S.%'), "
        "COUNT(*) FILTER (WHERE source NOT LIKE 'U.S.%') FROM release"
    ).fetchone()
    print(f"  rows={total:,}  sources={sources}  sec={sec:,}  pension={pension:,}")
    for row in con.execute(
        "SELECT source, COUNT(*) FROM release GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall():
        print(f"  {row[1]:>10,}  {row[0]}")
    print("Upload these to the CDN (sizes for web/config/downloads.ts):")
    for fpath in (zip_fpath, parquet_fpath, gz_fpath):
        size = fpath.stat().st_size
        print(f"  {fpath.name:<50} {size:>14,} bytes  {size / 1_000_000:.0f} MB")


if __name__ == "__main__":
    main()
