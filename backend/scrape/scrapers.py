"""Scrapers for SEC EDGAR domain entities.
"""

# Standard library imports
import json
import logging
import os
import re
import time
from abc import ABC
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from typing import Iterator, List, Tuple

# Third-party imports
import requests
from bs4 import BeautifulSoup
from more_itertools import chunked
from stream_unzip import stream_unzip

# Application imports
from scrape.domain import (
    CusipMapping,
    ScrapedCompany,
    ScrapedForm13FCoverPageManager,
    ScrapedForm13FStock,
)

EDGAR_RATE_LIMIT_IN_SECONDS = 10


class EdgarScraper(ABC):
    """An abstract class for SEC Edgar scrapers."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initializes a new instance of a `SubmissionsScraper`.

        Args:
            logger (`logging.Logger`): A standard logger instance.

        Returns:
            `None`
        """
        # Parse environment variables
        try:
            user_agent = os.environ["EDGAR_API_USER_AGENT"]
        except KeyError as e:
            raise ValueError(
                "Unable to instantiate scraper. Missing "
                f'required environment variable "{e}".'
            )

        # Initialize fields
        self._headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
        self._logger = logger

    @property
    def sec_base_url(self) -> str:
        """The base URL for the U.S. SEC website."""
        return "https://www.sec.gov"


class BulkSubmissionsScraper(EdgarScraper):
    """Scrapes the SEC EDGAR submissions bulk archive zip file
    to extract company and form submission data and upsert those
    records to the database, as well as build URLs to the filed forms.

    For more information, please see:
    https://www.sec.gov/search-filings/edgar-application-programming-interfaces
    """

    @property
    def submissions_file_url(self) -> str:
        """The URL to the zip file."""
        return "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"

    def _stream_zip_file(self, chunk_size: int = 65536) -> Iterator[bytes]:
        """Yields the bytes of the submissions zip file in chunks.

        Args:
            chunk_size (`int`): The number of bytes per chunk.

        Returns:
            (`iterator` of `bytes`): The iterator.
        """
        with requests.get(
            self.submissions_file_url,
            headers=self._headers,
            timeout=None,
            stream=True,
        ) as r:
            yield from r.iter_content(chunk_size=chunk_size)

    def _process_file(
        self,
        file_name: str,
        file_size: int,
        file_contents: bytearray,
    ) -> ScrapedCompany | None:
        """Decodes and then parses the given submission file
        contents to extract an SEC company with filings.
        Returns `None` if the file type is invalid.

        Args:
            file_name (`str`): The name of the file.
                Used for informational display.

            file_size (`int`): The number of bytes contained
                in the file. Used for informational display.

            file_contents (`bytearray`): The raw file contents.

        Returns:
            (`ScrapedCompany` | `None`): The company.
        """
        # Log start of processing
        self._logger.info(
            f'Processing file "{file_name}" ({file_size:,} bytes).'
        )

        # Skip processing if file does not contain recent submissions
        if not re.match(r"CIK(0?\d{10})\.json", file_name):
            self._logger.info(
                "The file does not contain recent submissions. Skipping."
            )
            return None

        # Otherwise, decode and parse file contents
        submission = json.loads(file_contents.decode())

        # Map submission to scraped company model
        return ScrapedCompany.create(submission)

    def _process_file_batch(
        self,
        batch: List[Tuple[str, int, bytearray]],
        form_types: List[str],
        start_date: date,
        end_date: date,
    ) -> List[ScrapedCompany]:
        """Processes each file in the given batch by scraping and mapping the
        data to create an instance of a `ScrapedCompany` domain model. Files
        are processed in parallel using a multiprocessing pool and the results
        are then combined and filtered to include only those companies with
        filings of the given form type(s) and between the given start and end
        filing dates.

        Args:
            batch (`list` of (`str`, `int`, `bytearray`)): The files
                to process. Each item in the list is a three-item
                tuple consisting of the file name, file size in bytes,
                and file contents.

            form_types (`list` of `str`): The form types (e.g., "13F-HR").

            start_date (`date`): The earliest filing date for
                which submissions should be included.

            end_date (`date`): The latest filing date for which
                submissions should be included.

        Returns:
            (`list` of `ScrapedCompany`): The scraped companies.
        """
        # Process files in parallel
        try:
            self._logger.info("Processing file batch.")
            with ProcessPoolExecutor(max_workers=len(batch)) as executor:
                batch_results = executor.map(self._process_file, *zip(*batch))
        except Exception as e:
            raise RuntimeError(
                f"Failed to process batch of files in parallel. {e}"
            )

        # Combine and filter results
        pruned_companies = []
        for company in batch_results:

            # Skip files unable to be processed
            if not company:
                continue

            # Prune recent filings to include only matches
            company.prune_recent_filings(form_types, start_date, end_date)

            # If company contains matches, append to collection
            if company.recent_filings:
                pruned_companies.append(company)

        self._logger.info(
            f"Found {len(pruned_companies):,} companies with "
            f"one or more forms matching type and date range."
        )

        return pruned_companies

    def scrape(
        self,
        form_types: List[str],
        start_date: date,
        end_date: date,
        batch_size: int,
    ) -> Iterator[List[ScrapedCompany]]:
        """Scrapes the submissions data file for records matching
        one of the given form types and filed between the given
        start and end dates, inclusive. Yields results in batches.

        Args:
            form_types (`list` of `str`): The form types to extract.

            start_date (`date`): The earliest filing date for
                which submissions data should be included.

            end_date (`date`): The latest filing date for which
                submissions data should be included.

            batch_size (`int`): The number of files to process in parallel.

        Returns:
            (`list` of `ScrapedCompany`): The scraped company filing data.
        """
        # Log start of scraping
        self._logger.info(
            "Scraping submissions zip file for data pertaining "
            f"to filings submitted between {start_date.strftime('%Y-%m-%d')} "
            f"and {end_date.strftime('%Y-%m-%d')}, inclusive, for form "
            f"type(s) {', '.join(form_types)}."
        )

        # Initialize result variables
        current_batch = []

        # Stream zip file due to large size
        self._logger.info(
            "Streaming zip file to unzip and process each file in sequence."
        )
        for file_name, file_size, unzipped_chunks in stream_unzip(
            self._stream_zip_file()
        ):
            # Consolidate file chunks
            arr = bytearray()
            for chunk in unzipped_chunks:
                arr.extend(chunk)

            # Add file metadata and contents to batch
            current_batch.append((file_name.decode("utf-8"), file_size, arr))

            # Process batch data in parallel
            if len(current_batch) == batch_size:
                batch_results = self._process_file_batch(
                    current_batch, form_types, start_date, end_date
                )
                yield batch_results
                current_batch = []

        # Process remaining data
        if current_batch:
            batch_results = self._process_file_batch(
                current_batch, form_types, start_date, end_date
            )
            yield batch_results


