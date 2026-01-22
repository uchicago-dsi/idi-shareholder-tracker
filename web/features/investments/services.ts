"server only";

// Feature imports
import { InvestmentSearchRequest, InvestmentSearchResult } from "./interfaces";

/**
 * A data access layer for investments.
 */
export const investmentService = {
  search: async (
    request: InvestmentSearchRequest,
  ): Promise<InvestmentSearchResult> => {
    const url = `${process.env.NEXT_PUBLIC_DASHBOARD_BASE_URL}/api/investments`;
    const r = await fetch(url, {
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
