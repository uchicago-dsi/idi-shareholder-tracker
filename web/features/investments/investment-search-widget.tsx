"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { ArrowDownUpIcon, FunnelIcon } from "lucide-react";

// Application imports
import { ErrorMessage } from "@/components/error-message";
import { StackedDropdown } from "@/components/dropdown";
import { LoadingSpinner } from "@/components/loading";
import { SearchConfig } from "@/config/site";

// Feature imports
import { ResultCount } from "@/features/search/result-count";
import { SearchBar } from "@/features/search/search-bar";
import { InvestmentCardList } from "./investment-card-list";
import { DataTable } from "./investment-table";
import { InvestmentViewButtonRow } from "./investment-view-toggle";
import { PageToolbar } from "../pagination/toolbar";
import { useInvestments } from "./use-investments";
import { InvestmentDownloadButton } from "./investment-download-button";

type InvestmentSearchWidgetProps = {
  tableConfig: SearchConfig["table"];
};

/**
 * A widget that permits searching, filtering, and pagination of investments <data value="
 * The investment data can be displayed in table or card format.
 *
 * @param config - Configuration for the widget's data table.
 *
 * @returns A React JSX element.
 */
export const InvestmentSearchWidget: React.FC<InvestmentSearchWidgetProps> = ({
  tableConfig,
}) => {
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
    defaultPageSize: parseInt(tableConfig.pageSizes.default),
    defaultSortColumn: tableConfig.sort.default.column,
    defaultSortDirection: tableConfig.sort.default.direction as
      | "ascending"
      | "descending",
    defaultFilter: tableConfig.filter.investorType.default as
      | "Pension Funds"
      | "Institutional Investors"
      | "All Records",
  });

  if (isLoading) {
    return <LoadingSpinner messages={tableConfig.loading.messages} />;
  } else if (error) {
    return <ErrorMessage />;
  } else {
    return (
      <div className="flex w-full flex-col gap-4">
        <SearchBar
          placeholder={tableConfig.search.placeholder}
          submitLabel={tableConfig.search.submitLabel}
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
                  options: tableConfig.sort.dropdown.columnName.options,
                  onChange: onSortColumnChange,
                },
                {
                  value: sortDirection,
                  options: tableConfig.sort.dropdown.direction.options,
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
                  options: tableConfig.filter.investorType.options,
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
            <InvestmentViewButtonRow
              value={currentView}
              onSelect={setCurrentView}
            />
            <InvestmentDownloadButton
              isDownloading={isDownloading}
              handleDownload={handleDownload}
            />
          </div>
        </div>
        <div
          className={`flex flex-col ${currentView === "cards" ? "gap-8" : "gap-0"}`}
        >
          {currentView === "cards" ? (
            <InvestmentCardList investments={investments} />
          ) : (
            <>
              <div className="hidden lg:flex">
                <DataTable
                  columns={tableConfig.columns}
                  investments={investments}
                />
              </div>
              <div className="flex lg:hidden">
                <InvestmentCardList investments={investments} />
              </div>
            </>
          )}
          <PageToolbar
            currentPageSize={pageSize}
            pageSizes={tableConfig.pageSizes.options}
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
