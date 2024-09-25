import { SVGProps } from "react";

export type IconSvgProps = SVGProps<SVGSVGElement> & {
  size?: number;
};

export type InvestmentSearchRequest = {
  cik: string | null;
  cusip: string | null;
  ticker: string | null;
  issuer: string | null;
  investor: string | null;
  document: string | null;
  limit: number;
  page: number;
  sortColumn: string;
  sortDirection: string;
};

export type Investment = {
  stock_id: string;
  investor_cik: string;
  investor_name: string;
  investor_former_names: string;
  investor_country: string;
  investor_region: string;
  other_investor_names: string[];
  form_accession_number: string;
  form_report_date: string;
  form_filing_date: string;
  stock_issuer: string;
  stock_cusip: string;
  stock_ticker: string;
  stock_value_x1000: string;
  stock_shares_prn_amt: string;
  stock_prn_amt: string;
  stock_voting_auth_sole: string;
  stock_voting_auth_shared: string;
  stock_voting_auth_none: string;
  form_url: string;
};

export type InvestmentSearchResult = {
  data: Investment[];
  total: number;
};
