// Standard library imports
import React from "react";

// Third-party imports
import { Button, Input } from "@heroui/react";
import { SearchIcon } from "lucide-react";

type SearchBarProps = {
  placeholder: string;
  submitLabel: string;
  currentQuery: string;
  onValueChange: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onClear: () => void;
};

/**
 * A generic search bar component with a submit button.
 *
 * @param props - The component props.
 * @param props.placeholder - The text to display in the search field when it is empty.
 * @param props.submitLabel - The label for the submit button.
 * @param props.currentQuery - The current user query string being searched for.
 * @param props.onValueChange - A callback function to handle query updates.
 * @param props.onSubmit - A callback function to handle submissions.
 * @param props.onClear - A callback function to handle query deletions.
 *
 * @returns The JSX element.
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder,
  submitLabel,
  currentQuery,
  onValueChange,
  onSubmit,
  onClear,
}) => {
  return (
    <div className="mx-auto w-full max-w-xs sm:max-w-md md:max-w-lg lg:max-w-7xl">
      <form
        onSubmit={onSubmit}
        className="flex w-full flex-col items-center gap-4 lg:flex-row lg:gap-0"
      >
        <Input
          size="lg"
          className="font-montserrat w-full"
          classNames={{
            inputWrapper: ["lg:rounded-r-none"],
          }}
          value={currentQuery}
          onValueChange={onValueChange}
          onClear={onClear}
          placeholder={placeholder}
          startContent={
            <SearchIcon className="text-default-400 text-seagreen pointer-events-none flex-shrink-0" />
          }
        />
        <Button
          className="bg-seagreen font-montserrat font-bold text-white uppercase lg:rounded-l-none"
          size="lg"
          type="submit"
        >
          {submitLabel}
        </Button>
      </form>
    </div>
  );
};
