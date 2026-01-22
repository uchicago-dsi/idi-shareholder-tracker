// Standard library imports
import React from "react";

// Third-party imports
import { Button } from "@heroui/react";
import { Sheet, StretchHorizontal } from "lucide-react";

type InvestmentViewButtonRowProps = {
  value: "table" | "cards";
  onSelect: (value: "table" | "cards") => void;
};

/**
 * A component for toggling between table and card views of investments.
 * Renders two {@link Button} components with table and card icons. The
 * selected view is highlighted in green while the other view is gray.
 *
 * @param props - The component props.
 * @param props.value - The current selected view (either "table" or "cards").
 * @param props.onSelect - A callback function to handle changes in the selected view.
 *
 * @returns The JSX element.
 */
export const InvestmentViewButtonRow: React.FC<
  InvestmentViewButtonRowProps
> = ({ value, onSelect }) => {
  return (
    <div className="hidden flex-row items-center gap-4 lg:flex">
      <div className="flex flex-row items-center">
        <Button
          aria-label="Table view button"
          isIconOnly
          className={`rounded-full ${value === "table" ? "bg-seagreen dark:bg-green-300" : "bg-transparent"}`}
          onPress={() => onSelect("table")}
        >
          <Sheet
            strokeWidth={1.5}
            className={`${value === "table" ? "stroke-white dark:stroke-black" : "stroke-default-400"}`}
          />
        </Button>
        <Button
          aria-label="Card view button"
          isIconOnly
          className={`rounded-full ${value === "cards" ? "bg-seagreen dark:bg-green-300" : "bg-transparent"}`}
          onPress={() => onSelect("cards")}
        >
          <StretchHorizontal
            strokeWidth={1.5}
            className={`${value === "cards" ? "stroke-white dark:stroke-black" : "stroke-default-400"}`}
          />
        </Button>
      </div>
    </div>
  );
};
