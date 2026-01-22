// Standard library imports
import React from "react";

// Third-party imports
import { hasFlag } from "country-flag-icons";
import * as flags from "country-flag-icons/react/3x2";
import { Link } from "@heroui/react";
import { ArrowUpRightFromSquareIcon, CircleSmall } from "lucide-react";

// Feature imports
import { Investment } from "./interfaces";
import { InvestmentSummaryBuilder } from "./investment-summary";

type OrganizationNameWithFlagProps = {
  name: string;
  countryCode: string;
};

/**
 * A span element that displays an organization's name and country flag.
 *
 * @param props - The component props.
 * @param props.name - The name of the organization.
 * @param props.countryCode - The country code of the organization.
 *
 * @returns The JSX element.
 */
const OrganizationNameWithFlag: React.FC<OrganizationNameWithFlagProps> = ({
  name,
  countryCode,
}) => {
  return (
    <span className="dark:text-white">
      {hasFlag(countryCode) &&
        React.createElement(flags[countryCode as keyof typeof flags], {
          style: {
            width: 25,
            display: "inline-block",
            border: "0.5px solid gray",
          },
        })}{" "}
      {name}
    </span>
  );
};

type InvestmentTitleProps = {
  reportDate: string;
  investorName: string;
  investorCountryCode: string;
  issuerName: string;
  issuerCountryCode: string;
};

/**
 * A div element that displays an investment's report date, investor name, and issuer name.
 *
 * @param props - The component props.
 * @param props.reportDate - The report date of the investment.
 * @param props.investorName - The name of the investor.
 * @param props.investorCountryCode - The country code of the investor.
 * @param props.issuerName - The name of the issuer.
 * @param props.issuerCountryCode - The country code of the issuer.
 *
 * @returns The JSX element.
 */
const InvestmentTitle: React.FC<InvestmentTitleProps> = ({
  reportDate,
  investorName,
  investorCountryCode,
  issuerName,
  issuerCountryCode,
}) => {
  const parsedReportDate = new Date(
    reportDate + "T00:00:00",
  ).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
  return (
    <div className="font-bebas-neue text-seagreen flex flex-col items-start text-2xl uppercase lg:flex-row lg:items-start dark:text-white">
      <span>{parsedReportDate}</span>{" "}
      <span className="hidden lg:inline">|</span>{" "}
      <span>
        <OrganizationNameWithFlag
          name={investorName}
          countryCode={investorCountryCode}
        />{" "}
        <span className="text-seagreen dark:text-white">investment in</span>{" "}
        <OrganizationNameWithFlag
          name={issuerName}
          countryCode={issuerCountryCode}
        />{" "}
        <Link
          className="inline-flex lg:hidden"
          isExternal
          showAnchorIcon
          anchorIcon={
            <ArrowUpRightFromSquareIcon
              size={18}
              className="stroke-3 text-green-700 dark:text-green-300"
            />
          }
        ></Link>
      </span>
    </div>
  );
};

type SecurityMetadataLineProps = {
  ticker: string;
  cusip: string;
  figi: string;
  isin: string;
};

/**
 * A div element that displays the ticker, CUSIP, FIGI, and/or ISIN of the security if availble.
 *
 * @param props.ticker - The ticker symbol of the investment.
 * @param props.cusip - The CUSIP number of the investment.
 * @param props.figi - The FIGI number of the investment.
 * @param props.isin - The ISIN number of the investment.
 *
 * @returns The JSX element.
 */
const SecurityMetadataLine: React.FC<SecurityMetadataLineProps> = ({
  ticker,
  cusip,
  figi,
  isin,
}) => {
  const identifiers = [];
  if (ticker !== "") identifiers.push(`TICKER: ${ticker}`);
  if (cusip !== "") identifiers.push(`CUSIP: ${cusip}`);
  if (figi !== "") identifiers.push(`FIGI: ${figi}`);
  if (isin !== "") identifiers.push(`ISIN: ${isin}`);

  return (
    <div className="font-montserrat flex flex-col items-start gap-2 text-sm font-bold uppercase lg:flex-row lg:items-center">
      {identifiers.length === 0 ? (
        <p>NO SECURITY CODES AVAILABLE</p>
      ) : (
        identifiers.map((id, idx) => (
          <span key={idx} className="flex flex-row items-center gap-2">
            {id}{" "}
            {idx < identifiers.length - 1 && (
              <CircleSmall
                size={12}
                className="fill-seagreen hidden stroke-0 lg:block dark:fill-green-300"
              />
            )}
          </span>
        ))
      )}
    </div>
  );
};

type InvestmentCardHeaderProps = {
  reportDate: string;
  investorName: string;
  investorCountryCode: string;
  issuerName: string;
  issuerCountryCode: string;
  ticker: string;
  cusip: string;
  figi: string;
  isin: string;
  url: string;
};

/**
 * The header for an {@link InvestmentCard}.
 *
 * @param props - The component props.
 * @param props.reportDate - The report date of the investment.
 * @param props.investorName - The name of the investor.
 * @param props.investorCountryCode - The country code of the investor.
 * @param props.issuerName - The name of the issuer.
 * @param props.issuerCountryCode - The country code of the issuer.
 * @param props.ticker - The ticker symbol of the investment.
 * @param props.cusip - The CUSIP number of the investment.
 * @param props.figi - The FIGI number of the investment.
 * @param props.isin - The ISIN number of the investment.
 * @param props.url - The URL to the investment source document.
 *
 * @returns The JSX element.
 */
