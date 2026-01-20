// Standard library imports
import React from "react";

// Feature imports
import { PageSizer } from "@/features/pagination/sizer";
import { ResponsivePagination } from "@/features/pagination/paginator";

type PageToolbarProps = {
  pageSizes: number[];
  currentPageSize: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
};

/**
 * A component that displays a toolbar for pagination controls.
 * The toolbar includes a page size selector and a responsive pagination component.
 *
 * @param props - The component props.
 * @param props.pageSizes - The list of page sizes to display.
 * @param props.currentPageSize - The currently-selected page size.
 * @param props.currentPage - The currently-selected page number.
 * @param props.totalPages - The total number of pages available.
 * @param props.onPageChange - The function to call when the page number changes.
 * @param props.onPageSizeChange - The function to call when the page size changes.
 *
 * @returns The JSX element for the page toolbar component.
 */
export const PageToolbar: React.FC<PageToolbarProps> = ({
  pageSizes,
  currentPageSize,
  currentPage,
  totalPages,
  onPageChange,
  onPageSizeChange,
}) => {
  return (
    <div className="lg:bg-default-100 flex w-full flex-col items-center justify-center gap-4 rounded-b-lg p-3 pt-5 lg:flex-row lg:justify-between lg:shadow-sm dark:bg-transparent">
      <PageSizer
        currentValue={currentPageSize}
        options={pageSizes}
        onChange={onPageSizeChange}
      />
      <div className="flex w-full flex-row justify-center lg:justify-end">
        <ResponsivePagination
          page={currentPage}
          total={totalPages}
          onChange={onPageChange}
        />
      </div>
    </div>
  );
};
