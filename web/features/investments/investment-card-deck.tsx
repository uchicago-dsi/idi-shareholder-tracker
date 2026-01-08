import React from "react";
import { Investment } from "./interfaces";
import { SortDescriptor } from "@heroui/table";
import { ResponsivePagination } from "@/components/pagination";
import { InvestmentCard } from "./investment-card";

type InvestmentCardProps = {
  investments: Investment[];
  currentPage: number;
  totalPages: number;
  currentSort: SortDescriptor;
  onPageChange: (page: number) => void;
  onSortChange: (item: SortDescriptor) => void;
};

export const InvestmentCardDeck: React.FC<InvestmentCardProps> = ({
  investments,
  currentPage,
  totalPages,
  currentSort,
  onPageChange,
  onSortChange,
}) => {
  return (
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
