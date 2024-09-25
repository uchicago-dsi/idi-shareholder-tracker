// @ts-nocheck
import { post } from "@/services/http";
import { InvestmentSearchRequest } from "@/types";

export const investmentService = {
  search: async (request: InvestmentSearchRequest) => {
    const url = `${process.env.NEXT_PUBLIC_DASHBOARD_BASE_URL}/api/investments`;
    const errMsg = `Failed to search investments.`;

    return await post(url, request, errMsg);
  },
};
