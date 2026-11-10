# Standard library imports
import argparse
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Third-party imports
import duckdb
import numpy as np
import pandas as pd

# Local imports
from currency import CurrencyConverter

logger = logging.getLogger("MANUAL DATA MERGE")


def _process_nbim_investments(
    data_fpath: Path, report_date: str
) -> pd.DataFrame:
    """Loads, cleans, and standardizes NBIM (Norges Bank) equity holdings.

    Reads the "total holdings by country" Equity report downloaded from
    nbim.no: UTF-16 with BOM, semicolon-delimited, one row per company
    (see PENSION_FUND_REFRESH.md § 5a). The returned frame carries every
    column `_merge_datasets` expects, so it can be merged on its own.

    Args:
        data_fpath: The path to the NBIM equity report CSV file.

        report_date: The report's snapshot date, formatted as `YYYY-MM-DD`.
            Used for `document_report_date` and the row URL.

    Returns:
        A DataFrame of NBIM investments.
    """
    # Read file
    nbim_df = pd.read_csv(data_fpath, sep=";", encoding="utf-16")

    # Rename columns, keeping only those that are loaded
    col_map = {
        "Name": "issuer_name",
        "Country": "issuer_country_name",
        "Industry": "issuer_sector",
        "Market Value(USD)": "security_market_value_amount",
        "Ownership": "stock_percent_ownership",
        "Voting": "stock_percent_voting_power",
    }
    missing_cols = sorted(set(col_map) - set(nbim_df.columns))
    if missing_cols:
        raise ValueError(
            f"NBIM report {data_fpath.name} is missing expected "
            f"columns {missing_cols}. Found: {nbim_df.columns.tolist()}"
        )
    nbim_df = nbim_df.rename(columns=col_map)[list(col_map.values())]

    # Convert percentage strings (e.g., "1.43%") to floats
    for col in ("stock_percent_ownership", "stock_percent_voting_power"):
        nbim_df[col] = pd.to_numeric(
            nbim_df[col].astype(str).str.strip().str.rstrip("%")
        ).astype(float)

    # Add constant columns
    nbim_df["source"] = "NORGES BANK"
    nbim_df["document_report_date"] = report_date
    nbim_df["document_filing_date"] = ""
    nbim_df["investor_type"] = "PENSION FUND"
    nbim_df["investor_abbreviation"] = "NBIM"
    nbim_df["investor_cik"] = ""
    nbim_df["investor_name"] = "NORGES BANK"
    nbim_df["investor_country_name"] = "NORWAY"
    nbim_df["investor_country_code"] = "NO"
    nbim_df["investor_region_name"] = "OSLO"
    nbim_df["investor_region_code"] = "NO-03"
    nbim_df["security_vintage_year"] = ""
    nbim_df["security_type"] = "STOCK"
    nbim_df["security_market_value_currency_code"] = "USD"
    nbim_df["security_market_value_multiplier"] = "x1"
    nbim_df["security_market_value_conversion_rate"] = 1
    nbim_df["security_isin"] = ""
    nbim_df["security_cusip"] = ""
    nbim_df["security_figi"] = ""
    nbim_df["stock_ticker"] = ""
    nbim_df["url"] = (
        "https://www.nbim.no/en/investments/all-investments"
        f"#/{report_date}/0-equity"
    )

    # Add columns NBIM does not report but the merge expects
    nbim_df["security_principal_amount_currency_code"] = ""
    nbim_df["security_principal_amount"] = np.nan
    nbim_df["stock_number_of_shares"] = np.nan
    nbim_df["stock_voting_auth_sole"] = np.nan
    nbim_df["stock_voting_auth_shared"] = np.nan
    nbim_df["stock_voting_auth_none"] = np.nan

    # Make text-based column values uppercase
    for col in ("issuer_name", "issuer_country_name", "issuer_sector"):
        nbim_df.loc[:, [col]] = nbim_df[col].str.upper()

    # Define country code mapping
    country_codes = {
        "ARGENTINA": "AR",
        "AUSTRALIA": "AU",
        "AUSTRIA": "AT",
        "BAHAMAS": "BS",
        "BANGLADESH": "BD",
        "BELGIUM": "BE",
        "BERMUDA": "BM",
        "BRAZIL": "BR",
        "BRITISH VIRGIN ISLANDS": "VG",
        "BULGARIA": "BG",
        "BURKINA FASO": "BF",
        "CANADA": "CA",
        "CAYMAN ISLANDS": "KY",
        "CHILE": "CL",
        "CHINA": "CN",
        "COLOMBIA": "CO",
        "COSTA RICA": "CR",
        "CYPRUS": "CY",
        "CZECH REPUBLIC": "CZ",
        "CZECHIA": "CZ",
        "DENMARK": "DK",
        "DOMINICAN REPUBLIC": "DO",
        "EGYPT": "EG",
        "ESTONIA": "EE",
        "FINLAND": "FI",
        "FRANCE": "FR",
        "GEORGIA": "GE",
        "GERMANY": "DE",
        "GIBRALTAR": "GI",
        "GREECE": "GR",
        "GREENLAND": "GL",
        "GUAM": "GU",
        "GUATEMALA": "GT",
        "GUERNSEY": "GG",
        "HONDURAS": "HN",
        "HONG KONG": "HK",
        "HUNGARY": "HU",
        "ICELAND": "IS",
        "INDIA": "IN",
        "INDONESIA": "ID",
        "IRELAND": "IE",
        "ISLE OF MAN": "IM",
        "ISRAEL": "IL",
        "ITALY": "IT",
        "JAPAN": "JP",
        "JERSEY": "JE",
        "JORDAN": "JO",
        "KAZAKHSTAN": "KZ",
        "KENYA": "KE",
        "KUWAIT": "KW",
        "LIECHTENSTEIN": "LI",
        "LITHUANIA": "LT",
        "LUXEMBOURG": "LU",
        "MACAU": "MO",
        "MALAYSIA": "MY",
        "MAURITIUS": "MU",
        "MEXICO": "MX",
        "MONACO": "MC",
        "MOROCCO": "MA",
        "NETHERLANDS": "NL",
        "NEW ZEALAND": "NZ",
        "NIGERIA": "NG",
        "NORWAY": "NO",
        "OMAN": "OM",
        "PANAMA": "PA",
        "PARAGUAY": "PY",
        "PERU": "PE",
        "PHILIPPINES": "PH",
        "POLAND": "PL",
        "PORTUGAL": "PT",
        "PUERTO RICO": "PR",
        "QATAR": "QA",
        "REPUBLIC OF KOREA": "KR",
        "ROMANIA": "RO",
        "RUSSIA": "RU",
        "SAUDI ARABIA": "SA",
        "SERBIA": "RS",
        "SINGAPORE": "SG",
        "SLOVAKIA": "SK",
        "SLOVENIA": "SI",
        "SOUTH AFRICA": "ZA",
        "SOUTH KOREA": "KR",
        "SPAIN": "ES",
        "SWEDEN": "SE",
        "SWITZERLAND": "CH",
        "TAIWAN": "TW",
        "TANZANIA": "TZ",
        "THAILAND": "TH",
        "TRINIDAD AND TOBAGO": "TT",
        "TURKEY": "TR",
        "TÜRKIYE": "TR",
        "UKRAINE": "UA",
        "UNITED ARAB EMIRATES": "AE",
        "UNITED KINGDOM": "GB",
        "UNITED STATES": "US",
        "URUGUAY": "UY",
        "UZBEKISTAN": "UZ",
        "VIETNAM": "VN",
    }

    # Add issuer country code column
    nbim_df["issuer_country_code"] = nbim_df["issuer_country_name"].map(
        country_codes
    )
    unmapped = sorted(
        nbim_df.loc[
            nbim_df["issuer_country_code"].isna(), "issuer_country_name"
        ].unique()
    )
    if unmapped:
        logger.warning(
            "No country code for NBIM issuer countries %s; add them to the "
            "map in _process_nbim_investments.",
            unmapped,
        )

    # Set USD market value column (values are native USD, x1)
    nbim_df["security_market_value_amount_usd"] = nbim_df[
        "security_market_value_amount"
    ]

    # Finalize columns
    return nbim_df[
        [
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
            "security_vintage_year",
            "security_type",
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
        ]
    ]


