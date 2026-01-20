// Feature imports
import { Investment } from "./interfaces";

/**
 * A class for building investment summary strings.
 */
export class InvestmentSummaryBuilder {
  /** The investment being summarized. */
  private readonly _inv: Investment;

  /**
   * The constructor.
   *
   * @param investment - The investment to summarize
   */
  constructor(investment: Investment) {
    this._inv = investment;
  }

  /**
   * Generates a statement about the location of the investor.
   */
  get investorLocation() {
    if (this._inv.investor_country_name && this._inv.investor_region_name) {
      return `(${this._inv.investor_region_name}, ${this._inv.investor_country_name})`;
    } else if (this._inv.investor_country_name) {
      return `(${this._inv.investor_country_name})`;
    } else {
      return "";
    }
  }

  /**
   * Generates a statement about the location of the issuer.
   */
  get issuerLocation() {
    if (this._inv.issuer_country_name) {
      return `(${this._inv.issuer_country_name})`;
    } else {
      return "";
    }
  }

  /**
   * Generates a statement about the number of shares purchased.
   */
  get financialAmount() {
    return this._inv.stock_number_of_shares
      ? `${this._inv.stock_number_of_shares.toLocaleString()}`
      : "";
  }

  /**
   * Generates an asterisk when the market value has been converted to USD and an empty string otherwise.
   */
  get hasConvertedMarketValue() {
    return !(
      this._inv.security_market_value_conversion_rate == 0 ||
      this._inv.security_market_value_conversion_rate == 1
    );
  }

  /**
   * Generates a statement about the market value of the shares.
   */
  get marketValue() {
    return this._inv.security_market_value_amount_usd
      ? `$${this._inv.security_market_value_amount_usd.toLocaleString()} USD`
      : "";
  }

  /**
   * Generates a statement about the economic sector of the stock issuer.
   */
  get issuerSector() {
    return this._inv.issuer_sector
      ? `, a company within the ${this._inv.issuer_sector} sector`
      : "";
  }

  /**
   * Generates a statement about the original market value of the shares prior to their conversion to USD.
   */
  get originalAmount() {
    return this._inv.security_market_value_amount &&
      this._inv.security_market_value_currency_code &&
      this._inv.security_market_value_currency_code !== "USD"
      ? `${this._inv.security_market_value_amount.toLocaleString()} ${this._inv.security_market_value_currency_code}`
      : "";
  }

  /**
   * Generates a statement about the voting authority of the shares.
   */
  get investmentAuthoritySentence() {
    const statements = [];
    if (this._inv.stock_voting_auth_sole) {
      statements.push(
        `${this._inv.stock_voting_auth_sole.toLocaleString()} had sole voting authority rights`,
      );
    }
    if (this._inv.stock_voting_auth_shared) {
      statements.push(
        `${this._inv.stock_voting_auth_shared.toLocaleString()} had shared voting authority rights`,
      );
    }
    if (this._inv.stock_voting_auth_none) {
      statements.push(
        `${this._inv.stock_voting_auth_none.toLocaleString()} had no voting authority rights`,
      );
    }
    if (statements.length == 1) {
      return `Of the shares, ${statements[0]}.`;
    } else if (statements.length == 2) {
      return `Of the shares, ${statements[0]} while ${statements[1]}.`;
    } else if (statements.length == 3) {
      return `Of the shares, ${statements[0]}, ${statements[1]}, and ${statements[2]}.`;
    } else {
      return "";
    }
  }

  /**
   * Generates a statement about the percentage ownership and percentage voting power of the shares.
   */
  get stockPercentage() {
    if (
      this._inv.stock_percent_ownership &&
      this._inv.stock_percent_voting_power
    ) {
      return `The investor's shares give it ${this._inv.stock_percent_ownership * 1}% ownership and ${this._inv.stock_percent_voting_power * 1}% voting power.`;
    } else if (this._inv.stock_percent_ownership) {
      return `The investor's shares give it ${this._inv.stock_percent_ownership * 1}% ownership.`;
    } else if (this._inv.stock_percent_voting_power) {
      return `The investor's shares give it ${this._inv.stock_percent_voting_power * 1}% voting power.`;
    } else {
      return "";
    }
  }

  /**
   * Generates a statement about the action taken by the investor using the investment type and value.
   */
  get investorAction() {
    if (this._inv.security_type === "PRIVATE EQUITY FUND") {
      return `invested ${this.marketValue} in private equity fund`;
    } else {
      return `purchased ${this.financialAmount} share${this._inv.stock_number_of_shares === 1 ? "" : "s"} with a total market value of  ${this.marketValue} in`;
    }
  }

  /**
   * Generates a statement about the vintage year of a private equity fund.
   */
  get vintageYear() {
    if (this._inv.security_vintage_year) {
      return `The fund had a vintage year of ${this._inv.security_vintage_year}.`;
    } else {
      return "";
    }
  }

  /**
   * Generates a summary of the investment from its properties.
   */
  get summarySentence() {
    const phrases = [
      this._inv.investor_name,
      this.investorLocation,
      this.investorAction,
      this._inv.issuer_name,
      this.issuerLocation,
      this.issuerSector,
      ".",
    ];
    return phrases
      .filter((phrase) => phrase !== "")
      .join(" ")
      .replace(/\s+\./, ".")
      .replace(/\s+,/, ",");
  }

  get votingAuthoritySentence() {
    const phrases = [
      this.investmentAuthoritySentence,
      this.stockPercentage,
      this.vintageYear,
    ];
    return phrases
      .filter((phrase) => phrase !== "")
      .join(" ")
      .replace(/\s+\./, ".")
      .replace(/\s+,/, ",");
  }

  /**
   * Generates a footnote about the conversion of the market value to USD.
   */
  get conversionRateFootnote() {
    return (
      `The market value was converted from ${this.originalAmount} at a rate of ` +
      `${this._inv.security_market_value_conversion_rate} for the given ` +
      `report date of ${this._inv.document_report_date}.`
    );
  }
}
