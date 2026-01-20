# Standard library imports
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


def _process_nbim_investments(data_fpath: Path) -> pd.DataFrame:
    """Loads, cleans, and standardizes NBIM investments.

    Args:
        data_fpath: The path to the NBIM investments file.

    Returns:
        A DataFrame of NBIM investments.
    """
    # Read file
    nbim_df = pd.read_csv(data_fpath)

    # Add constant columns
    nbim_df["source"] = "NORGES BANK"
    nbim_df["document_report_date"] = "2025-06-30"
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
        "https://www.nbim.no/en/investments/all-investments#/2025-06-30/0-equity"
    )

    # Rename columns
    col_map = {
        "company": "issuer_name",
        "country": "issuer_country_name",
        "sector": "issuer_sector",
        "value (USD)": "security_market_value_amount",
        "ownership": "stock_percent_ownership",
    }
    nbim_df = nbim_df.rename(columns=col_map)

    # Make text-based column values uppercase
    for col in ("issuer_name", "issuer_country_name", "issuer_sector"):
        nbim_df.loc[:, [col]] = nbim_df[col].str.upper()

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

    # Add issuer country code column
    nbim_df["issuer_country_code"] = nbim_df["issuer_country_name"].map(
        country_codes
    )

    # Set USD market value column
    nbim_df.loc[:, ["security_market_value_amount_usd"]] = nbim_df[
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
            "security_market_value_currency_code",
            "security_market_value_amount",
            "security_market_value_multiplier",
            "security_market_value_conversion_rate",
            "security_market_value_amount_usd",
            "security_isin",
            "security_cusip",
            "security_figi",
            "stock_ticker",
            "url",
        ]
    ]


