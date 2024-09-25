// @ts-nocheck
import { post } from "@/services/http";
import { InvestmentSearchRequest } from "@/types";

export const investmentService = {
  search: async (request: InvestmentSearchRequest) => {
    const url = `/api/investments`;
    const errMsg = `Failed to search investments.`;

    return await post(url, request, errMsg);
  },
};