# Metadata for each tab of the pension fund workbook, keyed on the tab name
# (PENSION_FUND_REFRESH.md § 4.1). `source` strings for funds already in
# prod are kept verbatim so each load is a clean per-source replace;
# `investor_name` is the About-page spelling (uppercased on load, like every
# other investor name in the table) and deliberately does *not* come from
# the sheet's `Shareholder - Name`, which varies between rows.
# `multiplier` is used when the tab has no multiplier value; `currency`
# when it has no currency value; `assert_currency` fails the run if any
# row's currency differs (AP7's values are SEK whatever the sheet says).
# Sampension has no tab today (§ 3.3) but keeps its entry so the
# re-scraped tab loads without a code change.
PENSION_FUND_TABS: dict[str, dict] = {
    "AMF (checked)": {
        "source": "AMF PENSIONSFÖRSÄKRING AB",
        "investor_abbreviation": "AMF",
        "investor_name": "AMF Pension",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
    },
    "AP2 (checked)": {
        "source": "ANDRA AP-FONDEN",
        "investor_abbreviation": "AP2",
        "investor_name": "Andra AP-Fonden",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
    },
    "AP3 (checked)": {
        "source": "TREDJE AP-FONDEN",
        "investor_abbreviation": "AP3",
        "investor_name": "Tredje AP-fonden",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
    },
    "AP4 (checked)": {
        "source": "FJÄRDE AP-FONDEN",
        "investor_abbreviation": "AP4",
        "investor_name": "Fjärde AP-fonden",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
        "map_percent_ownership": True,
    },
    "AP7 (checked)": {
        "source": "SJUNDE AP-FONDEN",
        "investor_abbreviation": "AP7",
        "investor_name": "Sjunde AP-fonden",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
        "multiplier": "x1",
        "assert_currency": "SEK",
    },
    "BPFBOUW (checked)": {
        "source": "BOUWNIJVERHEID",
        "investor_abbreviation": "bpfBOUW",
        "investor_name": "bpfBOUW",
        "investor_country_name": "NETHERLANDS",
        "investor_country_code": "NL",
    },
    "DANICA (checked)": {
        "source": "DANICA PENSION LIVSFORSIKRINGS AB",
        "investor_abbreviation": "",
        "investor_name": "Danica Pension",
        "investor_country_name": "DENMARK",
        "investor_country_code": "DK",
    },
    "KPA (checked)": {
        "source": "KPA PENSIONSFORSAKRING",
        "investor_abbreviation": "KPA",
        "investor_name": "KPA Pension",
        "investor_country_name": "SWEDEN",
        "investor_country_code": "SE",
    },
    "LACERA (checked)": {
        "source": "LOS ANGELES COUNTY EMPLOYEES RETIREMENT ASSOCIATION",
        "investor_abbreviation": "LACERA",
        "investor_name": "Los Angeles County Employees Retirement Association",
        "investor_country_name": "UNITED STATES",
        "investor_country_code": "US",
        "investor_region_name": "CALIFORNIA",
        "investor_region_code": "US-CA",
        "multiplier": "x1",
        "currency": "USD",
    },
    "PENSION DANMARK (checked)": {
        "source": "PENSIONDANMARK PENSIONSFORSIKRING A/S",
        "investor_abbreviation": "",
        "investor_name": "PensionDanmark",
        "investor_country_name": "DENMARK",
        "investor_country_code": "DK",
    },
    "PKA (checked)": {
        "source": "PENSIONSKASSERNES ADMINISTRATION A/S",
        "investor_abbreviation": "PKA",
        "investor_name": "Pensionskassernes Administration",
        "investor_country_name": "DENMARK",
        "investor_country_code": "DK",
        "multiplier": "x1",
    },
    "PME (checked)": {
        "source": "PENSIOENFONDS VAN DE METALEKTRO",
        "investor_abbreviation": "PME",
        "investor_name": "PME pensioenfonds",
        "investor_country_name": "NETHERLANDS",
        "investor_country_code": "NL",
        "multiplier": "x1",
    },
    "PMT (checked)": {
        "source": "PENSIOENFONDS METAAL EN TECHNIEK",
        "investor_abbreviation": "PMT",
        "investor_name": "Metal and Technology Pension Fund",
        "investor_country_name": "NETHERLANDS",
        "investor_country_code": "NL",
        "multiplier": "x1",
    },
    "RAILOV (checked)": {
        "source": "PENSIOENFONDS RAIL & OV",
        "investor_abbreviation": "Rail & OV",
        "investor_name": "Rail & OV",
        "investor_country_name": "NETHERLANDS",
        "investor_country_code": "NL",
        "multiplier": "x1",
    },
    "SAMPENSION (checked)": {
        "source": "SAMPENSION ADMINISTRATIONSSELSKAB A/S",
        "investor_abbreviation": "",
        "investor_name": "Sampension",
        "investor_country_name": "DENMARK",
        "investor_country_code": "DK",
        "multiplier": "x1",
    },
    "VERVOER (checked)": {
        "source": "PENSIOENFONDS VERVOER",
        "investor_abbreviation": "",
        "investor_name": "Pensioenfonds Vervoer",
        "investor_country_name": "NETHERLANDS",
        "investor_country_code": "NL",
    },
}

