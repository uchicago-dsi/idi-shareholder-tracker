/**
 * The search configuration.
 */
export const SEARCH_CONFIG = Object.freeze({
  table: {
    columns: [
      {
        key: "investor_name",
        label: "Investor",
      },
      {
        key: "issuer_name",
        label: "Company",
      },
      {
        key: "stock_ticker",
        label: "Ticker",
      },
      {
        key: "security_cusip",
        label: "CUSIP",
      },
      {
        key: "security_market_value_amount_usd",
        label: "Market Value (USD)",
      },
      {
        key: "stock_number_of_shares",
        label: "Total Shares",
      },
      {
        key: "document_report_date",
        label: "Report Date",
      },
      {
        key: "investor_type",
        label: "Investor Type",
      },
    ],
    filter: {
      investorType: {
        default: "All Records",
        label: "Filter:",
        options: [
          {
            label: "All Data",
            value: "All Records",
          },
          {
            label: "Pension Funds",
            value: "Pension Fund",
          },
          {
            label: "Institutional Investors",
            value: "Institutional Investor",
          },
        ],
      },
    },
    loading: {
      messages: [
        "Loading investments...",
        "This may take a few more seconds...",
        "Please wait...",
      ],
    },
    pageSizes: {
      default: "25",
      options: [10, 25, 50, 100],
      label: "Rows per page:",
    },
    search: {
      placeholder: "E.g., AngloGold Ashanti",
      submitLabel: "Search",
    },
    sort: {
      default: {
        column: "investor_name",
        direction: "ascending",
      },
      dropdown: {
        label: "Sort by:",
        columnName: {
          default: "investor_name",
          options: [
            {
              label: "Investor",
              value: "investor_name",
            },
            {
              label: "Issuer",
              value: "issuer_name",
            },
            {
              label: "Market Value (USD)",
              value: "security_market_value_amount_usd",
            },
            {
              label: "Total Shares",
              value: "stock_number_of_shares",
            },
            {
              label: "Report Date",
              value: "document_report_date",
            },
          ],
        },
        direction: {
          default: "ascending",
          options: [
            {
              label: "Ascending",
              value: "ascending",
            },
            {
              label: "Descending",
              value: "descending",
            },
          ],
        },
      },
    },
  },
});

export type SearchConfig = typeof SEARCH_CONFIG;
