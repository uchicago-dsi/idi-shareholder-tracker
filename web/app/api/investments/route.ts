"server only";

// Third-party imports
import { NextRequest, NextResponse } from "next/server";

// Application imports
import { sql } from "@/lib/db";

// Feature imports
import {
  Investment,
  InvestmentSearchRequest,
  InvestmentSearchResult,
} from "@/features/investments/interfaces";

/**
 * The maximum number of seconds the route can be executed on Vercel.
 * Up to 300 seconds is permitted on the Pro tier.
 */
export const maxDuration = 300;

/**
 * Forces dynamic rendering (i.e., the route is always rendered for each user at request time).
 */
export const dynamic = "force-dynamic";

/**
 * Fetches a page of investments matching a search query.
 *
 * @param request - The HTTP request. Contains the search term, limit and offset parameters, and the sorting column and direction.
 *
 * @returns A Promise containing the API response.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  // Parse JSON request body
  const searchParams: InvestmentSearchRequest = await request.json();

  // Prepare variables for dynamic SQL query
  const tsquerySearchPhrase = searchParams.query?.replace(/\s+/g, " ")?.trim();

  // Execute raw query
  const searchResults: Investment[] = await sql`
    SELECT
        id::text,
        source,
        document_report_date,
        investor_type,
        investor_cik,
        investor_name,
        investor_aliases,
        investor_country_name,
        investor_country_code,
        investor_region_name,
        investor_region_code,
        issuer_name,
        issuer_country_name,
        issuer_country_code,
        issuer_sector,
        security_type,
        security_vintage_year,
        security_principal_amount_currency_code,
        security_principal_amount,
        security_market_value_currency_code,
        security_market_value_amount,
        security_market_value_multiplier,
        security_market_value_conversion_rate,
        security_market_value_amount_usd,
        security_isin,
        security_cusip,
        security_figi,
        stock_ticker,
        stock_number_of_shares,
        stock_percent_ownership,
        stock_percent_voting_power,
        stock_voting_auth_sole,
        stock_voting_auth_shared,
        stock_voting_auth_none,
        url,
        last_accessed_date
    FROM investment ${
      searchParams.query
        ? sql`WHERE document @@ websearch_to_tsquery(${tsquerySearchPhrase + ":*"})`
        : sql``
    }
    ORDER BY ${sql(searchParams.sortColumn)} ${sql.unsafe(searchParams.sortDirection)}
    LIMIT ${searchParams.limit} OFFSET ${searchParams.offset};
    `;

  // Parse BigInt DB fields in search results to JS Number instances
  const parsedData = searchResults.map((r) => {
    r["security_principal_amount"] = Number(r["security_principal_amount"]);
    r["security_market_value_amount"] = Number(
      r["security_market_value_amount"],
    );
    r["security_market_value_amount_usd"] = Number(
      r["security_market_value_amount_usd"],
    );
    r["stock_number_of_shares"] = Number(r["stock_number_of_shares"]);
    r["stock_voting_auth_sole"] = Number(r["stock_voting_auth_sole"]);
    r["stock_voting_auth_shared"] = Number(r["stock_voting_auth_shared"]);
    r["stock_voting_auth_none"] = Number(r["stock_voting_auth_none"]);

    return r;
  });

  // Query database for total number of records with search phrase
  const tallyResult = await sql`
      SELECT COUNT(*)
      FROM investment ${
        searchParams.query
          ? sql`WHERE document @@ websearch_to_tsquery(${tsquerySearchPhrase + ":*"})`
          : sql``
      }
    `;

  // Parse result
  const count = Number(tallyResult[0]["count"]);

  // Compose response payload
  const payload: InvestmentSearchResult = {
    data: parsedData,
    totalRecords: count,
  };

  return NextResponse.json(payload);
}
