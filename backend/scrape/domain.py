"""Domain entities used across the application.
"""

# Standard library imports
from datetime import date
from typing import Any, Dict, List, Literal

# Third-party imports
import pandas as pd
from pydantic import BaseModel, computed_field


class ScrapedStreetAddress(BaseModel):
    """Represents a raw, non-standardized street address."""

    street: str = ""
    """The street number and name (e.g., "277 Bedford Ave")."""

    secondary: str = ""
    """The sub-premise (e.g., apartment, unit, suite) at the street address."""

    city: str = ""
    """The name of the locality or sublocality (e.g., "Brooklyn")."""

    state_or_country: str
    """The state or country (e.g., "NY", "Germany")."""

    zip_code: str = ""
    """The zip or postal code (e.g., "11211")."""

    @computed_field
    @property
    def formatted(self) -> str:
        """The full, formatted address
        (e.g., "277 Bedford Avenue, Brooklyn, NY 11211, USA").
        """
        fields = [
            self.street,
            self.city,
            self.state_or_country,
            self.zip_code if self.zip_code != "00000" else "",
        ]
        return ", ".join([f for f in fields if f])


class ScrapedFiling(BaseModel):
    """Represents a form submission made to the SEC."""

    form: str
    """The form type."""

    accession_number: str
    """The unique number identifying the submission. Consists of 
    ten digits representing the CIK of the entity used to submit the filing,
    followed by two digits that represent the current year, and a final set
    of digits assigned sequentially to the CIK starting with one on the
    first business day of each year. For more information, please see:
    https://www.sec.gov/files/edgar/filermanual/edgarfm-vol2-v70_c2.pdf
    """

    filing_date: str | None = None
    """The date the company submitted the form (e.g., "2019-10-31")."""

    report_date: str | None = None
    """The period for which the form was filed (e.g., "2019-09-28")."""

    url: str
    """The URL to the submitted form."""

    @staticmethod
    def create(
        parent_cik: str, recent_filings: Dict[str, List[Any]]
    ) -> List["ScrapedFiling"]:
        """Creates a collection of `Filing` instances from recent
        filings received from an SEC EDGAR Submissions API response.

        Args:
            parent_cik (`str`): The CIK of the parent company
                submitting the filings.

            recent_filings (`dict`): The recent filings. Keys
                are strings while values are lists of values.

        Returns:
            (`list` of `Filing`): The mapped filings.
        """
        # Parse filings into DataFrame
        df = pd.DataFrame(recent_filings)

        # Return empty list if DataFrame empty
        if df.empty:
            return []

        # Otherwise, instantiate filings
        df["formattedAccessionNumber"] = df["accessionNumber"].str.replace(
            "-", ""
        )
        df["filingUrl"] = df.apply(
            lambda r: (
                f"https://www.sec.gov/Archives/edgar/data/{parent_cik}"
                f"/{r.formattedAccessionNumber}/{r.accessionNumber}-index.htm"
            ),
            axis=1,
        )
        return [
            ScrapedFiling(
                form=row["form"],
                accession_number=row["accessionNumber"],
                filing_date=row["filingDate"] or None,
                report_date=row["reportDate"] or None,
                url=row["filingUrl"],
            )
            for _, row in df.iterrows()
        ]


class ScrapedCompany(BaseModel):
    """Represents a company filing to the SEC."""

    cik: str
    """The company's central index number (CIK)."""

    name: str
    """The company name."""

    former_names: List[str] = []
    """The former names of the company, if any."""

    address: ScrapedStreetAddress
    """The company's business address, or if not provided, mailing address."""

    recent_filings: List[ScrapedFiling] = []
    """The filer's form submissions from the past calendar year or
    its 1,000 most recent submissions—whichever number is greater.
    """

    @staticmethod
    def create(submission: Dict) -> "ScrapedCompany":
        """Creates a company with recent filing information
        from an SEC EDGAR Submissions API response body.

        Args:
            submission (`dict`): The submission.

        Returns:
            (`ScrapedCompany`): The company instance.
        """
        # Map CIK
        cik = f"CIK{submission['cik'].zfill(10)}"

        # Map business address, falling back to mailing address if needed
        try:
            business_addr = submission["addresses"]["business"]
            address = ScrapedStreetAddress(
                street=business_addr.get("street1") or "",
                secondary=business_addr.get("street2") or "",
                city=business_addr.get("city") or "",
                state_or_country=business_addr["stateOrCountry"],
                zip_code=business_addr.get("zipCode") or "",
            )
        except KeyError:
            mailing_addr = submission["addresses"]["mailing"]
            address = ScrapedStreetAddress(
                street=mailing_addr.get("street1") or "",
                secondary=mailing_addr.get("street2") or "",
                city=mailing_addr.get("city") or "",
                state_or_country=mailing_addr.get("stateOrCountry") or "",
                zip_code=mailing_addr.get("zipCode") or "",
            )

        # Map company
        return ScrapedCompany(
            cik=cik,
            name=submission["name"],
            former_names=[
                entry["name"] for entry in submission["formerNames"]
            ],
            address=address,
            recent_filings=ScrapedFiling.create(
                parent_cik=cik, recent_filings=submission["filings"]["recent"]
            ),
        )

    def prune_recent_filings(
        self, form_types: List[str], start_date: date, end_date: date
    ) -> None:
        """Prunes the company's recent filings for those
        of the given form type(s), reported between the given
        start and end filing dates, inclusive.

        Args:
            form_types (`list` of `str`): The form types (e.g., "13F-HR").

            start_date (`date`): The earliest filing date for
                which submissions should be included.

            end_date (`date`): The latest filing date for which
                submissions should be included.

        Returns:
            `None`
        """
        matches = []
        for filing in self.recent_filings:
            if (
                (filing.form in form_types)
                and filing.filing_date
                and (filing.filing_date >= start_date.strftime("%Y-%m-%d"))
                and (filing.filing_date <= end_date.strftime("%Y-%m-%d"))
            ):
                matches.append(filing)
        self.recent_filings = matches