# Workbook tabs that are not fund data
PENSION_FUND_SKIPPED_TABS = ("SOURCES",)

# Header renames applied to every tab (PENSION_FUND_REFRESH.md § 4.2.1)
PENSION_FUND_HEADER_RENAMES = {
    "Security - Market Value": "Security - Market Value - Amount",
    "Report Date URL": "Data Source URL",
}

# Header renames applied to one tab only: AP4's country column holds codes
PENSION_FUND_TAB_HEADER_RENAMES = {
    "AP4 (checked)": {"Issuer - Country Name": "Issuer - Country Code"},
}

# Every sheet column the parser reads, mapped to its release column. Tabs
# missing one of these get it added as empty.
PENSION_FUND_COLUMNS = {
    "Issuer - Name": "issuer_name",
    "Issuer - Country Name": "issuer_country_name",
    "Issuer - Country Code": "issuer_country_code",
    "Issuer - Sector": "issuer_sector",
    "Security - Type": "security_type",
    "Security - ISIN": "security_isin",
    "Security - Report Date": "document_report_date",
    "Security - Market Value - Currency Code": (
        "security_market_value_currency_code"
    ),
    "Security - Market Value - Amount": "security_market_value_amount",
    "Security - Market Value - Multiplier": (
        "security_market_value_multiplier"
    ),
    "Stock - Ticker": "stock_ticker",
    "Stock - Number of Shares": "stock_number_of_shares",
    "Stock - Percent Ownership": "stock_percent_ownership",
    "Stock - Percent Voting Power": "stock_percent_voting_power",
    "Data Source URL": "url",
}

# Issuer names that are really country subtotal lines (bpfBOUW, § 4.2.2)
PENSION_FUND_SUBTOTAL_ISSUERS = {"Hong Kong", "Saoedi-Arabië", "Zuid Korea"}

# Multiplier spellings after normalisation (lowercase, no `_`/spaces),
# mapped to the canonical spelling stored in the release, and the factor
# each applies to a market value
PENSION_FUND_MULTIPLIERS = {
    "x1": "x1",
    "x100": "x100",
    "x1000": "x1_000",
    "x1000000": "x1_000_000",
}
MULTIPLIER_FACTORS = {
    "x1": 1,
    "x100": 100,
    "x1_000": 1_000,
    "x1_000_000": 1_000_000,
}

ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def _parse_number(value: object) -> float:
    """Parses a sheet cell that should hold a number.

    Handles whitespace used as a digit grouping character (`1 146 640`),
    `,` as a thousands separator (`1,146,640`), `,` as a decimal mark when
    there is no `.` and at most two digits follow it (`0,04`), and a
    trailing `%`. Anything else that is not numeric becomes NaN.

    Args:
        value: The raw cell value.

    Returns:
        The parsed number, or NaN.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = re.sub(r"\s+", "", str(value)).rstrip("%")
    if "," in text and "." not in text:
        if re.fullmatch(r"-?\d+,\d{1,2}", text):
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return np.nan


def _parse_report_date(value: object) -> str:
    """Parses a sheet report date into an ISO `YYYY-MM-DD` string.

    Accepts real dates/timestamps and ISO strings; falls back to
    day-first parsing for strings such as `31-12-2025` (Danica).

    Args:
        value: The raw cell value.

    Returns:
        The date as `YYYY-MM-DD`, or an empty string if blank.

    Raises:
        ValueError: If the value cannot be read as a date.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if not text:
        return ""
    parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Cannot parse report date {value!r}.")
    return parsed.strftime("%Y-%m-%d")


def _canonical_multiplier(value: object, default: str) -> str:
    """Maps a sheet multiplier to its canonical spelling.

    Normalises spelling variants (`x1_00` → `x100`, `X1 000` → `x1_000`)
    and fails on anything that is not one of the four known multipliers.

    Args:
        value: The raw cell value.

        default: The multiplier to use when the cell is blank.

    Returns:
        One of `x1`, `x100`, `x1_000`, `x1_000_000`.

    Raises:
        ValueError: If the value is not a recognised multiplier.
    """
    raw = "" if value is None or pd.isna(value) else str(value).strip()
    if not raw:
        raw = default
    key = re.sub(r"[\s_,]", "", raw.lower())
    if key not in PENSION_FUND_MULTIPLIERS:
        raise ValueError(
            f"Unknown market value multiplier {value!r}; expected one of "
            f"{sorted(MULTIPLIER_FACTORS)}."
        )
    return PENSION_FUND_MULTIPLIERS[key]


