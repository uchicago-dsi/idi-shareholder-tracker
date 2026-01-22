// Third-party imports
import { z } from "zod";

/**
 * A validation schema for investment search requests.
 */
export const InvestmentSearchRequestSchema = z.object({
  query: z.string().optional().default(""),
  filter: z
    .enum(["Pension Fund", "Institutional Investor", "All Records"])
    .default("All Records"),
  sortColumn: z
    .enum([
      "investor_name",
      "issuer_name",
      "security_market_value_amount_usd",
      "stock_number_of_shares",
      "document_report_date",
    ])
    .default("investor_name"),
  sortDirection: z.enum(["ASC", "DESC"]).default("ASC"),
  limit: z.number().int().positive().max(100).default(10),
  offset: z.number().int().min(0).default(0),
  isDownload: z.boolean(),
});

/**
 * A type representing an investment search request.
 */
export type InvestmentSearchRequest = z.infer<
  typeof InvestmentSearchRequestSchema
>;
