"""Checks a pipeline release CSV, per source, before it is loaded into prod.

Read-only dry-run helper for PENSION_FUND_REFRESH.md § 4.5 and § 5c step 5.
Reads a `data/output/shareholder_tracker_release_*.csv` (pipe-delimited,
`NULL` for nulls, quoted fields may contain `|`) with DuckDB and prints one
row per `source` with the numbers the runbook asks a human to check against
§ 6c and § 5a, followed by warnings. Nothing is written and no database is
touched.

Usage:

    python manual/validate_release.py data/output/shareholder_tracker_release_YYYYMMDD.csv
    python manual/validate_release.py data/output/shareholder_tracker_release_YYYYMMDD.csv \
        --targets manual/validation_targets_2026-11.csv

Per source the table shows: row count; distinct `investor_name` count (and
the names when there are 2-5 of them); min/max `document_report_date`;
SUM(`security_market_value_amount_usd`) in billions; null-USD, null/blank-ISIN,
null-url and null-`issuer_country_code` counts; populated
`stock_percent_ownership` count; distinct `investor_abbreviation`,
`security_market_value_currency_code` and `security_market_value_multiplier`
values. A value of `(blank)` in a distinct-values cell means NULL or ''.

`--targets` takes a CSV with columns `source,expected_rows,expected_usd_bn`
(see `manual/validation_targets_2026-11.csv`, populated from § 6c and § 5a).
It adds `exp_rows`, `exp_usd_bn`, `usd_diff` and `flag` columns: PASS when the
USD total is within ±15 % of `expected_usd_bn`, WARN otherwise, `n/a` when the
target has no USD figure (AMF, AP4, KPA). Row counts are shown for comparison
only; the merge legitimately collapses duplicate securities, so they are not
flagged. Target sources absent from the file are listed as a note, not a
warning, because the NBIM and workbook loads are run and checked separately.

Warnings, printed after the table: a non-SEC source with more than one
`investor_name`; any `P2` abbreviation; a multiplier outside
x1/x100/x1_000/x1_000_000; rows with a blank `issuer_name`; a blank `source`;
USD values that do not parse as numbers; USD totals outside ±15 % of a target.
Exits 0 when there are no warnings, 1 when there is at least one, 2 on bad
input.
"""

# Standard library imports
import argparse
import csv
import sys
import time
from pathlib import Path

# Third-party imports
import duckdb

# DuckDB read_csv options: the release files only parse with these (the
# sniffer misses the quote character, and issuer names contain `|`)
READ_CSV_OPTIONS = (
    "delim='|', quote='\"', escape='\"', header=true, nullstr='NULL', "
    "all_varchar=true, strict_mode=false"
)

# Columns the checks read; the file may hold more
REQUIRED_COLUMNS = [
    "source",
    "document_report_date",
    "investor_name",
    "investor_abbreviation",
    "issuer_name",
    "issuer_country_code",
    "security_market_value_currency_code",
    "security_market_value_multiplier",
    "security_market_value_amount_usd",
    "security_isin",
    "stock_percent_ownership",
    "url",
]

TARGET_COLUMNS = ["source", "expected_rows", "expected_usd_bn"]
VALID_MULTIPLIERS = {"x1", "x100", "x1_000", "x1_000_000"}
USD_TOLERANCE_PCT = 15.0
BLANK = "(blank)"
MAX_NAMES_SHOWN = 5

# One pass over the file; every number below comes out of this query.
# `nullif(x, '')` treats '' like NULL, so "null" counts cover both.
SUMMARY_QUERY = f"""
SELECT
    coalesce(nullif(source, ''), '{BLANK}') AS source,
    COUNT(*) AS n_rows,
    list_sort(list(DISTINCT coalesce(nullif(investor_name, ''), '{BLANK}')))
        AS investor_names,
    MIN(nullif(document_report_date, '')) AS min_report_date,
    MAX(nullif(document_report_date, '')) AS max_report_date,
    SUM(TRY_CAST(security_market_value_amount_usd AS DOUBLE)) / 1e9 AS usd_bn,
    COUNT(*) FILTER (WHERE nullif(security_market_value_amount_usd, '') IS NULL)
        AS null_usd,
    COUNT(*) FILTER (
        WHERE nullif(security_market_value_amount_usd, '') IS NOT NULL
          AND TRY_CAST(security_market_value_amount_usd AS DOUBLE) IS NULL
    ) AS unparseable_usd,
    COUNT(*) FILTER (WHERE nullif(trim(security_isin), '') IS NULL) AS null_isin,
    COUNT(*) FILTER (WHERE nullif(stock_percent_ownership, '') IS NOT NULL)
        AS pct_ownership,
    list_sort(list(DISTINCT coalesce(nullif(investor_abbreviation, ''), '{BLANK}')))
        AS abbreviations,
    list_sort(list(DISTINCT coalesce(
        nullif(security_market_value_currency_code, ''), '{BLANK}')))
        AS currencies,
    list_sort(list(DISTINCT coalesce(
        nullif(security_market_value_multiplier, ''), '{BLANK}')))
        AS multipliers,
    COUNT(*) FILTER (WHERE nullif(url, '') IS NULL) AS null_url,
    COUNT(*) FILTER (WHERE nullif(issuer_country_code, '') IS NULL)
        AS null_issuer_country_code,
    COUNT(*) FILTER (WHERE nullif(trim(issuer_name), '') IS NULL) AS blank_issuer
FROM release
GROUP BY 1
ORDER BY n_rows DESC
"""