def _read_pension_fund_tab(
    xls: pd.ExcelFile, tab: str, meta: dict
) -> pd.DataFrame:
    """Reads and cleans one fund tab of the pension fund workbook.

    Applies the per-tab rules of PENSION_FUND_REFRESH.md § 4.2: header
    normalisation, row drops (exact duplicates, blank issuers with no
    ISIN, country subtotal lines), number/date/ISIN/multiplier/currency
    parsing and the security type rules. Drop and ISIN-blanking counts are
    logged per tab.

    Args:
        xls: The open workbook.

        tab: The tab name (a key of `PENSION_FUND_TABS`).

        meta: The tab's entry in `PENSION_FUND_TABS`.

    Returns:
        The tab's rows with release column names, before investor
            metadata, country codes and USD conversion are added.
    """
    df = xls.parse(tab)
    n_in = len(df)

    # Normalise headers
    df.columns = [str(col).strip() for col in df.columns]
    df = df.rename(columns=PENSION_FUND_HEADER_RENAMES)
    df = df.rename(columns=PENSION_FUND_TAB_HEADER_RENAMES.get(tab, {}))
    for col in PENSION_FUND_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[list(PENSION_FUND_COLUMNS)].rename(columns=PENSION_FUND_COLUMNS)

    # Drop exact duplicate rows
    n_dupes = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # Tidy text columns
    for col in (
        "issuer_name",
        "issuer_country_name",
        "issuer_country_code",
        "issuer_sector",
        "security_type",
        "stock_ticker",
        "security_market_value_currency_code",
        "url",
    ):
        df[col] = df[col].apply(
            lambda val: (
                "" if pd.isna(val) else re.sub(r"\s+", " ", str(val)).strip()
            )
        )

    # ISIN: truncate glued-on text (AP3), blank anything malformed (LACERA)
    isin = df["security_isin"].apply(
        lambda val: "" if pd.isna(val) else str(val).strip().upper()[:12]
    )
    malformed = (isin != "") & ~isin.str.match(ISIN_PATTERN)
    n_bad_isin = int(malformed.sum())
    df["security_isin"] = isin.where(~malformed, "")

    # Drop rows with no issuer name and no (valid) ISIN
    blank_issuer = (df["issuer_name"] == "") & (df["security_isin"] == "")
    n_blank_issuer = int(blank_issuer.sum())
    df = df[~blank_issuer]

    # Drop country subtotal lines that came through as issuers
    subtotal = df["issuer_name"].isin(PENSION_FUND_SUBTOTAL_ISSUERS)
    n_subtotal = int(subtotal.sum())
    df = df[~subtotal]

    # Numbers
    df["security_market_value_amount"] = df[
        "security_market_value_amount"
    ].apply(_parse_number)
    df["stock_number_of_shares"] = (
        df["stock_number_of_shares"].apply(_parse_number).astype("Int64")
    )
    for col in ("stock_percent_ownership", "stock_percent_voting_power"):
        if meta.get("map_percent_ownership"):
            df[col] = df[col].apply(_parse_number)
        else:
            df[col] = np.nan

    # Dates
    df["document_report_date"] = df["document_report_date"].apply(
        _parse_report_date
    )

    # Multiplier (sheet value, else fund override, else x1)
    df["security_market_value_multiplier"] = (
        df["security_market_value_multiplier"]
        .apply(_canonical_multiplier, default=meta.get("multiplier", "x1"))
    )

    # Currency (sheet value, else fund default)
    currency = df["security_market_value_currency_code"].str.upper()
    df["security_market_value_currency_code"] = currency.where(
        currency != "", meta.get("currency", "")
    )
    expected_currency = meta.get("assert_currency")
    if expected_currency:
        others = df.loc[
            df["security_market_value_currency_code"] != expected_currency,
            "security_market_value_currency_code",
        ]
        if len(others):
            raise ValueError(
                f"Tab {tab!r}: expected every row's currency to be "
                f"{expected_currency}, found {sorted(others.unique())} on "
                f"{len(others)} rows."
            )

    # Security type
    has_value = df["security_market_value_amount"].notna()
    has_isin = df["security_isin"] != ""
    security_type = pd.Series("STOCKS", index=df.index)
    is_private_stock = (
        df["security_type"].str.upper() == "PRIVATE SWEDISH STOCK"
    )
    security_type[is_private_stock] = "PRIVATE EQUITY"
    if tab.startswith("AP3"):
        security_type[~has_value & ~has_isin] = "PRIVATE EQUITY FUND"
    df["security_type"] = security_type

    # URL must be present on every row
    if (df["url"] == "").any():
        raise ValueError(
            f"Tab {tab!r}: {int((df['url'] == '').sum())} rows have no "
            "Data Source URL."
        )

    logger.info(
        "Tab %r: %s rows in, %s out (dropped %s exact duplicates, %s blank "
        "issuers without ISIN, %s country subtotals); %s malformed ISINs "
        "blanked.",
        tab,
        f"{n_in:,}",
        f"{len(df):,}",
        n_dupes,
        n_blank_issuer,
        n_subtotal,
        n_bad_isin,
    )
    return df


