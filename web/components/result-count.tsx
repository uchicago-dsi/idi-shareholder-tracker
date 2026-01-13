// Standard library imports
import React from "react";

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
    <h3 className="font-montserrat text-center text-xl font-bold">
      Showing {start.toLocaleString()} - {end.toLocaleString()} of{" "}
      <span className="font-bold text-green-600 dark:text-green-400">
        {totalRecords.toLocaleString()}
      </span>{" "}
      result{totalRecords === 1 ? "" : "s"}
    </h3>
  );
};
