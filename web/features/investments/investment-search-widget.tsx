"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { ArrowDownUpIcon, FunnelIcon } from "lucide-react";

// Application imports
import { ErrorMessage } from "@/components/error";
import { StackedDropdown } from "@/components/dropdown";
import { LoadingSpinner } from "@/components/loading";
import { PaginationToolbar } from "@/components/pagination";
import { ResultCount, SearchBar } from "@/components/search";

// Feature imports
import { INVESTMENT_LIST_CONFIG } from "./config";
import { Investment } from "./interfaces";
import { InvestmentCardList } from "./investment-card-list";
import { InvestmentDownloadButton } from "./investment-download-button";
import { InvestmentTable } from "./investment-table";
import { InvestmentViewToggle } from "./investment-view-toggle";
import { useInvestments } from "./use-investments";

type InvestmentDatasetToolbarProps = {
  sortColumn: string;
  onSortColumnChange: (value: string) => void;
  sortDirection: "ascending" | "descending";
  onSortDirectionChange: (value: "ascending" | "descending") => void;
  filter: "Pension Funds" | "Institutional Investors" | "All Records";
  onFilterChange: (
    value: "Pension Funds" | "Institutional Investors" | "All Records",
  ) => void;
  currentView: "table" | "cards";
  setCurrentView: (value: "table" | "cards") => void;
  isDownloading: boolean;
  handleDownload: () => void;
};

/**
 * A toolbar for filtering, sorting, downloading, and toggling between views of investment data.
 *
 * @param props - The component props.
 * @param props.sortColumn - The current sort column.
 * @param props.onSortColumnChange - A callback function to handle changes in the sort column.
 * @param props.sortDirection - The current sort direction.
 * @param props.onSortDirectionChange - A callback function to handle changes in the sort direction.
 * @param props.filter - The current filter value.
 * @param props.onFilterChange - A callback function to handle changes in the filter value.
 * @param props.currentView - The current view (either "table" or "cards").
 * @param props.setCurrentView - A callback function to handle changes in the view.
 * @param props.isDownloading - A flag indicating whether the data is currently being downloaded.
 * @param props.handleDownload - A callback function to handle the download action.
 *
 * @returns The JSX element.
 */
export const InvestmentDatasetToolbar: React.FC<
  InvestmentDatasetToolbarProps
> = ({
  sortColumn,
  onSortColumnChange,
  sortDirection,
  onSortDirectionChange,
  filter,
  onFilterChange,
  currentView,
  setCurrentView,
  isDownloading,
  handleDownload,
}) => {
  return (
    <div className="flex flex-row justify-between">
      <div className="flex w-full flex-row justify-start gap-4 lg:w-auto lg:items-center lg:justify-between lg:gap-6">
        <StackedDropdown
          label={
            <ArrowDownUpIcon
              className="text-seagreen dark:text-green-300"
              strokeWidth={2}
            />
          }
          menus={[
            {
              value: sortColumn,
              options: INVESTMENT_LIST_CONFIG.sort.dropdown.columnName.options,
              onChange: onSortColumnChange,
            },
            {
              value: sortDirection,
              options: INVESTMENT_LIST_CONFIG.sort.dropdown.direction.options,
              onChange: (value: string) =>
                onSortDirectionChange(value as "ascending" | "descending"),
            },
          ]}
        />
        <StackedDropdown
          label={
            <FunnelIcon
              className="text-seagreen dark:text-green-300"
              strokeWidth={2}
            />
          }
          menus={[
            {
              value: filter,
              options: INVESTMENT_LIST_CONFIG.filter.investorType.options,
              onChange: (value: string) =>
                onFilterChange(
                  value as
                    | "Pension Funds"
                    | "Institutional Investors"
                    | "All Records",
                ),
            },
          ]}
        />
      </div>
      <div className="flex flex-row gap-4">
        <InvestmentViewToggle value={currentView} onSelect={setCurrentView} />
        <InvestmentDownloadButton
          isDownloading={isDownloading}
          handleDownload={handleDownload}
        />
      </div>
    </div>
  );
};