def _process_pension_funds(
    data_fpath: Path, currency_map_fpath: Path
) -> pd.DataFrame:
    """Loads, cleans, and standardizes the pension fund workbook.

    Reads every fund tab of the workbook described in
    PENSION_FUND_REFRESH.md § 2 (one tab per fund, named `<FUND> (checked)`),
    applies the per-tab parsing rules of § 4.2 and the fund metadata of
    § 4.1, and converts market values to USD. The returned frame carries
    every column `_merge_datasets` expects, so it can be merged on its own.

    Args:
        data_fpath: The path to the pension fund workbook (`.xlsx`).

        currency_map_fpath: The path to a mapping between currency
            codes and codes of representative countries.

    Returns:
        A DataFrame of pension fund investments.

    Raises:
        ValueError: If the workbook has a tab that is not in
            `PENSION_FUND_TABS`, or a tab breaks one of the § 4.2 rules.
    """
    # Open workbook and check tab names against the metadata map
    xls = pd.ExcelFile(data_fpath)
    tabs = [t for t in xls.sheet_names if t not in PENSION_FUND_SKIPPED_TABS]
    unknown_tabs = sorted(set(tabs) - set(PENSION_FUND_TABS))
    if unknown_tabs:
        raise ValueError(
            f"Workbook {data_fpath.name} has tab(s) not in PENSION_FUND_TABS: "
            f"{unknown_tabs}. Add each fund's metadata before loading it."
        )
    missing_tabs = sorted(set(PENSION_FUND_TABS) - set(tabs))
    if missing_tabs:
        logger.info(
            "Tabs in PENSION_FUND_TABS but not in workbook: %s.", missing_tabs
        )

    # Read and clean each tab, then stamp it with the fund's metadata
    frames = []
    for tab in tabs:
        meta = PENSION_FUND_TABS[tab]
        tab_df = _read_pension_fund_tab(xls, tab, meta)
        tab_df["source"] = meta["source"]
        tab_df["investor_name"] = meta["investor_name"].upper()
        tab_df["investor_abbreviation"] = meta["investor_abbreviation"]
        tab_df["investor_country_name"] = meta["investor_country_name"]
        tab_df["investor_country_code"] = meta["investor_country_code"]
        tab_df["investor_region_name"] = meta.get("investor_region_name", "")
        tab_df["investor_region_code"] = meta.get("investor_region_code", "")
        frames.append(tab_df)
    pension_funds_df = pd.concat(frames, ignore_index=True)

    # Add constant columns
    pension_funds_df["investor_type"] = "PENSION FUND"
    pension_funds_df["document_filing_date"] = ""
    pension_funds_df["investor_cik"] = ""
    pension_funds_df["security_vintage_year"] = ""
    pension_funds_df["security_cusip"] = ""
    pension_funds_df["security_figi"] = ""

    # Add columns the workbook does not carry but the merge expects
    pension_funds_df["security_principal_amount_currency_code"] = ""
    pension_funds_df["security_principal_amount"] = np.nan
    pension_funds_df["stock_voting_auth_sole"] = np.nan
    pension_funds_df["stock_voting_auth_shared"] = np.nan
    pension_funds_df["stock_voting_auth_none"] = np.nan

    # Make text-based column values uppercase
    for col in ("issuer_name", "issuer_country_name", "issuer_sector"):
        pension_funds_df[col] = pension_funds_df[col].str.upper()

    # Define country code mapping
    country_codes = {
        "ARGENTINA": "AR",
        "AUSTRALIA": "AU",
        "AUSTRIA": "AT",
        "BELGIUM": "BE",
        "BERMUDA": "BM",
        "BRAZIL": "BR",
        "BRITISH VIRGIN ISLANDS": "VG",
        "BULGARIA": "BG",
        "BURKINA FASO": "BF",
        "CANADA": "CA",
        "CAYMAN ISLANDS": "KY",
        "CHILE": "CL",
        "CHINA": "CN",
        "COLOMBIA": "CO",
        "COSTA RICA": "CR",
        "CYPRUS": "CY",
        "CZECH REPUBLIC": "CZ",
        "CZECHIA": "CZ",
        "DENMARK": "DK",
        "DOMINICAN REPUBLIC": "DO",
        "EGYPT": "EG",
        "ESTONIA": "EE",
        "FINLAND": "FI",
        "FRANCE": "FR",
        "GEORGIA": "GE",
        "GERMANY": "DE",
        "GREECE": "GR",
        "GREENLAND": "GL",
        "GUATEMALA": "GT",
        "GUERNSEY": "GG",
        "HONDURAS": "HN",
        "HONG KONG": "HK",
        "HUNGARY": "HU",
        "ICELAND": "IS",
        "INDIA": "IN",
        "INDONESIA": "ID",
        "IRELAND": "IE",
        "ISRAEL": "IL",
        "ITALY": "IT",
        "JAPAN": "JP",
        "JERSEY": "JE",
        "KAZAKHSTAN": "KZ",
        "KOREA": "KR",
        "KUWAIT": "KW",
        "LIECHTENSTEIN": "LI",
        "LITHUANIA": "LT",
        "LUXEMBOURG": "LU",
        "MACAU": "MO",
        "MALAYSIA": "MY",
        "MALTA": "MT",
        "MAURITIUS": "MU",
        "MEXICO": "MX",
        "NETHERLANDS": "NL",
        "NEW ZEALAND": "NZ",
        "NIGERIA": "NG",
        "NORWAY": "NO",
        "OMAN": "OM",
        "PANAMA": "PA",
        "PARAGUAY": "PY",
        "PERU": "PE",
        "PHILIPPINES": "PH",
        "POLAND": "PL",
        "PORTUGAL": "PT",
        "QATAR": "QA",
        "ROMANIA": "RO",
        "RUSSIA": "RU",
        "SAUDI ARABIA": "SA",
        "SERBIA": "RS",
        "SINGAPORE": "SG",
        "SLOVAKIA": "SK",
        "SLOVENIA": "SI",
        "SOUTH AFRICA": "ZA",
        "SOUTH KOREA": "KR",
        "SPAIN": "ES",
        "SWEDEN": "SE",
        "SWITZERLAND": "CH",
        "TAIWAN": "TW",
        "TANZANIA": "TZ",
        "THAILAND": "TH",
        "TRINIDAD AND TOBAGO": "TT",
        "TURKEY": "TR",
        "UKRAINE": "UA",
        "UNITED ARAB EMIRATES": "AE",
        "UNITED KINGDOM": "GB",
        "UNITED STATES": "US",
        "URUGUAY": "UY",
        "UZBEKISTAN": "UZ",
        "VIETNAM": "VN",
    }

    # Fill issuer country codes from names (PensionDanmark, PME) and
    # names from codes (AP2, AP4); for codes with several names the
    # alphabetically last wins (CZECHIA, SOUTH KOREA)
    country_names = {
        code: name for name, code in sorted(country_codes.items())
    }
    has_name = pension_funds_df["issuer_country_name"] != ""
    has_code = pension_funds_df["issuer_country_code"] != ""
    pension_funds_df.loc[has_name & ~has_code, "issuer_country_code"] = (
        pension_funds_df.loc[has_name & ~has_code, "issuer_country_name"]
        .map(country_codes)
        .fillna("")
    )
    pension_funds_df.loc[has_code & ~has_name, "issuer_country_name"] = (
        pension_funds_df.loc[has_code & ~has_name, "issuer_country_code"]
        .map(country_names)
        .fillna("")
    )
    unmapped = sorted(
        pension_funds_df.loc[
            has_name & (pension_funds_df["issuer_country_code"] == ""),
            "issuer_country_name",
        ].unique()
    )
    if unmapped:
        logger.warning(
            "No country code for issuer countries %s; add them to the map "
            "in _process_pension_funds.",
            unmapped,
        )

    # Fetch exchange rate to USD for each currency and report year
    converter = CurrencyConverter(currency_map_fpath)
    rate_keys = pension_funds_df[
        ["security_market_value_currency_code", "document_report_date"]
    ].drop_duplicates()
    rates = {
        (currency, date): converter.get_usd_exchange_rate(
            currency=currency, year=date[:4]
        )
        for currency, date in rate_keys.itertuples(index=False)
    }
    pension_funds_df["security_market_value_conversion_rate"] = [
        rates[(currency, date)]
        for currency, date in zip(
            pension_funds_df["security_market_value_currency_code"],
            pension_funds_df["document_report_date"],
        )
    ]
    pension_funds_df["security_market_value_conversion_rate"] = (
        pension_funds_df["security_market_value_conversion_rate"].astype(float)
    )
    no_rate = (
        pension_funds_df["security_market_value_amount"].notna()
        & pension_funds_df["security_market_value_conversion_rate"].isna()
    )
    if no_rate.any():
        missing_rates = pension_funds_df.loc[
            no_rate,
            ["security_market_value_currency_code", "document_report_date"],
        ]
        logger.warning(
            "No exchange rate for %s rows with a market value "
            "(currency, year): %s.",
            f"{int(no_rate.sum()):,}",
            sorted(
                set(
                    zip(
                        missing_rates["security_market_value_currency_code"],
                        missing_rates["document_report_date"].str[:4],
                    )
                )
            ),
        )

    # Calculate market value in USD
    pension_funds_df["security_market_value_amount_usd"] = (
        (
            pension_funds_df["security_market_value_amount"]
            * pension_funds_df["security_market_value_multiplier"].map(
                MULTIPLIER_FACTORS
            )
            * pension_funds_df["security_market_value_conversion_rate"]
        )
        .round()
        .astype("Int64")
    )

    # Finalize columns
    return pension_funds_df[
        [
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
            "security_vintage_year",
            "security_type",
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
        ]
    ]


