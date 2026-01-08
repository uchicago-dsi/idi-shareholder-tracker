"use client";

// Standard library imports
import React, { useEffect, useState } from "react";

// Third-party imports
import { SortDescriptor } from "@heroui/table";

// Application imports
import {
  Investment,
  InvestmentSearchRequest,
  InvestmentSearchResult,
} from "./interfaces";
import { investmentService } from "./services";

type UseInvestmentsReturn = {
  isLoading: boolean;
  error: Error | null;
  investments: Investment[];
  currentPage: number;
  totalPages: number;
  totalRecords: number;
  currentQuery: string;
  sortObj: SortDescriptor;
  pageSize: number;
  currentView: "table" | "cards";
  setCurrentView: (value: "table" | "cards") => void;
  onSearchQueryChange: (value: string) => void;
  onSearchQuerySubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onSearchQueryClear: () => void;
  onPageSizeChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
  onPageChange: (page: number) => void;
  onSortChange: (item: SortDescriptor) => void;
};

/**
 * A custom React hook for fetching and managing a page of investments data from the API.
 *
 * @param defaultPageSize - The default number of records to show per page.
 * @param defaultSort - The default sorting scheme (i.e., column and direction).
 *
 * @returns An object containing the state and callbacks for the hook.
 */
export const useInvestments = (
  defaultPageSize: number,
  defaultSort: SortDescriptor,
): UseInvestmentsReturn => {
  // Initialize state
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(defaultPageSize);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [sortObj, setSortObj] = useState<SortDescriptor>(defaultSort);
  const [isNewSearch, setIsNewSearch] = useState<boolean>(true);
  const [currentView, setCurrentView] = useState<"table" | "cards">("table");

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
        sortColumn: String(sortObj.column),
        sortDirection: sortObj.direction === "ascending" ? "ASC" : "DESC",
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
  }, [currentQuery, currentPage, sortObj, pageSize, isNewSearch]);

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
  const onPageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setIsNewSearch(true);
    setPageSize(parseInt(event.target.value));
    setCurrentPage(1);
  };

  // Define callback function for updating the page number
  const onPageChange = (page: number) => {
    setCurrentPage(page);
    setIsNewSearch(true);
  };

  // Define callback function for updating the sorting scheme
  const onSortChange = (item: SortDescriptor) => {
    setCurrentPage(1);
    setSortObj(item);
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
    sortObj,
    currentView,
    setCurrentView,
    onSearchQueryChange,
    onSearchQuerySubmit,
    onSearchQueryClear,
    onPageSizeChange,
    onPageChange,
    onSortChange,
  };
};