class Form13FFilingDetailsScraper(EdgarScraper):
    """A webscraper for the SEC EDGAR filing detail page."""

    def scrape(self, url: str) -> Tuple[str, str]:
        """Requests the webpage detailing a company form
        submission and then parses the page's HTML to retrieve
        URLs to the form information table and cover page.

        Args:
            url (`str`): The URL to the form submission detail page.

        Returns:
            ((`str`, `str`)): A two-item tuple consisting of the
                URL to the form information table and the URL
                to the cover page.
        """
        # Request webpage
        r = requests.get(url, headers=self._headers)
        if not r.ok:
            raise Exception(
                "An error occurred fetching the filing detail page "
                f'at "{url}". The response returned a "{r.status_code}"'
                f'-{r.reason}" status code and the text "{r.text}".'
            )

        # Parse webpage into BeautifulSoup object
        soup = BeautifulSoup(r.text, "html.parser")

        # Find cells of information table
        table = soup.find("table", {"class": "tableFile"})
        info_type_cells = table.find_all("td", string="INFORMATION TABLE")

        # Iterate through cells until URL to HTML information table located
        info_tbl_url = None
        for cell in info_type_cells:
            info_tbl_cell = cell.parent.find("td", string=re.compile(".*html"))
            if info_tbl_cell:
                info_tbl_partial_url = info_tbl_cell.find("a")["href"]
                info_tbl_url = f"{self.sec_base_url}{info_tbl_partial_url}"
                break

        # Find URL to primary document/cover page
        primary_doc_cell = table.find(
            "td", string=re.compile("primary_doc.html")
        )
        primary_doc_parial_url = primary_doc_cell.find("a")["href"]
        primary_doc_url = f"https://www.sec.gov{primary_doc_parial_url}"

        return info_tbl_url, primary_doc_url


