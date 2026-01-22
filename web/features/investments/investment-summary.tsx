// Feature imports
import { Investment } from "./interfaces";

/**
 * A class for building investment summary strings.
 */
export class InvestmentSummaryBuilder {
  /**
   * A private reference to the investment being summarized.
   */
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
   * Determines whether the investment was successfully converted to USD during processing.
   */
  private get hasConvertedMarketValue(): boolean {
    return !(
      !this._inv.security_market_value_conversion_rate ||
      this._inv.security_market_value_conversion_rate == 0 ||
      this._inv.security_market_value_conversion_rate == 1
    );
  }

  /**
   * Generates a phrase about the action taken by the investor. Uses the investment type and value.
   */
  private get investorActionPhrase(): string {
    if (this._inv.security_type === "PRIVATE EQUITY FUND") {
      return `invested ${this.marketValuePhrase} in private equity fund`;
    } else if (
      this._inv.security_market_value_amount_usd &&
      this._inv.security_market_value_amount_usd > 0
    ) {
      return `purchased ${this.numberOfSharesPhrase} share${this._inv.stock_number_of_shares === 1 ? "" : "s"} with a total market value of  ${this.marketValuePhrase} in`;
    } else {
      return `purchased ${this.numberOfSharesPhrase} share${this._inv.stock_number_of_shares === 1 ? "" : "s"} in`;
    }
  }

  /**
   * Generates a phrase about the location of the investor.
   */
  private get investorLocationPhrase(): string {
    if (this._inv.investor_country_name && this._inv.investor_region_name) {
      return `(${this._inv.investor_region_name}, ${this._inv.investor_country_name})`;
    } else if (this._inv.investor_country_name) {
      return `(${this._inv.investor_country_name})`;
    } else {
      return "";
    }
  }

  /**
   * Generates a phrase about the location of the issuer.
   */
  private get issuerLocationPhrase(): string {
    return this._inv.issuer_country_name
      ? `(${this._inv.issuer_country_name})`
      : "";
  }

  /**
   * Generates a phrase about the economic sector of the stock issuer.
   */
  private get issuerSectorPhrase(): string {
    return this._inv.issuer_sector
      ? `, a company within the ${this._inv.issuer_sector} sector`
      : "";
  }

  /**
   * Generates a phrase about the market value of the security.
   */
  private get marketValuePhrase(): string {
    return this._inv.security_market_value_amount_usd
      ? `$${this._inv.security_market_value_amount_usd.toLocaleString()} USD`
      : "";
  }

  /**
   * Generates a phrase about the number of shares purchased.
   */
  private get numberOfSharesPhrase(): string {
    return this._inv.stock_number_of_shares
      ? `${this._inv.stock_number_of_shares.toLocaleString()}`
      : "";
  }

  /**
   * Generates a phrase about the original market value of the shares prior to their conversion to USD.
   */
  get originalMarketValuePhrase(): string {
    return this._inv.security_market_value_amount &&
      this._inv.security_market_value_currency_code &&
      this._inv.security_market_value_currency_code !== "USD"
      ? `${(this._inv.security_market_value_amount * this.parsedMultiplier).toLocaleString()} ${this._inv.security_market_value_currency_code}`
      : "";
  }

  /**
   * Converts the security market value multiplier from a string to an integer.
   * If the multiplier is not recognized, throws an error.
   */
  private get parsedMultiplier(): number {
    switch (this._inv.security_market_value_multiplier) {
      case "x1":
        return 1;
      case "x100":
        return 100;
      case "x1_000":
        return 1000;
      case "x10_000":
        return 10_000;
      case "x100_000":
        return 100_000;
      case "x1_000_000":
        return 1_000_000;
      default:
        throw Error(
          `Unknown multiplier: ${this._inv.security_market_value_multiplier}.`,
        );
    }
  }

  /**
   * Generates a sentence about the conversion of the market value to USD.
   */
  get conversionRateSentence(): string {
    return this.hasConvertedMarketValue
      ? `The market value was converted from ${this.originalMarketValuePhrase} at a rate of ` +
          `${this._inv.security_market_value_conversion_rate} for the given ` +
          `report date of ${this._inv.document_report_date}.`
      : "";
  }

  /**
   * Generates a sentence about the voting authority of the shares.
   */
  get investmentAuthoritySentence(): string {
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
   * Generates a sentence summarizing the basic details of the investment.
   */
  get summarySentence(): string {
    const phrases = [
      this._inv.investor_name,
      this.investorLocationPhrase,
      this.investorActionPhrase,
      this._inv.issuer_name,
      this.issuerLocationPhrase,
      this.issuerSectorPhrase,
      ".",
    ];
    return phrases
      .filter((phrase) => phrase !== "")
      .join(" ")
      .replace(/\s+\./, ".")
      .replace(/\s+,/, ",");
  }

  /**
   * Generates a sentence about the percentage ownership and percentage voting power of the shares.
   */
  get stockPercentageSentence(): string {
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
   * Generates a sentence about the vintage year of a private equity fund.
   */
  get vintageYearSentence(): string {
    return this._inv.security_vintage_year
      ? `The fund had a vintage year of ${this._inv.security_vintage_year}.`
      : "";
  }

  /**
   * Generates a sentence about the authority of the investment.
   */
  get votingAuthoritySentence(): string {
    const phrases = [
      this.investmentAuthoritySentence,
      this.stockPercentageSentence,
      this.vintageYearSentence,
    ];
    return phrases
      .filter((phrase) => phrase !== "")
      .join(" ")
      .replace(/\s+\./, ".")
      .replace(/\s+,/, ",");
  }
}
