/**
 * A generic interface for a data table column.
 */
export interface DataColumn {
  key: string;
  label: string;
  allowsSorting: boolean;
}

/**
 * A simple DTO for an investment retrieved from the database.
 */
export interface Investment {
  id: string;
  source: string;
  document_report_date: string;
  investor_type: string;
  investor_cik: string;
  investor_name: string;
  investor_aliases: string;
  investor_country_name: string;
  investor_country_code: string;
  investor_region_name: string;
  investor_region_code: string;
  issuer_name: string;
  issuer_country_name: string;
  issuer_country_code: string;
  issuer_sector: string;
  security_type: string;
  security_vintage_year: string;
  security_principal_amount_currency_code: string;
  security_principal_amount: number | null;
  security_market_value_currency_code: string;
  security_market_value_amount: number | null;
  security_market_value_multiplier: number | null;
  security_market_value_conversion_rate: number | null;
  security_market_value_amount_usd: number | null;
  security_isin: string;
  security_cusip: string;
  security_figi: string;
  stock_ticker: string;
  stock_number_of_shares: number | null;
  stock_percent_ownership: number | null;
  stock_percent_voting_power: number | null;
  stock_voting_auth_sole: number | null;
  stock_voting_auth_shared: number | null;
  stock_voting_auth_none: number | null;
  url: string;
}

/**
 * A generic interface for a search request.
 */
export interface InvestmentSearchRequest {
  query: string;
  limit: number;
  offset: number;
  sortColumn: string;
  sortDirection: "ASC" | "DESC";
}

/**
 * A generic interface for a search result.
 */
export interface InvestmentSearchResult {
  data: Investment[];
  totalRecords: number;
}