def _process_sec_investments(
    data_fpath: Path, pension_fund_labels_fpath: Path
) -> pd.DataFrame:
    """Loads, cleans, and standardizes Form 13F investments from the S.E.C.

    Args:
        data_fpath: The path to the Form 13F investments file.

        pension_fund_labels_fpath: The path to a CSV file identifying
            which S.E.C. filers are pension funds.

    Returns:
        A DataFrame of cleaned Form 13F investments.
    """
    # Read file using DuckDB
    db = duckdb.connect()
    sec_df = db.query(
        f"SELECT * FROM read_csv_auto('{data_fpath.as_posix()}', encoding='ISO_8859_1')"
    ).df()

    # Perform initial clean of stock issuer column to prepare for filtering
    sec_df.loc[:, "stock_issuer"] = sec_df["stock_issuer"].apply(
        lambda val: re.sub(r"\s{2,}", " ", val.strip())
    )

    # Define values that represent new, missing, or confidential issuers
    new_issuer = ["NEW ISSUER"]
    missing_issuer = [
        "0",
        "N/A",
        "NA",
        "NO SECURITIES",
        "NONE",
        "NO REMAINING HOLDINGS",
        "-",
        "NULL",
        "",
        "NONE TO REPORT",
        "NIL",
        "ISSUER",
        "NONE",
        "",
        "---",
        "#N/A INVALID SECURITY",
    ]
    confidential_issuer = ["CONFIDENTIAL", "CONFIDENTIAL TREATMENT REQUESTED"]

    # Drop rows representative of empty submissions
    has_empty_cusip = sec_df["stock_cusip"] == "000000000"
    has_missing_issuer = sec_df["stock_issuer"].isin(missing_issuer)
    sec_df = sec_df[~(has_empty_cusip & has_missing_issuer)]

    # Standardize remaining CUSIP values
    sec_df["stock_cusip"] = sec_df["stock_cusip"].str.replace("000000000", "")

    # Standardize stock issuer values
    def standardize_stock_issuer(value: str) -> str:
        """Maps a stock issue value to a special category if applicable.

        Args:
            value: The raw value.

        Returns:
            The mapped value.
        """
        if value in new_issuer or value in missing_issuer:
            return "NOT DISCLOSED"
        elif value in confidential_issuer:
            return "CONFIDENTIAL"
        else:
            return value

    sec_df.loc[:, "stock_issuer"] = sec_df["stock_issuer"].apply(
        standardize_stock_issuer
    )

    # Rename columns
    mapped_sec_df = sec_df.rename(
        columns={
            "form_report_date": "document_report_date",
            "form_filing_date": "document_filing_date",
            "investor_country": "investor_country_name",
            "investor_region": "investor_region_name",
            "stock_title_class": "security_type",
            "stock_figi": "security_figi",
            "stock_cusip": "security_cusip",
            "stock_issuer": "issuer_name",
            "stock_value_x1000": "security_market_value_amount",
            "form_url": "url",
        }
    )

    # Add new columns
    mapped_sec_df.loc[:, ["source"]] = (
        "U.S. SECURITIES AND EXCHANGE COMMISSION (SEC)"
    )
    mapped_sec_df.loc[:, ["investor_abbreviation"]] = ""
    mapped_sec_df.loc[:, ["investor_region_code"]] = ""
    mapped_sec_df.loc[:, ["issuer_country_name"]] = ""
    mapped_sec_df.loc[:, ["issuer_country_code"]] = ""
    mapped_sec_df.loc[:, ["issuer_sector"]] = ""
    mapped_sec_df.loc[:, ["security_isin"]] = ""
    mapped_sec_df.loc[:, ["security_market_value_currency_code"]] = "USD"
    mapped_sec_df.loc[:, ["security_market_value_multiplier"]] = "x1_000"
    mapped_sec_df.loc[:, ["security_market_value_conversion_rate"]] = 1
    mapped_sec_df.loc[:, ["security_market_value_amount_usd"]] = mapped_sec_df[
        "security_market_value_amount"
    ]
    mapped_sec_df.loc[:, ["security_principal_amount_currency_code"]] = "USD"
    mapped_sec_df.loc[:, ["security_principal_amount"]] = mapped_sec_df.apply(
        lambda row: (
            row["stock_shares_prn_amt"]
            if row["stock_prn_amt"] == "PRN"
            else np.nan
        ),
        axis=1,
    )
    mapped_sec_df.loc[:, ["stock_number_of_shares"]] = mapped_sec_df.apply(
        lambda row: (
            row["stock_shares_prn_amt"]
            if row["stock_prn_amt"] == "SH"
            else np.nan
        ),
        axis=1,
    )
    mapped_sec_df.loc[:, ["stock_percent_voting_power"]] = np.nan

    # Subset columns to define logical order and drop those unused
    mapped_sec_df = mapped_sec_df[
        [
            "source",
            "document_report_date",
            "document_filing_date",
            "investor_cik",
            "investor_name",
            "investor_abbreviation",
            "investor_country_name",
            "investor_region_name",
            "investor_region_code",
            "issuer_name",
            "issuer_country_name",
            "issuer_country_code",
            "issuer_sector",
            "security_type",
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
            "stock_percent_voting_power",
            "stock_voting_auth_sole",
            "stock_voting_auth_shared",
            "stock_voting_auth_none",
            "url",
        ]
    ]

    # Load pension fund labels
    sec_pension_funds_df = pd.read_csv(pension_fund_labels_fpath)

    # Use labels to assign investor type
    mapped_sec_df.loc[:, ["investor_type"]] = mapped_sec_df[
        "investor_name"
    ].apply(
        lambda name: (
            "PENSION FUND"
            if name.upper() in sec_pension_funds_df["name"].values
            else "INSTITUTIONAL INVESTOR"
        )
    )

    # Define country code mapping
    country_codes = {
        "ARGENTINA": "AR",
        "AUSTRALIA": "AU",
        "AUSTRIA": "AT",
        "BAMAHAS": "BS",
        "BELGIUM": "BE",
        "BERMUDA": "BM",
        "BRAZIL": "BR",
        "BRITISH VIRGIN ISLANDS": "VG",
        "BULGARIA": "BG",
        "BURKINA FASO": "BF",
        "CANADA": "CA",
        "CAYMAN ISLANDS": "KY",
        "CHILE": "CL",
        "CHINA": "CN",
        "COLOMBIA": "CO",
        "COSTA RICA": "CR",
        "CYPRUS": "CY",
        "CZECH REPUBLIC": "CZ",
        "CZECHIA": "CZ",
        "DENMARK": "DK",
        "DOMINICAN REPUBLIC": "DO",
        "EGYPT": "EG",
        "ESTONIA": "EE",
        "FINLAND": "FI",
        "FRANCE": "FR",
        "GEORGIA": "GE",
        "GERMANY": "DE",
        "GIBRALTAR": "GI",
        "GREECE": "GR",
        "GREENLAND": "GL",
        "GUAM": "GU",
        "GUATEMALA": "GT",
        "GUERNSEY": "GG",
        "HONDURAS": "HN",
        "HONG KONG": "HK",
        "HUNGARY": "HU",
        "ICELAND": "IS",
        "INDIA": "IN",
        "INDONESIA": "ID",
        "IRELAND": "IE",
        "ISLE OF MAN": "IM",
        "ISRAEL": "IL",
        "ITALY": "IT",
        "JAPAN": "JP",
        "JERSEY": "JE",
        "KAZAKHSTAN": "KZ",
        "KUWAIT": "KW",
        "LIECHTENSTEIN": "LI",
        "LITHUANIA": "LT",
        "LUXEMBOURG": "LU",
        "MACAU": "MO",
        "MALAYSIA": "MY",
        "MAURITIUS": "MU",
        "MEXICO": "MX",
        "MONACO": "MC",
        "NETHERLANDS": "NL",
        "NEW ZEALAND": "NZ",
        "NIGERIA": "NG",
        "NORWAY": "NO",
        "OMAN": "OM",
        "PANAMA": "PA",
        "PARAGUAY": "PY",
        "PERU": "PE",
        "PHILIPPINES": "PH",
        "POLAND": "PL",
        "PORTUGAL": "PT",
        "PUERTO RICO": "PR",
        "QATAR": "QA",
        "REPUBLIC OF KOREA": "KR",
        "ROMANIA": "RO",
        "RUSSIA": "RU",
        "SAUDI ARABIA": "SA",
        "SERBIA": "RS",
        "SINGAPORE": "SG",
        "SLOVAKIA": "SK",
        "SLOVENIA": "SI",
        "SOUTH AFRICA": "ZA",
        "SOUTH KOREA": "KR",
        "SPAIN": "ES",
        "SWEDEN": "SE",
        "SWITZERLAND": "CH",
        "TAIWAN": "TW",
        "TANZANIA": "TZ",
        "THAILAND": "TH",
        "TRINIDAD AND TOBAGO": "TT",
        "TURKEY": "TR",
        "UKRAINE": "UA",
        "UNITED ARAB EMIRATES": "AE",
        "UNITED KINGDOM": "GB",
        "UNITED STATES": "US",
        "URUGUAY": "UY",
        "UZBEKISTAN": "UZ",
        "VIETNAM": "VN",
    }
    mapped_sec_df.loc[:, ["investor_country_code"]] = (
        mapped_sec_df["investor_country_name"]
        .map(country_codes)
        .replace({np.nan: ""})
    )

    # Correct column types
    mapped_sec_df.loc[:, ["investor_region_name"]] = (
        mapped_sec_df["investor_region_name"]
        .replace({"nan": None})
        .replace({None: ""})
    )
    for col in ("security_type", "investor_country_name"):
        mapped_sec_df.loc[:, [col]] = mapped_sec_df[col].replace(
            {None: "", np.nan: ""}
        )

    # Drop erroneous records
    mapped_sec_df = mapped_sec_df.query("issuer_name != 'NULL'")

    return mapped_sec_df


