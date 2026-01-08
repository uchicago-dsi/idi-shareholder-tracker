"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { SortDescriptor } from "@heroui/table";
import { Spinner } from "@heroui/react";

// Application imports
import { SiteConfig } from "@/config/site";
import { Dropdown } from "@/components/dropdown";
import { ResultCount } from "@/components/result-count";
import { SearchBar } from "@/components/search-bar";

// Feature imports
import { DataTable } from "./investment-table";
import { InvestmentViewButtonRow } from "./investment-view-toggle";
import { useInvestments } from "./use-investments";
import { InvestmentCardDeck } from "./investment-card-deck";

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
    sortObj,
    currentView,
    setCurrentView,
    onSearchQueryChange,
    onSearchQuerySubmit,
    onSearchQueryClear,
    onPageSizeChange,
    onPageChange,
    onSortChange,
  } = useInvestments(
    tableConfig.pageSizes.default,
    tableConfig.sort.default as SortDescriptor,
  );

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-2">
        <Spinner size="lg" color="success" />
        <span className="text-muted font-montserrat text-xl">Loading...</span>
      </div>
    );
  } else if (error) {
    return <div>Error</div>;
  } else {
    return (
      <div className="flex w-full flex-col gap-4">
        <SearchBar
          placeholder={tableConfig.search.placeholder}
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
          <Dropdown
            label={tableConfig.pageSizes.label}
            options={tableConfig.pageSizes.options}
            value={pageSize}
            onChange={onPageSizeChange}
          />
          <InvestmentViewButtonRow
            value={currentView}
            onSelect={setCurrentView}
          />
        </div>
        {currentView == "cards" ? (
          <InvestmentCardDeck
            investments={investments}
            currentPage={currentPage}
            totalPages={totalPages}
            currentSort={sortObj}
            onPageChange={onPageChange}
            onSortChange={onSortChange}
          />
        ) : (
          <>
            <div className="hidden lg:flex">
              <DataTable
                columns={tableConfig.columns}
                investments={investments}
                currentPage={currentPage}
                totalPages={totalPages}
                currentSort={sortObj}
                onPageChange={onPageChange}
                onSortChange={onSortChange}
              />
            </div>
            <div className="flex lg:hidden">
              <InvestmentCardDeck
                investments={investments}
                currentPage={currentPage}
                totalPages={totalPages}
                currentSort={sortObj}
                onPageChange={onPageChange}
                onSortChange={onSortChange}
              />
            </div>
          </>
        )}
      </div>
    );
  }
};
