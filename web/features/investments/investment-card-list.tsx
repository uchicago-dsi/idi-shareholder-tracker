// Standard library imports
import React from "react";

// Feature imports
import { Investment } from "./interfaces";
import { InvestmentCard } from "./investment-card";

type InvestmentCardListProps = {
  investments: Investment[];
};

/**
 * Renders a list of investment cards.
 *
 * @param props - The component props.
 * @param props.investments - The investments to render.
 *
 * @returns The JSX element.
 */
export const InvestmentCardList: React.FC<InvestmentCardListProps> = ({
  investments,
}) => {
  return investments.length === 0 ? (
    <div className="border-default-200 flex flex-col items-center rounded-xl border p-10 shadow-xs">
      <p className="text-default-400 font-montserrat uppercase">
        NO ROWS TO DISPLAY.
      </p>
    </div>
  ) : (
    <div className="flex flex-col gap-8">
      {investments.map((investment) => (
        <InvestmentCard key={investment.id} investment={investment} />
      ))}
    </div>
  );
};
