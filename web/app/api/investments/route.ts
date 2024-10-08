"server only";

/**
 * API route for investment search requests.
 *
 * References:
 * - https://nextjs.org/docs/app/api-reference/functions/next-request
 * - https://nextjs.org/docs/app/api-reference/functions/next-response
 * - https://github.com/prisma/prisma/issues/11584
 */

import { NextRequest, NextResponse } from "next/server";
import { Prisma } from "@prisma/client";

import prismaHelper from "@/services/db";
import {
  Investment,
  InvestmentSearchRequest,
  InvestmentSearchResult,
} from "@/types";
import prisma from "@/services/db";

export const maxDuration = 300;
export const dynamic = "force-dynamic";

/**
 * Searches for investments satisfying multiple
 * criteria and then returns a subset of the results.
 *
 *  @param {NextRequest} - The HTTP request. Contains the
 *      search term and the number of matches to return.
 */
export async function POST(request: NextRequest) {
  // Parse JSON request body
  let searchParams: InvestmentSearchRequest = await request.json();

  // Prepare variables for dynamic SQL query
  let sortCol = Prisma.sql([searchParams.sortColumn]);
  let sortDirection = Prisma.sql([
    searchParams.sortDirection == "ascending" ? "ASC" : "DESC",
  ]);
  let offset = searchParams.limit * (searchParams.page - 1);
  let hasFilters =
    searchParams.cik ||
    searchParams.ticker ||
    searchParams.cusip ||
    searchParams.investor ||
    searchParams.issuer ||
    searchParams.document;
  let formattedSearchPhrase = searchParams.document
    ?.replace(/\s+/g, " ")
    ?.trim();
  let tsquerySearchPhrase = formattedSearchPhrase?.replace(/\s+/g, " & ");

  // Execute raw query
  let searchResults: Investment[] = await prismaHelper.$queryRaw`
    SELECT
        stock_id::text,
        investor_cik,
        investor_name,
        investor_former_names,
        investor_country,
        investor_region,
        other_investor_names,
        form_accession_number,
        to_char(form_report_date, 'YYYY-MM-DD') as form_report_date,
        to_char(form_filing_date, 'YYYY-MM-DD') as form_filing_date,
        stock_issuer,
        stock_cusip,
        stock_ticker,
        stock_value_x1000::text,
        stock_shares_prn_amt,
        stock_prn_amt,
        stock_voting_auth_sole::text,
        stock_voting_auth_shared::text,
        stock_voting_auth_none::text,
        form_url
    FROM current_investments
    WHERE TRUE
    ${searchParams.cik ? Prisma.sql` AND investor_cik ILIKE ${"%" + searchParams.cik + "%"}` : Prisma.empty}
    ${searchParams.ticker ? Prisma.sql` AND stock_ticker ILIKE ${"%" + searchParams.ticker + "%"}` : Prisma.empty}
    ${searchParams.cusip ? Prisma.sql` AND stock_cusip ILIKE ${"%" + searchParams.cusip + "%"}` : Prisma.empty}
    ${searchParams.investor ? Prisma.sql` AND concat(investor_name, ' ', investor_former_names::text) ILIKE ${"%" + searchParams.cusip + "%"}` : Prisma.empty}
    ${searchParams.issuer ? Prisma.sql` AND stock_issuer ILIKE ${"%" + searchParams.issuer + "%"}` : Prisma.empty}
    ${searchParams.document ? Prisma.sql` AND document @@ to_tsquery(${tsquerySearchPhrase + ":*"})` : Prisma.empty}
    ORDER BY ${sortCol} ${sortDirection}
    ${!hasFilters ? Prisma.sql`LIMIT ${searchParams.limit} OFFSET ${offset}` : Prisma.empty}
    `;

  // Parse BigInt DB fields in search results to JS Number instances
  let parsed_data = searchResults.map((r) => {
    r["stock_shares_prn_amt"] = Number(r["stock_shares_prn_amt"]);

    return r;
  });

  // Determine total number of records for query and results to return
  let count = undefined;
  let data = undefined;

  if (!hasFilters) {
    count = await prisma.current_investments.count();
    data = parsed_data;
  } else {
    count = parsed_data.length;
    data = parsed_data.slice(offset, offset + searchParams.limit);
  }

  // Compose response payload
  let payload: InvestmentSearchResult = {
    data: data,
    total: count,
  };

  return NextResponse.json(payload);
}
