// Standard library imports
import React from "react";

// Third-party imports
import { Button } from "@heroui/react";

type PageSizerProps = {
  currentValue: number;
  options: number[];
  onChange: (value: number) => void;
};

/**
 * A component that renders a row of page sizes as buttons.
 *
 * @param props - The component props.
 * @param props.currentValue - The currently-selected value.
 * @param props.options - The list of page sizes to display.
 * @param props.onChange - The function to call when a button is clicked.
 *
 * @returns The JSX element for the button row component.
 */
export const PageSizer: React.FC<PageSizerProps> = ({
  currentValue,
  options,
  onChange,
}) => {
  return (
    <div className="flex flex-row gap-0">
      {options.map((opt, idx) => (
        <Button
          key={idx}
          disabled={opt === currentValue}
          onPress={() => onChange(opt)}
          aria-label="page-ellipsis"
          className={`font-montserrat border-default-200 dark:hover:bg-default-300 border-1/2 h-8 rounded-none border bg-white font-bold text-black hover:bg-neutral-300 dark:bg-black dark:font-bold dark:text-white ${opt === currentValue ? "dark:bg-default-300 bg-neutral-300 disabled:pointer-events-none" : ""}`}
        >
          {opt}
        </Button>
      ))}
    </div>
  );
};
