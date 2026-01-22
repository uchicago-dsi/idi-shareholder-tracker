"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Chip } from "@heroui/chip";
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
} from "@heroui/table";
import { CalendarIcon, LandmarkIcon } from "lucide-react";

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
      isCompact
      isStriped
      classNames={{
        wrapper: ["rounded-b-none"],
        th: [
          "bg-forest",
          "text-white",
          "data-[sortable=true]:hover:text-orange-200",
        ],
        td: ["lg:text-xs"],
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
            <TableCell className="font-bold text-green-600 dark:text-green-500">
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
              {item.investor_type === "INSTITUTIONAL INVESTOR" ? (
                <Chip
                  color="warning"
                  variant="light"
                  className="p-3"
                  startContent={<LandmarkIcon size={16} />}
                >
                  <span className="text-xs font-bold normal-case">
                    Institutional Investor
                  </span>
                </Chip>
              ) : (
                <Chip
                  color="primary"
                  variant="light"
                  className="p-3"
                  startContent={
                    <CalendarIcon size={16} className="stroke-blue-400" />
                  }
                >
                  <span className="text-xs font-bold text-blue-400 normal-case">
                    Pension Fund
                  </span>
                </Chip>
              )}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
};
