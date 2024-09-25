"use client";

import {
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from "@nextui-org/react";
import { useEffect, useMemo, useState } from "react";
import React from "react";
import Link from "next/link";
import { Input } from "@nextui-org/input";
import { Spinner } from "@nextui-org/react";
import debounce from "lodash.debounce";
import { Chip } from "@nextui-org/react";

import { investmentService } from "./services";

import { title, subtitle } from "@/components/primitives";
import { Investment } from "@/types";
import { InvestmentSearchRequest } from "@/types";
import { SearchIcon } from "@/components/icons";

export default function Home() {
  const [investmentsLoading, setInvestmentsLoading] = useState(true);
  const [investments, setInvestments] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortObj, setSortObj] = useState({
    column: "investor_name",
    direction: "ascending",
  });
  const recordsPerPage = parseInt(
    process.env.NEXT_PUBLIC_DEFAULT_TABLE_ROWS ?? "",
  );

  const totalPages = useMemo(() => {
    return totalRecords ? Math.ceil(totalRecords / recordsPerPage) : 0;
  }, [totalRecords]);

  useEffect(() => {
    setInvestmentsLoading(true);
    let request: InvestmentSearchRequest = {
      cik: null,
      cusip: null,
      ticker: null,
      issuer: null,
      investor: null,
      document: searchTerm ?? null,
      limit: recordsPerPage,
      page: currentPage,
      sortColumn: sortObj["column"],
      sortDirection: sortObj["direction"],
    };

    investmentService.search(request).then((results) => {
      setTotalRecords(results["total"]);
      setInvestments(results["data"]);
      setInvestmentsLoading(false);
    });
  }, [currentPage, sortObj, searchTerm]);

  const onSearchChange = (value) => {
    if (value) {
      setSearchTerm(value);
      setCurrentPage(1);
    } else {
      setSearchTerm("");
    }
  };

  return (
    <div>
      <section className="flex flex-col items-center justify-center gap-4 py-8 md:py-10">
        <div className="inline-block max-w-4xl text-center justify-center">
          <span className={title()}>Shareholder Tracker</span>{" "}
          <Chip color="success" size="lg" variant="bordered">
            Beta
          </Chip>
          <div className={subtitle({ class: "mt-4" })}>
            Discover institutional investments disclosed in SEC 13F filings
          </div>
        </div>
        <div className="inline-block max-w-4xl">
          This database compiles the latest quarterly shareholdings disclosed by
          investors to the U.S. Securities and Exchange Commission. To search
          for a company’s shareholders, type the name of the company or its
          ticker symbol or CUSIP number in the search bar. You can also search
          for shareholders by name. All search results can be sorted in
          ascending or descending order by clicking on the select column
          heading. To see the original Form 13F on the Securities and Exchange
          Commission's website, click on the linked value in the "Company"
          column.
        </div>
        <div className="inline-block max-w-4xl italic">
          NOTE: This page is currently under development. We will be optimizing
          the user experience and adding new investors over time. Please refresh
          the page and reattempt your query if any unexpected errors occur.
        </div>
        <div className="inline-block max-w-4xl">
          <h2 className="py-4 font-bold text-lg">
            Disclosures for Quarter 2024-06-30
          </h2>
          <Input
            placeholder="Search investments by keyword..."
            size={"lg"}
            startContent={<SearchIcon />}
            type="text"
            value={searchTerm}
            onValueChange={debounce((val) => onSearchChange(val), 400)}
          />
          <div className="w-screen font-bold" />
        </div>
        <div>
          {investmentsLoading ? (
            <div className="py-8">
              <Spinner color="primary" label="Loading..." size="lg" />
            </div>
          ) : (
            <>
              <h3 className="font-bold py-4">
                {totalRecords.toLocaleString()} Total Record(s)
              </h3>
              <Table
                aria-label=""
                bottomContent={
                  investments.length > 0 ? (
                    <div className="flex w-full justify-center">
                      <Pagination
                        isCompact
                        showControls
                        showShadow
                        color="primary"
                        page={currentPage}
                        size="lg"
                        total={totalPages}
                        onChange={(page) => setCurrentPage(page)}
                      />
                    </div>
                  ) : null
                }
                bottomContentPlacement="outside"
                sortDescriptor={sortObj}
                onSortChange={(item) => {
                  setSortObj(item);
                }}
              >
                <TableHeader>
                  <TableColumn key="stock_issuer" allowsSorting>
                    COMPANY
                  </TableColumn>
                  <TableColumn key="stock_ticker" allowsSorting>
                    TICKER
                  </TableColumn>
                  <TableColumn key="stock_cusip" allowsSorting>
                    CUSIP
                  </TableColumn>
                  <TableColumn key="investor_name" allowsSorting>
                    SHAREHOLDER
                  </TableColumn>
                  <TableColumn>OTHER SHAREHOLDERS</TableColumn>
                  <TableColumn>STAKE</TableColumn>
                  <TableColumn>REPORT DATE</TableColumn>
                  <TableColumn key="form_filing_date" allowsSorting>
                    FILING DATE
                  </TableColumn>
                </TableHeader>
                <TableBody
                  emptyContent={
                    investmentsLoading ? "Loading..." : "No rows to display."
                  }
                  items={investments}
                >
                  {(item: Investment) => (
                    <TableRow key={item.stock_id}>
                      <TableCell>
                        <Link
                          className="text-cyan-500 hover:text-indigo-900 font-bold"
                          href={item.form_url}
                        >
                          {item.stock_issuer}
                        </Link>
                      </TableCell>
                      <TableCell>{item?.stock_ticker ?? "-"}</TableCell>
                      <TableCell>{item?.stock_cusip ?? "-"}</TableCell>
                      <TableCell>{item?.investor_name ?? "-"}</TableCell>
                      <TableCell>
                        {item.other_investor_names?.join(", ") ?? "-"}
                      </TableCell>
                      <TableCell>
                        {parseInt(item.stock_shares_prn_amt).toLocaleString() +
                          " " +
                          item.stock_prn_amt}
                      </TableCell>
                      <TableCell>{item.form_report_date}</TableCell>
                      <TableCell>{item.form_filing_date}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