def _read_targets(fpath: Path) -> dict[str, tuple[int | None, float | None]]:
    """Reads the optional targets CSV.

    Args:
        fpath: The path to a CSV with columns `source,expected_rows,expected_usd_bn`.
            Either expected value may be blank.

    Returns:
        A dict of source string to `(expected_rows, expected_usd_bn)`.
    """
    targets: dict[str, tuple[int | None, float | None]] = {}
    with open(fpath, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != TARGET_COLUMNS:
            raise ValueError(
                f"Targets header must be {','.join(TARGET_COLUMNS)}; "
                f"found {reader.fieldnames}."
            )
        for lineno, row in enumerate(reader, start=2):
            source = (row["source"] or "").strip()
            if not source:
                raise ValueError(f"{fpath}:{lineno}: blank source.")
            if source in targets:
                raise ValueError(f"{fpath}:{lineno}: duplicate source {source!r}.")
            rows_str = (row["expected_rows"] or "").strip().replace(",", "")
            usd_str = (row["expected_usd_bn"] or "").strip().replace(",", "")
            targets[source] = (
                int(rows_str) if rows_str else None,
                float(usd_str) if usd_str else None,
            )
    return targets


def _summarize(csv_fpath: Path) -> list[dict]:
    """Runs the per-source summary query over the release CSV.

    Args:
        csv_fpath: The path to the release CSV.

    Returns:
        One dict per source, keyed by the summary query's column names.
    """
    con = duckdb.connect()
    con.execute(
        f"CREATE VIEW release AS SELECT * FROM read_csv("
        f"'{csv_fpath.as_posix()}', {READ_CSV_OPTIONS})"
    )
    columns = [row[0] for row in con.execute("DESCRIBE release").fetchall()]
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise ValueError(
            f"CSV is missing release column(s) {missing}; found {columns}."
        )
    result = con.execute(SUMMARY_QUERY)
    names = [desc[0] for desc in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def _fmt_list(values: list[str]) -> str:
    """Joins distinct values for a table cell."""
    return ", ".join(values)


def _fmt_names(names: list[str]) -> str:
    """Shows the investor-name count, plus the names when there are a few."""
    if 2 <= len(names) <= MAX_NAMES_SHOWN:
        return f"{len(names)}: {'; '.join(names)}"
    return f"{len(names):,}"


def _fmt_dates(min_date: str | None, max_date: str | None) -> str:
    """Shows one date when min and max agree, otherwise a range."""
    if min_date is None and max_date is None:
        return BLANK
    if min_date == max_date:
        return str(min_date)
    return f"{min_date}..{max_date}"


def _fmt_usd(usd_bn: float | None) -> str:
    """Formats a USD total in billions."""
    return "-" if usd_bn is None else f"{usd_bn:,.1f}"


def _print_table(header: list[str], rows: list[list[str]], numeric: set[str]) -> None:
    """Prints a fixed-width text table.

    Args:
        header: The column labels.

        rows: One list of cell strings per row.

        numeric: The labels of right-aligned columns.

    Returns:
        `None`
    """
    widths = [
        max(len(header[i]), *(len(row[i]) for row in rows)) if rows else len(header[i])
        for i in range(len(header))
    ]

    def fmt(cells: list[str]) -> str:
        return "  ".join(
            cell.rjust(widths[i]) if header[i] in numeric else cell.ljust(widths[i])
            for i, cell in enumerate(cells)
        ).rstrip()

    print(fmt(header))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt(row))


def main() -> int:
    """Summarizes a release CSV per source and reports warnings.

    Args:
        `None`

    Returns:
        The process exit code: 0 clean, 1 if any warning, 2 on bad input.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Prints per-source dry-run numbers for a release CSV (rows, USD "
            "total, null counts, distinct abbreviations/currencies/"
            "multipliers) and warns on the conditions listed in "
            "PENSION_FUND_REFRESH.md § 4.5. Exits 1 if any warning."
        )
    )
    parser.add_argument(
        "csv", type=Path, help="Pipe-delimited release CSV written by main.py."
    )
    parser.add_argument(
        "--targets",
        type=Path,
        help=(
            "CSV with columns source,expected_rows,expected_usd_bn; adds "
            "expected columns and a PASS/WARN flag (±15%% on USD)."
        ),
    )
    args = parser.parse_args()

    if not args.csv.is_file():
        parser.error(f"{args.csv} is not a file.")
    try:
        targets = _read_targets(args.targets) if args.targets else {}
        started = time.monotonic()
        summary = _summarize(args.csv)
    except (ValueError, OSError, duckdb.Error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    total_rows = sum(row["n_rows"] for row in summary)
    print(
        f"{args.csv}: {total_rows:,} rows, {len(summary)} sources "
        f"({time.monotonic() - started:.0f}s)"
    )
    print()

    # Build the table
    header = [
        "source", "rows", "inv_names", "report_date", "usd_bn", "null_usd",
        "null_isin", "pct_own", "abbrev", "ccy", "mult", "null_url", "null_cc",
    ]
    numeric = {
        "rows", "usd_bn", "null_usd", "null_isin", "pct_own", "null_url",
        "null_cc", "exp_rows", "exp_usd_bn", "usd_diff",
    }
    if targets:
        header += ["exp_rows", "exp_usd_bn", "usd_diff", "flag"]

    warnings: list[str] = []
    table: list[list[str]] = []
    for row in summary:
        source = row["source"]
        is_sec = source.startswith("U.S.")
        cells = [
            source,
            f"{row['n_rows']:,}",
            _fmt_names(row["investor_names"]),
            _fmt_dates(row["min_report_date"], row["max_report_date"]),
            _fmt_usd(row["usd_bn"]),
            f"{row['null_usd']:,}",
            f"{row['null_isin']:,}",
            f"{row['pct_ownership']:,}",
            _fmt_list(row["abbreviations"]),
            _fmt_list(row["currencies"]),
            _fmt_list(row["multipliers"]),
            f"{row['null_url']:,}",
            f"{row['null_issuer_country_code']:,}",
        ]

        # Warnings that do not need targets
        if source == BLANK:
            warnings.append(f"{row['n_rows']:,} rows have a blank source.")
        if not is_sec and len(row["investor_names"]) > 1:
            warnings.append(
                f"{source}: {len(row['investor_names'])} investor_name spellings: "
                f"{'; '.join(row['investor_names'])}."
            )
        if "P2" in row["abbreviations"]:
            warnings.append(
                f"{source}: abbreviation P2 present "
                f"(abbreviations: {_fmt_list(row['abbreviations'])})."
            )
        bad_multipliers = [m for m in row["multipliers"] if m not in VALID_MULTIPLIERS]
        if bad_multipliers:
            warnings.append(
                f"{source}: multiplier not in "
                f"{'/'.join(sorted(VALID_MULTIPLIERS))}: {_fmt_list(bad_multipliers)}."
            )
        if row["blank_issuer"]:
            warnings.append(f"{source}: {row['blank_issuer']:,} rows have a blank issuer_name.")
        if row["unparseable_usd"]:
            warnings.append(
                f"{source}: {row['unparseable_usd']:,} security_market_value_amount_usd "
                f"values are not numeric (excluded from usd_bn)."
            )

        # Target comparison
        if targets:
            target = targets.get(source)
            if target is None:
                cells += ["", "", "", ""]
            else:
                expected_rows, expected_usd_bn = target
                exp_rows = "" if expected_rows is None else f"{expected_rows:,}"
                if expected_usd_bn is None:
                    cells += [exp_rows, "-", "", "n/a"]
                elif row["usd_bn"] is None or row["usd_bn"] == 0:
                    cells += [exp_rows, _fmt_usd(expected_usd_bn), "", "WARN"]
                    warnings.append(
                        f"{source}: no USD values, expected "
                        f"{expected_usd_bn:,.1f} bn."
                    )
                else:
                    diff_pct = (row["usd_bn"] - expected_usd_bn) / expected_usd_bn * 100
                    flag = "PASS" if abs(diff_pct) <= USD_TOLERANCE_PCT else "WARN"
                    cells += [exp_rows, _fmt_usd(expected_usd_bn), f"{diff_pct:+.1f}%", flag]
                    if flag == "WARN":
                        warnings.append(
                            f"{source}: USD total {row['usd_bn']:,.1f} bn is "
                            f"{diff_pct:+.1f}% from the target "
                            f"{expected_usd_bn:,.1f} bn (tolerance ±{USD_TOLERANCE_PCT:.0f}%)."
                        )
        table.append(cells)

    _print_table(header, table, numeric)

    # Targets for sources that are not in this file: a note, not a warning,
    # since the NBIM and workbook loads are checked separately
    if targets:
        in_file = {row["source"] for row in summary}
        absent = [source for source in targets if source not in in_file]
        if absent:
            print()
            print(f"Note: {len(absent)} target source(s) not in this file: {'; '.join(absent)}.")

    print()
    if warnings:
        print(f"{len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"  WARN  {warning}")
        return 1
    print("No warnings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
