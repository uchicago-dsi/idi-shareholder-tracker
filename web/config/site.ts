/**
 * The application configuration.
 */
export const SITE_CONFIG = Object.freeze({
  title: "Shareholder Tracker",
  subtitle:
    "Discover institutional investments disclosed in national pension funds and SEC 13F filings",
  description: [
    "This database compiles the latest disclosures from 18 national pension \
          funds, as well as quarterly shareholdings reported by investors to the \
          U.S. Securities and Exchange Commission. It is updated once per quarter.",
    'To search for a company’s shareholders, type the company\'s name or CUSIP number \
          in the search bar. You can also search investments more broadly by country, \
          sector, or security identifier (e.g., ticker, CUSIP, ISIN, FIGI). The search \
          results can be viewed as a data table (default) or as a list of cards \
          with more detailed information summarized in text format. Sort the results \
          in ascending or descending order for a given column by using the "Sort by" \
          dropdown. Double click on a row in the table view or a link icon in the \
          card view to navigate to the original data source for that investment.',
  ],
  acknowledgments:
    "This resource was developed through a partnership with Inclusive Development \
    International and the University of Chicago Data Science Institute in 2025, with \
    funding generously provided by the 11th Hour Project of the Schmidt Family Foundation.",
  table: {
    columns: [
      {
        key: "investor_name",
        label: "Investor",
      },
      {
        key: "issuer_name",
        label: "Issuer",
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
    loading: {
      messages: [
        "Loading investments...",
        "This may take a few more seconds...",
        "Please wait...",
      ],
    },
    pageSizes: {
      default: "10",
      options: [
        {
          label: "10",
          value: "10",
        },
        {
          label: "25",
          value: "25",
        },
        {
          label: "50",
          value: "50",
        },
        {
          label: "100",
          value: "100",
        },
      ],
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
  navbarLinks: {
    github: "https://github.com/uchicago-dsi/idi-shareholder-tracker",
  },
  footerLinks: {
    idi: "https://www.inclusivedevelopment.net/",
    uchicagoDsi: "https://datascience.uchicago.edu/",
    quick: [
      {
        text: "DeBIT",
        url: "https://debit.datascience.uchicago.edu/",
      },
      {
        text: "PalmWatch",
        url: "https://palmwatch.inclusivedevelopment.net/",
      },
      {
        text: "Contribute",
        url: "https://github.com/uchicago-dsi/idi-shareholder-tracker",
      },
    ],
  },
});

export type SiteConfig = typeof SITE_CONFIG;