const InvestmentCardHeader: React.FC<InvestmentCardHeaderProps> = ({
  reportDate,
  investorName,
  investorCountryCode,
  issuerName,
  issuerCountryCode,
  ticker,
  cusip,
  figi,
  isin,
  url,
}) => {
  return (
    <div className="flex w-full flex-col gap-2 p-3 lg:gap-0">
      {/** FIRST ROW - TITLE AND DATA SOURCE LINK */}
      <div className="lg: flex flex-col justify-between lg:flex-row lg:items-center">
        {/** TITLE */}
        <InvestmentTitle
          investorName={investorName}
          investorCountryCode={investorCountryCode}
          issuerName={issuerName}
          issuerCountryCode={issuerCountryCode}
          reportDate={reportDate}
        />

        {/** DESKTOP-ONLY LINK */}
        <Link
          href={url}
          className="font-montserrat hidden font-bold text-green-700 hover:text-orange-400 md:block dark:text-green-500 dark:hover:text-orange-200"
          isExternal
          showAnchorIcon
          anchorIcon={
            <ArrowUpRightFromSquareIcon
              size={20}
              className="stroke-seagreen stroke-3 dark:stroke-green-200 dark:stroke-2"
            />
          }
          size="lg"
        ></Link>
      </div>

      {/** SECOND ROW - SECURITY CODES */}
      <SecurityMetadataLine
        ticker={ticker}
        cusip={cusip}
        figi={figi}
        isin={isin}
      />
    </div>
  );
};

type InvestmentCardBodyProps = {
  investment: Investment;
};

/**
 * A component for displaying the investment body content.
 * Takes an investment object and creates a summary string,
 * as well as a footnote detailing the conversion rate of the
 * investment value to USD when applicable.
 *
 * @param props - The component props.
 * @param props.investment - The investment object.
 *
 * @returns The JSX element.
 */
const InvestmentCardBody: React.FC<InvestmentCardBodyProps> = ({
  investment,
}) => {
  const summaryBuilder = new InvestmentSummaryBuilder(investment);
  return (
    <div className="font-montserrat flex flex-col gap-4 px-3 pb-5 uppercase lg:text-left">
      <ul className="marker:text-seagreen list-disc px-4 text-sm marker:text-lg dark:marker:text-green-300">
        <li>{summaryBuilder.summarySentence}</li>
        {summaryBuilder.conversionRateSentence && (
          <li>{summaryBuilder.conversionRateSentence}</li>
        )}
        {summaryBuilder.investmentAuthoritySentence && (
          <li>{summaryBuilder.investmentAuthoritySentence}</li>
        )}
        {summaryBuilder.stockPercentageSentence && (
          <li>{summaryBuilder.stockPercentageSentence}</li>
        )}
        {summaryBuilder.vintageYearSentence && (
          <li>{summaryBuilder.vintageYearSentence}</li>
        )}
      </ul>
    </div>
  );
};

type InvestmentCardFooterProps = {
  dataSource: string;
  lastAccessed: string;
};

/**
 * A div that displays the data source of the investment and the last accessed date.
 *
 * @param props - The component props.
 * @param props.dataSource - The name of the investment data source (e.g., "U.S. Securities and Exchange Commission").
 * @param props.lastAccessed - The date the data source was accessed for data collection. Formatted as "YYYY-mm-dd".
 *
 * @returns The JSX element.
 */
const InvestmentCardFooter: React.FC<InvestmentCardFooterProps> = ({
  dataSource,
  lastAccessed,
}) => {
  const parsedAccessDate = new Date(
    lastAccessed + "T00:00:00",
  ).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  return (
    <div className="font-montserrat dark:bg-forest flex flex-col gap-4 rounded-b-xl bg-neutral-100 p-3 text-left text-xs uppercase lg:flex-row lg:justify-between dark:font-bold dark:text-white">
      <p className="flex flex-col lg:flex-row lg:gap-1">
        <span>Source:</span>
        <span>{dataSource}</span>
      </p>
      <p className="flex flex-col lg:flex-row lg:gap-1">
        <span>Last Accessed:</span>
        <span>{parsedAccessDate}</span>
      </p>
    </div>
  );
};

type InvestmentCardProps = {
  investment: Investment;
};

/**
 * A card summarizing an {@link Investment} object. Contains a header, body, and footer.
 *
 * @param props - The component props.
 * @param props.investment - The investment.
 *
 * @returns The JSX element.
 */
export const InvestmentCard: React.FC<InvestmentCardProps> = ({
  investment,
}) => {
  return (
    <div className="dark:bg-default-100 border-default-300 dark:shadow-default-600 flex w-full flex-col rounded-xl border border-1 shadow-sm">
      <InvestmentCardHeader
        reportDate={investment.document_report_date}
        investorName={investment.investor_name}
        investorCountryCode={investment.investor_country_code}
        issuerName={investment.issuer_name}
        issuerCountryCode={investment.issuer_country_code}
        ticker={investment.stock_ticker}
        cusip={investment.security_cusip}
        figi={investment.security_figi}
        isin={investment.security_isin}
        url={investment.url}
      />
      <InvestmentCardBody investment={investment} />
      <InvestmentCardFooter
        dataSource={investment.source}
        lastAccessed={investment.last_accessed_date}
      />
    </div>
  );
};