def _merge_datasets(
    nbim_df: pd.DataFrame,
    pension_funds_df: pd.DataFrame,
    sec_df: pd.DataFrame,
    last_accessed_date: str,
) -> pd.DataFrame:
    """Combines equity datasets from NBIM, the SEC, and various pension funds.

    Aggregates records by unique security, summing market value, share counts,
    percent ownership, etc., when applicable.

    Args:
        nbim_df: A DataFrame of NBIM data.

        pension_funds_df: A DataFrame of pension funds data.

        sec_df: A DataFrame of SEC data.

        last_accessed_date: The value to use for the
            release's `last_accessed_date` column.

    Returns:
        A DataFrame containing all data from the three sources.
    """
    # Concatenate DataFrames
    merged_df = pd.concat(
        [sec_df, pension_funds_df, nbim_df], ignore_index=True
    )

    # Clean final date columns
    for col in ("document_report_date", "document_filing_date"):
        merged_df[col] = (
            merged_df[col]
            .astype(str)
            .apply(lambda dt: dt.split(" ")[0] if dt else "")
        )

    # Aggregate records by unique security
    final_df = (
        merged_df.groupby(
            by=[
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
                "security_cusip",
                "security_isin",
                "security_figi",
                "url",
            ],
            dropna=False,
        )
        .agg(
            {
                "security_vintage_year": "first",
                "security_principal_amount_currency_code": "first",
                "security_principal_amount": "sum",
                "security_market_value_currency_code": "first",
                "security_market_value_amount": "sum",
                "security_market_value_multiplier": "first",
                "security_market_value_conversion_rate": "first",
                "security_market_value_amount_usd": "sum",
                "stock_ticker": "first",
                "stock_number_of_shares": "sum",
                "stock_percent_ownership": "sum",
                "stock_percent_voting_power": "sum",
                "stock_voting_auth_sole": "sum",
                "stock_voting_auth_shared": "sum",
                "stock_voting_auth_none": "sum",
            }
        )
        .reset_index()
    )

    # Create text column
    def safe_get(row: pd.Series, col: str) -> str:
        """Returns a column value, or an empty string if the value is missing.

        Args:
            row: The data row/investment entry.

            col: The column name.

        Returns:
            The column value, or an empty string if the value is missing.
        """
        return row[col] if not pd.isna(row[col]) else ""

    def concatenate_fields(row: pd.Series) -> str:
        """Concatenates data fields for lookup.

        Args:
            row: The data row/investment entry.

        Returns:
            A relevant set of the row's fields, appended together.
        """
        raw_text = (
            safe_get(row, "investor_name")
            + " "
            + safe_get(row, "investor_abbreviation")
            + " "
            + safe_get(row, "investor_country_name")
            + " "
            + safe_get(row, "investor_country_code")
            + " "
            + safe_get(row, "issuer_name")
            + " "
            + safe_get(row, "issuer_country_name")
            + " "
            + safe_get(row, "issuer_country_code")
            + " "
            + safe_get(row, "issuer_sector")
            + " "
            + safe_get(row, "security_type")
            + " "
            + safe_get(row, "security_cusip")
            + " "
            + safe_get(row, "security_isin")
            + " "
            + safe_get(row, "security_figi")
            + " "
            + safe_get(row, "stock_ticker")
        )
        return " ".join(raw_text.split())

    final_df.loc[:, ["text"]] = final_df.apply(concatenate_fields, axis=1)

    # Finalize columns
    final_df = final_df[
        [
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
        ]
    ]

    # Correct column missing values
    for col in (
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
        "security_market_value_currency_code",
        "security_market_value_multiplier",
        "security_isin",
        "security_cusip",
        "security_figi",
        "stock_ticker",
    ):
        final_df.loc[:, [col]] = final_df[col].replace({np.nan: ""})

    # Correct data types for integer columns
    final_df = final_df.astype(
        {
            "stock_number_of_shares": "Int64",
            "stock_voting_auth_sole": "Int64",
            "stock_voting_auth_shared": "Int64",
            "stock_voting_auth_none": "Int64",
        }
    )

    # Replace zeroes with nulls in number columns
    for col in (
        "security_principal_amount",
        "security_market_value_amount",
        "security_market_value_amount_usd",
        "stock_number_of_shares",
        "stock_percent_ownership",
        "stock_percent_voting_power",
        "stock_voting_auth_sole",
        "stock_voting_auth_shared",
        "stock_voting_auth_none",
    ):
        final_df.loc[final_df[col] == 0, [col]] = np.nan

    # Add last accesssed date
    final_df.loc[:, "last_accessed_date"] = last_accessed_date

    return final_df


