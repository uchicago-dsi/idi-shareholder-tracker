"use client";

// Standard library imports
import React from "react";

// Third-party imports
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@heroui/table";

// Feature imports
import { DataColumn, Investment } from "./interfaces";

type DataTableProps = {
  columns: DataColumn[];
  investments: Investment[];
};

/**
 * A table component for displaying investments data.
 * Customizes a HeroUI Table component under the hood.
 *
 * @param props - The component props.
 * @param props.columns - The configured columns to display.
 * @param props.investments - The page of investments.
 *
 * @returns The JSX element for the table component.
 */
export const DataTable: React.FC<DataTableProps> = ({
  columns,
  investments,
}) => {
  return (
    <Table
      isStriped
      classNames={{
        wrapper: ["rounded-b-none"],
        th: [
          "bg-seagreen",
          "text-white",
          "data-[sortable=true]:hover:text-orange-200",
        ],
        sortIcon: ["text-white", "hover:text-orange-200"],
      }}
      className="font-montserrat uppercase"
      aria-label="Investments data table."
    >
      <TableHeader columns={columns}>
        {(column) => <TableColumn key={column.key}>{column.label}</TableColumn>}
      </TableHeader>
      <TableBody
        emptyContent={<p className="text-center">No rows to display.</p>}
        items={investments}
      >
        {(item: Investment) => (
          <TableRow
            key={item.id}
            onDoubleClick={() => window.open(item.url, "_blank")}
            className="hover:bg-default-200 cursor-pointer"
          >
            <TableCell>{item.investor_name}</TableCell>
            <TableCell>{item.issuer_name}</TableCell>
            <TableCell>{item.stock_ticker || "—"}</TableCell>
            <TableCell>{item.security_cusip || "—"}</TableCell>
            <TableCell>
              {item.security_market_value_amount_usd
                ? `$${item.security_market_value_amount_usd.toLocaleString()}`
                : "—"}
            </TableCell>
            <TableCell>
              {item.stock_number_of_shares
                ? item.stock_number_of_shares.toLocaleString()
                : "—"}
            </TableCell>
            <TableCell>{item.document_report_date}</TableCell>
            <TableCell>
              <p
                className={`text-xs font-bold ${item.investor_type === "PENSION FUND" ? "text-seagreen dark:text-green-400" : "text-orange-500 dark:text-orange-300"}`}
              >
                {item.investor_type}
              </p>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};