type InvestmentDatasetProps = {
  currentView: "cards" | "table";
  investments: Investment[];
};

/**
 * A page of investment data rendered as a list of cards or a data table depending on the `currentView` prop.
 *
 * @param props - The component props.
 * @param props.currentView - Either "cards" or "table".
 * @param props.investments - The page of investments to render.
 *
 * @returns The JSX element.
 */
export const InvestmentDataset: React.FC<InvestmentDatasetProps> = ({
  currentView,
  investments,
}) => {
  return currentView === "cards" ? (
    <InvestmentCardList investments={investments} />
  ) : (
    <>
      <div className="hidden lg:flex">
        <InvestmentTable
          columns={INVESTMENT_LIST_CONFIG.columns}
          investments={investments}
        />
      </div>
      <div className="flex lg:hidden">
        <InvestmentCardList investments={investments} />
      </div>
    </>
  );
};

/**
 * A widget that permits searching, filtering, and pagination of investments <data value="
 * The investment data can be displayed in table or card format.
 *
 * @returns The JSX element.
 */
export const InvestmentSearchWidget: React.FC = () => {
  const {
    isLoading,
    isDownloading,
    error,
    currentQuery,
    investments,
    currentPage,
    pageSize,
    totalPages,
    totalRecords,
    sortColumn,
    sortDirection,
    currentView,
    filter,
    setCurrentView,
    onSearchQueryChange,
    onSearchQuerySubmit,
    onSearchQueryClear,
    onPageSizeChange,
    onPageChange,
    onSortColumnChange,
    onSortDirectionChange,
    onFilterChange,
    handleDownload,
  } = useInvestments({
    defaultPageSize: parseInt(INVESTMENT_LIST_CONFIG.pageSizes.default),
    defaultSortColumn: INVESTMENT_LIST_CONFIG.sort.default.column,
    defaultSortDirection: INVESTMENT_LIST_CONFIG.sort.default.direction as
      | "ascending"
      | "descending",
    defaultFilter: INVESTMENT_LIST_CONFIG.filter.investorType.default as
      | "Pension Funds"
      | "Institutional Investors"
      | "All Records",
  });

  if (isLoading) {
    return (
      <LoadingSpinner messages={INVESTMENT_LIST_CONFIG.loading.messages} />
    );
  } else if (error) {
    return <ErrorMessage />;
  } else {
    return (
      <div className="flex w-full flex-col gap-4">
        <SearchBar
          placeholder={INVESTMENT_LIST_CONFIG.search.placeholder}
          submitLabel={INVESTMENT_LIST_CONFIG.search.submitLabel}
          currentQuery={currentQuery}
          onValueChange={onSearchQueryChange}
          onSubmit={onSearchQuerySubmit}
          onClear={onSearchQueryClear}
        />
        <ResultCount
          currentPage={currentPage}
          recordsPerPage={pageSize}
          totalRecords={totalRecords}
        />
        <InvestmentDatasetToolbar
          sortColumn={sortColumn}
          onSortColumnChange={onSortColumnChange}
          sortDirection={sortDirection}
          onSortDirectionChange={onSortDirectionChange}
          filter={filter}
          onFilterChange={onFilterChange}
          currentView={currentView}
          setCurrentView={setCurrentView}
          isDownloading={isDownloading}
          handleDownload={handleDownload}
        />
        <div
          className={`flex flex-col ${currentView === "cards" ? "gap-8" : "gap-0"}`}
        >
          <InvestmentDataset
            currentView={currentView}
            investments={investments}
          />
          <PaginationToolbar
            currentPageSize={pageSize}
            pageSizes={INVESTMENT_LIST_CONFIG.pageSizes.options}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
            onPageSizeChange={onPageSizeChange}
          />
        </div>
      </div>
    );
  }
};