class Form13FStockScraper(EdgarScraper):
    """A webscraper for the SEC EDGAR Form 13F information table page."""

    def scrape(self, url: str) -> List[ScrapedForm13FStock]:
        """Scrapes an information table page for a Form 13F filing.

        Args:
            url (`str`): The URL to the information page.

        Returns:
            (`list` of `dict`): The investments.
        """
        # Request webpage
        r = requests.get(url, headers=self._headers)
        if not r.ok:
            raise Exception(
                "An error occurred fetching the Form 13F information table "
                f'at "{url}". The response returned a "{r.status_code}"'
                f'-{r.reason}" status code and the text "{r.text}".'
            )

        # Parse webpage into BeautifulSoup object
        soup = BeautifulSoup(r.text, "html.parser")

        # Extract investment rows from HTML
        table = soup.find("table", summary="Form 13F-NT Header Information")
        num_header_rows = 3
        investment_rows = table.find_all("tr")[num_header_rows:]

        def replace_null(value: str, replacement_value: str = "") -> str:
            """Local function to replace null or blank
            unicode values with a replacement value
            that defaults to `None`.

            Args:
                value (`str`): The raw string.

            Returns:
                (`str`): The cleaned string.
            """
            is_null = value in ("\u00a0", "Â")
            return replacement_value if is_null else value

        def get_digits(value: str) -> int:
            """Local function to convert a string representation of a
            number into an integer by removing commas and decimals.

            Args:
                value (`str`): The number string.

            Returns:
                (`int`): The parsed number.
            """
            try:
                stripped = value.replace(",", "").replace(".", "")
                return int(stripped)
            except Exception:
                raise Exception(
                    f'Value "{value}" could not be coerced into an integer.'
                )

        def build_accession_number(url: str) -> str:
            """Builds a form accession number from
            the stock information data table page URL.

            Args:
                url (`str`): The URL.

            Returns:
                (`str`): The accession number.
            """
            digits = url.split("/")[-3]
            return f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"

        # Generate investments
        investments = []
        for row in investment_rows:
            cells = row.find_all("td")
            investments.append(
                ScrapedForm13FStock(
                    form_accession_number=build_accession_number(url),
                    issuer_name=cells[0].text,
                    title_class=cells[1].text,
                    cusip=cells[2].text,
                    value_x1000=get_digits(cells[4].text),
                    shares_prn_amt=get_digits(cells[5].text),
                    sh_prn=cells[6].text.strip(),
                    put_call=replace_null(cells[7].text.strip()),
                    investment_discretion=replace_null(cells[8].text.strip()),
                    other_manager=replace_null(cells[9].text),
                    voting_auth_sole=get_digits(cells[10].text),
                    voting_auth_shared=get_digits(cells[11].text),
                    voting_auth_none=get_digits(cells[12].text),
                )
            )

        return investments