def _iso_date(value: str) -> str:
    """Validates a `YYYY-MM-DD` command line argument.

    Args:
        value: The raw argument value.

    Returns:
        The value, unchanged, if it is a valid `YYYY-MM-DD` date.

    Raises:
        argparse.ArgumentTypeError: If the value is not a `YYYY-MM-DD` date.
    """
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("wrong shape")
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"expected a date formatted as YYYY-MM-DD, got {value!r}"
        ) from e
    return value


def main() -> None:
    """Loads, cleans, and combines securities from three separate datasets.

    Args:
        `None`

    Returns:
        `None`
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Merges securities datasets into a combined release file."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--sec-only",
        action="store_true",
        help=(
            "Process only SEC Form 13F investments, skipping "
            "the NBIM and pension fund input files."
        ),
    )
    mode.add_argument(
        "--nbim-only",
        action="store_true",
        help=(
            "Process only the NBIM (Norges Bank) equity report, skipping "
            "the SEC and pension fund input files. "
            "Requires --nbim-report-date."
        ),
    )
    mode.add_argument(
        "--pension-only",
        action="store_true",
        help=(
            "Process only the pension fund workbook, skipping the SEC and "
            "NBIM input files. Requires --pension-file."
        ),
    )
    parser.add_argument(
        "--pension-file",
        type=Path,
        metavar="PATH",
        help=(
            "Path to the pension fund workbook (.xlsx) described in "
            "PENSION_FUND_REFRESH.md § 2. Required whenever the pension "
            "funds are processed."
        ),
    )
    parser.add_argument(
        "--nbim-report-date",
        type=_iso_date,
        metavar="YYYY-MM-DD",
        help=(
            "Snapshot date of the NBIM equity report. Required whenever NBIM "
            "is processed. Selects data/input/nbim_equity_<date>.csv and "
            "sets document_report_date and the row URL."
        ),
    )
    parser.add_argument(
        "--last-accessed-date",
        default=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
        help=(
            "Value for the release's last_accessed_date column. "
            "Defaults to today's date (UTC)."
        ),
    )
    args = parser.parse_args()

    # Decide which sources to process. A "--<source>-only" flag narrows the
    # set to that source; with no mode flag, every source is processed. To
    # add a mode (e.g., --pension-only), add the flag to the `mode` group
    # above and an `elif` here.
    all_sources = {"sec", "nbim", "pension"}
    if args.sec_only:
        sources = {"sec"}
    elif args.nbim_only:
        sources = {"nbim"}
    elif args.pension_only:
        sources = {"pension"}
    else:
        sources = set(all_sources)

    if "nbim" in sources and args.nbim_report_date is None:
        parser.error("--nbim-report-date is required when NBIM is processed.")
    if "pension" in sources and args.pension_file is None:
        parser.error(
            "--pension-file is required when the pension funds are processed."
        )

    # Configure logger (shared with the processing functions)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Define directory file paths
    parent_dir = Path(__file__).parents[1]
    data_dir = parent_dir / "data"
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"

    # Define input and output file paths
    currency_map_fpath = input_dir / "currency_country_map.json"
    sec_fpath = input_dir / "current_investments.csv"
    pension_fund_labels_fpath = input_dir / "sec_pension_funds.csv"

    # Record date of processing
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    # Load and clean each selected source
    skipped = sorted(all_sources - sources)
    if skipped:
        logger.info("Skipping sources: %s.", ", ".join(skipped))
    frames: dict[str, pd.DataFrame] = {}

    if "sec" in sources:
        logger.info("Processing SEC Form 13F investments.")
        frames["sec"] = _process_sec_investments(
            sec_fpath, pension_fund_labels_fpath
        )

    if "nbim" in sources:
        logger.info("Processing NBIM securities.")
        nbim_fpath = input_dir / f"nbim_equity_{args.nbim_report_date}.csv"
        frames["nbim"] = _process_nbim_investments(
            nbim_fpath, args.nbim_report_date
        )

    if "pension" in sources:
        logger.info("Processing pension fund securities.")
        frames["pension"] = _process_pension_funds(
            data_fpath=args.pension_file,
            currency_map_fpath=currency_map_fpath,
        )

    if sources == {"sec"}:
        # On its own, the SEC frame lacks the columns the external sources
        # would otherwise contribute during concatenation
        frames["sec"]["security_vintage_year"] = ""
        frames["sec"]["stock_percent_ownership"] = np.nan

    # Substitute an empty frame (same columns and dtypes as a processed
    # frame, so concatenation adds nothing) for each skipped source
    empty_df = next(iter(frames.values())).iloc[0:0]

    # Merge datasets
    logger.info("Merging datasets.")
    final_df = _merge_datasets(
        nbim_df=frames.get("nbim", empty_df),
        pension_funds_df=frames.get("pension", empty_df),
        sec_df=frames.get("sec", empty_df),
        last_accessed_date=args.last_accessed_date,
    )

    # Write output dataset to disk as CSV file
    logger.info("Writing output dataset to CSV file.")
    final_df.to_csv(
        output_dir / f"shareholder_tracker_release_{timestamp}.csv",
        sep="|",
        index=False,
        na_rep="NULL",
    )

    # Write output dataset to disk as Parquet file
    logger.info("Writing output dataset to Parquet file.")
    final_df.to_parquet(
        output_dir / f"shareholder_tracker_release_{timestamp}.parquet",
        index=False,
    )

    # Write output dataset to SQLite database
    logger.info("Writing output dataset to SQLite database.")
    conn = sqlite3.connect(
        output_dir / f"shareholder_tracker_release_{timestamp}.sqlite"
    )
    final_df.to_sql(
        name="investments",
        con=conn,
        if_exists="replace",
        index=False,
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred while running the data merge pipeline. {e}")
        exit(1)
