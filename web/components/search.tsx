// Standard library imports
import React from "react";

// Third-party imports
import { Button, Input } from "@heroui/react";
import { ArrowRightIcon, SearchIcon } from "lucide-react";

type ResultCountProps = {
  currentPage: number;
  recordsPerPage: number;
  totalRecords: number;
};

/**
 * A generic component for displaying the total number of records
 * found in a search query, as well as the range of records
 * currently being viewed.
 *
 * @param props - The component props.
 * @param props.currentPage - The current page number.
 * @param props.recordsPerPage - The number of records to display per page.
 * @param props.totalRecords - The total number of records found.
 *
 * @returns A JSX element displaying the total number of records and the current viewing range.
 */
export const ResultCount: React.FC<ResultCountProps> = ({
  currentPage,
  recordsPerPage,
  totalRecords,
}: ResultCountProps) => {
  const start = (currentPage - 1) * recordsPerPage + 1;
  const end = Math.min(totalRecords, currentPage * recordsPerPage);
  return totalRecords === 0 ? (
    <h3 className="font-montserrat text-center text-xl font-bold">
      0 Results Found
    </h3>
  ) : (
    <h3 className="font-montserrat text-center text-base font-bold lg:text-xl">
      Showing {start.toLocaleString()} - {end.toLocaleString()} of{" "}
      <span className="font-bold text-orange-400 dark:text-orange-300">
        {totalRecords.toLocaleString()}
      </span>{" "}
      result{totalRecords === 1 ? "" : "s"}
    </h3>
  );
};

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
        className="flex w-full flex-row items-center gap-0"
      >
        <Input
          className="font-montserrat w-full"
          classNames={{
            inputWrapper: ["rounded-r-none", "h-8", "lg:h-10"],
            input: ["lg:text-sm"],
          }}
          value={currentQuery}
          onValueChange={onValueChange}
          onClear={onClear}
          placeholder={placeholder}
          startContent={
            <SearchIcon className="text-default-400 text-seagreen pointer-events-none hidden flex-shrink-0 lg:inline" />
          }
        />
        <Button
          className="bg-seagreen h-10 w-10 min-w-3 rounded-l-none font-bold text-white uppercase lg:h-10 lg:w-25"
          type="submit"
        >
          <span className="font-montserrat hidden lg:inline">
            {submitLabel}
          </span>
          <span className="inline lg:hidden">
            <ArrowRightIcon />
          </span>
        </Button>
      </form>
    </div>
  );
};
