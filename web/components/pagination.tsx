// Standard library imports
import React from "react";

// Third-party imports
import { usePagination, PaginationItemType, Button } from "@heroui/react";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

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

type PaginationProps = {
  page: number;
  total: number;
  onChange: (page: number) => void;
  boundaries?: number;
};

/**
 * A pagination component intended for desktop screen sizes.
 * Uses HeroUI's {@link usePagination} hook under the hood.
 *
 * @param props - The component props.
 * @param props.page - The current/active page number.
 * @param props.total - The total number of pages available.
 * @param props.onChange - A callback function to use when the page number changes.
 * @param props.boundaries - The number of pages to show at the start or end of the pagination. Defaults to 1.
 *
 * @returns The JSX element for the large pagination component.
 */
export const LargePagination: React.FC<PaginationProps> = ({
  page,
  total,
  onChange,
  boundaries = 1,
}) => {
  const { activePage, range, setPage, onNext, onPrevious, dotsJump } =
    usePagination({
      page,
      total,
      onChange,
      showControls: true,
      siblings: 1,
      boundaries: boundaries,
    });

  return (
    <div className="hidden h-8 flex-row gap-0 rounded-sm lg:flex">
      {range.map((page, idx) => {
        if (page === PaginationItemType.NEXT) {
          return (
            <Button
              key={idx}
              size="sm"
              onPress={onNext}
              isIconOnly={true}
              aria-label="next page"
              className="bg-seagreen border-default-200 border-1/2 dark:bg-forest rounded-none border text-white disabled:pointer-events-none"
              disabled={activePage === total || total === 0}
            >
              <ChevronRight />
            </Button>
          );
        } else if (page === PaginationItemType.PREV) {
          return (
            <Button
              key={idx}
              size="sm"
              onPress={onPrevious}
              isIconOnly={true}
              aria-label="previous page"
              className="bg-seagreen border-default-200 border-1/2 dark:bg-forest rounded-none border text-white disabled:pointer-events-none"
              disabled={activePage === 1 || total === 0}
            >
              <ChevronLeft />
            </Button>
          );
        } else if (page === PaginationItemType.DOTS) {
          return (
            <Button
              key={idx}
              size="sm"
              onPress={() => {
                const jumpDirection = idx == boundaries + 1 ? -1 : 1;
                setPage(activePage + dotsJump * jumpDirection);
              }}
              aria-label="page-ellipsis"
              className="border-default-200 border-1/2 dark:hover:bg-default-300 rounded-none border bg-white font-bold text-black hover:bg-neutral-300 dark:bg-black dark:text-white"
            >
              ...
            </Button>
          );
        } else {
          return (
            <Button
              key={idx}
              size="sm"
              onPress={() => setPage(page)}
              aria-label={`page ${page}`}
              className={`font-montserrat border-default-200 border-1/2 dark:hover:bg-default-300 rounded-none border bg-white text-sm font-bold text-black hover:bg-neutral-300 disabled:pointer-events-none dark:bg-black dark:text-white ${activePage === page && "dark:bg-default-300 bg-neutral-300"}`}
              disabled={activePage === page}
            >
              {page.toLocaleString()}
            </Button>
          );
        }
      })}
    </div>
  );
};

/**
 * A pagination component intended for mobile screen sizes.
 * Uses HeroUI's {@link usePagination} hook under the hood.
 *
 * @param props - The component props.
 * @param props.page - The current/active page number.
 * @param props.total - The total number of pages available.
 * @param props.onChange - A callback function to use when the page number changes.
 *
 * @returns The JSX element for the small pagination component.
 */
export const SmallPagination: React.FC<PaginationProps> = ({
  page,
  total,
  onChange,
}) => {
  const { activePage, setPage, onNext, onPrevious } = usePagination({
    page,
    total,
    showControls: true,
    onChange,
    siblings: 1,
    boundaries: 0,
  });

  return (
    <div className="flex h-10 flex-row items-center gap-0 rounded-sm lg:hidden">
      <Button
        size="md"
        onPress={() => setPage(1)}
        isIconOnly={true}
        aria-label="next page"
        className="bg-seagreen dark:bg-forest rounded-none border border-1 border-white text-white disabled:pointer-events-none"
        disabled={activePage === 1}
      >
        <ChevronsLeft />
      </Button>
      <Button
        size="md"
        onPress={onPrevious}
        isIconOnly={true}
        aria-label="previous page"
        className="bg-seagreen dark:bg-forest rounded-none border border-1 border-white text-white disabled:pointer-events-none"
        disabled={activePage === 1}
      >
        <ChevronLeft />
      </Button>
      {total > 0 && (
        <div className="font-montserrat flex flex-col items-center px-5 text-center font-bold">
          <p className="text-xs text-neutral-500 uppercase">Page</p>
          <p>
            {activePage.toLocaleString()} of {total.toLocaleString()}
          </p>
        </div>
      )}
      <Button
        size="md"
        onPress={onNext}
        isIconOnly={true}
        aria-label="next page"
        className="bg-seagreen dark:bg-forest rounded-none border border-1 border-white text-white disabled:pointer-events-none"
        disabled={activePage === total || total === 0}
      >
        <ChevronRight />
      </Button>
      <Button
        size="md"
        onPress={() => setPage(total)}
        isIconOnly={true}
        aria-label="next page"
        className="bg-seagreen dark:bg-forest rounded-none border border-1 border-white text-white disabled:pointer-events-none"
        disabled={activePage === total || total === 0}
      >
        <ChevronsRight />
      </Button>
    </div>
  );
};

/**
 * A responsive pagination component. Displays a {@link SmallPagination}
 * component for mobile screen sizes and a {@link LargePagination} component
 * for desktop screen sizes.
 *
 * @param page - The current page number.
 * @param total - The total number of pages available.
 * @param onChange - The callback function to use when the page number changes.
 *
 * @returns The JSX element for the responsive pagination component.
 */
export const ResponsivePagination: React.FC<PaginationProps> = ({
  page,
  total,
  onChange,
}) => {
  return (
    <div className="flex">
      <SmallPagination page={page} total={total} onChange={onChange} />
      <LargePagination page={page} total={total} onChange={onChange} />
    </div>
  );
};

type PaginationToolbarProps = {
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
export const PaginationToolbar: React.FC<PaginationToolbarProps> = ({
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