class Form13FCoverPageScraper(EdgarScraper):
    """A webscraper for the SEC EDGAR Form 13F cover page."""

    def scrape(self, url: str) -> List[ScrapedForm13FCoverPageManager]:
        """Scrapes a Form 13F cover page for the "other manager"
        names and numbers.

        Args:
            url (`str`): The URL to the cover page.

        Returns:
            (`list` of `ScrapedForm13FManager`): The managers.
        """
        # Build form accession number from URL
        digits = url.split("/")[-3]
        accession_number = f"{digits[:10]}-{digits[10:12]}-{digits[12:]}"

        # Request webpage
        r = requests.get(
            url,
            headers={
                "User-Agent": "University of Chicago launagreer@uchicago.edu",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        if not r.ok:
            raise Exception(
                "An error occurred fetching the Form 13F cover page "
                f'at "{url}". The response returned a "{r.status_code}"'
                f'-{r.reason}" status code and the text "{r.text}".'
            )

        # Parse webpage into BeautifulSoup object
        soup = BeautifulSoup(r.text, "html.parser")

        # Get table of other manager names
        table = soup.find(
            "table", summary="Report Summary Other Included Managers"
        )

        # Get data rows
        num_txt_rows = 3
        data_rows = table.find_all("tr")[num_txt_rows:]

        # Return empty list if no other managers listed
        if "NONE" in [r.text for r in data_rows]:
            return []

        # Parse header
        name_idx = None
        number_idx = None
        header = data_rows[0]
        for idx, td in enumerate(header.find_all("td", {"class": "FormText"})):
            if "name" == td.text.strip().lower():
                name_idx = idx
            if "no." == td.text.strip().lower():
                number_idx = idx

        if name_idx is None or number_idx is None:
            raise RuntimeError(
                "Failed to parse manager names and numbers from "
                "the webpage due to an unexpected HTML schema."
            )

        # Otherwise, map rows to manager instances
        managers = []
        for row in data_rows[1:]:
            cells = row.find_all("td", {"class": "FormData"})
            managers.append(
                ScrapedForm13FCoverPageManager(
                    form_accession_number=accession_number,
                    name=(
                        cells[name_idx].text.strip().upper()
                        if name_idx
                        else ""
                    ),
                    number=cells[number_idx].text.strip(),
                )
            )

        return managers


class OpenFigiApiClient:
    """An interface for fetching stock values and metadata."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initializes a new instance of an `OpenFigiApiClient`.

        Args:
            logger (`logging.Logger`): A standard logger instance.

        Raises:
            (`RuntimeError`) if any of the following environment variables
                are not present, or if their value is of an unexpected type:

            - `OPEN_FIGI_API_KEY`
            - `OPEN_FIGI_API_BASE_URL`
            - `OPEN_FIGI_MAX_JOBS_PER_REQUEST`
            - `OPEN_FIGI_MAX_REQUESTS_PER_WINDOW`
            - `OPEN_FIGI_REQUEST_WINDOW_SECONDS`

        Returns:
            `None`
        """
        # Set logger
        self._logger = logger

        # Parse environment variables
        try:
            self._api_key = os.environ["OPEN_FIGI_API_KEY"]
            self._api_base_url = os.environ["OPEN_FIGI_API_BASE_URL"]
            self._max_jobs_per_request = int(
                os.environ["OPEN_FIGI_MAX_JOBS_PER_REQUEST"]
            )
            self._max_requests_per_window = int(
                os.environ["OPEN_FIGI_MAX_REQUESTS_PER_WINDOW"]
            )
            self._request_window_seconds = int(
                os.environ["OPEN_FIGI_REQUEST_WINDOW_SECONDS"]
            )
        except KeyError as e:
            raise RuntimeError(
                "Missing environment variable " f'"{e}".'
            ) from None
        except ValueError as e:
            raise RuntimeError(
                "Failed to cast environment "
                "variable to expected data type. "
                f'"{e}".'
            ) from None

    def fetch_stock_metadata(
        self, cusips: List[str]
    ) -> Iterator[List[CusipMapping]]:
        """Fetches metadata (e.g., market sector, ticker symbol)
        for one or more stocks given their CUSIP numbers--unique
        nine-digit identification numbers assigned to stocks and
        registered bonds in the U.S. and Canada. The dataset is
        fetched from the Open Figi API run by the Object Management
        Group, an international, open membership, nonprofit
        technology standards consortium. NOTE: Requests are throttled,
        with rates based on whether an API key is used.

        Documentation:
        - [Rate Limit](https://www.openfigi.com/api#rate-limit)
        - [POST /v3/mapping](https://www.openfigi.com/api#post-v3-mapping)

        Args:
            cusips (`list` of `str`): The CUSIP numbers.

        Yields:
            (`list` of `CusipMapping`): The CUSIP and its
                associated stock metadata.
        """
        # Initialize variables
        num_requests = 0
        mapping_url = f"{self._api_base_url}/v3/mapping"
        batch_size = self._max_jobs_per_request
        headers = {
            "Content-Type": "application/json",
            "X-OPENFIGI-APIKEY": self._api_key,
        }

        # Process each cusip
        for idx, batch in enumerate(chunked(cusips, batch_size)):

            # Initialize stock metadata
            stock_metadata = []

            # Map batch of cusips to expected request body
            lookups = [{"idType": "ID_CUSIP", "idValue": c} for c in batch]

            # Make request to map third party identifiers to FIGIs
            self._logger.info(
                f"Requesting stock metadata for CUSIP batch {idx + 1}."
            )
            r = requests.post(url=mapping_url, headers=headers, json=lookups)
            num_requests += 1

            # Sleep and reattempt call if throttled
            if r.status_code == 429:
                self._logger.warning(
                    "Attempted too many calls. Sleeping "
                    f"for {self._request_window_seconds} "
                    "seconds."
                )
                time.sleep(self._request_window_seconds)
                r = requests.post(
                    url=mapping_url, headers=headers, json=lookups
                )
                num_requests += 1

            # Raise an exception if server returns an error
            if not r.ok:
                raise RuntimeError(
                    "The Open FIGI API server returned an error with "
                    f'the status code "{r.status} - {r.reason}" and '
                    f'the message: "{r.json()}".'
                )

            # Sleep if max requests has been reached
            if num_requests % self._max_requests_per_window == 0:
                time.sleep(self._request_window_seconds)

            # Collect stock metadata from response JSON
            for cusip, result in zip(batch, r.json()):
                if "data" in result:
                    metadata = result["data"][0]
                    stock_metadata.append(
                        CusipMapping(
                            name=metadata["name"] or "",
                            cusip=cusip,
                            figi=metadata["figi"] or "",
                            composite_figi=metadata["compositeFIGI"] or "",
                            share_class_figi=metadata["shareClassFIGI"] or "",
                            ticker=metadata["ticker"] or "",
                            exchange_codes=[
                                r["exchCode"]
                                for r in result["data"]
                                if r["exchCode"]
                            ],
                            market_sector=metadata["marketSector"] or "",
                            security_type=metadata["securityType"] or "",
                            security_type_2=metadata["securityType2"] or "",
                            security_description=metadata[
                                "securityDescription"
                            ]
                            or "",
                        )
                    )

            yield stock_metadata