def _process_pension_funds(
    data_fpath: Path, currency_map_fpath: Path
) -> pd.DataFrame:
    """Loads, cleans, and standarizes pension fund data.

    Args:
        data_fpath: The path to the pension funds data file.

        currency_map_fpath: The path to a mapping between currency
            codes and codes of representative countries.

    Returns:
        A DataFrame of the pension funds data.
    """
    # Read Excel file
    xls = pd.ExcelFile(data_fpath)

    # Concatenate data from all sheets into a single DataFrame
    pension_funds_df = None
    for sheet in xls.sheet_names:
        if sheet not in ("Pension Fund Labeling"):
            sheet_df = xls.parse(sheet)
            sheet_df["Source"] = sheet
            sheet_df.columns = [col.strip() for col in sheet_df.columns]
            pension_funds_df = (
                sheet_df
                if pension_funds_df is None
                else pd.concat([pension_funds_df, sheet_df])
            )

    # Drop erroneous records at bottom of sheets
    pension_funds_df = pension_funds_df.query(
        "`Shareholder - Name` == `Shareholder - Name`"
    )

    # Drop rows with invalid share counts
    invalid_rows_idx = pension_funds_df[
        pension_funds_df["Stock - Number of Shares"].apply(
            lambda val: not pd.isna(val)
            and isinstance(val, str)
            and ("A" in val or "B" in val)
        )
    ].index
    pension_funds_df = pension_funds_df.drop(index=invalid_rows_idx)

    # Drop pension funds with missing or invalid issuer names
    excluded_issuers = [
        "BØRSNOTEREDE KAPITALANDELE I ALT",
        "UNOTEREDE KAPITALANDELE",
    ]
    pension_funds_df = pension_funds_df.query(
        "(`Issuer - Name` == `Issuer - Name`) & (`Issuer - Name` not in @excluded_issuers)"
    )

    # Drop rows with corporate bonds
    pension_funds_df = pension_funds_df.query(
        "`Security - Type` != 'CORPORATE BOND'"
    )

    # Drop pension sources that have not been properly verified
    excluded_sources = [
        "Pensioenfonds Detailhandel",
        "PMT pensioenfonds",
        "Pensioenfonds Rail & OV",
    ]
    pension_funds_df = pension_funds_df.query(
        "`Shareholder - Name` not in @excluded_sources"
    )

    # Rename columns
    col_map = {
        "Source": "source",
        "Shareholder - Name": "investor_name",
        "Issuer - Name": "issuer_name",
        "Issuer - Country Name": "issuer_country_name",
        "Issuer - Country Code": "issuer_country_code",
        "Issuer - Sector": "issuer_sector",
        "Security - Type": "security_type",
        "Security - ISIN": "security_isin",
        "Security - Report Date": "document_report_date",
        "Security - Market Value - Currency Code": "security_market_value_currency_code",
        "Security - Market Value - Amount": "security_market_value_amount",
        "Security - Market Value - Multiplier": "security_market_value_multiplier",
        "BB Ticker": "stock_ticker",
        "Stock - Percent Ownership": "stock_percent_ownership",
        "Stock - Number of Shares": "stock_number_of_shares",
        "Stock - Percent Voting Power": "stock_percent_voting_power",
        "Private Equity - Vintage Year": "security_vintage_year",
    }

    # Subset columns
    pension_funds_df = pension_funds_df[list(col_map.keys())].rename(
        columns=col_map
    )

    # Add constant columns
    pension_funds_df.loc[:, ["investor_type"]] = "Pension Fund"
    for col in (
        "investor_cik",
        "investor_region_name",
        "investor_region_code",
        "document_filing_date",
        "security_cusip",
        "security_figi",
    ):
        pension_funds_df.loc[:, [col]] = ""

    # Define investor abbreviation mapping
    investor_abbreviation_map = {
        "Copy of AMF": "AMF",
        "Copy of BPL": "BPL",
        "Copy of Fjarde AP Foreignshares": "AP4",
        "Copy of Fjarde APswedishshares": "AP4",
        "Copy of KPA": "KPA",
        "Copy of PFZW": "PFZW",
        "Copy of PKA": "PKA",
        "Copy of PME": "PME",
        "Copy of PMT": "PMT",
        "Copy of Sjunde AP": "AP7",
        "Copy of ap2 foreignequity": "AP2",
        "Copy of ap2swedishequity": "P2",
        "Copy of ap3foreignequity": "AP3",
        "Copy of ap3privateequity": "AP3",
        "Copy of ap3swedishequity": "AP3",
        "Copy of bpfbouw": "bpfBOUW",
        "Copy of danicapension": "",
        "Copy of detailhandel": "",
        "Copy of pansiondanmark": "",
        "Copy of rail+ov": "Rail & OV",
        "Copy of sampension": "",
        "Copy of stichting_pensioenfonds": "ABP",
        "Copy of vervoershares": "",
    }
    pension_funds_df.loc[:, ["investor_abbreviation"]] = pension_funds_df[
        "source"
    ].map(investor_abbreviation_map)

    # Correct issuer names
    pension_funds_df.loc[:, "issuer_name"] = pension_funds_df[
        "issuer_name"
    ].str.replace("ΜΟΝΕΤΑ MONEY BANK AS", "MONETA MONEY BANK AS")

    # Correct security types
    def correct_security_type(row: pd.Series) -> str:
        """Corrects a security type field by populating a missing value.

        Args:
            row: The investment.

        Returns:
            The corrected security type.
        """
        if row["source"] == "Copy of ap3privateequity":
            return "Private Equity Fund"
        elif not pd.isna(row["security_type"]) and row["security_type"] in (
            "FUND EQ"
        ):
            return "Equity Fund"
        else:
            return "Stocks"

    pension_funds_df.loc[:, ["security_type"]] = pension_funds_df.apply(
        correct_security_type, axis=1
    )

    # Correct vintage year column
    pension_funds_df["security_vintage_year"] = (
        pension_funds_df["security_vintage_year"]
        .fillna("")
        .astype(str)
        .str[:4]
    )

    # Define country name mapping
    country_map = {
        "": ["Empty"],
        "Argentina": ["Argentina", "Argentinie"],
        "British Virgin Islands": ["Britse Maagdeneilanden"],
        "Bulgaria": ["Bulgarije"],
        "Chile": ["Chili"],
        "Czechia": ["Czech Republic", "Tsjechie"],
        "Egypt": ["Egypt", "Egypte"],
        "Georgia": ["Georgie"],
        "Hong Kong": ["Hongkong"],
        "Hungary": ["Hungry"],
        "Israel": ["Isreal"],
        "Luxembourg": ["Luxemburg"],
        "Russia": ["Rusland"],
        "Serbia": ["Servie"],
        "Singapore": ["Singapore "],
        "Slovakia": ["Slowakije"],
        "Slovenia": ["Slovenie"],
        "South Korea": ["Korea Republic of"],
        "Ukraine": ["Oekra�ne"],
        "United Kingdom": ["United Kingdom "],
        "Uzbekistan": ["Oezbekistan"],
    }

    # Create reverse lookup to standardized country names
    lookup = {
        raw_val.upper(): std_val.upper()
        for std_val, lst in country_map.items()
        for raw_val in lst
    }

    # Standardize issuer country names
    pension_funds_df.loc[:, "issuer_country_name"] = (
        pension_funds_df["issuer_country_name"]
        .replace({np.nan: ""})
        .apply(
            lambda name: (
                lookup.get(name.upper())
                if name.upper() in lookup
                else name.upper()
            )
        )
    )

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
        "KUWAIT": "KW",
        "LITHUANIA": "LT",
        "LUXEMBOURG": "LU",
        "MACAU": "MO",
        "MALAYSIA": "MY",
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

    # Correct issuer country codes
    pension_funds_df.loc[:, ["issuer_country_code"]] = pension_funds_df.apply(
        lambda row: (
            country_codes.get(row["issuer_country_name"], "")
            if row["issuer_country_name"] in country_codes
            else row["issuer_country_name"]
        ),
        axis=1,
    )

    # Add investor country name and code
    investor_country_name_map = {
        "Copy of AMF": "SWEDEN",
        "Copy of BPL": "NETHERLANDS",
        "Copy of Fjarde AP Foreignshares": "SWEDEN",
        "Copy of Fjarde APswedishshares": "SWEDEN",
        "Copy of KPA": "SWEDEN",
        "Copy of PFZW": "NETHERLANDS",
        "Copy of PKA": "DENMARK",
        "Copy of PME": "NETHERLANDS",
        "Copy of PMT": "NETHERLANDS",
        "Copy of Sjunde AP": "SWEDEN",
        "Copy of ap2 foreignequity": "SWEDEN",
        "Copy of ap2swedishequity": "SWEDEN",
        "Copy of ap3foreignequity": "SWEDEN",
        "Copy of ap3privateequity": "SWEDEN",
        "Copy of ap3swedishequity": "SWEDEN",
        "Copy of bpfbouw": "NETHERLANDS",
        "Copy of danicapension": "DENMARK",
        "Copy of detailhandel": "NETHERLANDS",
        "Copy of pansiondanmark": "DENMARK",
        "Copy of rail+ov": "NETHERLANDS",
        "Copy of sampension": "DENMARK",
        "Copy of stichting_pensioenfonds": "NETHERLANDS",
        "Copy of vervoershares": "NETHERLANDS",
    }
    pension_funds_df.loc[:, ["investor_country_name"]] = pension_funds_df[
        "source"
    ].map(investor_country_name_map)
    pension_funds_df.loc[:, ["investor_country_code"]] = pension_funds_df[
        "investor_country_name"
    ].map(country_codes)

    # Correct share counts
    corrected_counts = pension_funds_df["stock_number_of_shares"].apply(
        lambda val: val.replace(" ", "") if isinstance(val, str) else val
    )

    # Cast counts to nullable integer column
    pension_funds_df.loc[:, ["stock_number_of_shares"]] = (
        pd.to_numeric(corrected_counts, errors="coerce")
        .replace({pd.NA: np.nan})
        .astype("Int64")
    )

    # Define function to correct security market value amounts
    def correct_market_value(row: pd.Series) -> float:
        """Correctly formats the market value amount."""
        if isinstance(row["security_market_value_amount"], str) and any(
            char.isalpha() for char in row["security_market_value_amount"]
        ):
            return np.nan
        elif row["source"] in (
            "Copy of Fjarde APswedishshares",
            "Copy of Fjarde AP Foreignshares",
            "Copy of ap2 foreignequity",
            "Copy of ap2swedishequity",
            "Copy of vervoershares",
        ):
            return (
                row["security_market_value_amount"]
                .replace(" ", "")
                .replace(",", "")
                if isinstance(row["security_market_value_amount"], str)
                else row["security_market_value_amount"]
            )
        elif row["source"] == "Copy of detailhandel":

            return (
                row["security_market_value_amount"].replace(".", "")
                if isinstance(row["security_market_value_amount"], str)
                else row["security_market_value_amount"]
            )
        else:
            return row["security_market_value_amount"]

    # Correct share counts and cast to nullable integer column
    pension_funds_df.loc[:, ["security_market_value_amount"]] = (
        pension_funds_df.apply(correct_market_value, axis=1).astype(float)
    )

    # Add URL column
    url_map = {
        "Copy of AMF": "https://www.amf.se/globalassets/pdf/rapporter/innehav_2024.pdf",
        "Copy of BPL": "https://www.bplpensioen.nl/sites/default/files/documenten/beleggingsoverzicht.pdf",
        "Copy of Fjarde AP Foreignshares": "https://www.ap4.se/globalassets/rapporter-och-innehav/2025/ap4-listed-shares-and-participations-2025-06-30.pdf",
        "Copy of Fjarde APswedishshares": "https://www.ap4.se/globalassets/rapporter-och-innehav/2025/ap4-listed-shares-and-participations-2025-06-30.pdf",
        "Copy of KPA": "https://www.kpa.se/globalassets/trycksaker/hallbarhet/kpa-innehav-30-oktober-2025.pdf",
        "Copy of PFZW": "https://www.pfzw.nl/over-pfzw/beleggen-voor-een-goed-pensioen/soorten-beleggingen.html",
        "Copy of PKA": "https://pka.dk/globalassets/_2-ansvarlighed/ansvarlige-investeringer/politikker-og-rapporter/beholdningsliste.pdf",
        "Copy of PME": "https://www.pmepensioen.nl/en/investments/we-do-invest-in",
        "Copy of PMT": "https://www.pmt.nl/over-pmt/zo-beleggen-we/waar-beleggen-we-in/aandelen-en-obligaties",
        "Copy of Sjunde AP": "https://www.ap7.se/english/ap7-equity-fund/",
        "Copy of ap2 foreignequity": "https://ap2.se/wp-content/uploads/2025/08/2025_6_30_Utlandska_Aktier_Hemsidan.pdf",
        "Copy of ap2swedishequity": "https://ap2.se/wp-content/uploads/2025/08/2025_6_30_Svenska_Aktier_Hemsidan.pdf",
        "Copy of ap3foreignequity": "https://a.storyblok.com/f/257759/x/21eb85d815/ap3-foreign-equity-holdings-30-june-2025.pdf",
        "Copy of ap3privateequity": "https://a.storyblok.com/f/257759/x/61b8d40700/ap3-private-equity-investments-june-30-2025.pdf",
        "Copy of ap3swedishequity": "https://a.storyblok.com/f/257759/x/1000eb0ade/ap3-swedish-equity-holdings-30-june-2025.pdf",
        "Copy of bpfbouw": "https://www.bpfbouw.nl/content/dam/bpfbouw/documenten/beleggen/bpfbouw-aandelenportefeuille.pdf",
        "Copy of danicapension": "https://danica.dk/-/media/pdf/danica-pension/dk/regnskaber/2024/q4/kapitalandele-31-12-2024.pdf",
        "Copy of detailhandel": "https://pensioenfondsdetailhandel.nl/content/pdfs/Beleggingen-Pensioenfonds-Detailhandel.pdf",
        "Copy of pansiondanmark": "https://www.pensiondanmark.com/en/investments/equity-list",
        "Copy of rail+ov": "https://railov.nl/documents/1174/Overzicht_beleggingen_MVB_voor_de_website_20241231.pdf",
        "Copy of sampension": "https://www.sampension.dk/3db25a/globalassets/global-media/dokumenter/shared-links---pdf/sampension/beholdningslister/20250831---aktieliste---sampension.pdf",
        "Copy of stichting_pensioenfonds": "https://www.abp.nl/content/dam/abp/documenten/beleggen/abp-beursgenoteerde-beleggingen.pdf",
        "Copy of vervoershares": "https://www.pfvervoer.nl/sites/default/files/documenten/overzicht-beleggingen.pdf",
    }
    pension_funds_df.loc[:, ["url"]] = pension_funds_df["source"].map(url_map)

    # Update source column
    source_map = {
        "Copy of AMF": "AMF Pensionsförsäkring AB",
        "Copy of BPL": "Stichting BPL Pensioen",
        "Copy of Fjarde AP Foreignshares": "Fjärde AP-fonden",
        "Copy of Fjarde APswedishshares": "Fjärde AP-fonden",
        "Copy of KPA": "KPA Pensionsforsakring",
        "Copy of PFZW": "Pensioenfonds Zorg en Welzijn",
        "Copy of PKA": "Pensionskassernes Administration A/S",
        "Copy of PME": "Pensioenfonds van de Metalektro",
        "Copy of PMT": "Pensioenfonds Metaal en Techniek",
        "Copy of Sjunde AP": "Sjunde AP-fonden",
        "Copy of ap2 foreignequity": "Andra AP-fonden",
        "Copy of ap2swedishequity": "Andra AP-fonden",
        "Copy of ap3foreignequity": "Tredje AP-fonden",
        "Copy of ap3privateequity": "Tredje AP-fonden",
        "Copy of ap3swedishequity": "Tredje AP-fonden",
        "Copy of bpfbouw": "Bouwnijverheid",
        "Copy of danicapension": "Danica Pension Livsforsikrings AB",
        "Copy of detailhandel": "Pensioenfonds Detailhandel",
        "Copy of pansiondanmark": "Pensiondanmark Pensionsforsikring A/S",
        "Copy of rail+ov": "Pensioenfonds Rail & OV",
        "Copy of sampension": "Sampension Administrationsselskab A/S",
        "Copy of stichting_pensioenfonds": "Stichting Pensioenfonds ABP",
        "Copy of vervoershares": "Pensioenfonds Vervoer",
    }
    pension_funds_df.loc[:, ["source"]] = (
        pension_funds_df["source"].map(source_map).str.upper()
    )

    # Capitalize text-based columns
    for col in (
        "investor_name",
        "investor_type",
        "issuer_name",
        "issuer_sector",
        "security_type",
    ):
        pension_funds_df.loc[:, [col]] = pension_funds_df[col].str.upper()

    # Replace NaNs with empty strings in text columns
    for col in (
        "issuer_country_name",
        "issuer_country_code",
        "issuer_name",
        "issuer_sector",
        "security_type",
        "security_isin",
        "document_report_date",
        "security_market_value_currency_code",
        "security_market_value_multiplier",
        "stock_ticker",
    ):
        pension_funds_df.loc[:, [col]] = pension_funds_df[col].replace(
            {np.nan: ""}
        )

    # Initialize currency converter
    converter = CurrencyConverter(currency_map_fpath)

    # Fetch exchange rate to USD for investment year and currency code
    pension_funds_df.loc[:, ["security_market_value_conversion_rate"]] = (
        pension_funds_df.apply(
            lambda row: converter.get_usd_exchange_rate(
                currency=row["security_market_value_currency_code"],
                year=str(row["document_report_date"])[:4],
            ),
            axis=1,
        )
    )

    # Correct market value multiplier
    pension_funds_df.loc[:, ["security_market_value_multiplier"]] = (
        pension_funds_df["security_market_value_multiplier"].replace(
            {"": "x1"}
        )
    )

    # Define local function to perform conversion
    def convert(row: pd.Series) -> int | None:
        """Converts nominal currency to USD.

        Args:
            row: A row of data from the DataFrame.

        Returns:
            The exchange rate to USD, or `None`
                if the rate cannot be determined.
        """
        if pd.isna(row["security_market_value_amount"]) or pd.isna(
            row["security_market_value_conversion_rate"]
        ):
            return np.nan
        converted_base_amount = int(
            row["security_market_value_amount"]
            * row["security_market_value_conversion_rate"]
        )
        multiplier_map = {
            "x1": 1,
            "x1_000": 1_000,
            "x1_000_000": 1_000_000,
        }
        return int(
            converted_base_amount
            * multiplier_map[row["security_market_value_multiplier"]]
        )

    # Calculate market value in USD
    pension_funds_df["security_market_value_amount_usd"] = (
        pension_funds_df.apply(convert, axis=1).astype("Int64")
    )

    return pension_funds_df


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
    mapped_sec_df.loc[:, ["investor_abbreviation"]] = mapped_sec_df[
        "investor_name"
    ].apply(lambda name: "NBIM" if name.upper() == "NORGES BANK" else "")
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
    nbim_df: pd.DataFrame, pension_funds_df: pd.DataFrame, sec_df: pd.DataFrame
) -> pd.DataFrame:
    """Combines equity datasets from NBIM, the SEC, and various pension funds.

    Aggregates records by unique security, summing market value, share counts,
    percent ownership, etc., when applicable.

    Args:
        nbim_df: A DataFrame of NBIM data.

        pension_funds_df: A DataFrame of pension funds data.

        sec_df: A DataFrame of SEC data.

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
    final_df.loc[:, "last_accessed_date"] = "2025-12-18"

    return final_df


def main() -> None:
    """Loads, cleans, and combines securities from three separate datasets.

    Args:
        `None`

    Returns:
        `None`
    """
    # Instantiate logger
    logger = logging.getLogger("MANUAL DATA MERGE")
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
    nbim_fpath = input_dir / "nbim-1765555755557.csv"
    pension_funds_fpath = (
        input_dir / "Pension Fund for Shareholder Tracker.xlsx"
    )
    currency_map_fpath = input_dir / "currency_country_map.json"
    sec_fpath = input_dir / "current_investments.csv"
    pension_fund_labels_fpath = input_dir / "sec_pension_funds.csv"

    # Record date of processing
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d")

    # Load and clean NBIM investments
    logger.info("Processing NBIM securities.")
    nbim_df = _process_nbim_investments(nbim_fpath)

    # Load and clean pension funds
    logger.info("Processing pension fund securites.")
    pension_funds_df = _process_pension_funds(
        data_fpath=pension_funds_fpath, currency_map_fpath=currency_map_fpath
    )

    # Load and clean SEC investments
    logger.info("Processing SEC Form 13F investments.")
    sec_df = _process_sec_investments(sec_fpath, pension_fund_labels_fpath)

    # Merge datasets
    logger.info("Merging datasets.")
    final_df = _merge_datasets(sec_df, pension_funds_df, nbim_df)

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
