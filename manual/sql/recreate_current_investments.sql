-- Recreates the `current_investments` materialized view in the production
-- database (Cloud SQL instance: shareholder-tracker:us-central1:idi-shareholder-db-prod).
--
-- This view is the export source for manual/main.py (dumped to
-- data/input/current_investments.csv at the repo root). It is the Django
-- Form13FStockInvestmentView SQL (backend/scrape/models.py) extended with:
--   * a concatenated `text` column and a `document` tsvector for search parity
--     with the `investment` table, and
--   * a WHERE clause pinning the snapshot to a single quarterly report date.
--
-- !! The report date is hard-coded. A REFRESH alone will NOT pick up a new
-- !! quarter -- you must edit the date below and re-run this whole script.
--
-- Depends on the immutable_date_to_string() function already present in prod.
-- DDL recovered from pg_matviews / \d on 2026-09-01.

DROP MATERIALIZED VIEW IF EXISTS current_investments;

CREATE MATERIALIZED VIEW current_investments AS
WITH t1 AS (
    SELECT investment.id AS stock_id,
        cmpy.cik AS investor_cik,
        cmpy.name AS investor_name,
        cmpy.former_names AS investor_former_names,
        place.country AS investor_country,
        place.state AS investor_region,
        to_jsonb(string_to_array(TRIM(BOTH FROM investment.other_manager), ','::text)) AS other_investor_numbers,
        managers.names AS other_investor_names,
        form.accession_number AS form_accession_number,
        form.report_date AS form_report_date,
        form.filing_date AS form_filing_date,
        upper((investment.issuer_name)::text) AS stock_issuer,
        investment.cusip AS stock_cusip,
        cusip_mapping.figi AS stock_figi,
        cusip_mapping.ticker AS stock_ticker,
        upper((cusip_mapping.security_type)::text) AS stock_description,
        investment.value_x1000 AS stock_value_x1000,
        investment.shares_prn_amt AS stock_shares_prn_amt,
        investment.sh_prn AS stock_prn_amt,
        investment.voting_auth_sole AS stock_voting_auth_sole,
        investment.voting_auth_shared AS stock_voting_auth_shared,
        investment.voting_auth_none AS stock_voting_auth_none,
        cusip_mapping.exchange_codes AS stock_exchange_codes,
        form.url AS form_url
    FROM (SELECT scraped_company.id,
                 scraped_company.cik,
                 upper(scraped_company.name) AS name,
                 jsonb_agg(upper(elem.value)) AS former_names,
                 scraped_company.state_or_country
          FROM scraped_company
          LEFT JOIN LATERAL jsonb_array_elements_text(scraped_company.former_names) elem(value) ON true
          GROUP BY scraped_company.id) cmpy
    JOIN scraped_form_submission form ON cmpy.id = form.company_id
    LEFT JOIN edgar_place_code place ON (cmpy.state_or_country)::text = (place.code)::text
    JOIN scraped_form_13f_investment investment ON form.id = investment.filing_id
    LEFT JOIN edgar_cusip_mapping cusip_mapping ON (investment.cusip)::text = (cusip_mapping.cusip)::text
    LEFT JOIN (SELECT clean_form_13f_stock_manager.stock_id,
                      array_agg(clean_form_13f_stock_manager.name) AS names
               FROM clean_form_13f_stock_manager
               GROUP BY clean_form_13f_stock_manager.stock_id) managers
        ON investment.id = managers.stock_id
), t2 AS (
    SELECT t1.*,
        concat(
            TRIM(BOTH FROM t1.investor_name), ' ',
            TRIM(BOTH FROM t1.stock_issuer), ' ',
            TRIM(BOTH FROM t1.stock_ticker), ' ',
            TRIM(BOTH FROM t1.stock_cusip), ' ',
            TRIM(BOTH FROM t1.stock_figi)
        ) AS text
    FROM t1
)
SELECT t2.*,
    to_tsvector('english'::regconfig, text) AS document
FROM t2
-- ============================================================================
-- TARGET QUARTER -- update this date each refresh (13F report period end):
WHERE form_report_date = '2026-06-30'::date;
-- ============================================================================

-- Indexes (recovered from \d current_investments)
CREATE UNIQUE INDEX current_investments_index ON current_investments (stock_id);
CREATE INDEX current_investments_document_idx ON current_investments USING gin (document);
CREATE INDEX current_investments_filing_date_idx ON current_investments (immutable_date_to_string(form_filing_date));
CREATE INDEX current_investments_report_date_idx ON current_investments (immutable_date_to_string(form_report_date));
CREATE INDEX current_investments_investor_name_idx ON current_investments (investor_name);
CREATE INDEX current_investments_stock_cusip_idx ON current_investments (stock_cusip);
CREATE INDEX current_investments_stock_issuer_idx ON current_investments (stock_issuer);
CREATE INDEX current_investments_stock_shares_prn_amt_idx ON current_investments (stock_shares_prn_amt);
CREATE INDEX current_investments_stock_ticker_idx ON current_investments (stock_ticker);
