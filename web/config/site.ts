export const SITE_CONFIG = Object.freeze({
  title: "Shareholder Tracker",
  subtitle:
    "Discover institutional investments disclosed in national pension funds and SEC 13F filings",
  description:
    "This database compiles the latest disclosures from 18 national pension \
          funds, as well as quarterly shareholdings reported by investors to the \
          U.S. Securities and Exchange Commission. To search for a company’s \
          shareholders, type the name of the company or its ticker symbol or \
          CUSIP number in the search bar. You can also search for shareholders \
          by name. All search results can be sorted in ascending or descending \
          order by clicking on the select column heading.",
  acknowledgments:
    "This resource was developed through a partnership with Inclusive Development \
    International and the University of Chicago Data Science Institute in 2025, with \
    funding generously provided by the 11th Hour Project of the Schmidt Family Foundation.",
  table: {
    columns: [
      {
        key: "investor_name",
        label: "Investor",
        allowsSorting: true,
      },
      {
        key: "issuer_name",
        label: "Issuer",
        allowsSorting: true,
      },
      {
        key: "stock_ticker",
        label: "Ticker",
        allowsSorting: false,
      },
      {
        key: "security_cusip",
        label: "CUSIP",
        allowsSorting: false,
      },
      {
        key: "security_market_value_amount_usd",
        label: "Market Value (USD)",
        allowsSorting: true,
      },
      {
        key: "stock_number_of_shares",
        label: "Total Shares",
        allowsSorting: true,
      },
      {
        key: "document_report_date",
        label: "Report Date",
        allowsSorting: true,
      },
      {
        key: "investor_type",
        label: "Investor Type",
        allowsSorting: false,
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
      default: 10,
      options: [10, 25, 50, 100],
      label: "Rows per page:",
    },
    search: {
      placeholder: "E.g., AngloGold Ashanti",
    },
    sort: {
      default: {
        column: "issuer_name",
        direction: "ascending",
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
