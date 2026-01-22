"use client";

// Standard library imports
import React from "react";

// Third-party imports
import { Link } from "@heroui/react";

// Feature imports
import { InvestmentSearchWidget } from "@/features/investments";

/**
 * The application homepage. Renders a navigation bar, title and subtitle, description, search widget, and footer.
 */
const Home: React.FC = () => {
  return (
    <div className="flex w-full flex-col gap-8">
      {/** HEADER */}
      <div className="flex w-full flex-col gap-8">
        {/** TITLE BLOCK */}
        <div className="flex flex-col items-center text-center">
          <h1 className="font-bebas-neue text-4xl lg:text-6xl">
            Shareholder Tracker
          </h1>
          <h2 className="font-montserrat text-zinc-500 lg:text-xl dark:text-zinc-400">
            Search for the shareholders of publicly traded companies
          </h2>
        </div>

        {/** DESCRIPTION */}
        <div className="font-montserrat flex flex-col gap-2 text-base">
          <p>
            This database allows you to see the shareholders of thousands of
            publicly traded companies based around the world. It compiles public
            disclosures made by more than 4,200 investors showing the shares
            that they own. For more information about the database, and the
            sources it scrapes, see the{" "}
            <Link
              href="/about"
              className="decoration-seagreen inline text-base font-bold text-black underline underline-offset-4 dark:text-white dark:decoration-green-300"
            >
              About
            </Link>{" "}
            page.
          </p>
          <p>
            To search for a company’s shareholders, type the company&#39;s name
            or CUSIP number in the search bar. You can also search investments
            more broadly by country, sector, or security identifier (e.g.,
            ticker, CUSIP, ISIN, FIGI). The search results can be viewed as a
            data table (default) or as a list of cards with more detailed
            information summarized in text format. Sort the results in ascending
            or descending order for a given column by using the &quot;Sort
            by&quot; dropdown. Double click on a row in the table view or a link
            icon in the card view to navigate to the original data source for
            that investment. Finally, to download your current search results as
            a CSV file, click on the download button. At this time, a maximum of
            10,000 records can be downloaded at once through the interface. To
            access larger selections of data, please visit the{" "}
            <Link
              href="/downloads"
              className="decoration-seagreen inline text-base font-bold text-black underline underline-offset-4 dark:text-white dark:decoration-green-300"
            >
              Downloads
            </Link>{" "}
            page.
          </p>
        </div>
      </div>

      {/** SEARCH WIDGET */}
      <InvestmentSearchWidget />
    </div>
  );
};

export default Home;