class ScrapedForm13FStock(BaseModel):
    """Represents an investment reported in a Form 13F submission."""

    form_accession_number: str
    """The unique identifier of the parent form submission."""

    issuer_name: str
    """The name of the company issuing the stock (e.g., "Adobe".)"""

    title_class: str
    """The title of the stock class (e.g., "COM")."""

    cusip: str
    """A unique identifier assigned to a financial security.
    Consists of nine alphanumeric characters (e.g., "00724F101").
    """

    value_x1000: int
    """The value of the security in thousands of dollars (e.g., 6,716,226)."""

    shares_prn_amt: int
    """The reported number of shares or percentage 
    owned in the security (e.g., 14,196).
    """

    sh_prn: Literal["SH", "PRN", ""]
    """The type of amount reported—"SH" for shares or "PRN" for percentage."""

    put_call: Literal["Put", "Call", ""]
    """The type of option contract, if applicable. A call option is a
    contract that gives the buyer the right to buy shares of an underlying
    stock at the strike price for a specified period of time, while a put
    option gives the buyer the right to sell shares at the strike price for
    a specified period of time. For more information, please see:
    https://www.sec.gov/resources-for-investors/investor-alerts-bulletins/ib_introductionoptions
    """

    investment_discretion: Literal["SOLE", "DFND", "OTR", ""]
    """Indicates whether the security was purchased under a sole or 
    shared authority on behalf of the institutional account. Options
    include sole ("SOLE"), defined ("DFND"), or other ("OTR").
    """

    other_manager: str
    """The sequence number of the other manager included 
    in the report, with whom investment discretion is shared.
    """

    voting_auth_sole: int
    """The number of shares for which the manager exercised sole authority."""

    voting_auth_shared: int
    """The number of shares for which the manager exercised shared authority."""

    voting_auth_none: int
    """The number of shares for which the manager exercised no authority."""


class ScrapedForm13FCoverPageManager(BaseModel):

    form_accession_number: str
    """The unique identifier of the parent form
    submission containing the manager information.
    """

    name: str
    """The manager name."""

    number: int
    """The manager number."""


class CusipMapping(BaseModel):
    """Financial metadata associated with a CUSIP number."""

    name: str = ""
    """The company issuing the security."""

    cusip: str
    """A unique identifier assigned to a financial security.
    Consists of nine alphanumeric characters (e.g., "00724F101").
    """

    figi: str = ""
    """The Financial Instrument Global Identifier (FIGI).
    A 12-character, alphanumeric randomly-generated id
    for the security.
    """

    composite_figi: str = ""
    """The composite FIGI code."""

    share_class_figi: str = ""
    """The highest tier of the FIGI hierarchy."""

    ticker: str = ""
    """The security's symbol on a stock exchange."""

    exchange_codes: List[str] = []
    """The three-letter mnemonics that identify the security's primary
    trading markets (e.g., "LSE" for the London Stock Exchange).
    """

    market_sector: str = ""
    """The market sector (e.g., "Equity")."""

    security_type: str = ""
    """The security type (e.g., "Common Stock")."""

    security_type_2: str = ""
    """An alternative, less specific security type."""

    security_description: str = ""
    """A description of the security.s"""


class ScrapedForm13FStockManagerList(BaseModel):
    """Represents a raw entry for a manager associated with a stock
    investment, as reported in a Form 13F information table.
    """

    form_id: int
    """The form submission id from the database table."""

    stock_id: int
    """The stock investment id from the database table."""

    names: str
    """A comma-delimited list of manager numbers/references.
    May contain extraneous characters and/or be improperly formatted.
    """


class CleanedForm13FStockManager(BaseModel):
    """Represents a cleaned entry for a manager associated with a stock
    investment, as reported in a Form 13F information table.
    """

    form_id: int
    """The form submission id from the database table."""

    stock_id: int
    """The stock investment id."""

    manager_name: str
    """"""

    manager_number: int
    """The manager number/reference."""


class ParsedForm13FStockManager(BaseModel):
    """Represents a manager parsed from a Form 13F stock
    investment disclosed in an information table. Due to
    the lack of form validation, some values will represent
    manager numbers and others, manager names.
    """

    is_number: bool
    """A boolean indicating whether the parsed
    value represents a manager number.
    """

    value: str
    """The parsed value."""
