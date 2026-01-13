// Standard library imports
import React, { useEffect, useRef, useState } from "react";

// Third-party imports
import { Button, Listbox, ListboxItem, Selection } from "@heroui/react";
import { ChevronDownIcon } from "lucide-react";

interface Option {
  label: string;
  value: string;
}

type StackedDropdownMenuProps = {
  value: string;
  options: Option[];
  onChange: (value: string) => void;
};

/**
 * A controlled HeroUI {@link Listbox} that allows users to select a single value from a list of options.
 *
 * @param props - The component props.
 * @param props.value - The currently-selected value.
 * @param props.options - The list of options to select from.
 * @param props.onChange - The function to call when the user selects a new value.
 *
 * @returns The menu.
 */
const StackedDropdownMenu: React.FC<StackedDropdownMenuProps> = ({
  value,
  options,
  onChange,
}) => {
  return (
    <Listbox
      className="border-default-300 border-1 font-bold dark:bg-black"
      selectionMode="single"
      variant="flat"
      selectedKeys={[value]}
      onSelectionChange={(keys: Selection) => {
        const value = Array.from(keys)[0];
        if (value) onChange(value as string);
      }}
    >
      {options.map((opt) => (
        <ListboxItem key={opt.value} classNames={{ title: "text-sm" }}>
          {opt.label}
        </ListboxItem>
      ))}
    </Listbox>
  );
};

type UseStackedDropdownReturn = {
  dropdownRef: React.RefObject<HTMLDivElement | null>;
  isOpen: boolean;
  toggleDropdown: () => void;
};

/**
 * A hook for managing a dropdown menu with multiple stacked submenus.
 *
 * @returns An object with the following properties:
 * - `dropdownRef`: A reference to the dropdown menu element.
 * - `isOpen`: A boolean indicating whether the dropdown menu is open.
 * - `toggleDropdown`: A function to toggle the dropdown menu open state.
 */
const useStackedDropdown = (): UseStackedDropdownReturn => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const toggleDropdown = () => setIsOpen((prev) => !prev);

  return {
    dropdownRef,
    isOpen,
    toggleDropdown,
  };
};

type StackedDropdownProps = {
  label: string;
  menus: StackedDropdownMenuProps[];
};

/**
 * A dropdown component that displays one or more independent option menus stacked on top of each other.
 *
 * @param props - The component props.
 * @param props.label - The label to display next to the stacked dropdown.
 * @param props.menus - An array of objects containing the value and options for each dropdown.
 *
 * @returns The JSX element for the stacked dropdown component.
 */
export const StackedDropdown: React.FC<StackedDropdownProps> = ({
  label,
  menus,
}) => {
  const { dropdownRef, isOpen, toggleDropdown } = useStackedDropdown();
  const displayValue = menus
    .map((menu) =>
      menu.options
        .filter((opt) => opt.value === menu.value)
        .map((opt) => opt.label),
    )
    .join(" ");
  return (
    <div
      ref={dropdownRef}
      className="font-montserrat relative flex flex-col font-bold"
    >
      <div className="flex flex-row items-center gap-1">
        <p className="flex flex-row gap-2">
          {label}
          <span className="hidden lg:inline">{displayValue}</span>
        </p>
        <Button isIconOnly className="bg-transparent" onPress={toggleDropdown}>
          <ChevronDownIcon size={18} />
        </Button>
      </div>
      {isOpen && (
        <div
          className={`font-montserrat border-default-300 absolute top-full right-0 z-10 mt-1 flex flex-col gap-0 border-1 bg-white`}
        >
          {menus.map((menu, idx) => (
            <StackedDropdownMenu
              key={idx}
              value={menu.value}
              options={menu.options}
              onChange={menu.onChange}
            />
          ))}
        </div>
      )}
    </div>
  );
};
