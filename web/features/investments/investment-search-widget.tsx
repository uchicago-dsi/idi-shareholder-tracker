"use client";

// Standard library imports
import React from "react";

// Application imports
import { SiteConfig } from "@/config/site";
import { StackedDropdown } from "@/components/dropdown";
import { ResultCount } from "@/components/result-count";
import { SearchBar } from "@/components/search-bar";

// Feature imports
import { PaginatedInvestmentCardList } from "./investment-card-list";
import { DataTable } from "./investment-table";
import { InvestmentViewButtonRow } from "./investment-view-toggle";
import { useInvestments } from "./use-investments";
import { LoadingSpinner } from "@/components/loading";
import { ErrorMessage } from "@/components/error-message";

type InvestmentSearchWidgetProps = {
  tableConfig: SiteConfig["table"];
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
    setCurrentView,
    onSearchQueryChange,
    onSearchQuerySubmit,
    onSearchQueryClear,
    onPageSizeChange,
    onPageChange,
    onSortColumnChange,
    onSortDirectionChange,
  } = useInvestments({
    defaultPageSize: parseInt(tableConfig.pageSizes.default),
    defaultSortColumn: tableConfig.sort.default.column,
    defaultSortDirection: tableConfig.sort.default.direction as
      | "ascending"
      | "descending",
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
          <div className="flex w-full flex-row justify-between lg:w-auto lg:items-center lg:gap-4">
            <StackedDropdown
              label={tableConfig.pageSizes.label}
              menus={[
                {
                  value: String(pageSize),
                  options: tableConfig.pageSizes.options,
                  onChange: (value: string) =>
                    onPageSizeChange(parseInt(value)),
                },
              ]}
            />
            <StackedDropdown
              label={tableConfig.sort.dropdown.label}
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
          </div>

          <InvestmentViewButtonRow
            value={currentView}
            onSelect={setCurrentView}
          />
        </div>
        {currentView === "cards" ? (
          <PaginatedInvestmentCardList
            investments={investments}
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
          />
        ) : (
          <>
            <div className="hidden lg:flex">
              <DataTable
                columns={tableConfig.columns}
                investments={investments}
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={onPageChange}
              />
            </div>
            <div className="flex lg:hidden">
              <PaginatedInvestmentCardList
                investments={investments}
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={onPageChange}
              />
            </div>
          </>
        )}
      </div>
    );
  }
};
