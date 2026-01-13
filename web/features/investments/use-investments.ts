"use client";

// Standard library imports
import React, { useEffect, useState } from "react";

// Feature imports
import {
  Investment,
  InvestmentSearchRequest,
  InvestmentSearchResult,
} from "./interfaces";
import { investmentService } from "./services";

type UseInvestmentsParams = {
  defaultPageSize: number;
  defaultSortColumn: string;
  defaultSortDirection: "ascending" | "descending";
};

type UseInvestmentsReturn = {
  isLoading: boolean;
  error: Error | null;
  investments: Investment[];
  currentPage: number;
  totalPages: number;
  totalRecords: number;
  currentQuery: string;
  sortColumn: string;
  sortDirection: "ascending" | "descending";
  pageSize: number;
  currentView: "table" | "cards";
  setCurrentView: (value: "table" | "cards") => void;
  onSearchQueryChange: (value: string) => void;
  onSearchQuerySubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onSearchQueryClear: () => void;
  onPageSizeChange: (value: number) => void;
  onPageChange: (page: number) => void;
  onSortColumnChange: (column: string) => void;
  onSortDirectionChange: (direction: "ascending" | "descending") => void;
};

/**
 * A custom React hook for fetching and managing a page of investments data from the API.
 *
 * @param defaultPageSize - The default number of records to show per page.
 * @param defaultSort - The default sorting scheme (i.e., column and direction).
 *
 * @returns An object containing the state and callbacks for the hook.
 */
export const useInvestments = ({
  defaultPageSize,
  defaultSortColumn,
  defaultSortDirection,
}: UseInvestmentsParams): UseInvestmentsReturn => {
  // Initialize state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [isNewSearch, setIsNewSearch] = useState<boolean>(true);
  const [currentView, setCurrentView] = useState<"table" | "cards">("table");
  const [sortDirection, setSortDirection] = useState<
    "ascending" | "descending"
  >(defaultSortDirection);
  const [sortColumn, setSortColumn] = useState<string>(
    String(defaultSortColumn),
  );

  // Initialize derived state
  const totalPages = totalRecords ? Math.ceil(totalRecords / pageSize) : 0;

  // Fetch data after change to page size, page number, search query, or sorting
  useEffect(() => {
    const updateData = () => {
      // Set status to loading
      setIsLoading(true);

      // Compose API request
      const request: InvestmentSearchRequest = {
        query: currentQuery ?? null,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
        sortColumn: sortColumn,
        sortDirection: sortDirection === "ascending" ? "ASC" : "DESC",
      };

      // Post search request and parse response
      investmentService
        .search(request)
        .then((result: InvestmentSearchResult) => {
          setTotalRecords(result.totalRecords);
          setInvestments(result.data);
          setIsNewSearch(false);
        })
        .catch((error) => {
          setError(error);
        })
        .finally(() => setIsLoading(false));
    };

    if (isNewSearch) updateData();
  }, [
    currentQuery,
    currentPage,
    sortColumn,
    sortDirection,
    pageSize,
    isNewSearch,
  ]);

  // Define callback function for updating a search query
  const onSearchQueryChange = (value: string) => setCurrentQuery(value);

  // Define callback function for submitting a search query
  const onSearchQuerySubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCurrentPage(1);
    setIsNewSearch(true);
    (document.activeElement as HTMLElement)?.blur();
  };

  // Define callback function for clearing a search query
  const onSearchQueryClear = () => {
    setCurrentPage(1);
    setIsNewSearch(true);
  };

  // Define callback function for updating the page size
  const onPageSizeChange = (value: number) => {
    setIsNewSearch(true);
    setPageSize(value);
    setCurrentPage(1);
  };

  // Define callback function for updating the page number
  const onPageChange = (page: number) => {
    setCurrentPage(page);
    setIsNewSearch(true);
  };

  // Define callback function for updating the sorted column
  const onSortColumnChange = (name: string) => {
    setCurrentPage(1);
    setSortColumn(name);
    setIsNewSearch(true);
  };

  // Define ccallback function for updating the sort direction
  const onSortDirectionChange = (direction: "ascending" | "descending") => {
    setCurrentPage(1);
    setSortDirection(direction);
    setIsNewSearch(true);
  };

  return {
    isLoading,
    error,
    currentQuery,
    investments,
    totalRecords,
    currentPage,
    totalPages,
    pageSize,
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
  };
};
