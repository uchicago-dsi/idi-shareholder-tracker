// Standard library imports
import React from "react";

type DropdownProps = {
  label: string;
  options: number[];
  value: number;
  onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
};

/**
 * A generic dropdown component.
 *
 * @param props - The component props.
 * @param props.label - The label for the dropdown.
 * @param props.options - The options available for selection.
 * @param props.value - The current selected value.
 * @param props.onChange - The callback function for changes in th selection.
 *
 * @returns The JSX element for the dropdown component.
 */
export const Dropdown: React.FC<DropdownProps> = ({
  label,
  options,
  value,
  onChange,
}) => {
  return (
    <div className="font-montserrat flex flex-row gap-2 font-bold">
      <label className="flex items-center">{label}</label>
      <select
        className="flex w-10 items-center bg-transparent outline-none"
        value={value}
        onChange={onChange}
      >
        {options.map((opt, idx) => (
          <option key={idx} value={opt} className="dark:text-black">
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
};
