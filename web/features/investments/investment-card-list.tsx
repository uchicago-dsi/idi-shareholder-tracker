// Standard library imports
import React from "react";

// Application imports
import { ResponsivePagination } from "@/components/pagination";

// Feature imports
import { Investment } from "./interfaces";
import { InvestmentCard } from "./investment-card";

type PaginatedInvestmentCardListProps = {
  investments: Investment[];
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

/**
 * Renders a paginated list of investment cards.
 *
 * @param props - The component props.
 * @param props.investments - The investments to render.
 * @param props.currentPage - The number of the current page.
 * @param props.totalPages - The total number of pages available.
 * @param props.onPageChange - The callback function to use for page changes.
 *
 * @returns The JSX element for the investment card list.
 */
export const PaginatedInvestmentCardList: React.FC<
  PaginatedInvestmentCardListProps
> = ({ investments, currentPage, totalPages, onPageChange }) => {
  return investments.length === 0 ? (
    <div className="flex flex-col gap-8">
      <div className="text-default-400 font-montserrat border-default-200 flex flex-col items-center gap-4 rounded-xl border p-10 uppercase shadow-xs">
        <p>NO ROWS TO DISPLAY.</p>
      </div>
      <ResponsivePagination
        showControls
        page={currentPage}
        total={totalPages}
        onChange={onPageChange}
      />
    </div>
  ) : (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-4">
        {investments.map((investment) => (
          <InvestmentCard key={investment.id} investment={investment} />
        ))}
      </div>
      <ResponsivePagination
        showControls
        page={currentPage}
        total={totalPages}
        onChange={onPageChange}
      />
    </div>
  );
};
