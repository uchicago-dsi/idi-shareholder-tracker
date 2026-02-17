// Feature imports
import { InvestmentSearchRequest, InvestmentSearchResult } from "./interfaces";

/**
 * A data access layer for investments.
 */
export const investmentService = {
  search: async (
    request: InvestmentSearchRequest,
  ): Promise<InvestmentSearchResult> => {
    const r = await fetch("/api/investments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!r.ok) {
      throw Error(
        `Failed to ${request.isDownload ? "download" : "search"} investments.`,
      );
    }
    return await r.json();
  },
};
